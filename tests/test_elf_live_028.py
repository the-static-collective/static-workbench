"""Credential-free genuine OpenManus local model profile: strict refusal tests."""
from pathlib import Path
from unittest.mock import patch
import pytest

from static_workbench.elf_live_027 import live_elf_probe, LiveGateRefusal

SAFE='''[llm]
api_type = "ollama"
model = "qwen2.5:1.5b"
base_url = "http://127.0.0.1:11434/v1"
api_key = "ollama"
max_tokens = 512
temperature = 0.0

[daytona]
daytona_api_key = "disabled-local-placeholder"
'''

def _profile(tmp_path: Path, content: str):
    root=tmp_path/"loadout";root.mkdir()
    checkout=tmp_path/"openmanus";(checkout/"config").mkdir(parents=True)
    (checkout/"config/config.toml").write_text(content)
    workspace=tmp_path/"fresh-child";workspace.mkdir()
    return root,checkout,workspace

def _try(tmp_path,config):
    root,checkout,workspace=_profile(tmp_path,config)
    with patch("static_workbench.elf_live_027.pinned_loadout",return_value=root), patch(
         "static_workbench.elf_live_027.verify_original_live_loadout_files"):
        return live_elf_probe(
            loadout_root=root,provider_checkout=checkout,
            provider_python=tmp_path/"missing-python",workspace=workspace,
            output=tmp_path/"new-evidence",model_config_class="local-ollama",
            forwarded_env_names=(),source_env={
                "OPENAI_API_KEY":"secret-will-not-inherit",
                "OLLAMA_HOST":"http://remote-host:11434"
            },timeout_seconds=60,max_steps=6)

def test_local_ollama_profile_accepts_credentialless_gate_but_never_launches_bad_provider(tmp_path):
    with pytest.raises(LiveGateRefusal,match="ORIGINAL_OPENMANUS_WORKER_MISSING"):
        _try(tmp_path,SAFE)

@pytest.mark.parametrize("changed",[
    SAFE.replace("127.0.0.1","evil.remote"),
    SAFE.replace("api_key = \"ollama\"","api_key = \"private-key\""),
    SAFE.replace("disabled-local-placeholder","external-daytona-key"),
    SAFE.replace("qwen2.5:1.5b","anything:latest"),
    SAFE.replace("temperature = 0.0","temperature = 1.0"),
    SAFE + '\n[sandbox]\nuse_sandbox = true\n',
    SAFE.replace("max_tokens = 512","max_tokens = 9999999"),
])
def test_ollama_never_accepts_remote_endpoint_or_external_credentials(tmp_path,changed):
    with pytest.raises(LiveGateRefusal,match="LOCAL_OLLAMA_NONLOCAL_OR_CREDENTIAL_CONFIGURATION"):
        _try(tmp_path,changed)

def test_local_ollama_requires_no_forwarded_secret_variables(tmp_path):
    root,checkout,workspace=_profile(tmp_path,SAFE)
    with pytest.raises(LiveGateRefusal,match="EXPLICIT_MODEL_ENV_ALLOWLIST_REQUIRED"):
        live_elf_probe(
            loadout_root=root,provider_checkout=checkout,
            provider_python=tmp_path/"missing-python",workspace=workspace,
            output=tmp_path/"evidence",model_config_class="local-ollama",
            forwarded_env_names=("OPENAI_API_KEY",),
            source_env={"OPENAI_API_KEY":"do-not-forward"})

def test_ollama_must_have_explicit_config_without_hidden_fallback(tmp_path):
    with pytest.raises(LiveGateRefusal,match="LOCAL_OLLAMA_NONLOCAL_OR_CREDENTIAL_CONFIGURATION"):
        _try(tmp_path,SAFE.replace("base_url = \"http://127.0.0.1:11434/v1\"",
                                   "base_url = \"http://localhost:11434/v1\""))



def test_venv_symlink_path_is_not_collapsed_to_system_python(tmp_path):
    import subprocess
    import sys
    from static_workbench.elf_live_027 import select_provider_interpreter

    venv = tmp_path / "isolated-original-provider"
    subprocess.run([sys.executable, "-m", "venv", str(venv)],
                   capture_output=True, check=True)
    executable = venv / "bin" / "python"
    assert executable.is_symlink()
    selected = select_provider_interpreter(executable)
    assert selected == executable
    assert selected != executable.resolve()
    invocation = subprocess.check_output(
        [str(selected), "-c", "import sys;print(sys.prefix)"], text=True
    ).strip()
    resolved = subprocess.check_output(
        [str(executable.resolve()), "-c", "import sys;print(sys.prefix)"], text=True
    ).strip()
    assert Path(invocation) == venv
    assert Path(resolved) != venv


def test_venv_invocation_must_be_explicit_existing_absolute_path(tmp_path):
    from static_workbench.elf_live_027 import select_provider_interpreter
    with pytest.raises(LiveGateRefusal,match="PROVIDER_INTERPRETER_MUST_BE_ABSOLUTE"):
        select_provider_interpreter(Path("relative/bin/python"))
    with pytest.raises(LiveGateRefusal,match="PINNED_PROVIDER_INTERPRETER_MISSING"):
        select_provider_interpreter(tmp_path / "missing/bin/python")
