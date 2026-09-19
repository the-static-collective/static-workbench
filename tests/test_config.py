from pathlib import Path

from static_workbench.config import RootConfig, WorkbenchConfig, load_config


def test_load_config_defaults_to_home_static_root_when_file_missing(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "static").mkdir()
    monkeypatch.setenv("HOME", str(home))

    config = load_config(tmp_path / "missing.toml")

    assert isinstance(config, WorkbenchConfig)
    assert config.bind_host == "127.0.0.1"
    assert config.port == 13700
    assert config.roots == (RootConfig(id="static", path=(home / "static").resolve()),)


def test_load_config_reads_explicit_roots(tmp_path: Path):
    one = tmp_path / "one"
    two = tmp_path / "two"
    one.mkdir()
    two.mkdir()
    cfg = tmp_path / "workbench.toml"
    cfg.write_text(
        f'''bind_host = "127.0.0.1"\nport = 14000\nstate_dir = "{tmp_path / "state"}"\n\n[[roots]]\nid = "one"\npath = "{one}"\n\n[[roots]]\nid = "two"\npath = "{two}"\n''',
        encoding="utf-8",
    )

    config = load_config(cfg)

    assert config.port == 14000
    assert [root.id for root in config.roots] == ["one", "two"]
    assert all(root.path.is_absolute() for root in config.roots)
