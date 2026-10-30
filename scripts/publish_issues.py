#!/usr/bin/env python3
"""Publish the reviewed backlog. Dry-run by default; requires authenticated gh."""
# SPDX-License-Identifier: MPL-2.0
import argparse
import json
import subprocess
from pathlib import Path


def gh(*args, payload=None):
    command = ['gh', 'api', *args]
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, help='owner/repository')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    tasks = json.loads((root / 'docs/backlog.json').read_text())
    if not args.apply:
        for task in tasks:
            print(f"{task['key']}: {task['title']} (dependencies: {task['dependencies']})")
        return
    base = f'repos/{args.repo}'
    labels = {'ready': '0e8a16', 'blocked': 'd93f0b', 'research': '0075ca',
              'binary-re': 'b60205', 'engine': '5319e7', 'implementation': '1d76db',
              'quality': 'fbca04', 'maintainer-review': 'd876e3'}
    existing_labels = {x['name'] for x in gh(base + '/labels?per_page=100')}
    for name, color in labels.items():
        if name not in existing_labels:
            gh(base + '/labels', payload={'name': name, 'color': color})
    existing = []
    page = 1
    while True:
        batch = gh(base + f'/issues?state=all&per_page=100&page={page}')
        existing.extend(x for x in batch if 'pull_request' not in x)
        if len(batch) < 100:
            break
        page += 1
    by_title = {x['title']: x for x in existing}
    results = {}
    created = set()
    for task in tasks:
        title = f"[{task['key']}] {task['title']}"
        issue = by_title.get(title)
        if issue is None:
            tags = [task['area'], 'blocked' if task['dependencies'] else 'ready']
            if task['area'] == 'binary-re':
                tags.append('maintainer-review')
            issue = gh(base + '/issues', payload={'title': title, 'body': task['body'], 'labels': tags})
            created.add(task['key'])
        results[task['key']] = issue
        print(issue['html_url'])
    for task in tasks:
        if task['dependencies'] and task['key'] in created:
            links = ', '.join(results[key]['html_url'] for key in task['dependencies'])
            gh('-X', 'PATCH', base + f"/issues/{results[task['key']]['number']}",
               payload={'body': task['body'] + '\nTracking links: ' + links + '\n'})
    index = '# Published contributor issues\n\n' + ''.join(
        f"- [{key}: {issue['title']}]({issue['html_url']})\n" for key, issue in results.items())
    (root / 'docs/ISSUES.md').write_text(index)


if __name__ == '__main__':
    main()
