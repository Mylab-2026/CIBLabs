#!/usr/bin/env python3
"""CIBLens CLI parser: Bangladesh Bank CIB PDF -> JSON that index.html can import.
Needs poppler-utils (pdftotext). Usage: python tools/cib_parser.py report.pdf [out.json]"""
import re, json, subprocess, sys

def n(s): return int(s.replace(',', '')) if s else 0
def iso(d): return '-'.join(reversed(d.split('/'))) if d else ''
def short(f):
    f = f.strip()
    for p, s in [('PAD/BLC/BE', 'PAD/BLC/BE loan'), ('Export loan', 'Export loan'), ('Guarantee', 'Guarantee (non-funded)'),
                 ('Credit Card', 'Credit Card'), ('Demand Loan', 'Demand Loan'), ('Financial', 'Financial Leasing'),
                 ('Term', 'Term Loan'), ('Cash Credit', 'Cash Credit'), ('Overdraft', 'Overdraft')]:
        if f.startswith(p): return s
    return f

def parse(pdf):
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True, check=True).stdout
    L = txt.split('\n')
    g = lambda rx, t=txt: (re.search(rx, t) or [None, ''])[1].strip()
    subj = dict(name=g(r'Name:\s+([A-Z][^\n]*?)(?:\s+Verified|\s{3,}|\n)'), cibId=g(r'CIB subject code:\s+([A-Z]\d{10})'),
                type=g(r'Type of subject:\s+(\w+)').title())
    d = g(r'Date of Inquiry[\s\S]*?(\d{2}-[A-Za-z]{3}-\d{4})')
    mon = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
    subj['reportDate'] = '%s-%02d-%s' % (d[-4:], mon[d[3:6]], d[:2]) if d else ''
    props = {}
    for m in re.finditer(r'Trade Name:\s+(.+?)(?:\s{3,}|\n)[\s\S]{0,300}?Code:([A-Z]\d{10})\)', txt): props[m.group(2)] = m.group(1).strip()
    subj['nid'] = g(r'NID \(17 Digit\):\s+(\d+)') or g(r'NID no:\s+(\d+)'); subj['reg'] = ''
    subj['props'] = [[k, v] for k, v in props.items()]
    a, b, c = txt.find('1. SUMMARY OF FACILITY'), txt.find('2. SUMMARY OF FACILITY'), txt.find('3. SUMMARY OF PRIVATE')
    def sm(x, y):
        t = txt[x:y]; f = lambda rx: n((re.search(rx, t) or [0, ''])[1])
        return dict(inst=f(r'No of reporting Institutes:\s+(\d+)'), live=f(r'No of Living Contracts:\s+(\d+)'), out=f(r'Total Outstanding Amount:\s+([\d,]+)'),
                    od=f(r'Total Overdue Amount:\s+([\d,]+)'), funded=f(r'\(A\) SUMMARY OF THE FUNDED[\s\S]*?Total Outstanding Amount:\s+([\d,]+)'),
                    nonf=f(r'\(B\) SUMMARY OF THE NON-FUNDED[\s\S]*?Total Outstanding Amount:\s+([\d,]+)'))
    summary = dict(borrower=sm(a, b), guarantor=sm(b, c))
    heads = [(i, l.strip()) for i, l in enumerate(L) if l.startswith('DETAILS OF')]
    starts = [i for i, l in enumerate(L) if re.match(r'^\s*Ref\s+FI code', l)]
    F = []
    for bi, s in enumerate(starts):
        e = starts[bi + 1] if bi + 1 < len(starts) else len(L)
        lines = L[s:e]; blk = '\n'.join(lines); left = '\n'.join(l[:95] for l in lines)
        h = [x for x in heads if x[0] < s][-1][1]; k = 'card' if 'CREDIT' in h else 'noninst' if 'NONINST' in h else 'inst'
        ph = re.search(r'Phase:\s+(\S[^\n]*?)\s{2,}', left)
        fac = re.split(r'\s{3,}', (re.search(r'Facility:\s+(.+)', left) or [0, ''])[1].strip())[0]
        f = dict(id=g(r'\b([A-Z]\d{10})\b', blk), subj=g(r'Code:([A-Z]\d{10})', blk), fi=(re.findall(r'^\s*\d\s+\(CIB Subject\s+(\S+)', blk, re.M) or [''])[0],
                 role=g(r'Role:\s+(\w+)', left), live=bool(ph and ph.group(1).strip() == 'Living'), type=short(fac))
        f['funded'] = 'Guarantee' not in fac
        num = lambda rx: n((re.search(rx, left) or [0, ''])[1])
        f.update(limit=num(r'(?:Sanction Limit|Credit limit):\s+([\d,]+)'), sec=num(r'Security Amount:\s+([\d,]+)'), tpg=num(r'Third Party guarantee\s+([\d,]+)'),
                 start=iso(g(r'Starting date:\s+(\S+)', left)), end=iso(g(r'End date of contract:\s+(\S+)', left)), upd=iso(g(r'Date of Last Update:\s+(\S+)', left)))
        cut = next((j for j, l in enumerate(lines) if 'Contribution History' in l), len(lines)); rows = []
        for l in lines[:cut]:
            for m in re.finditer(r'(\d\d/\d\d/\d{4})\s+((?:[\d,]+\s+)+)([A-Z]{2,4})\s+(Yes|No)\b', l):
                v = [n(x) for x in m.group(2).split()]
                if k == 'inst' and len(v) >= 3: o, od = v[0], v[1]; lim = 0
                elif len(v) >= 3: lim, o, od = v[0], v[1], v[2]
                else: continue
                rows.append([iso(m.group(1)), o, od, m.group(3), lim, 1 if m.group(4) == 'Yes' else 0]); f['limit'] = f['limit'] or lim
        f['resch'] = bool(re.search(r'Date of last rescheduling:\s+\d\d/\d\d/\d{4}', left)); f['reorg'] = bool(re.search(r'Reorganized credit:\s+YES', left, re.I)); f['lawsuit'] = bool(re.search(r'Date of Law suit:\s+\d\d/\d\d/\d{4}', left))
        f['hist'] = rows; f['out'] = rows[0][1] if rows else 0; f['od'] = rows[0][2] if rows else 0
        st = rows[0][3] if rows else 'STD'; f['cls'] = 'UC' if st == 'STD' else st
        f['linked'] = [[a, b, c] for a, b, c in re.findall(r'^\s*([A-Z]\d{10})\s+(Borrower|Guarantor|Co-Borrower)\s+(.+?)\s{2,}', blk, re.M)]
        F.append(f)
    names = dict(props); names[subj['cibId']] = subj['name']
    for f in F: f['subjName'] = names.get(f['subj'], f['subj'])
    return dict(subject=subj, summary=summary, facilities=F)

if __name__ == '__main__':
    out = parse(sys.argv[1]); p = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].rsplit('.', 1)[0] + '.json'
    json.dump(out, open(p, 'w'), separators=(',', ':')); print('Saved', p, len(out['facilities']), 'facilities')
