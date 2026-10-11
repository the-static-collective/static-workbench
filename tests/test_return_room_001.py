from pathlib import Path
from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig

def config(tmp_path: Path):
    root=tmp_path/'root'
    root.mkdir()
    return WorkbenchConfig(bind_host='127.0.0.1',port=13700,
       state_dir=tmp_path/'state',roots=(RootConfig('static',root),))

def test_return_room_is_linked_from_real_ghot_workbench_without_becoming_effectful(tmp_path):
    with TestClient(create_app(config(tmp_path)),base_url='http://127.0.0.1') as c:
        shell=c.get('/')
        script=c.get('/assets/app.js')
        page=c.get('/return-room')
        core=c.get('/assets/return-room-core.mjs')
        ui=c.get('/assets/return-room-ui.mjs')
        css=c.get('/assets/return-room.css')
        for response in [shell,script,page,core,ui,css]:
            assert response.status_code==200
        assert 'href="/return-room"' in shell.text
        assert "returnDoor.href = '/return-room'" in script.text
        assert 'id="dials"' in page.text
        assert 'id="session"' in page.text
        assert 'id="checkpoint"' in page.text
        assert 'id="replay"' in page.text
        assert 'id="carry"' in page.text
        assert "import {LENSES" in ui.text
        assert "LOCAL_SESSION_ADDRESS_CHECKED" in core.text
        assert "NOT_REVERIFIED_IN_BROWSER" in core.text
        assert 'connect-src \'none\'' in page.text
        assert "PRIVATE SOURCE" in page.text or "SOURCE" in page.text
        assert c.post('/return-room',json={'execute':True}).status_code==405
        assert c.post('/api/return-room',json={'open':True}).status_code==404
        assert c.get('/return-room',headers={'host':'evil.example'}).status_code==400
