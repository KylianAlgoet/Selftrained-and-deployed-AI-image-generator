"""`.env.example` must describe the configuration that exists, and only that.

WHY THIS TEST EXISTS.

Until M8 this file advertised `MODEL_CACHE_DIR`, `BASE_MODEL_ID`,
`LORA_WEIGHTS_PATH`, `ALLOWED_UPLOAD_EXTENSIONS` and `UPLOAD_TMP_DIR`. Not one of
them is read anywhere in the codebase. Nothing failed, no test complained, and
the file looked more complete than the truthful version would have - which is
exactly the failure mode. Someone deploying from it would have set five
variables that do nothing and, worse, would reasonably believe the upload
allowlist and the model path were configurable when they are not.

The keys are derived from the source by AST rather than kept in a list here, so
this cannot drift the way the file it guards drifted.
"""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "apps" / "api" / "config.py"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"

# Read only in order to be REJECTED above 1. They belong in the file as a
# warning, not as settings, so they are listed apart from the settings keys.
WORKER_VARS = frozenset({"WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"})


def _keys_read_by_config() -> set[str]:
    """Every string literal passed to `env.get(...)` in config.py."""
    tree = ast.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "get"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "env"):
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            value = node.args[0].value
            if isinstance(value, str):
                keys.add(value)
    return keys


def _keys_declared_in_env_example() -> set[str]:
    """Every KEY= in the file, including the commented-out optional ones."""
    keys: set[str] = set()
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip().lstrip("#").strip()
        match = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
        if match:
            keys.add(match.group(1))
    return keys


def _vite_keys_used_by_the_frontend() -> set[str]:
    """`VITE_*` identifiers appearing in the frontend source, tests excluded."""
    keys: set[str] = set()
    for path in WEB_SRC.rglob("*.ts*"):
        if ".test." in path.name:
            continue
        keys.update(re.findall(r"VITE_[A-Z0-9_]+", path.read_text(encoding="utf-8")))
    return keys


def test_every_documented_key_is_one_the_code_actually_reads():
    documented = _keys_declared_in_env_example()
    supported = _keys_read_by_config() | WORKER_VARS | _vite_keys_used_by_the_frontend()

    unread = documented - supported
    assert not unread, (
        f".env.example documents keys nothing reads: {sorted(unread)}. "
        "Either wire them up or remove them - a settings file that lies is worse "
        "than one that is incomplete."
    )


def test_every_setting_the_api_reads_is_documented():
    """The reverse direction: an undocumented setting is invisible to a deployer."""
    documented = _keys_declared_in_env_example()
    missing = _keys_read_by_config() - documented
    assert not missing, f".env.example does not document: {sorted(missing)}"


def test_the_worker_variables_are_documented_as_rejected_not_as_settings():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for name in WORKER_VARS:
        assert name in text, f"{name} must be documented"
    # The file must not present them as something to tune.
    for name in WORKER_VARS:
        assert not re.search(rf"^{name}=", text, re.MULTILINE), (
            f"{name} must not appear as an active assignment - it is read only to "
            "be rejected above 1"
        )


def test_the_frozen_upload_rules_are_not_presented_as_configurable():
    """`ALLOWED_UPLOAD_EXTENSIONS` and `UPLOAD_TMP_DIR` must stay gone.

    Both were in this file before M8. The extension allowlist lives in
    `uploads.py` because a security rule that an environment variable can widen
    is not a rule, and there is no temporary upload directory at all - nothing
    user-supplied is ever written to disk.
    """
    documented = _keys_declared_in_env_example()
    assert "ALLOWED_UPLOAD_EXTENSIONS" not in documented
    assert "UPLOAD_TMP_DIR" not in documented


def test_the_key_extractor_is_sensitive():
    """The extractor is only evidence if it finds something. Prove it does."""
    keys = _keys_read_by_config()
    assert "API_HOST" in keys and "CHECKPOINT_ROOT" in keys
    assert len(keys) >= 8
