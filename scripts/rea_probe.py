"""Run a bounded MCP stdio probe without executing the selected target."""
import json, os, selectors, subprocess, sys, time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ, GHIDRA_INSTALL_DIR=str(root/'.local-tools/ghidra_12.1.4_PUBLIC'))
node=root/'.local-tools/node-v22.23.4-linux-x64/bin/node'
server=root/'.local-tools/rea/node_modules/rea-agents/scripts/rea.mjs'
proc=subprocess.Popen([str(node),str(server),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(root/('artifacts/rea-server-'+str(os.getpid())+'.log'),'w'),text=True,env=env)
def request(i, method, params):
    proc.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n'); proc.stdin.flush()
    sel=selectors.DefaultSelector(); sel.register(proc.stdout,selectors.EVENT_READ)
    until=time.monotonic()+360
    while time.monotonic()<until:
        if not sel.select(1): continue
        line=proc.stdout.readline()
        if not line: raise RuntimeError('server exited')
        msg=json.loads(line)
        if msg.get('id')==i: return msg
    raise TimeoutError(method)
try:
    init=request(1,'initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'arcreverse-probe','version':'1'}})
    proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n'); proc.stdin.flush()
    listing=request(2,'tools/list',{})
    (root/'artifacts/rea-tools.json').write_text(json.dumps(listing,indent=2))
    if len(sys.argv)==1:
        print(json.dumps([x for x in listing['result']['tools'] if x['name'] in ('open_binary','analyze_function','close_binary','inspect_binary','inspect_signature')],indent=2))
    else:
        result=request(3,'tools/call',{'name':sys.argv[1],'arguments':json.loads(sys.argv[2])})
        if len(sys.argv)>3:
            result={'open':result,'analysis':request(5,'tools/call',{'name':'analyze_function','arguments':{'procedure':sys.argv[3],'detail':'complete'}})}
        print(json.dumps(result,indent=2))
        request(4,'tools/call',{'name':'close_binary','arguments':{}})
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
