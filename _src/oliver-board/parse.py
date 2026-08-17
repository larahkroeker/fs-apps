import zipfile, re, json, os
import xml.etree.ElementTree as ET

NS = {
 'm':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
 'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
 'xdr':'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
 'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
 'pr':'http://schemas.openxmlformats.org/package/2006/relationships',
}
z = zipfile.ZipFile('calendar.xlsx')

# shared strings
ss = []
root = ET.fromstring(z.read('xl/sharedStrings.xml'))
for si in root.findall('m:si', NS):
    ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))

# workbook sheet order -> rels
wb = ET.fromstring(z.read('xl/workbook.xml'))
rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
relmap = {r.get('Id'): r.get('Target') for r in rels}
sheets = []
for sh in wb.find('m:sheets', NS):
    rid = sh.get('{%s}id' % NS['r'])
    tgt = relmap[rid].lstrip('/')
    if not tgt.startswith('xl/'): tgt = 'xl/' + tgt
    sheets.append((sh.get('name'), tgt))

def colnum(ref):
    c = re.match(r'([A-Z]+)', ref).group(1)
    n = 0
    for ch in c: n = n*26 + (ord(ch)-64)
    return n

os.makedirs('media', exist_ok=True)
out = {}
for name, path in sheets:
    sx = ET.fromstring(z.read(path))
    rows = {}
    for row in sx.iter('{%s}row' % NS['m']):
        rn = int(row.get('r'))
        cells = {}
        for c in row.findall('m:c', NS):
            ref = c.get('r'); t = c.get('t')
            v = c.find('m:v', NS); isv = c.find('m:is', NS)
            val = ''
            if t == 's' and v is not None:
                val = ss[int(v.text)]
            elif isv is not None:
                val = ''.join(x.text or '' for x in isv.iter('{%s}t' % NS['m']))
            elif v is not None:
                val = v.text or ''
            if val.strip(): cells[colnum(ref)] = val.strip()
        if cells: rows[rn] = cells

    # hyperlinks
    links = {}
    relp = path.replace('worksheets/', 'worksheets/_rels/') + '.rels'
    srel = {}
    if relp in z.namelist():
        rr = ET.fromstring(z.read(relp))
        srel = {x.get('Id'): x.get('Target') for x in rr}
    for hl in sx.iter('{%s}hyperlink' % NS['m']):
        rid = hl.get('{%s}id' % NS['r'])
        tgt = srel.get(rid, hl.get('location', ''))
        links[hl.get('ref')] = tgt

    # images via drawing
    imgs = {}
    dr = sx.find('m:drawing', NS)
    if dr is not None:
        drid = dr.get('{%s}id' % NS['r'])
        dpath = srel.get(drid, '')
        dpath = os.path.normpath(os.path.join('xl/worksheets', dpath)).replace('\\', '/')
        if dpath in z.namelist():
            drels_p = dpath.replace('drawings/', 'drawings/_rels/') + '.rels'
            drels = {}
            if drels_p in z.namelist():
                dr2 = ET.fromstring(z.read(drels_p))
                drels = {x.get('Id'): x.get('Target') for x in dr2}
            dxml = ET.fromstring(z.read(dpath))
            for anch in list(dxml):
                frm = anch.find('xdr:from', NS)
                blip = anch.find('.//a:blip', NS)
                if frm is None or blip is None: continue
                rowi = int(frm.find('xdr:row', NS).text) + 1
                coli = int(frm.find('xdr:col', NS).text) + 1
                embed = blip.get('{%s}embed' % NS['r'])
                tgt = drels.get(embed, '')
                mp = os.path.normpath(os.path.join('xl/drawings', tgt)).replace('\\', '/')
                if mp in z.namelist():
                    fn = 'media/%s_r%d_c%d_%s' % (name.replace(' ', '').replace("'", ''), rowi, coli, os.path.basename(mp))
                    with open(fn, 'wb') as f: f.write(z.read(mp))
                    imgs['%d,%d' % (rowi, coli)] = fn
    out[name] = {'rows': rows, 'links': links, 'imgs': imgs}

json.dump(out, open('sheet.json', 'w'), indent=1)
for n, d in out.items():
    print('==', n, 'rows:', len(d['rows']), 'links:', len(d['links']), 'imgs:', len(d['imgs']))
