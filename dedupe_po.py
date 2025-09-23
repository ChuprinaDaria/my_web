import os, polib
from collections import OrderedDict

BASE = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(BASE, 'locale')

def key_of(e: polib.POEntry):
    ctx = e.msgctxt or ''
    mid = (e.msgid or '').replace('\r','').strip()
    mpl = (e.msgid_plural or '').replace('\r','').strip()
    return (ctx, mid, mpl)

def score(e: polib.POEntry):
    # Вищий бал = корисніший переклад
    s = 0
    if e.msgstr and e.msgstr.strip(): s += 2
    if e.msgstr_plural: s += 3
    if e.tcomment: s += 1
    return s

def merge(a: polib.POEntry, b: polib.POEntry):
    keep, drop = (a, b) if score(a) >= score(b) else (b, a)
    # мерджимо коментарі/флаги
    keep.comment = keep.comment or drop.comment
    keep.tcomment = keep.tcomment or drop.tcomment
    keep.flags = list(sorted(set(list(keep.flags)+list(drop.flags))))
    return keep

def dedupe_file(path: str):
    po = polib.pofile(path)
    uniq = OrderedDict()
    dups = 0
    for e in po:
        k = key_of(e)
        if k in uniq:
            uniq[k] = merge(uniq[k], e)
            dups += 1
        else:
            uniq[k] = e
    po._entries = list(uniq.values())
    po.save(path)
    print(f'✅ {os.path.relpath(path)}: {dups} duplicates removed, {len(po._entries)} entries')

def main():
    for root, _, files in os.walk(LOCALE_DIR):
        for f in files:
            if f == 'django.po':
                dedupe_file(os.path.join(root, f))

if __name__ == '__main__':
    main()