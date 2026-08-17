#!/usr/bin/env python3
"""Oliver board. One card per blog package, plus special projects and reporting.
Regenerate with: python3 build2.py
"""
import json, os, re, base64, subprocess, html, datetime, collections

os.chdir(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open('sheet.json'))
TODAY = datetime.date(2026, 8, 17)
MONTHS = ['MAY 26', 'JUNE 26', 'JULY 26', 'AUGUST 26', 'SEPTEMBER 26']
DOC = 'https://docs.google.com/document/d/%s/edit'
FILE = 'https://drive.google.com/file/d/%s/view'
FOLDER = 'https://drive.google.com/drive/folders/%s'

# ---------------- images ----------------
os.makedirs('thumbs', exist_ok=True)
def _uri(src, out, px, q):
    if not os.path.exists(out):
        subprocess.run(['sips', '-Z', str(px), '-s', 'format', 'jpeg',
                        '-s', 'formatOptions', str(q), src, '--out', out], capture_output=True)
    if not os.path.exists(out): return None
    return 'data:image/jpeg;base64,' + base64.b64encode(open(out, 'rb').read()).decode()

ASPECT = {}
def thumb(p):
    """Returns a data URI and records its aspect ratio, so portrait creatives can be
    shown whole rather than cropped to a landscape card."""
    if not p or not os.path.exists(p): return None
    out = 'thumbs/' + os.path.basename(p).rsplit('.', 1)[0] + '.jpg'
    uri = _uri(p, out, 760, 72)
    if uri and uri not in ASPECT:
        try:
            g = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', out],
                               capture_output=True, text=True).stdout
            w = int(re.search(r'pixelWidth:\s*(\d+)', g).group(1))
            h = int(re.search(r'pixelHeight:\s*(\d+)', g).group(1))
            ASPECT[uri] = w / h
        except Exception:
            ASPECT[uri] = 1.6
    return uri

HERO = _uri('hero_poster.jpg', 'thumbs/hero.jpg', 1600, 62)

