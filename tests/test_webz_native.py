"""WEBZ-NATIVE-001: closed, untrusted-input-safe world-address resolver."""
import copy
import json
from pathlib import Path

import pytest

from static_workbench.webz_native import (
    WebzRegistryError,
    load_registry,
    parse_webz_address,
    resolve_webz_address,
    world_by_slug,
)

WEB_DIR = Path(__file__).resolve().parents[1] / "static_workbench" / "web"


def test_parser_accepts_exact_first_world_addresses():
    assert parse_webz_address("webz::static/sanctuary") == ("static", "sanctuary")
    assert parse_webz_address("webz::static/orchard/022100") == (
        "static", "orchard", "022100"
    )


@pytest.mark.parametrize("unsafe", [
    "", "webz:", "webz::", "webz::static", "WEBZ::static/sanctuary",
    "webz::Static/sanctuary", "webz::static/Sanctuary",
    "webz::static/../orchard", "webz::static/./orchard",
    "webz::static//orchard", "webz::static/%2f",
    "webz::static/a%2fb", "webz::static/a#x", "webz::static/a?x=1",
    "webz::static/a@b", "webz::http://example.test",
    "webz::static/a:80", "webz::static/a b", "webz::static/a\\b",
    "webz::static/a\n", "webz::static/a\x00", "webz::static/é",
    "webz::static/a/b/c/d", "webz::static/" + ("x" * 257),
    " webz::static/sanctuary ", "https://example.test", 17, None,
])
def test_parser_rejects_unsafe_or_ambiguous_inputs(unsafe):
    with pytest.raises(ValueError):
        parse_webz_address(unsafe)


def test_registry_loads_two_distinct_worlds_and_doors():
    registry = load_registry(WEB_DIR)
    home = resolve_webz_address("webz::static/sanctuary", registry)
    orchard = resolve_webz_address("webz::static/orchard/022100", registry)
    assert home == {
        "status": "resolved",
        "typed_address": "webz::static/sanctuary",
        "world_id": "webz:the-static-collective/sanctuary",
        "title": "Psychedelic Punk Sanctuary",
        "entry_route": "/webz/world/sanctuary",
        "manifest_revision": "genesis-001",
        "source": "trusted-workbench-fixture",
    }
    assert orchard["world_id"] == "webz:the-static-collective/orchard-022100"
    assert orchard["entry_route"] == "/webz/world/orchard"
    assert home["world_id"] != orchard["world_id"]
    sanctuary = world_by_slug("sanctuary", registry)
    grove = world_by_slug("orchard", registry)
    assert sanctuary["doors"][0]["door_id"] == "sanctuary-to-orchard"
    assert sanctuary["doors"][0]["to_world_id"] == grove["world_id"]
    assert sanctuary["doors"][0]["to_address"] == "webz::static/orchard/022100"
    assert grove["doors"][0]["door_id"] == "orchard-to-sanctuary"
    assert grove["doors"][0]["to_world_id"] == sanctuary["world_id"]
    assert world_by_slug("elsewhere", registry) is None


def test_unknown_address_never_fetches(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("resolving a logical world address must not fetch a URL")
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    registry = load_registry(WEB_DIR)
    assert resolve_webz_address("webz::static/unbuilt", registry) == {
        "status": "unresolved", "typed_address": "webz::static/unbuilt"
    }
    bad = resolve_webz_address("webz::http://evil.test", registry)
    assert bad["status"] == "invalid"
    assert "entry_route" not in bad


@pytest.mark.parametrize("mutation", [
    "duplicate-alias", "duplicate-world", "duplicate-door", "outside-route",
    "traversal-filename", "extra-manifest-key", "wrong-target", "mismatched-address",
    "broken-json", "schema",
])
def test_invalid_registry_rejected(tmp_path, mutation):
    for name in ["webz-registry.json", "webz-sanctuary.json", "webz-orchard.json"]:
        (tmp_path / name).write_bytes((WEB_DIR / name).read_bytes())
    path = tmp_path / "webz-registry.json"
    reg = json.loads(path.read_text())
    sanctuary_path = tmp_path / "webz-sanctuary.json"
    sanctuary = json.loads(sanctuary_path.read_text())
    if mutation == "duplicate-alias":
        reg["aliases"].append(copy.deepcopy(reg["aliases"][0]))
    elif mutation == "duplicate-world":
        orchard_path = tmp_path / "webz-orchard.json"
        orchard = json.loads(orchard_path.read_text())
        orchard["world_id"] = sanctuary["world_id"]
        orchard_path.write_text(json.dumps(orchard))
    elif mutation == "duplicate-door":
        sanctuary["doors"].append(copy.deepcopy(sanctuary["doors"][0]))
    elif mutation == "outside-route":
        reg["aliases"][0]["entry_route"] = "/api/doorhouse/enter"
    elif mutation == "traversal-filename":
        reg["aliases"][0]["manifest_file"] = "../../secrets.json"
    elif mutation == "extra-manifest-key":
        sanctuary["arbitrary_script"] = "alert(1)"
    elif mutation == "wrong-target":
        sanctuary["doors"][0]["to_world_id"] = "webz:someone-else/world"
    elif mutation == "mismatched-address":
        sanctuary["doors"][0]["to_address"] = "webz::static/sanctuary"
    elif mutation == "broken-json":
        sanctuary_path.write_text("{broken")
    elif mutation == "schema":
        reg["schema"] = "webz/registry/v99"
    if mutation not in {"broken-json", "duplicate-world"}:
        sanctuary_path.write_text(json.dumps(sanctuary))
    path.write_text(json.dumps(reg))
    with pytest.raises(WebzRegistryError):
        load_registry(tmp_path)
