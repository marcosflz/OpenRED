#!/usr/bin/env bash
# OpenRED — fetch and verify the portable Python runtime (Linux/macOS / CI).
#
# Downloads the pinned python-build-standalone release from tools/python-portable/python.lock,
# verifies its SHA-256, extracts it to engine/python/ and installs the locked wheels *into*
# that runtime (Lib/site-packages) with uv when available (pip fallback). Idempotent:
# re-running with the same lock is a no-op unless --force is passed.
#
# The sidecar can then run without PYTHONPATH; the Tauri supervisor still exports the engine
# directory (see apps/desktop/src-tauri/README.md and tests/clean-machine/smoke.ps1).
#
# Usage:
#   bash tools/python-portable/fetch_python.sh [--flavor <flavor>] [--force] [--skip-deps]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENGINE_DIR="${REPO_ROOT}/engine"
LOCK_FILE="${SCRIPT_DIR}/python.lock"
FLAVOR=""
FORCE=0
SKIP_DEPS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --flavor) FLAVOR="$2"; shift 2 ;;
    --lock|--lock-file) LOCK_FILE="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --skip-deps) SKIP_DEPS=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

json_get() {  # json_get <file> <python-expression using variable 'data'>
  python3 - "$1" "$2" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(eval(sys.argv[2]))  # noqa: S307 - fixed expressions only
PY
}

detect_flavor() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "${os}" in
    Darwin) [[ "${arch}" == "arm64" ]] && echo "aarch64-apple-darwin" || echo "x86_64-apple-darwin" ;;
    Linux)  [[ "${arch}" == "aarch64" || "${arch}" == "arm64" ]] && echo "aarch64-unknown-linux-gnu" || echo "x86_64-unknown-linux-gnu" ;;
    *) echo "unsupported OS: ${os}" >&2; exit 2 ;;
  esac
}

[[ -n "${FLAVOR}" ]] || FLAVOR="$(detect_flavor)"
ASSET="$(json_get "${LOCK_FILE}" "data['flavors']['${FLAVOR}']['asset']")"
SHA256="$(json_get "${LOCK_FILE}" "data['flavors']['${FLAVOR}']['sha256']")"
URL="$(json_get "${LOCK_FILE}" "data['flavors']['${FLAVOR}']['url']")"
EXTRACT_DIR="$(json_get "${LOCK_FILE}" "data['flavors']['${FLAVOR}']['extract_dir']")"
RELEASE_TAG="$(json_get "${LOCK_FILE}" "data['release_tag']")"
PY_VERSION="$(json_get "${LOCK_FILE}" "data['python_version']")"
[[ -n "${ASSET}" ]] || { echo "flavor '${FLAVOR}' not present in ${LOCK_FILE}" >&2; exit 2; }

PYTHON_DIR="${ENGINE_DIR}/python"
MARKER="${PYTHON_DIR}/.openred-runtime.json"

if [[ -f "${MARKER}" && "${FORCE}" -eq 0 ]]; then
  if grep -q "\"asset\": \"${ASSET}\"" "${MARKER}" && grep -q "\"sha256\": \"${SHA256}\"" "${MARKER}"; then
    echo "[fetch_python] runtime already present and matches ${ASSET} — nothing to do"
    exit 0
  fi
fi

CACHE_DIR="${TMPDIR:-/tmp}/openred-python-cache"
mkdir -p "${CACHE_DIR}"
ARCHIVE="${CACHE_DIR}/${ASSET}"
if [[ ! -f "${ARCHIVE}" ]]; then
  echo "[fetch_python] downloading ${URL}"
  curl --fail --location --retry 3 --output "${ARCHIVE}" "${URL}"
fi

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
else
  ACTUAL="$(shasum -a 256 "${ARCHIVE}" | awk '{print $1}')"
fi
if [[ "${ACTUAL}" != "${SHA256}" ]]; then
  rm -f "${ARCHIVE}"
  echo "[fetch_python] SHA256 mismatch for ${ASSET}: expected ${SHA256}, got ${ACTUAL}; archive removed" >&2
  exit 1
fi
echo "[fetch_python] SHA256 OK: ${ACTUAL}"

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/openred-python-staging-XXXXXX")"
trap 'rm -rf "${STAGING}"' EXIT
tar -xzf "${ARCHIVE}" -C "${STAGING}"
[[ -d "${STAGING}/${EXTRACT_DIR}" ]] || { echo "expected ${EXTRACT_DIR}/ inside ${ASSET}" >&2; exit 1; }
rm -rf "${PYTHON_DIR}"
mkdir -p "${PYTHON_DIR%/*}"
mv "${STAGING}/${EXTRACT_DIR}" "${PYTHON_DIR}"

PYTHON_EXE="${PYTHON_DIR}/bin/python3"
[[ -x "${PYTHON_EXE}" ]] || PYTHON_EXE="${PYTHON_DIR}/python.exe"
[[ -x "${PYTHON_EXE}" || -f "${PYTHON_EXE}" ]] || { echo "python executable not found under ${PYTHON_DIR}" >&2; exit 1; }

if [[ "${SKIP_DEPS}" -eq 0 ]]; then
  # Dependencies go *into* the portable runtime (Lib/site-packages), so the sidecar works
  # without PYTHONPATH. uv is preferred (portable copy in tools/uv or on PATH); the runtime
  # pip is the fallback.
  UV_EXE=""
  for candidate in "${REPO_ROOT}/tools/uv/uv" "${REPO_ROOT}/tools/uv/uv.exe"; do
    if [[ -x "${candidate}" ]]; then UV_EXE="${candidate}"; break; fi
  done
  if [[ -z "${UV_EXE}" ]] && command -v uv >/dev/null 2>&1; then UV_EXE="$(command -v uv)"; fi
  if [[ -n "${UV_EXE}" ]]; then
    echo "[fetch_python] installing locked wheels with uv (${UV_EXE})"
    "${UV_EXE}" pip install --system --python "${PYTHON_EXE}" \
      --requirement "${ENGINE_DIR}/requirements-core.lock" \
      --only-binary :all: --no-progress
  else
    if ! "${PYTHON_EXE}" -m pip --version >/dev/null 2>&1; then
      echo "[fetch_python] uv not found; bootstrapping pip with ensurepip"
      "${PYTHON_EXE}" -m ensurepip --upgrade
    fi
    echo "[fetch_python] installing locked wheels with the runtime pip"
    "${PYTHON_EXE}" -m pip install \
      --requirement "${ENGINE_DIR}/requirements-core.lock" \
      --only-binary :all: --no-warn-script-location --disable-pip-version-check
  fi
  PYTHONNOUSERSITE=1 "${PYTHON_EXE}" -c \
    "import numpy, scipy, matplotlib, serial; print('[fetch_python] runtime OK:', numpy.__version__, scipy.__version__, matplotlib.__version__, serial.__version__)"
fi

cat > "${MARKER}" <<EOF
{
  "asset": "${ASSET}",
  "sha256": "${SHA256}",
  "release_tag": "${RELEASE_TAG}",
  "python_version": "${PY_VERSION}",
  "flavor": "${FLAVOR}"
}
EOF
echo "[fetch_python] done: ${PYTHON_DIR}"
