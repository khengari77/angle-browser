#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Read an explicitly supplied COPY of Arc sidebar JSON; emit angle-workspace-v1.

Supports only the documented version-1 community shapes. No profile discovery,
account access or input modification. Original code; references in reconstruction docs.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


MAX_DEPTH = 128


class Unsupported(ValueError):
    pass


def pairs(value, name):
    if not isinstance(value, list) or len(value) % 2:
        raise Unsupported(f'{name}: expected alternating key/value array')
    result = {}
    for key, item in zip(value[::2], value[1::2]):
        if not isinstance(key, str) or not key or key in result:
            raise Unsupported(f'{name}: invalid or duplicate key')
        result[key] = item
    return result


def export(document):
    if not isinstance(document, dict) or type(document.get('version')) is not int or document['version'] != 1:
        raise Unsupported('Only integer sidebar version 1 is supported')
    sidebar = document.get('sidebar')
    if not isinstance(sidebar, dict) or not isinstance(sidebar.get('containers'), list):
        raise Unsupported('Missing sidebar.containers array')
    output = {'format': 'angle-workspace-v1', 'source_version': 1, 'spaces': [],
              'warnings': ['Credentials, sync state, themes and Favorites mapping are not exported.']}
    found = False
    for ci, container in enumerate(sidebar['containers']):
        if not isinstance(container, dict):
            raise Unsupported('Container must be an object')
        if container == {'global': {}}:
            continue
        if 'spaces' not in container or 'items' not in container:
            raise Unsupported('Unknown container shape')
        found = True
        spaces = pairs(container['spaces'], 'spaces')
        items = pairs(container['items'], 'items')
        child_sets = {}
        for key, item in items.items():
            if not isinstance(item, dict) or item.get('id') != key:
                raise Unsupported('Item ID does not match dictionary key')
            children = item.get('childrenIds', [])
            if not isinstance(children, list) or any(not isinstance(x, str) for x in children) or len(set(children)) != len(children):
                raise Unsupported('Invalid child list')
            if any(x not in items for x in children):
                raise Unsupported('Missing child reference')
            child_sets[key] = set(children)
            parent = item.get('parentID')
            if parent is not None and (not isinstance(parent, str) or parent not in items):
                raise Unsupported('Missing parent reference')
        # Validate all components, including cycles outside selected Space roots.
        for key, item in items.items():
            visited = set()
            cursor = key
            while cursor is not None:
                if cursor in visited:
                    raise Unsupported('Folder cycle')
                visited.add(cursor)
                # tree() starts at section children: allow section root plus
                # the first child before counting its MAX_DEPTH descendants.
                if len(visited) > MAX_DEPTH + 2:
                    raise Unsupported('Workspace nesting exceeds 128')
                cursor = items[cursor].get('parentID')
            for child in item.get('childrenIds', []):
                if items[child].get('parentID') != key:
                    raise Unsupported('Inconsistent parent/child relation')
            parent = item.get('parentID')
            if parent is not None and key not in child_sets[parent]:
                raise Unsupported('Parent omits child; ordering is ambiguous')
        def tree(key, depth=0):
            if depth > MAX_DEPTH:
                raise Unsupported('Workspace nesting exceeds 128')
            item = items[key]
            data = item.get('data')
            if not isinstance(data, dict) or len(data) != 1:
                raise Unsupported('Unknown item variant')
            title = item.get('title')
            if title is not None and not isinstance(title, str):
                raise Unsupported('Title must be text or null')
            if 'list' in data:
                return {'kind': 'folder', 'title': title or '',
                        'children': [tree(x, depth + 1) for x in item.get('childrenIds', [])]}
            if 'tab' in data and isinstance(data['tab'], dict):
                tab = data['tab']
                url = tab.get('savedURL') or tab.get('currentURL')
                if not isinstance(url, str) or urlsplit(url).scheme not in ('http', 'https') or not urlsplit(url).hostname:
                    raise Unsupported('Only absolute HTTP(S) tab URLs are supported')
                saved_title = tab.get('savedTitle', '')
                if not isinstance(saved_title, str) or item.get('childrenIds'):
                    raise Unsupported('Invalid tab title or child tabs')
                return {'kind': 'tab', 'title': title or saved_title, 'url': url}
            raise Unsupported('Unsupported reachable item variant')
        used = set()
        for sid, space in spaces.items():
            if not isinstance(space, dict) or space.get('id', sid) != sid or not isinstance(space.get('title', ''), str):
                raise Unsupported('Invalid Space record')
            field = 'containerIDs' if 'containerIDs' in space else 'newContainerIDs'
            raw = space.get(field)
            if not isinstance(raw, list) or len(raw) % 2:
                raise Unsupported('Unknown Space container mapping')
            mapping = {}
            for tag, target in zip(raw[::2], raw[1::2]):
                if isinstance(tag, dict) and len(tag) == 1 and next(iter(tag.values())) == {}:
                    tag = next(iter(tag))
                if not isinstance(tag, str) or tag not in ('pinned', 'unpinned') or tag in mapping:
                    raise Unsupported('Unknown or duplicate section')
                if not isinstance(target, str) or target not in items or target in used:
                    raise Unsupported('Missing or reused section root')
                root = items[target]
                if root.get('parentID') is not None or not isinstance(root.get('data'), dict) or set(root['data']) != {'itemContainer'}:
                    raise Unsupported('Invalid section root')
                used.add(target)
                mapping[tag] = [tree(x) for x in root.get('childrenIds', [])]
            output['spaces'].append({'source_container': ci, 'title': space.get('title', ''),
                                     'pinned': mapping.get('pinned', []), 'temporary': mapping.get('unpinned', [])})
    if not found:
        raise Unsupported('No supported sidebar container found')
    return output


def unique_object(entries):
    result = {}
    for key, value in entries:
        if key in result:
            raise Unsupported("Duplicate JSON object key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='New JSON file; never overwritten')
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 32 * 1024 * 1024:
            raise Unsupported('Input exceeds 32 MiB limit')
        result = export(json.loads(args.input.read_text(encoding='utf-8'), object_pairs_hook=unique_object))
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    except (OSError, ValueError, RecursionError) as exc:
        print(f'Export refused: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
