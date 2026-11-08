# Provisional workspace export

Tracking: #16; evidence prerequisite #15. This implements a community-documented compatibility subset, not a verified Arc storage specification. No Arc-produced runtime fixture was available. The source keys are supported by independently published parsers and our static declaration dossier; particular encodings and omission rules remain third-party claims. See REFERENCES.md and CONFIRMED_BEHAVIOR.md.

```
python3 scripts/export_workspace.py /path/to/copied-sidebar.json --output /path/to/new-export.json
```

The tool reads only the explicitly supplied copy, never discovers profiles, and never opens Arc or contacts a service. Output creation is exclusive; existing files, including the source, cannot be overwritten. Input size is limited to 32 MiB and reachable hierarchy depth to 128. Invalid inputs exit with status 2 and a diagnostic.

Supported input is integer version 1 with `sidebar.containers`. A `{ "global": {} }` marker is skipped; other containers must have alternating ID/record `spaces` and `items` arrays. `containerIDs` supports string section tags; `newContainerIDs` additionally supports singleton enum tags such as `{ "pinned": {} }`. Recognized sections are pinned/unpinned. IDs, ordering, roots and parent/child relationships are validated; missing references, cycles, duplicate keys, unknown reachable item kinds and non-HTTP(S) URLs are rejected rather than guessed.

Output `angle-workspace-v1` has source_version, warnings and spaces. Each Space contains source_container (source array index, not a profile identity), title, pinned and temporary lists. Folder nodes contain kind/title/children; tab nodes contain kind/title/url. Saved URL takes precedence over current URL, and item title over saved title. Ordering and duplicate URLs are retained. Original profile IDs, credentials, sync records, themes, Favorites associations and unrelated top-level state are omitted. A warnings array always declares the principal omissions. This is not an Angle database import format or an original Arc export.

All test fixtures are constructed independently in tests/test_export_workspace.py. No third-party source was incorporated. Source inspection exposure: ivnvxd/arc-export main.py and Icesource/arc-tab-organizer DATA_MODEL.md; exact source identities are in the reference registry. Their claims are research inputs, not proof of runtime compatibility.

No full profile, export containing personal data, or private URL list should be attached to a public bug report. Reproduce failures with a synthetic fixture.