# ---------------- text helpers ----------------
def clean(s):
    s = (s or '').replace('​', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return re.sub(r'\n{2,}', '\n', s).strip()

STAGES = ('FEEL', 'BELIEVE', 'KNOW')
def split_title(raw):
    lines = [l.strip() for l in raw.split('\n') if l.strip()]
    if not lines: return '', '', None, None
    first, rest = lines[0], lines[1:]
    m = re.search(r'post\s*#?\s*(\d+)', first, re.I)
    num = 'Post %s' % m.group(1) if m else None
    stage = next((s for s in STAGES if re.search(r'\b' + s + r'\b', first, re.I)), None)
    head = first
    if re.match(r'^\s*(blog|social)?\s*post\s*#?\s*\d*\s*:', head, re.I):
        head = re.sub(r'^\s*(blog|social)?\s*post\s*#?\s*\d*\s*:\s*', '', head, flags=re.I)
        head = re.sub(r'^(FEEL|BELIEVE|KNOW)\b\s*(social)?\s*', '', head, flags=re.I).strip()
    elif re.match(r'^\s*reshare\s+post', head, re.I):
        head = re.sub(r'^\s*reshare\s+post\s*#?\s*\d*\s*', 'Reshare ', head, flags=re.I).strip().rstrip(':')
    if not head and rest: head = rest.pop(0)
    return (head or first).strip(), ' '.join(rest).strip(), num, stage

LEADERS = ('Riyaad', 'Corwyn', 'Gerald')
def person(ch):
    c = (ch or '').replace('-', ' ').lower()
    for n in LEADERS:
        if n.lower() in c: return n
    return 'Brand page' if 'brand' in c else 'Team'

def parse_date(t):
    m = re.search(r'([A-Z][a-z]+)\s+(\d{1,2})', t or '')
    if not m: return None
    try: return datetime.datetime.strptime('%s %s 2026' % m.groups(), '%B %d %Y').date()
    except ValueError: return None

# ---------------- gather calendar posts, grouped by package ----------------
packages = collections.OrderedDict()
for sheet in MONTHS:
    s = D[sheet]
    rowimg = {}
    for k, v in s['imgs'].items():
        rowimg.setdefault(int(k.split(',')[0]), v)
    a_img, a_links, a_pkg = None, [], ''
    for rn in sorted(s['rows'], key=lambda x: int(x)):
        if int(rn) == 1: continue
        c = s['rows'][rn]
        raw = clean(c.get('3', ''))
        if not raw: continue
        fmt = clean(c.get('2', ''))
        resh = 'reshare' in fmt.lower()
        img = thumb(rowimg.get(int(rn)))
        if img and not resh: a_img = img
        links = []
        for col, lab in ((3, 'Copy doc'), (10, 'Design file')):
            u = s['links'].get('%s%s' % (chr(64 + col), rn), '')
            if u.startswith('http'): links.append((lab, u))
        for u in re.findall(r'https://drive\.google\.com/\S+', c.get('10', '')):
            links.append(('Assets', u.rstrip(' ,'))); break
        if links and not resh: a_links = links
        t, pkg, num, stage = split_title(raw)
        if not resh: a_pkg = pkg or t
        key = (a_pkg or t).lower()[:45]
        p = packages.setdefault(key, {'name': a_pkg or t, 'month': sheet.replace(' 26', ''),
                                      'img': None, 'links': [], 'posts': []})
        if a_img and not p['img']: p['img'] = a_img
        if a_links and not p['links']: p['links'] = a_links
        p['posts'].append({
            'num': num, 'stage': stage, 'reshare': resh, 'fmt': fmt,
            'status': clean(c.get('6', '')) or 'No status',
            'person': person(c.get('7', '')), 'channel': clean(c.get('7', '')),
            'date': (parse_date(c.get('1', '')) or TODAY).strftime('%b %-d'),
            'copy': clean(c.get('4', '')), 'todo': clean(c.get('5', '')),
        })

def pkg_for(*keys):
    for k in keys:
        for pk, p in packages.items():
            if k.lower() in pk: return p
    return None

# ---------------- the blogs ----------------
# status / live URLs verified against oliver.app/blog; package docs read directly
BLOGS = [
    dict(title='Making Benefits Human: Why User Experience Matters in Benefits Technology',
         match='making benefits human', status='Live', live='14 Apr 2026',
         url='https://oliver.app/post/making-benefits-human-why-user-experience-matters-in-benefits-technology',
         doc=DOC % '1SxM3O35-7RB0D0FlVGDoYXLwc6SYJbTxKrzav-6tn7o',
         pillar='Better Human Experience', audience='HR, Carriers, TPAs',
         cta='Explore Oliver AD & Connect', news=None, extra=[],
         featured='featured/human.jpg'),
    dict(title='Partnership Over Competition: How Collaboration Builds Better Technology',
         match='partnership over competition', status='Live', live='14 Apr 2026',
         url='https://oliver.app/post/partnership-over-competition-how-collaboration-builds-better-technology',
         doc=DOC % '1kADaTs1XFDwmI3NQhvwDn1JUr0r9TrQUwqYT4kfkbxM',
         pillar='Connected Systems', audience='Carriers, TPAs',
         cta='Start a conversation', news=None, extra=[],
         featured='featured/partnership.png'),
    dict(title='What Makes Oliver an Award-winning Insurance and Benefits Technology Company',
         match='award-winning', status='Live', live='16 Apr 2026',
         url='https://oliver.app/post/what-makes-oliver-an-award-winning-insurance-and-benefits-technology-company',
         doc=DOC % '17d-PrFVDD1wMA3YaVtuAMAd66KOe5c1PNY9hz2jIHe8',
         pillar='Better Human Experience', audience='Carriers, TPAs',
         cta='Establish trust & credibility', news=None, extra=[],
         featured='featured/award.png'),
    dict(title='The Benefits Modernization Checklist: Is Your Organization Ready?',
         match=None, status='Waiting on Oliver review', live=None, url=None,
         doc=DOC % '1rlo1f0ceITdDx--vwRoibbi2IFAUQAT76wZ-zNyRBZI',
         pillar='Simplified Operations',
         audience='Carrier execs (COO/CIO/CTO), TPA operations leaders',
         cta='Get in touch to start the conversation', news=True,
         featured='featured/modernization.jpg',
         manual=dict(brand=3, resh=3, resh_who='Riyaad or Corwyn', graphics=True,
                     note='Package is complete: blog, all three social posts written for '
                          'both brand and leadership accounts, graphics linked, '
                          'newsletter teaser drafted. Waiting on a yes.'),
         todo=[('Review and approve the blog', 'Riyaad'),
               ('Publish to oliver.app once approved', 'Oliver web team'),
               ('Schedule the social package', 'Nicole / F&S')],
         extra=[('Blog draft', DOC % '15L6wV8Gx3UN96t7oItnLRZgdPV7iNUZQ_oQsu31oFAE'),
                ('Interview questions', DOC % '1bpdM-5HrTxTsYmizlldmWzZuQ2wcf63qTlAkZCcAeEQ')]),
    dict(title='How Advisors Close Deals Faster with Instant-issue Insurance',
         match=None, status='Waiting on Oliver review', live=None, url=None,
         doc=DOC % '1q8jVy6LQX2ExMjBc_-S2dY2HAQTffd_U59xYur_Jeuk',
         pillar='Simplified Operations',
         audience='Advisors, distribution partners (the Jason persona)',
         cta='Get in touch', news=False, featured=None,
         manual=dict(brand=0, resh=0, resh_who=None, graphics=False,
                     note='Blog copy is written. The social package is not: every brand and '
                          'leadership LinkedIn field is empty, the newsletter teaser is blank, '
                          'and the two Canva links point at September’s Healthy Habits graphics.'),
         todo=[('Review and approve the blog', 'Riyaad'),
               ('Subject-matter input', 'Luciana'),
               ('Write the three social posts + leadership copy', 'F&S'),
               ('Replace the wrong Canva links', 'F&S')],
         extra=[]),
    dict(title='Healthy Habits Your Body Needs at Every Stage of Life',
         match='healthy habits', status='Approved, not yet live', live=None, url=None,
         doc=DOC % '1ZRqtZzMUeTwQomAZPvkrDYuhHGAkZWLz27LgERTGb50',
         pillar='Not mapped to a story pillar', audience='Plan members',
         cta=None, news=None, featured='featured/healthy.jpg',
         todo=[('Publish the blog so the posts have a link', 'Oliver web team'),
               ('Confirm this fits the 2026 strategy', 'Riyaad / F&S')],
         extra=[]),
]

STANDALONE = dict(title='Independent Social Package', match='independent social',
                  note='Three standalone social posts with no blog behind them.')

def summarise(posts):
    brand = [p for p in posts if not p['reshare']]
    resh = [p for p in posts if p['reshare']]
    def tally(items):
        c = collections.Counter(p['status'] for p in items)
        return ', '.join('%d %s' % (n, s.lower()) for s, n in c.most_common())
    who = collections.Counter(p['person'] for p in resh)
    return brand, resh, tally(brand), tally(resh), who

# ---------------- special projects ----------------
SPECIALS = [
    dict(title='Website Form Analysis & Recommendations', status='Waiting on Oliver review',
         what='An audit of the Request a Demo form on oliver.app, backed by 90 days of '
              'analytics, with prioritised fixes and a clickable prototype of the reworked '
              'form. Headline numbers: form starts fell from 71 in May to 27 in June, while '
              'submits rose from 4 to 5 — so the submit rate went from roughly 6% to 19%.',
         why='Lead forms are the conversion point for every blog, campaign and sales '
             'conversation. The roadmap commits to lifting completed forms from 5 to 8 a month '
             'and holding a 60%+ completion rate — which makes this the one change that '
             'raises the return on all the other content.',
         note_label='The problem', note='The form is a pop-up, not a page. A modal cannot be '
              'linked to from an ad, an email or a social bio; a misclick, the Escape key or '
              'the back button wipes whatever was typed (worse on mobile); and it cannot be '
              'tracked cleanly. The recommendation is a real page at oliver.app/contactus, '
              'plus a lightweight embed near the footer — both pointing at the same endpoint.',
         todo=[('Decide which recommendations to implement', 'Riyaad'),
               ('Build the page and form', 'Oliver web/Webflow dev'),
               ('Fire a GTM conversion event on submit', 'Oliver web/Webflow dev'),
               ('Apply UTMs consistently across outbound links', 'Sonam (F&S) + Oliver'),
               ('Submit the new URL to Search Console', 'Whoever holds access')],
         links=[('Recommendations', DOC % '1iDtYDz0Dwnn2FReiWblD7cnIy7bdlJA3812MitQpIiw'),
                ('Form prototype', 'https://larahkroeker.github.io/fs-apps/clients/OLIVER-form-prototype.html')]),
    dict(title='Sales Deck', status='Waiting on final design',
         what='One modular master deck the team tailors for any audience by removing slides '
              'rather than building new ones. Works as a live presentation or a standalone PDF.',
         why='The roadmap’s sales enablement objective: create a new sales asset that '
             'speaks credibly to carriers, TPAs, advisors, employers and partners, leads with '
             'outcomes rather than features, and stays reusable for years. It is also the '
             'gate on the explainer video — the video follows the deck so both tell the '
             'same story.',
         todo=[('Final design pass', 'Ren (F&S)'),
               ('Sign off so the video can start', 'Riyaad')],
         links=[('Brief', DOC % '12SZ-XivwcoyyENISs9fi_ox3cWHXmbErR-kn18HtmJk'),
                ('Outline', DOC % '12g-yaU2gYWYeLwWzlpq62rGmg55-OtV06384j6NDDd8'),
                ('Draft content', DOC % '111oK-oCsFngkHxUAqEKu5tiR9dZgytbBjis-Op5hvcM'),
                ('Latest deck', FILE % '1aDrTeb0gFOm1Z8XEOADMKGy-Sn4fkBX6')]),
    dict(title='Proposal Deck', status='Drafting',
         what='A reusable proposal template so Oliver can respond to new opportunities '
              'quickly and consistently, in the same visual language as the sales deck.',
         why='Removes the scramble of rebuilding a proposal from scratch each time, and keeps '
             'every proposal on the approved messaging — the roadmap asks that 100% of new '
             'assets align to the messaging framework.',
         note_label='Idea', note='Worth a look while Ren finishes the document version — an interactive '
              'builder where every line is click-to-edit, it saves itself as you type, and '
              'it exports straight to PDF. Same structure as the written proposal — cover, '
              'letter from Gerald, Oliver at-a-glance, clarifying your needs, scope of '
              'services, piloting the transition — but the rep fills in the bracketed fields '
              'in the browser instead of wrangling a Word file.',
         todo=[('Finish the draft', 'F&S'), ('Review', 'Riyaad'),
               ('Decide: document, interactive builder, or both', 'Riyaad / F&S')],
         links=[('Interactive builder (idea)', 'https://larahkroeker.github.io/oliver-proposal-builder/'),
                ('Brief – for review', DOC % '19S5XmKXwES_d6Hq1CckTEXJpMQpm-Z_vIhkpFILZ4cM'),
                ('Draft template', DOC % '1biJwCGtK1u8CtNJp5B9uxHOr5TPGAxbSDzstlUDumgI')]),
    dict(title='Explainer Video', status='Not started — blocked',
         what='A 60–90 second video covering what Oliver is, how the ecosystem fits '
              'together and why it is different. Lives on the Products page, with cutdowns '
              'for LinkedIn and YouTube.',
         why='Gives board members and internal stakeholders a story they can confidently '
             'retell — the roadmap builds a whole persona around this (Lou, the board '
             'director who wants something shareable that is not an internal deck). '
             'Scripting deliberately waits for the sales deck so the narrative matches.',
         todo=[('Approve the sales deck first', 'Riyaad'),
               ('Then scripting and storyboarding', 'F&S')],
         links=[('Brief', DOC % '1GQ0S09WORh1Pgx7R4WmBDaL0PNUnZFtoiaDDmMXFRAk')]),
    dict(title='Webinar Brief', status='Not started',
         what='Scoping for a webinar as a future quarterly special project.',
         why='The roadmap lists webinars under community and trust — a way to put Oliver’s '
             'own experts in front of carriers and TPAs, which the competitor audit found is '
             'exactly what Majesco and Guidewire do well.',
         todo=[('Decide whether this is the next special project', 'Riyaad / F&S')],
         links=[]),
]

REPORTS = [('Monthly report – July 2026', DOC % '1kTe9wOrEvIpzS6uCN_qvHRFaiRJA_s6l4jIk87_rnyc'),
           ('Monthly report – June 2026', DOC % '1dItG-XTrVu2kOY7Zac68kHBcZYTJdJUEe4aRz1x9Kyo'),
           ('Monthly report – May 2026', DOC % '1VgiRDEs_UaQy1IewueS0R3HjysJMBu77QMN1c9-3aOY')]

# why we publish - from the Content Roadmap, OKRs updated July 2026
CHAIN = ['1 blog (the anchor)', '3 social posts', 'Leadership reshares', 'Newsletter teaser']
OBJECTIVES = [
    ('Awareness, visibility &amp; trust',
     '1 long-form asset + 3–4 brand posts a month. LinkedIn following +8–10%, engagement 12%+. '
     'Website sessions 1,084 → 1,250.'),
    ('Differentiation &amp; positioning',
     '5 thought-leadership assets and 2 client stories over the period. 3.5%+ CTR on thought leadership.'),
    ('Leadership visibility',
     'Corwyn 433 → 520 followers. Gerald 1,816 → 2,000. Riyaad 393 → 470.'),
    ('Sales &amp; lead generation',
     'Completed lead forms 5 → 8 a month, 35+ over the period, 60%+ completion rate.'),
]

REF_LINKS = [('Shared drive', FOLDER % '12qJq3J2WVGMKdXkTxcqgOVrZe_PImG7m'),
             ('Content Roadmap', 'https://docs.google.com/presentation/d/1cIEW9bj_QK95hnqB34JlJHz2PAVw3yNqTjffdzDf70g/edit'),
             ('Content Calendar', 'https://docs.google.com/spreadsheets/d/1Wm_pWJqyg4NRmZVk875g7TcV4PKTE8v7WpFoseOMNxA/edit')]

ST = {'Live': 'st-ok', 'Approved, not yet live': 'st-sched',
      'Waiting on Oliver review': 'st-need', 'Waiting on final design': 'st-prog',
      'Drafting': 'st-prog', 'Not started': 'st-idle', 'Not started — blocked': 'st-idle'}
e = html.escape

# ---------------- render ----------------
IMG_CLASS, IMG_CSS = {}, []
def shot(img, label):
    if img:
        if img not in IMG_CLASS:
            IMG_CLASS[img] = 'i%d' % (len(IMG_CLASS) + 1)
            IMG_CSS.append('.%s{background-image:url(%s)}' % (IMG_CLASS[img], img))
        cls = IMG_CLASS[img] + (' fit' if ASPECT.get(img, 1.6) < 1.15 else '')
        return '<div class="shot %s"></div>' % cls
    return '<div class="shot noshot"><span>%s</span></div>' % e(label)

def manifest(rows):
    out = []
    for label, val, ok in rows:
        cls = 'yes' if ok else ('no' if ok is False else 'unk')
        mark = '✓' if ok else ('—' if ok is False else '·')
        out.append('<li class="%s"><i>%s</i><b>%s</b><span>%s</span></li>' % (cls, mark, e(label), e(val)))
    return '<ul class="mani">%s</ul>' % ''.join(out)

def todos(items):
    if not items: return ''
    return ('<div class="todo"><b>Needs doing</b><ul>%s</ul></div>'
            % ''.join('<li>%s <em>%s</em></li>' % (e(w), e(who)) for w, who in items))

def linkrow(links):
    return '<div class="links">%s</div>' % ''.join(
        '<a href="%s" target="_blank" rel="noopener">%s ↗</a>' % (e(u), e(l)) for l, u in links if u)

def blog_card(b):
    p = pkg_for(b['match']) if b.get('match') else None
    posts = p['posts'] if p else []
    img = thumb(b.get('featured')) or (p['img'] if p else None)
    todo = list(b.get('todo', []))
    people = set()

    if posts:
        brand, resh, bt, rt, who = summarise(posts)
        rows = [('Blog', 'Written' + (' · live %s' % b['live'] if b.get('live') else ''), True),
                ('Brand social posts', '%d — %s' % (len(brand), bt) if brand else 'none', bool(brand)),
                ('Leadership reshares',
                 '%d — %s' % (len(resh), ', '.join('%s ×%d' % (k, v) for k, v in who.most_common()))
                 if resh else 'none', bool(resh)),
                ('Graphics', 'In Canva and Drive' if img else 'Not in the calendar', bool(img))]
        pend = [x for x in posts if x['status'] == 'Pending Approval']
        by = collections.Counter(x['person'] for x in pend)
        for nm, n in by.most_common():
            if nm in LEADERS:
                todo.append(('Approve and post %d reshare%s' % (n, 's' if n > 1 else ''), nm))
                people.add(nm)
            else:
                todo.append(('Approve %d brand post%s' % (n, 's' if n > 1 else ''), 'Riyaad'))
                people.add('Riyaad')
        if any('live blog link' in x['todo'].lower() for x in posts):
            todo.append(('Add the live blog link to the posts', 'Oliver web team'))
    else:
        m = b.get('manual', {})
        rows = [('Blog', 'Written, not published', True),
                ('Brand social posts', '3 written' if m.get('brand') else 'not written yet',
                 bool(m.get('brand'))),
                ('Leadership reshares',
                 'written for %s' % m['resh_who'] if m.get('resh') else 'not written yet',
                 bool(m.get('resh'))),
                ('Graphics', 'Canva linked' if m.get('graphics') else 'wrong links / missing',
                 bool(m.get('graphics'))),
                ('Newsletter teaser', 'Drafted' if b.get('news') else 'blank', bool(b.get('news')))]
        people.add('Riyaad')

    note = '<p class="note2">%s</p>' % e(b['manual']['note']) if b.get('manual') else ''
    postlist = ''
    if posts:
        items = ''.join(
            '<li><span class="pl">%s</span> %s<em>%s</em>%s</li>'
            % (e(' · '.join(x for x in (x['num'], x['stage'], x['fmt']) if x)),
               e(re.sub(r'\s*-\s*', ' – ', x['channel'])), e(x['status']),
               '<p>%s</p>' % e(x['copy'][:400] + ('…' if len(x['copy']) > 400 else '')) if x['copy'] else '')
            for x in posts)
        postlist = ('<details><summary>The %d posts in this package</summary>'
                    '<ol class="posts">%s</ol></details>' % (len(posts), items))

    why = ('<div class="why"><b>Why this exists</b><span>%s · %s</span>%s</div>'
           % (e(b['pillar']), e(b['audience']),
              '<span>CTA: %s</span>' % e(b['cta']) if b.get('cta') else ''))
    links = ([('Read it live', b['url'])] if b.get('url') else []) + \
            [('Package doc', b['doc'])] + b.get('extra', [])
    return ('<article class="card" data-b="%s" data-p="%s">%s<div class="body">'
            '<div class="chips"><span class="chip %s">%s</span>%s</div><h3>%s</h3>%s%s%s%s%s%s</div></article>'
            % ('live' if b['status'] == 'Live' else ('needs' if 'Waiting' in b['status'] else 'prog'),
               e(' '.join(sorted(people)) or 'Team'),
               shot(img, 'No creative yet'), ST.get(b['status'], 'st-idle'), e(b['status']),
               ''.join('<span class="chip st-who">%s</span>' % e(x) for x in sorted(people) if x in LEADERS),
               e(b['title']), why, note, manifest(rows), todos(todo), postlist, linkrow(links)))

def special_card(s):
    return ('<article class="card" data-b="%s" data-p="Team">%s<div class="body">'
            '<div class="chips"><span class="chip %s">%s</span></div><h3>%s</h3>'
            '<p class="ex">%s</p><div class="why"><b>Why this matters</b><span>%s</span></div>'
            '%s%s%s</div></article>'
            % ('needs' if 'Waiting on Oliver' in s['status'] else
               ('prog' if s['status'] in ('Drafting', 'Waiting on final design') else 'idle'),
               shot(None, 'Special project'), ST.get(s['status'], 'st-idle'), e(s['status']),
               e(s['title']), e(s['what']), e(s['why']),
               '<p class="note2"><b>%s</b> %s</p>' % (e(s.get('note_label','Note')), e(s['note']))
               if s.get('note') else '',
               todos(s['todo']), linkrow(s['links'])))

sp = pkg_for(STANDALONE['match'])
extra_content = ''
if sp:
    brand, resh, bt, rt, who = summarise(sp['posts'])
    pend = collections.Counter(x['person'] for x in sp['posts'] if x['status'] == 'Pending Approval')
    extra_content = ('<article class="card" data-b="needs" data-p="%s">%s<div class="body">'
                     '<div class="chips"><span class="chip st-need">Awaiting approval</span></div>'
                     '<h3>%s</h3><p class="ex">%s</p>%s%s%s</div></article>'
                     % (e(' '.join(sorted(k for k in pend if k in LEADERS))),
                        shot(sp['img'], 'Social only'), e(STANDALONE['title']),
                        e(STANDALONE['note']),
                        manifest([('Brand social posts', '%d — %s' % (len(brand), bt), True),
                                  ('Leadership reshares', '%d — %s' % (len(resh), ', '.join(
                                      '%s ×%d' % (k, v) for k, v in who.most_common())), True),
                                  ('Blog behind it', 'none', False)]),
                        todos([('Approve and post %d reshare%s' % (n, 's' if n > 1 else ''), nm)
                               for nm, n in pend.most_common() if nm in LEADERS] +
                              [('Approve the brand posts', 'Riyaad')]),
                        linkrow(sp['links'])))

n_live = sum(1 for b in BLOGS if b['status'] == 'Live')
n_wait = sum(1 for b in BLOGS if b['status'] != 'Live')
n_social = sum(1 for p in packages.values() for x in p['posts'] if x['status'] == 'Pending Approval')

SEC = [('blogs', 'Blogs', 'One card per blog: what is in the package and what still needs doing.',
        '\n'.join(blog_card(b) for b in BLOGS) + extra_content),
       ('special', 'Special projects', 'Sales deck, explainer video, proposal, form recommendations.',
        '\n'.join(special_card(s) for s in SPECIALS)),
       ('reporting', 'Reporting', 'Monthly performance against the roadmap OKRs.',
        '\n'.join('<article class="card" data-b="live" data-p="Team">%s<div class="body">'
                  '<div class="chips"><span class="chip st-ok">Delivered</span></div>'
                  '<h3>%s</h3>%s</div></article>' % (shot(None, 'Report'), e(t), linkrow([('Open', u)]))
                  for t, u in REPORTS))]

LOGO = open('logo.svg').read() if os.path.exists('logo.svg') else ''

TPL = open('template.html').read()
for tok, val in (
    ('@@LOGO@@', LOGO),
    ('@@REFS@@', ''.join('<a href="%s" target="_blank" rel="noopener">%s ↗</a>' % (u, l)
                         for l, u in REF_LINKS)),
    ('@@N_LIVE@@', str(n_live)), ('@@N_WAIT@@', str(n_wait)), ('@@N_SOCIAL@@', str(n_social)),
    ('@@N_SPECIAL@@', str(len(SPECIALS))), ('@@N_REPORTS@@', str(len(REPORTS))),
    ('@@SECTIONS@@', ''.join(
        '<section class="sec" data-g="%s"><div class="sechead"><h2>%s</h2><p>%s</p></div>'
        '<div class="grid">%s</div></section>' % (k, n, d, c) for k, n, d, c in SEC)),
    ('@@CHAIN@@', ''.join('<span>%s</span>' % x for x in CHAIN)),
    ('@@OBJS@@', ''.join('<div class="obj"><b>%s</b><span>%s</span></div>' % (n, d)
                         for n, d in OBJECTIVES)),
    ('@@IMG_CSS@@', '\n'.join(IMG_CSS)), ('@@HERO@@', HERO),
):
    TPL = TPL.replace(tok, val)
OUT = '../../clients/OLIVER-content-board.html'
open(OUT, 'w').write(TPL)
print('blogs %d (live %d, waiting %d) | specials %d | social pending %d | %.2f MB'
      % (len(BLOGS), n_live, n_wait, len(SPECIALS), n_social,
         os.path.getsize(OUT) / 1e6))
