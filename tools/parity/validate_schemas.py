#!/usr/bin/env python3
"""Validate contracts/schemas/*.schema.json and the golden fixtures.

Checks performed
----------------
1. Every schema is a valid JSON Schema draft 2020-12 document.
2. The methods listed by the schemas match ``contracts/methods.md`` exactly
   (and the events table of section 3.10 matches ``events.schema.json``).
3. Every fixture JSON that embeds an ``rpc`` object is validated as a contract
   call: ``{method, params, result}`` built from ``rpc.result`` /
   ``rpc.result_from`` (JSON pointer) or ``{method, params, error}`` for error
   fixtures; ``rpc.calls_from`` validates a list of calls (used by the sweep).
4. Fixtures carry the required document keys for their ``id``.

Usage:
    uv run python tools/parity/validate_schemas.py
    uv run python tools/parity/validate_schemas.py --fixtures contracts/fixtures

Exit code 0 = all good, 1 = validation errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]

# Required top-level keys per fixture id (contract freeze guard: adding a fixture
# with a new id requires updating this table, which keeps the review honest).
FIXTURE_SCHEMA = {
    "adiabatic_knsu": ("inputs", "outputs", "rpc"),
    "adiabatic_error": ("inputs", "error", "rpc"),
    "engine_knsu": ("inputs", "arrays", "console", "stop_reason", "expected", "rpc"),
    "engine_knsu_smoke": ("inputs", "arrays", "console", "stop_reason", "expected", "rpc"),
    "nozzle_bn1": ("inputs", "result", "rpc"),
    "nozzle_bn1_op_points": ("points", "rpc"),
    "cad_bn1_sketches": ("settings", "sketches"),
    "tests_replay": ("lines", "records", "csv", "rpc"),
}

METHOD_RE = re.compile(r"^\|\s*`([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)`", re.MULTILINE)
EVENT_RE = re.compile(r"^\|\s*`([a-z][a-z0-9_]*)`", re.MULTILINE)
EVENT_HEADING = "### 3.10"
METHOD_CONST_RE = re.compile(r'^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$')


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checks = 0

    def check(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.errors.append(message)
        return condition

    def fail(self, message: str) -> None:
        self.checks += 1
        self.errors.append(message)


def load_schemas(schemas_dir: Path) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for path in sorted(schemas_dir.glob("*.schema.json")):
        with path.open(encoding="utf-8") as fh:
            schema = json.load(fh)
        schema_id = schema.get("$id")
        if not schema_id:
            raise SystemExit(f"schema {path} has no $id")
        schemas[path.name] = schema
    return schemas


def build_registry(schemas: dict[str, dict]) -> Registry:
    resources = []
    for schema in schemas.values():
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def collect_schema_methods(schemas: dict[str, dict]) -> dict[str, str]:
    """Map method name -> schema file name, scanning the oneOf/$defs const values."""
    methods: dict[str, str] = {}
    for filename, schema in schemas.items():
        if filename in ("envelope.schema.json", "events.schema.json"):
            continue
        for definition in schema.get("$defs", {}).values():
            method = definition.get("properties", {}).get("method", {}).get("const")
            if isinstance(method, str) and METHOD_CONST_RE.match(method):
                previous = methods.get(method)
                if previous is not None and previous != filename:
                    raise SystemExit(f"method {method} declared in both {previous} and {filename}")
                methods[method] = filename
    return methods


def collect_event_names(schemas: dict[str, dict]) -> set[str]:
    events = schemas.get("events.schema.json", {})
    names = set()
    for definition in events.get("$defs", {}).values():
        params = definition.get("allOf", [{}, {}])[1].get("properties", {}).get("params", {})
        name = params.get("properties", {}).get("name", {}).get("const")
        if isinstance(name, str):
            names.add(name)
    return names


def documented_methods(methods_md: Path) -> set[str]:
    text = methods_md.read_text(encoding="utf-8")
    return set(METHOD_RE.findall(text))


def documented_events(methods_md: Path) -> set[str]:
    lines = methods_md.read_text(encoding="utf-8").splitlines()
    names: set[str] = set()
    inside = False
    for line in lines:
        if line.startswith(EVENT_HEADING):
            inside = True
            continue
        if inside and line.startswith("#"):
            break
        if inside:
            match = EVENT_RE.match(line)
            if match:
                names.add(match.group(1))
    return names


def resolve_pointer(document, pointer: str):
    if not pointer.startswith("#"):
        raise ValueError(f"only local JSON pointers are supported, got {pointer!r}")
    if pointer in ("#", "#/"):
        return document
    current = document
    for token in pointer[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    return current


def validate_fixture(
    path: Path,
    document: dict,
    validator_for_schema,
    report: ValidationReport,
) -> None:
    fixture_id = document.get("id", path.stem)
    report.check("id" in document, f"{path.name}: missing 'id'")
    report.check("tag" in document, f"{path.name}: missing 'tag'")
    report.check("provenance" in document, f"{path.name}: missing 'provenance'")
    required = FIXTURE_SCHEMA.get(fixture_id)
    if required is None:
        report.fail(f"{path.name}: unknown fixture id {fixture_id!r}; add it to FIXTURE_SCHEMA")
        return
    for key in required:
        report.check(key in document, f"{path.name}: missing required key {key!r} (id={fixture_id})")

    rpc = document.get("rpc")
    if not rpc:
        return
    method = rpc.get("method")
    schema = validator_for_schema(method)
    if schema is None:
        report.fail(f"{path.name}: rpc.method {method!r} is not declared by any namespace schema")
        return

    if "error" in rpc:
        triple = {"method": method, "params": rpc.get("params", {}), "error": rpc["error"]}
        _validate(report, path, schema, triple)
        return
    if "calls_from" in rpc:
        calls = resolve_pointer(document, rpc["calls_from"])
        base = rpc.get("params_base", {})
        report.check(isinstance(calls, list) and calls, f"{path.name}: {rpc['calls_from']} is not a non-empty list")
        for index, call in enumerate(calls if isinstance(calls, list) else []):
            params = {**base, **call.get("params", {})}
            triple = {"method": method, "params": params, "result": call.get("result")}
            _validate(report, path, schema, triple, suffix=f" call[{index}]")
        return
    if "result_from" in rpc:
        result = resolve_pointer(document, rpc["result_from"])
    elif "result" in rpc:
        result = rpc["result"]
    else:
        report.fail(f"{path.name}: rpc has no result/result_from/error/calls_from")
        return
    triple = {"method": method, "params": rpc.get("params", {}), "result": result}
    _validate(report, path, schema, triple)


def _leaf_errors(error, limit: int = 3) -> list[tuple[str, str]]:
    """Flatten a jsonschema error tree into (json path, message) leaves."""
    leaves: list[tuple[str, str]] = []
    stack = [error]
    while stack and len(leaves) < limit * 4:
        current = stack.pop(0)
        if current.context:
            stack.extend(current.context)
            continue
        path = "/".join(str(part) for part in current.absolute_path) or "<root>"
        leaves.append((path, current.message))
    # oneOf/anyOf parent messages embed the whole instance; drop them when leaves exist
    trimmed = [(path, message) for path, message in leaves if not message.startswith("{")]
    return (trimmed or leaves)[:limit]


def _validate(report: ValidationReport, path: Path, validator: Draft202012Validator, triple: dict, suffix: str = "") -> None:
    errors = sorted(validator.iter_errors(triple), key=lambda err: list(err.absolute_path))
    if errors:
        for location, message in _leaf_errors(errors[0]):
            if len(message) > 300:
                message = message[:300] + "..."
            report.fail(f"{path.name}{suffix}: schema error at {location}: {message}")
    else:
        report.checks += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--schemas", default=str(REPO_ROOT / "contracts" / "schemas"))
    parser.add_argument("--fixtures", default=str(REPO_ROOT / "contracts" / "fixtures"))
    parser.add_argument("--methods", default=str(REPO_ROOT / "contracts" / "methods.md"))
    args = parser.parse_args(argv)

    schemas_dir = Path(args.schemas)
    fixtures_dir = Path(args.fixtures)
    methods_md = Path(args.methods)
    report = ValidationReport()

    # 1. schemas are valid draft 2020-12
    schemas = load_schemas(schemas_dir)
    report.check(len(schemas) >= 11, f"expected >=11 schemas, found {len(schemas)}")
    for filename, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
            report.checks += 1
        except jsonschema.SchemaError as exc:  # pragma: no cover - defensive
            report.fail(f"{filename}: invalid JSON Schema: {exc.message}")
    registry = build_registry(schemas)

    # 2. methods and events match methods.md
    schema_methods = collect_schema_methods(schemas)
    doc_methods = documented_methods(methods_md)
    missing = sorted(doc_methods - set(schema_methods))
    extra = sorted(set(schema_methods) - doc_methods)
    report.check(not missing, f"methods.md documents methods missing from schemas: {missing}")
    report.check(not extra, f"schemas declare methods not documented in methods.md: {extra}")

    schema_events = collect_event_names(schemas)
    doc_events = documented_events(methods_md)
    missing_events = sorted(doc_events - schema_events)
    extra_events = sorted(schema_events - doc_events)
    report.check(not missing_events, f"methods.md documents events missing from events.schema.json: {missing_events}")
    report.check(not extra_events, f"events.schema.json declares events not documented: {extra_events}")

    # envelope self-test
    envelope_validator = Draft202012Validator(schemas["envelope.schema.json"], registry=registry)
    ready_example = {
        "method": "event",
        "params": {"name": "ready", "version": "0.2.0", "pid": 1234},
    }
    report.check(
        not list(envelope_validator.iter_errors(ready_example)),
        "envelope schema rejects a ready notification example",
    )
    events_validator = Draft202012Validator(schemas["events.schema.json"], registry=registry)
    report.check(
        not list(events_validator.iter_errors(ready_example)),
        "events schema rejects a ready notification example",
    )

    def validator_for_schema(method: str | None):
        filename = schema_methods.get(method or "")
        if not filename:
            return None
        return Draft202012Validator(schemas[filename], registry=registry)

    # 3/4. fixtures
    if fixtures_dir.is_dir():
        fixture_files = sorted(fixtures_dir.glob("*.json"))
        report.check(bool(fixture_files), f"no fixtures found in {fixtures_dir}")
        for path in fixture_files:
            with path.open(encoding="utf-8") as fh:
                document = json.load(fh)
            validate_fixture(path, document, validator_for_schema, report)
        # csv fixtures referenced by cad_bn1_sketches
        sketches = fixtures_dir / "cad_bn1_sketches.json"
        if sketches.is_file():
            with sketches.open(encoding="utf-8") as fh:
                document = json.load(fh)
            for kind, name in document.get("csv", {}).get("files", {}).items():
                report.check((fixtures_dir / name).is_file(), f"cad_bn1_sketches expects {name} ({kind})")

    if report.errors:
        print(f"FAIL: {len(report.errors)} error(s) after {report.checks} checks")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"OK: {report.checks} checks passed ({len(schemas)} schemas, {len(schema_methods)} methods, "
          f"{len(schema_events)} events, fixtures in {fixtures_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
