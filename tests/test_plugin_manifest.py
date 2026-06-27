import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_json_is_valid():
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert data["name"] == "scienceskills"
    assert data["version"]
    assert data["description"]


def test_marketplace_lists_the_plugin():
    data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    names = [p["name"] for p in data["plugins"]]
    assert "scienceskills" in names
    plugin = next(p for p in data["plugins"] if p["name"] == "scienceskills")
    assert plugin["source"] == "./"
