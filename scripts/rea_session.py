"""Persistent local MCP research client. Supply one JSON tool call per stdin line.

Results are saved under ignored artifacts/session-<pid>; stdout shows summaries.
A line with {"close": true} closes the target and shuts down the owned server.
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / 'artifacts' / f'session-{os.getpid()}'
    output.mkdir(parents=True)
    env = dict(os.environ, GHIDRA_INSTALL_DIR=str(root / '.local-tools/ghidra_12.1.4_PUBLIC'))
    log = (output / 'server.log').open('w')
    process = subprocess.Popen([
        str(root / '.local-tools/node-v22.23.4-linux-x64/bin/node'),
        str(root / '.local-tools/rea/node_modules/rea-agents/scripts/rea.mjs'), 'mcp',
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, env=env)
    messages = queue.Queue()
    def read():
        for line in process.stdout:
            try: messages.put(json.loads(line))
            except json.JSONDecodeError: messages.put({'parse_error': line})
        messages.put(None)
    threading.Thread(target=read, daemon=True).start()
    sequence = 0
    def request(method, params, timeout=1020):
        nonlocal sequence
        sequence += 1
        process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': sequence, 'method': method, 'params': params}) + '\n')
        process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            message = messages.get(timeout=max(0.01, deadline-time.monotonic()))
            if message is None: raise RuntimeError('REA server exited')
            if message.get('id') == sequence: return message
    try:
        request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'ArcReverse', 'version': '1'}})
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n'); process.stdin.flush()
        tools = request('tools/list', {})
        (output / 'tools.json').write_text(json.dumps(tools, indent=2))
        print(json.dumps({'ready': True, 'directory': str(output)}), flush=True)
        for line in sys.stdin:
            call = json.loads(line)
            if call.get('close'): break
            result = request('tools/call', {'name': call['tool'], 'arguments': call.get('arguments', {})})
            path = output / f'{sequence:03}-{call["tool"]}.json'
            path.write_text(json.dumps(result, indent=2))
            body = result.get('result', {})
            print(json.dumps({'saved': str(path), 'error': body.get('isError', False), 'rpc_error': result.get('error')}), flush=True)
    finally:
        if process.poll() is None:
            try: request('tools/call', {'name': 'close_binary', 'arguments': {}}, timeout=30)
            except (OSError, RuntimeError, queue.Empty): pass
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        log.close()

if __name__ == '__main__': main()
