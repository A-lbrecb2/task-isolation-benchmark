#!/usr/bin/env python3
"""Build one Crodox repoPatches modification from a before/after pair of files.

    python3 kit/scripts/make_patch.py --before app.module.before.ts --after app.module.after.ts \
        --dir src/app/app.module.ts --condition 1 --key 9 --selector myPatch

Prints the JSON object to paste into the "mods" array of the condition node whose "key"
equals --condition. The "after" file may contain Crodox placeholders such as <~name.0~>,
<~file~.ts~>, <~selector.0~> or <~[parent].name.0~>; they are kept verbatim.
"""
import argparse, difflib, json


def hunk(old, new, n=4):
    lines = list(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), n=n, lineterm=''))
    return ''.join(l if l.endswith('\n') else l + '\n' for l in lines[2:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', required=True)
    ap.add_argument('--after', required=True)
    ap.add_argument('--dir', required=True, help='target path inside the template repository')
    ap.add_argument('--condition', type=int, required=True, help='key of the condition node this mod belongs to')
    ap.add_argument('--key', type=int, required=True, help='unique mod key')
    ap.add_argument('--selector', required=True, help='short name shown in the Patch Maker')
    a = ap.parse_args()
    before = open(a.before, encoding='utf-8').read()
    after = open(a.after, encoding='utf-8').read()
    m = {"condition": a.condition, "dir": a.dir, "key": a.key, "parent": "",
         "patch": hunk(before, after), "patchText": after, "fileText": before, "selector": a.selector}
    print(json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
