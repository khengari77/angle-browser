# SPDX-License-Identifier: MPL-2.0
"""Run native Qt/WebEngine checks twice against an isolated persistent profile."""
import http.server
import os
from pathlib import Path
import subprocess
import tempfile
import threading

root=Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(root/'tests/fixtures'),**kwargs)
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with tempfile.TemporaryDirectory(prefix='arcreverse-gate-') as data:
    env=dict(os.environ,ARCREVERSE_TEST_DATA=data,ARCREVERSE_TEST_URL=f'http://localhost:{server.server_port}/')
    for phase in ([],['--restore']):
        command=[str(root/'build/arcreverse'),'--engine-gate',*phase]
        if os.getenv("ARCREVERSE_ENGINE_DEBUG"): command=["gdb","--batch","-ex","set debuginfod enabled off","-ex","run","-ex","bt 35","--args",*command]
        result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=180)
        print(result.stdout+result.stderr,flush=True)
        if result.returncode or 'ENGINE_GATE_PASS' not in result.stderr:
            raise SystemExit(result.returncode or 1)
server.shutdown()
