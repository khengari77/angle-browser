"""Select evidence-backed workspace declarations from a Swift metadata report.

Usage: python3 scripts/workspace_dossier.py artifacts/swift-all-fields.json
No decoding or JSON-file compatibility claims are made by this selection.
"""
import argparse
import json
from pathlib import Path

CONTEXTS = (
    'StorableSidebar.StorableSidebar',
    'SidebarDataStore.AppSidebarReducerState',
    'BaseModels.SidebarContainer',
    'BaseModels.SidebarContainerType',
    'BaseModels.SidebarItem',
    'BaseModels.SidebarItemData',
    'BaseModels.SidebarItemDictionaryCoding',
    'BaseModels.SpaceModel',
    'BaseModels.SpaceModel.CodingKeys',
    'BaseModels.SpaceModel.CustomInfo',
    'BaseModels.SpaceModel.ContainerType',
    'BaseModels.SpaceModel.ContainerType.UnpinnedContainerType',
    'SidebarSyncCloudKit.ZoneSyncData',
    'FirebaseSidebarSyncCommon.PersistedFirebaseSidebarSyncState',
)


def select(report):
    if report.get('format')!='arcreverse-swift-fields-v1':
        raise ValueError('expected a Swift field metadata report')
    matches = [r for r in report['matches'] if r['context'] in CONTEXTS]
    return {
        'format':'arcreverse-workspace-declarations-v1',
        'sha256':report['sha256'],
        'source_descriptor_count':report['descriptor_count'],
        'source_unresolved_names':report['unresolved_names'],
        'source_issues':report['issues'],
        'selection':list(CONTEXTS),
        'not_resolved_by_selection':[name for name in CONTEXTS if not any(r['context']==name for r in matches)],
        'declarations':matches,
        'limitations':report['limitations'],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    print(json.dumps(select(json.loads(args.report.read_text())),indent=2))

if __name__=='__main__': main()
