#!/usr/bin/env python3
"""Developer tool: parse a CIB PDF, mask names/IDs and embed it as the demo dataset in index.html."""
import json, sys, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from cib_parser import parse
pdf, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
d = parse(pdf); cm, nm = {}, {}
def code(c):
    if c not in cm: cm[c] = c[0] + str(len(cm) + 1).zfill(10)
    return cm[c]
def name(c, n, prefix):
    if c not in nm: nm[c] = '%s %d' % (prefix, len(nm) + 1)
    return nm[c]
s = d['subject']; main = s['cibId']
nm[main] = 'DEMO CLIENT'
for i, (c, n) in enumerate(s['props']): nm[c] = 'DEMO TRADERS %s' % 'ABC'[i]
for f in d['facilities']:
    for c, r, n in f['linked']:
        if c not in nm: nm[c] = 'RELATED PARTY %d' % (len(nm) - 3)
s['props'] = [[code(c), nm[c]] for c, _ in s['props']]; s['name'] = 'DEMO CLIENT'; s['cibId'] = code(main)
for f in d['facilities']:
    f['linked'] = [[code(c), r, nm[c]] for c, r, n in f['linked']]
    f['subjName'] = nm.get(f['subj'], f['subj']); f['subj'] = code(f['subj']); f['id'] = code(f['id']); f['fi'] = '###'
html = open(src).read().replace('/*SAMPLE_DATA*/null', json.dumps(d, separators=(',', ':')))
open(dst, 'w').write(html); print('built', dst, len(html))
