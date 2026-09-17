from __future__ import annotations

import json
import re

from afs.config import ROOT, Settings

# Settings that must be configured explicitly on Heroku; the rest have safe repo-relative defaults.
PRODUCTION_REQUIRED = {
    "database_url",
    "sectors_api_key",
    "telegram_bot_token",
    "telegram_chat_id",
    "base_web_url",
    "admin_password",
    "session_secret",
}


def _procfile() -> dict[str, str]:
    processes = {}
    for line in (ROOT / "Procfile").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, _, command = line.partition(":")
            processes[name.strip()] = command.strip()
    return processes


def test_procfile_has_web_and_release():
    processes = _procfile()
    assert processes["web"].startswith("uvicorn afs.web.app:app ")
    assert "--host 0.0.0.0" in processes["web"]
    assert "--port $PORT" in processes["web"]
    assert processes["release"] == "python -m afs initdb"


def test_production_required_settings_exist():
    assert PRODUCTION_REQUIRED <= set(Settings.model_fields)


def test_app_json_lists_production_env_and_addons():
    app = json.loads((ROOT / "app.json").read_text())
    assert {name.lower() for name in app["env"]} >= PRODUCTION_REQUIRED
    assert app["env"]["SESSION_SECRET"]["generator"] == "secret"
    plans = {a["plan"] if isinstance(a, dict) else a for a in app["addons"]}
    assert {"heroku-postgresql:essential-0", "scheduler:standard"} <= plans
    assert app["formation"]["web"]["size"].lower() == "basic"


def test_env_example_covers_every_setting():
    text = (ROOT / ".env.example").read_text()
    keys = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", text, flags=re.M))
    assert {name.upper() for name in Settings.model_fields} <= keys


def test_uv_files_present_for_heroku_buildpack():
    # Heroku's Python buildpack uses uv when uv.lock exists; .python-version pins the runtime.
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        assert (ROOT / name).is_file()
