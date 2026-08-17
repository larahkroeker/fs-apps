#!/usr/bin/env python3
"""Pull the featured image out of a package doc: the photo directly under the blog title."""
import json, base64, zipfile, re, sys, os
import xml.etree.ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def extract(b64path, outstem, anchor_words):
    d = json.load(open(b64path))
    docx = outstem + '.docx'
    open(docx, 'wb').write(base64.b64decode(d['content']))
    z = zipfile.ZipFile(docx)
    rels = {r.get('Id'): r.get('Target') for r in
            ET.fromstring(z.read('word/_rels/document.xml.rels'))}
    doc = ET.fromstring(z.read('word/document.xml'))

    # walk the body in document order, recording text and image rIds
    seq = []
    for el in doc.iter():
        tag = el.tag.split('}')[-1]
        if tag == 't' and el.text:
            seq.append(('t', el.text))
        elif tag == 'blip':
            rid = el.get('{%s}embed' % R)
            if rid: seq.append(('img', rid))

    # find the anchor (blog title), then the first image after it
    idx = None
    joined = ''
    marks = []
    for i, (k, v) in enumerate(seq):
        if k == 't':
            joined += v
            marks.append((len(joined), i))
    low = joined.lower()
    pos = -1
    for w in anchor_words:
        pos = low.find(w.lower())
        if pos >= 0: break
    if pos >= 0:
        for cum, i in marks:
            if cum >= pos:
                idx = i; break

    imgs = [(i, v) for i, (k, v) in enumerate(seq) if k == 'img']
    pick = next((v for i, v in imgs if idx is not None and i > idx), None)
    if pick is None and imgs:
        pick = imgs[0][1]
    if pick is None:
        print('  no images found'); return None

    tgt = rels[pick]
    path = 'word/' + tgt.lstrip('/')
    ext = os.path.splitext(path)[1] or '.png'
    out = outstem + ext
    open(out, 'wb').write(z.read(path))
    print('  anchor at char %s | %d images in doc | picked %s -> %s (%d bytes)'
          % (pos, len(imgs), tgt, out, os.path.getsize(out)))
    return out

if __name__ == '__main__':
    extract(sys.argv[1], sys.argv[2], sys.argv[3:])
