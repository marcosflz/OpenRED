"""OpenRED — verifica una migración de datos legacy sobre el motor empaquetado.

Arranca el sidecar del bundle (``artifacts/engine-bundle``) apuntando a la carpeta de datos y
al directorio de trabajo indicados, y comprueba por JSON-RPC que la BD y el ``workingDirectory``
migrados se leen y se usan igual que en el legacy.

Comprueba (según lo que exista):

* ``workspace.set_dir`` detecta ``config.json`` y crea lo que falte.
* ``workspace.list`` de ``Engines``/``Nozzles``/``Sketches``/``Tests`` (comparado con ``--legacy``
  cuando se indica).
* ``db.propellants.list`` y ``db.components.list`` (comparados con ``<legacy>/../database.db``).
* ``engine.load``/``nozzle.load`` de los ficheros migrados.
* ``nozzle.calculate`` y ``cad.export`` contra los fixtures dorados (``contracts/fixtures``).
* ``testbed.checklist.load``.
* Persistencia del workdir en ``<data>/config/app.json`` entre dos arranques del motor.

Efectos secundarios: selecciona (y persiste) el directorio de trabajo y escribe/borra los CSV
``OPENRED_*_CAD.csv`` en ``<workdir>/Sketches`` al comprobar el CAD.

Uso:
    python tools/migration/verify_migration.py
    python tools/migration/verify_migration.py --workdir "D:\\datos\\OpenRED" --legacy "D:\\legacy\\workingDirectory"
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

FAILURES: list[str] = []
CHECKS = 0
KINDS = ("Engines", "Nozzles", "Sketches", "Tests")


def check(ok: bool, label: str, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        FAILURES.append(f"{label} {detail}".strip())


def close_enough(actual: object, expected: object, rel: float = 1e-9, abs_tol: float = 1e-6) -> bool:
    try:
        left, right = float(actual), float(expected)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return actual == expected
    return abs(left - right) <= max(abs(right) * rel, abs_tol)


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip("\n")


class Engine:
    """Cliente JSON-RPC mínimo por stdio (mismo protocolo que contracts/methods.md)."""

    def __init__(self, python: Path, bundle: Path, data_dir: Path) -> None:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONNOUSERSITE": "1",
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLBACKEND": "Agg",
                "MPLCONFIGDIR": str(data_dir / "mpl-data"),
                "OPENRED_DATA_DIR": str(data_dir),
                "OPENRED_RESOURCE_DIR": str(bundle),
            }
        )
        env.pop("OPENRED_WORKDIR", None)
        self.console: list[str] = []
        self.proc = subprocess.Popen(
            [str(python), "-s", "-X", "utf8", "-m", "openred_engine"],
            cwd=str(bundle),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.seq = 0

    def call(self, method: str, params: dict | None = None):
        self.seq += 1
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps({"id": self.seq, "method": method, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        while True:
            assert self.proc.stdout is not None
            line = self.proc.stdout.readline()
            if not line:
                stderr = self.proc.stderr.read() if self.proc.stderr else ""
                raise RuntimeError(f"el motor cerró stdout esperando {method}:\n{stderr[-2000:]}")
            message = json.loads(line)
            if message.get("method") == "event":
                if message["params"].get("name") == "console":
                    self.console.append(message["params"]["line"])
                continue
            if message.get("id") == self.seq:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def close(self) -> None:
        try:
            self.call("app.shutdown")
        except Exception:
            pass
        try:
            self.proc.wait(5)
        except Exception:
            self.proc.kill()


def legacy_names(legacy: Path, kind: str) -> list[str]:
    return sorted(entry.name for entry in (legacy / kind).iterdir() if entry.is_file())


def list_names(engine: Engine, kind: str) -> list[str]:
    return sorted(item["name"] for item in engine.call("workspace.list", {"kind": kind})["files"])


def compare_databases(engine: Engine, db_file: Path) -> None:
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    legacy_propellants = [dict(row) for row in connection.execute("SELECT * FROM propelente")]
    legacy_components = [dict(row) for row in connection.execute("SELECT * FROM termoquimica")]
    connection.close()

    propellants = engine.call("db.propellants.list")["items"]
    check(len(propellants) == len(legacy_propellants), f"db.propellants.list: {len(legacy_propellants)} filas")
    for legacy_row, row in zip(legacy_propellants, propellants):
        for field, expected in legacy_row.items():
            if field == "id":
                continue
            check(
                close_enough(row.get(field), expected),
                f"propelente.{field}",
                f"esperado {expected!r}, obtenido {row.get(field)!r}",
            )

    components = engine.call("db.components.list")["items"]
    check(len(components) == len(legacy_components), f"db.components.list: {len(legacy_components)} filas")
    by_name = {row["Component"]: row for row in components}
    check(all(row["Component"] in by_name for row in legacy_components), "todos los componentes legacy presentes")
    check(all("latex" in row for row in components), "latex calculado en los componentes")


def check_calculate(engine: Engine, fixtures: Path, workdir: Path) -> None:
    fixture_file = fixtures / "nozzle_bn1.json"
    if not fixture_file.is_file():
        return
    fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
    setup = fixture.get("rpc", {}).get("setup") or []
    engine_file = setup[0]["params"]["path"] if setup else "KNSU-32-RT65.json"
    if not (workdir / "Engines" / engine_file).is_file():
        return
    result = engine.call("nozzle.calculate", fixture["rpc"]["params"])
    got = result.get("calculatedResults") or {}
    expected_raw = fixture["raw"]["calculatedResults"]
    expected_ui = fixture["result"]["calculatedResults"]
    problems = [
        f"{key}: got={got.get(key)!r} raw={raw!r} ui={expected_ui.get(key)!r}"
        for key, raw in expected_raw.items()
        if key not in got or not (close_enough(got[key], raw) or close_enough(got[key], expected_ui.get(key)))
    ]
    check(not problems, f"nozzle.calculate: {len(expected_raw)} valores", "; ".join(problems[:5]))
    samples = len(result.get("timeResults_data", {}).get("Time (s)", []))
    expected_samples = len(fixture["result"]["timeResults_data"]["Time (s)"])
    check(samples == expected_samples, "nozzle.calculate nº de muestras", f"{samples} vs {expected_samples}")


def check_cad(engine: Engine, fixtures: Path, workdir: Path) -> None:
    fixture_file = fixtures / "cad_bn1_sketches.json"
    if not fixture_file.is_file():
        return
    fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
    for required in ("Nozzles/" + fixture["nozzleFile"], "Engines/" + fixture["engineFile"]):
        if not (workdir / required).is_file():
            return
    loaded = engine.call("cad.load_nozzle", {"path": fixture["nozzleFile"]})
    config = loaded.get("config", loaded)
    for kind, fixture_name in fixture["csv"]["files"].items():
        result = engine.call(
            "cad.export",
            {"kind": kind, "config": config, "settings": fixture["settings"], "overwrite": True},
        )
        target = Path(result["path"])
        with (fixtures / fixture_name).open(encoding="utf-8", newline="") as handle:
            expected = handle.read()
        with target.open(encoding="utf-8", newline="") as handle:
            actual = handle.read()
        check(normalize(actual) == normalize(expected), f"cad.export {kind} idéntico a {fixture_name}", str(target))
        check(target.parent == workdir / "Sketches", f"cad.export {kind} escribió en el workdir", str(target))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bundle", type=Path, default=REPO / "artifacts" / "engine-bundle")
    default_data = Path(os.environ.get("APPDATA") or Path.home() / ".config") / "OpenRED"
    parser.add_argument("--data-dir", type=Path, default=default_data)
    parser.add_argument("--workdir", type=Path, default=Path.home() / "Documents" / "OpenRED")
    parser.add_argument("--legacy", type=Path, default=REPO / "legacy" / "workingDirectory")
    parser.add_argument("--fixtures", type=Path, default=REPO / "contracts" / "fixtures")
    args = parser.parse_args()

    bundle = args.bundle.resolve()
    data_dir = args.data_dir.resolve()
    workdir = args.workdir.resolve()
    legacy = args.legacy.resolve() if args.legacy.is_dir() else None
    fixtures = args.fixtures.resolve()
    python = bundle / "python" / "python.exe"
    if not python.is_file():
        python = bundle / "python" / "bin" / "python3"
    if not python.is_file():
        print(f"FAIL: no hay intérprete portable en {bundle}")
        return 2
    if not workdir.is_dir():
        print(f"FAIL: el directorio de trabajo migrado no existe: {workdir}")
        return 2

    print(f"[migración] bundle   : {bundle}")
    print(f"[migración] data dir : {data_dir}")
    print(f"[migración] workdir  : {workdir}")
    print(f"[migración] legacy   : {legacy or '(no indicado)'}")

    engine = Engine(python, bundle, data_dir)
    print("== proceso 1: workdir + datos migrados ==")
    ping = engine.call("app.ping")
    check(bool(ping.get("resourceDir")), "app.ping resourceDir")
    check(ping.get("workdir") in (None, "", str(workdir)), "workdir inicial", f"got {ping.get('workdir')!r}")

    result = engine.call("workspace.set_dir", {"path": str(workdir)})
    check(result.get("workdir") == str(workdir), "workspace.set_dir", json.dumps(result))
    if legacy and (legacy / "config.json").is_file():
        check(result.get("hasConfig") is True, "config.json detectado")
        config = engine.call("workspace.load_config")
        check(bool((config.get("config") or {}).get("tabs")), "workspace.load_config tiene tabs")
    if legacy and (legacy / "checklist.json").is_file():
        steps = json.loads((legacy / "checklist.json").read_text(encoding="utf-8"))
        expected_steps = len(steps.get("Checklist") or steps.get("checklist") or steps.get("items") or [])
        checklist = engine.call("testbed.checklist.load")
        items = checklist.get("items") or checklist.get("checklist") or []
        check(len(items) == expected_steps, f"testbed.checklist.load: {expected_steps} pasos", json.dumps(checklist)[:200])

    print("== listados del workdir ==")
    for kind in KINDS:
        names = list_names(engine, kind)
        if legacy and (legacy / kind).is_dir():
            expected = legacy_names(legacy, kind)
            check(names == expected, f"workspace.list {kind}", f"motor={names} legacy={expected}")
        else:
            check(True, f"workspace.list {kind}", f"{len(names)} ficheros")

    print("== base de datos ==")
    db_file = legacy.parent / "database.db" if legacy else None
    if db_file and db_file.is_file():
        compare_databases(engine, db_file)
    else:
        check(len(engine.call("db.propellants.list")["items"]) > 0, "db.propellants.list no vacío")

    print("== ficheros de motor y tobera ==")
    engine_files = [item["name"] for item in engine.call("engine.list")["files"]]
    nozzle_files = [item["name"] for item in engine.call("nozzle.list")["files"]]
    check(bool(engine_files), "engine.list", str(engine_files))
    check(bool(nozzle_files), "nozzle.list", str(nozzle_files))
    if engine_files:
        loaded = engine.call("engine.load", {"path": str(workdir / "Engines" / engine_files[0])})
        tree = ((loaded.get("payload") or {}).get("results") or {}).get("tree_data") or {}
        check(len(tree.get("Time (s)", [])) > 0, f"engine.load {engine_files[0]}")
    if nozzle_files:
        check(bool(engine.call("nozzle.load", {"path": nozzle_files[0]}).get("payload")), "nozzle.load")

    print("== cálculo y CAD contra los fixtures dorados ==")
    check_calculate(engine, fixtures, workdir)
    check_cad(engine, fixtures, workdir)
    engine.close()

    print("== proceso 2: persistencia del workdir ==")
    second = Engine(python, bundle, data_dir)
    ping2 = second.call("app.ping")
    check(ping2.get("workdirSelected") is True, "workdirSelected tras reiniciar")
    check(ping2.get("workdir") == str(workdir), "workdir persistido en app.json", f"got {ping2.get('workdir')!r}")
    second.close()

    for kind in ("ENGINE", "COVER", "TOOLS"):
        (workdir / "Sketches" / f"OPENRED_{kind}_CAD.csv").unlink(missing_ok=True)

    print()
    if FAILURES:
        print(f"RESULTADO: FAIL ({len(FAILURES)}/{CHECKS})")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"RESULTADO: PASS ({CHECKS} comprobaciones)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
