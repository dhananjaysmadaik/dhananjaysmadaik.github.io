"""Builds two versions of the portfolio from one source:
   1. GitHub Pages site (index.html + assets + reports) with self-hosted fonts and a strict Content-Security-Policy.
   2. Artifact page fragment that loads the same fonts from Google Fonts.
"""
import json, hashlib, base64, html, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from content import PROJECTS, EXPERIENCE, TOOLKIT, CATS

SRC = pathlib.Path(__file__).parent
SITE = SRC.parent
META = json.load(open(SRC / 'img_meta.json'))
e = html.escape

LINKEDIN = 'https://www.linkedin.com/in/dhananjaysinghmadaik/'
GITHUB = 'https://github.com/gis-14340308'

ICONS = {
 'arrow-ur': '<path d="M7 17 17 7M8 7h9v9"/>',
 'arrow-r': '<path d="M4 12h15M13 6l6 6-6 6"/>',
 'arrow-l': '<path d="M20 12H5M11 6l-6 6 6 6"/>',
 'close': '<path d="M6 6l12 12M18 6 6 18"/>',
 'plus': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5M11 8.2v5.6M8.2 11h5.6"/>',
 'minus': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5M8.2 11h5.6"/>',
 'reset': '<path d="M4 4v6h6"/><path d="M4.6 14.5A8 8 0 1 0 6 7l-2 3"/>',
 'doc': '<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z"/><path d="M14 3v5h5M8.5 13h7M8.5 16.5h7"/>',
 'ext': '<path d="M14 4h6v6M20 4l-9 9"/><path d="M19 14v4.5A1.5 1.5 0 0 1 17.5 20h-12A1.5 1.5 0 0 1 4 18.5v-12A1.5 1.5 0 0 1 5.5 5H10"/>',
 'mail': '<rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="m4 6.5 8 6 8-6"/>',
 'in': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 10.5V17M8 7.2v.01M12 17v-3.6c0-1.6 1-2.6 2.3-2.6s2.2 1 2.2 2.6V17M12 10.5V17"/>',
 'gh': '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
 # category map symbols
 'cat-hazards': '<path d="M2.5 19.5 9 7l4 6.5 2.5-4 6 10z"/><path d="M9 7l1.4 2.6"/>',
 'cat-rs': '<rect x="3.5" y="3.5" width="17" height="17"/><path d="M9.2 3.5v17M14.8 3.5v17M3.5 9.2h17M3.5 14.8h17"/><rect x="9.2" y="9.2" width="5.6" height="5.6" fill="currentColor" stroke="none"/><rect x="14.8" y="3.5" width="5.7" height="5.7" fill="currentColor" stroke="none" opacity=".45"/>',
 'cat-survey': '<circle cx="12" cy="12" r="6"/><path d="M12 2v6M12 16v6M2 12h6M16 12h6"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/>',
 'cat-census': '<path d="M4 6.5 11 3l9 4.5-1.5 11L9 21l-6-5z"/><path d="M5.5 15 15 5.8M8 18.5l10.6-9.7M3.8 11 11 4.2"/>',
 'cat-python': '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16"/>',
 'all': '<circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="6.5" r="2.5"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
}
def icon(name, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'

def img(key, alt, sm=True, eager=False, pos=None, cls=''):
    m = META[key]
    w, h = m['sw'], m['sh']
    src = f'thumbs/{key}.webp'
    style = f' style="object-position:{pos}"' if pos else ''
    load = 'eager' if eager else 'lazy'
    c = f' class="{cls}"' if cls else ''
    return f'<img{c} src="{src}" width="{w}" height="{h}" alt="{e(alt)}" loading="{load}" decoding="async"{style}>'

def tags_ul(tags):
    return '<ul class="tags">' + ''.join(f'<li>{e(t)}</li>' for t in tags) + '</ul>'

def meta_row(p):
    return (f'<div class="meta label"><span class="cat">{icon("cat-"+p["cat"])}{e(p["cat_label"])}</span>'
            f'<span>{e(p["date"])}</span></div>')

# ---------------- cards ----------------
def card(p, featured=False):
    alt = p['figs'][0][1] if p['figs'][0][0] == p['thumb'] else dict(p['figs']).get(p['thumb'], p['title'])
    thumb = f'<div class="thumb">{"<span class=featured-flag>Dissertation</span>" if featured else ""}{img(p["thumb"], alt, pos=p.get("thumb_pos"))}</div>'
    stats = ''
    if featured:
        stats = '<div class="stats">' + ''.join(f'<div><b>{e(v)}</b><span>{e(l)}</span></div>' for v, l in p['stats']) + '</div>'
    return (f'<article class="card{" featured" if featured else ""}" data-tags="{" ".join(p["tags"])}">{thumb}'
            f'<div class="body">{meta_row(p)}<h3><a href="#{p["id"]}" data-case="{p["id"]}">{e(p["card_title"])}</a></h3>'
            f'<p>{e(p["summary"])}</p>{stats}{tags_ul(p["card_tags"])}'
            f'<span class="open-hint" aria-hidden="true">Read the case study {icon("arrow-r")}</span></div></article>')

# ---------------- case studies ----------------
def fig(key, cap):
    m = META[key]
    return (f'<figure class="fig"><button type="button" data-full="maps/{key}.webp" data-thumb="thumbs/{key}.webp" data-w="{m["w"]}" data-h="{m["h"]}" aria-label="Enlarge: {e(cap)}">'
            f'{img(key, cap)}</button><figcaption>{e(cap)}</figcaption></figure>')

def report_links(p):
    links = []
    if p.get('report'):
        links.append(f'<a class="btn btn-primary btn-sm" href="{p["report"]}" target="_blank" rel="noopener">{e(p["report_label"])} {icon("doc")}</a>')
    for part in p.get('parts', []):
        if part.get('report'):
            links.append(f'<a class="btn btn-primary btn-sm" href="{part["report"]}" target="_blank" rel="noopener">{e(part["title"])} report (PDF) {icon("doc")}</a>')
    return links

def side(p):
    out = []
    links = []
    if p.get('report'):
        links.append(f'<a class="btn btn-primary btn-sm" href="{p["report"]}" target="_blank" rel="noopener">{e(p["report_label"])} {icon("doc")}</a>')
    for part in p.get('parts', []):
        if part.get('report'):
            links.append(f'<a class="btn btn-primary btn-sm" href="{part["report"]}" target="_blank" rel="noopener">{e(part["title"])} report (PDF) {icon("doc")}</a>')
    for url, label, note in p.get('extra_links', []):
        links.append(f'<a class="btn btn-ghost btn-sm" href="{url}" target="_blank" rel="noopener noreferrer">{e(label)} {icon("ext")}</a><p style="margin-top:.5rem">{e(note)}</p>')
    if links or p.get('report_note'):
        note = f'<p>{e(p["report_note"])}</p>' if p.get('report_note') else ''
        out.append(f'<div class="side-box"><h4>Report</h4>{"".join(links)}{note}</div>')
    out.append('<div class="side-box"><h4>At a glance</h4><ul>' + ''.join(f'<li><span class="label" style="display:block">{e(k)}</span>{e(v)}</li>' for k, v in p['context']) + '</ul></div>')
    out.append('<div class="side-box"><h4>Tools & methods</h4><ul>' + ''.join(f'<li>{e(t)}</li>' for t in p['tools']) + '</ul></div>')
    if p.get('crs'):
        out.append(f'<div class="side-box"><h4>Coordinate reference</h4><p>{e(p["crs"])}</p></div>')
    return '<aside class="case-side">' + ''.join(out) + '</aside>'

def head_links(p):
    l = report_links(p)
    return f'<div class="case-links">{"".join(l)}</div>' if l else ''

def case(p, idx):
    meta = (f'<div class="case-meta"><span class="label" style="display:inline-flex;gap:.45rem;align-items:center">{icon("cat-"+p["cat"])}{e(p["cat_label"])}</span>'
            f'<span class="label">{e(p["date"])}</span></div>')
    stats = '<div class="case-stats stats">' + ''.join(f'<div><b>{e(v)}</b><span>{e(l)}</span></div>' for v, l in p['stats']) + '</div>'
    body = []
    if 'question' in p:
        body.append(f'<section><h3>The question</h3><p class="q">{e(p["question"])}</p></section>')
    if 'data' in p:
        body.append('<section><h3>Data</h3><ul class="findings" style="gap:.4rem">' + ''.join(f'<li style="padding-left:1.4rem">{e(d)}</li>' for d in p['data']) + '</ul></section>')
    if 'steps' in p:
        body.append('<section><h3>What I did</h3><ol class="steps">' + ''.join(f'<li><span>{e(s)}</span></li>' for s in p['steps']) + '</ol></section>')
    if 'weights' in p:
        mx = max(w for _, w in p['weights'])
        body.append('<section><h3>Factor weights in the susceptibility model</h3><div class="weights" role="list">' +
                    ''.join(f'<div role="listitem"><span>{e(n)}</span><i style="width:{w/mx*100:.0f}%"></i><span>{w}%</span></div>' for n, w in p['weights']) + '</div></section>')
    for part in p.get('parts', []):
        code = ''
        if part.get('code'):
            c = e(part['code'])
            c = re.sub(r'\b(def|for|in|if|return)\b', r'<span class="k">\1</span>', c)
            code = f'<pre class="code"><code>{c}</code></pre>'
        body.append(f'<section class="case-part"><span class="label">{e(part["when"])}</span><h4>{e(part["title"])}</h4><p>{e(part["text"])}</p>'
                    f'<ol class="steps" style="margin-top:1.2rem">' + ''.join(f'<li><span>{e(s)}</span></li>' for s in part['steps']) + '</ol>'
                    f'{code}<ul class="findings" style="margin-top:1.2rem"><li>{e(part["result"])}</li></ul></section>')
    if 'findings' in p:
        body.append('<section><h3>What I found</h3><ul class="findings">' + ''.join(f'<li>{e(f)}</li>' for f in p['findings']) + '</ul></section>')
    body.append('<section><h3>Limits I flagged</h3><ul class="limits">' + ''.join(f'<li>{e(l)}</li>' for l in p['limits']) + '</ul></section>')
    figs = '<section class="figs"><h3>Maps and figures · select any to enlarge and zoom</h3><div class="fig-grid">' + ''.join(fig(k, c) for k, c in p['figs']) + '</div></section>'
    foot = (f'<nav class="case-foot" aria-label="More projects"><button type="button" class="icon-btn" data-go-label="prev">{icon("arrow-l")}<span></span></button>'
            f'<button type="button" class="icon-btn" data-go-label="next"><span></span>{icon("arrow-r")}</button></nav>')
    return (f'<article class="case-src" id="{p["id"]}" data-title="{e(p["card_title"])}" hidden><div class="wrap case-inner">'
            f'<header class="case-head">{meta}<h2>{e(p["title"])}</h2><p class="lead">{e(p["lead"])}</p>{head_links(p)}</header>{stats}'
            f'<div class="case-cols"><div class="case-body">{"".join(body)}</div>{side(p)}</div>{figs}{foot}</div></article>')

# ---------------- sections ----------------
def filters():
    counts = {k: sum(1 for p in PROJECTS if k in p['tags']) for k in CATS}
    chips = [f'<button type="button" class="chip" data-filter="all" aria-pressed="true">{icon("all")}All <small>{len(PROJECTS)}</small></button>']
    for k, label in CATS.items():
        chips.append(f'<button type="button" class="chip" data-filter="{k}" aria-pressed="false">{icon("cat-"+k)}{e(label)} <small>{counts[k]}</small></button>')
    return '<div class="filters" role="group" aria-label="Filter projects by theme">' + ''.join(chips) + '</div>'

def experience():
    out = []
    for x in EXPERIENCE:
        link = f' <a href="#{x["case"]}" data-case="{x["case"]}">See the project</a>' if x.get('case') else ''
        out.append(f'<article class="role"><p class="label">{e(x["when"])}</p><div><h3>{e(x["role"])}</h3><p class="org">{e(x["org"])}{link}</p>'
                   '<ul>' + ''.join(f'<li>{e(pt)}</li>' for pt in x['points']) + '</ul></div></article>')
    return ''.join(out)

def toolkit():
    out = []
    for title, ic, items in TOOLKIT:
        lis = ''.join(f'<li><span>{e(a)}</span>{f"<small>{e(b)}</small>" if b else ""}</li>' for a, b in items)
        out.append(f'<section><span class="label" style="display:inline-flex">{icon("cat-"+ic)}</span><h3>{e(title)}</h3><ul>{lis}</ul></section>')
    return ''.join(out)

LEGEND_SYMBOLS = {
 'poly': '<svg viewBox="0 0 30 22" aria-hidden="true"><path d="M3 15 9 4l7 3 6-3 5 9-7 6H8z" fill="#6F4E37" fill-opacity=".25" stroke="#6F4E37" stroke-width="1.3"/></svg>',
 'ramp': '<svg viewBox="0 0 30 22" aria-hidden="true"><defs><linearGradient id="lg-r" x1="0" x2="1"><stop offset="0" stop-color="#E5E4E2"/><stop offset=".5" stop-color="#C08A5B"/><stop offset="1" stop-color="#6F4E37"/></linearGradient></defs><rect x="1" y="5" width="28" height="12" fill="url(#lg-r)" stroke="#2E2119" stroke-width=".8"/></svg>',
 'gcp': '<svg viewBox="0 0 30 22" aria-hidden="true" fill="none" stroke="#007BA7" stroke-width="1.4"><circle cx="15" cy="11" r="6"/><path d="M15 1v6M15 15v6M5 11h6M19 11h6"/></svg>',
 'grid': '<svg viewBox="0 0 30 22" aria-hidden="true" fill="none" stroke="#2E2119" stroke-width=".9"><rect x="2" y="2" width="26" height="18"/><path d="M10.7 2v18M19.3 2v18M2 11h26"/><rect x="10.7" y="2" width="8.6" height="9" fill="#6F4E37" fill-opacity=".55" stroke="none"/></svg>',
}

def page_body():
    feat = [p for p in PROJECTS if p['id'] == 'landslide'][0]
    rest = [p for p in PROJECTS if p['id'] != 'landslide']
    return f'''
<a class="skip" href="#main">Skip to content</a>
<header class="site-head" id="site-head">
  <div class="wrap head-row">
    <a class="wordmark" href="#top">Dhananjay <em>Singh Madaik</em></a>
    <nav class="nav" aria-label="Primary"><ul>
      <li><a href="#work">Work</a></li><li><a href="#experience">Experience</a></li><li><a href="#toolkit">Toolkit</a></li><li><a href="#about">About</a></li><li><a href="#contact">Contact</a></li>
    </ul></nav>
    <div class="head-cta">
      <a class="btn btn-primary btn-sm" href="#contact">Get in touch {icon("arrow-ur")}</a>
      <button class="menu-btn" id="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav"><span id="menu-label">Menu</span></button>
    </div>
  </div>
  <div class="wrap mobile-nav" id="mobile-nav" hidden>
    <a href="#work">Work</a><a href="#experience">Experience</a><a href="#toolkit">Toolkit</a><a href="#about">About</a><a href="#contact">Contact</a>
    <a class="btn btn-primary" href="#contact">Get in touch {icon("arrow-ur")}</a>
  </div>
</header>

<main id="main">
<section class="band on-mocha hero" id="top" aria-labelledby="hero-title">
  <canvas id="contours" aria-hidden="true"></canvas>
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <p class="label"><span>GIS</span><span>·</span><span>Earth observation</span><span>·</span><span>UAV survey</span><span>·</span><span>Manchester, UK</span></p>
        <h1 class="display" id="hero-title">Reading the land from <em>orbit, air and ground.</em></h1>
        <p class="lead">I’m Dhananjay Singh Madaik, an MSc Geographical Information Science graduate from the University of Manchester with a forestry degree behind me. I map landslides, track vegetation change from satellites, survey woodland by drone and turn census data into evidence people can act on.</p>
        <div class="hero-ctas">
          <a class="btn btn-primary" href="#work">See the work {icon("arrow-r")}</a>
          <a class="btn btn-ghost" href="#contact">Get in touch</a>
        </div>
      </div>
      <aside class="legend" aria-label="Portfolio at a glance">
        <h2>Legend · selected work</h2>
        <ul>
          <li>{LEGEND_SYMBOLS["poly"]}<div><b>179</b><span>landslides hand-digitised along NH-5, Kinnaur</span></div></li>
          <li>{LEGEND_SYMBOLS["ramp"]}<div><b>2000–2024</b><span>Landsat NDVI record, Himachal Pradesh</span></div></li>
          <li>{LEGEND_SYMBOLS["gcp"]}<div><b>2</b><span>woodlands surveyed by UAV, Cornwall</span></div></li>
          <li>{LEGEND_SYMBOLS["grid"]}<div><b>12</b><span>LSOAs harmonised for a Manchester park study</span></div></li>
        </ul>
        <div class="foot">
          <p class="label" style="color:var(--umber);margin:0">Source: my MSc, dissertation and placement work</p>
          <svg class="northarrow" viewBox="0 0 22 30" aria-hidden="true"><path d="M11 1 19 25l-8-5-8 5z" fill="currentColor" fill-opacity=".85"/><path d="M11 1v19" stroke="#E5E4E2" stroke-width="1"/><text x="11" y="29.5" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="6" fill="currentColor">N</text></svg>
        </div>
      </aside>
    </div>
    <div class="hero-margin">
      <p class="label">Kafaur 31°34′N 77°50′E → Khab 31°48′N 78°38′E</p>
      <p class="label">Background: generated contours, not real terrain</p>
    </div>
  </div>
</section>

<section class="band" id="work" aria-labelledby="work-title">
  <div class="wrap">
    <div class="sec-head">
      <p class="label">Selected work</p>
      <h2 class="h2" id="work-title">Seven projects, <em>from Himalayan slopes to Manchester streets.</em></h2>
      <p class="lead">Each case study sets out the question, the data, what I did, what I found and the limits, with every map at full size.</p>
    </div>
    {filters()}
    <p class="label count" id="work-count" aria-live="polite">Showing {len(PROJECTS)} projects</p>
    {card(feat, featured=True)}
    <div class="grid">{"".join(card(p) for p in rest)}</div>
    <p class="empty" id="work-empty" hidden>No projects match this filter.</p>
  </div>
</section>

<section class="band on-loam" id="experience" aria-labelledby="xp-title">
  <div class="wrap xp">
    <div class="sec-head">
      <p class="label">Experience</p>
      <h2 class="h2" id="xp-title">Field, office <em>and research.</em></h2>
      <p class="lead">Mapping for a state government, environmental baselines for a consultancy, forest fieldwork and a university research placement.</p>
    </div>
    <div>{experience()}</div>
  </div>
</section>

<section class="band" id="toolkit" aria-labelledby="kit-title">
  <div class="wrap">
    <div class="sec-head">
      <p class="label">Toolkit</p>
      <h2 class="h2" id="kit-title">What I <em>work with.</em></h2>
      <p class="lead">Grouped the way the work happens: capture, measure, analyse, automate. Levels are stated where a tool is still developing.</p>
    </div>
    <div class="kit">{toolkit()}</div>
  </div>
</section>

<section class="band on-mocha" id="about" aria-labelledby="about-title">
  <div class="wrap">
    <div class="sec-head">
      <p class="label">About</p>
      <h2 class="h2" id="about-title">A forester who <em>learned to map from above.</em></h2>
    </div>
    <div class="about-grid">
      <div class="about-copy">
        <p>I grew up in Shimla and studied forests on foot in Himachal Pradesh before studying them from orbit in Manchester.</p>
        <p>My BSc (Hons) in Forestry covered geomatics, forest mensuration, hydrology and watershed management, geology and soils. Field training in Kullu covered forest nurseries and erosion-control works on steep catchments.</p>
        <p>My MSc in Geographical Information Science added Python, Google Earth Engine, SAR and UAV survey. Most of my projects end in a practical decision, such as where to inspect slopes, where to target green space, or whether a park’s users are new or long-standing residents.</p>
        <p>Outside the map I am a Global Shaper in the World Economic Forum’s Global Shapers Community, was elected Academic Representative for 54 GIS students, and from 2022 to 2025 ran blood-donation camps and tree-planting drives with The Voice, an NGO in India.</p>
      </div>
      <div class="edu">
        <article><p class="label">Sep 2025 – Sep 2026</p><h3>MSc Geographical Information Science</h3><p>The University of Manchester · Expected: Merit</p><p style="margin-top:.6rem">Modules include Data Acquisition for GI Scientists, Environmental Monitoring and Modelling Practice, GIS and Environmental Applications, Understanding GIS (Python), Environmental Remote Sensing and Fundamentals of SAR.</p></article>
        <article><p class="label">Nov 2020 – Jul 2024</p><h3>BSc (Hons) Forestry</h3><p>Dr YS Parmar University of Horticulture and Forestry, India · OGPA 7.80/10</p></article>
        <article><p class="label">Publication · 2024</p><div class="pub"><cite>Madaik, D.S. and Negi, M. (2024) ‘Mapping flames: leveraging remote sensing and GIS for forest fire prevention’, <i>TerraGreen</i>, 17(9), pp. 46–48.</cite></div></article>
      </div>
    </div>
    <div class="creds">
      <div><h3>Certifications & memberships</h3><ul>
        <li>CAA Flyer ID, A1/A3 Open Category<span>UK Civil Aviation Authority · Oct 2025 – Oct 2030</span></li>
        <li>Student Member<span>Royal Institution of Chartered Surveyors (RICS) · from Nov 2026</span></li>
        <li>Network Member<span>Association for Geographic Information (AGI) · from Mar 2026</span></li>
        <li>Student Member<span>International Association of Geodesy (IAG) · Apr – Dec 2026</span></li>
      </ul></div>
      <div><h3>Leadership & volunteering</h3><ul>
        <li>Global Shaper, Global Shapers Community<span>Mapping priority green-space sites for the hub’s pocket-forest project · from Apr 2026</span></li>
        <li>Academic Representative, The University of Manchester<span>Elected for a cohort of 54 GIS students · Oct 2025 – Sep 2026</span></li>
        <li>Operations Lead (volunteer), The Voice NGO, India<span>Blood-donation camps, tree planting and distribution drives · Mar 2022 – Aug 2025</span></li>
        <li>Cadet, National Cadet Corps (Army Wing), India<span>8 years, ‘C’ Certificate at Grade A · 2016 – 2024</span></li>
      </ul></div>
      <div><h3>Languages</h3><ul>
        <li>English<span>Fluent</span></li><li>Hindi<span>Native</span></li><li>Punjabi<span>Working</span></li><li>Urdu<span>Intermediate</span></li>
      </ul></div>
    </div>
  </div>
</section>

<section class="band contact" id="contact" aria-labelledby="contact-title">
  <div class="wrap contact-grid">
    <div class="sec-head" style="margin:0">
      <p class="label">Contact</p>
      <h2 class="h2" id="contact-title">Looking for graduate roles in <em>GIS, remote sensing and survey.</em></h2>
      <p class="lead">Based in Manchester and happy to relocate. I’m also open to placements, volunteering with mapping teams and freelance GIS work.</p>
    </div>
    <div class="contact-card">
      <p class="label">Email</p>
      <div class="mail-row"><span class="mail" id="mail-text" data-mail>dhananjaysmadaik [at] gmail [dot] com</span><button type="button" class="copy" id="copy-mail">Copy</button></div>
      <div class="contact-links">
        <a class="btn btn-primary" href="#contact" data-mail>Email me {icon("mail")}</a>
        <a class="btn btn-ghost" href="{LINKEDIN}" target="_blank" rel="noopener noreferrer">LinkedIn {icon("in")}</a>
        <a class="btn btn-ghost" href="{GITHUB}" target="_blank" rel="noopener noreferrer">GitHub {icon("gh")}</a>
      </div>
      <p class="contact-note">References available on request.</p>
    </div>
  </div>
</section>
</main>

<footer class="band on-night site-foot">
  <div class="wrap">
    <div class="foot-row">
      <a class="wordmark" href="#top">Dhananjay <em>Singh Madaik</em></a>
      <nav aria-label="Footer"><ul><li><a href="#work">Work</a></li><li><a href="#experience">Experience</a></li><li><a href="#toolkit">Toolkit</a></li><li><a href="#about">About</a></li><li><a href="#contact">Contact</a></li><li><a href="{LINKEDIN}" target="_blank" rel="noopener noreferrer">LinkedIn</a></li></ul></nav>
    </div>
    <div class="attrib">
      <p>Maps, figures and photographs are my own unless credited. Basemaps and source data are credited on each map, including Esri and contributors, Ordnance Survey (© Crown copyright and database rights), ONS, Copernicus Sentinel data and the USGS Landsat archive.</p>
      <p>© <span id="year">2026</span> Dhananjay Singh Madaik. Manchester, United Kingdom.</p>
    </div>
  </div>
</footer>

<noscript><style>.cases [hidden]{{display:block!important}}.cases .fig button{{pointer-events:none}}</style></noscript>
<div class="cases" id="cases">{"".join(case(p, i) for i, p in enumerate(PROJECTS))}</div>

<dialog class="case" id="case" aria-label="Project case study">
  <div class="case-bar">
    <div class="wrap">
      <button type="button" class="icon-btn back" data-close>{icon("arrow-l")}<span>All work</span></button>
      <span class="label" id="case-pos"></span>
      <div class="case-nav">
        <button type="button" class="icon-btn" id="case-prev" aria-label="Previous project">{icon("arrow-l")}</button>
        <button type="button" class="icon-btn" id="case-next" aria-label="Next project">{icon("arrow-r")}</button>
        <button type="button" class="icon-btn" data-close aria-label="Close case study">{icon("close")}</button>
      </div>
    </div>
  </div>
  <div id="case-mount"></div>
</dialog>

<dialog class="lightbox" id="lightbox" aria-label="Map viewer">
  <div class="lb-stage" id="lb-stage"><img id="lb-img" alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" draggable="false"></div>
  <p class="lb-hint">Scroll or pinch to zoom · drag to pan</p>
  <p class="lb-loading" id="lb-loading" hidden>Loading full resolution…</p>
  <div class="lb-bar">
    <p class="lb-cap" id="lb-cap"></p>
    <div class="lb-tools">
      <span class="label" id="lb-count" style="align-self:center;margin-right:.4rem;color:var(--dust)"></span>
      <button type="button" id="lb-out" aria-label="Zoom out">{icon("minus")}</button>
      <button type="button" id="lb-in" aria-label="Zoom in">{icon("plus")}</button>
      <button type="button" id="lb-reset" aria-label="Reset zoom">{icon("reset")}</button>
      <button type="button" id="lb-prev" aria-label="Previous figure">{icon("arrow-l")}</button>
      <button type="button" id="lb-next" aria-label="Next figure">{icon("arrow-r")}</button>
      <button type="button" id="lb-close" aria-label="Close viewer">{icon("close")}</button>
    </div>
  </div>
</dialog>
'''

TITLE = 'Dhananjay Singh Madaik · GIS & Earth Observation'
DESC = 'Portfolio of Dhananjay Singh Madaik, MSc Geographical Information Science (Manchester) and BSc Forestry: landslide mapping, Landsat time series, UAV survey and census GIS.'
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%236F4E37'/%3E"
           "%3Cpath d='M8 44c10-6 16-2 24-8s14-4 24-10M8 52c12-6 18-1 26-7s12-3 22-8M8 36c8-5 14-3 20-8s12-6 28-9' fill='none' stroke='%23E5E4E2' stroke-width='2.4' stroke-linecap='round' opacity='.9'/%3E%3C/svg%3E")

FONT_FACES = '''
@font-face{font-family:"Fraunces";font-style:normal;font-weight:100 900;font-display:swap;src:url(fonts/fraunces-latin-opsz-normal.woff2) format("woff2-variations"),url(fonts/fraunces-latin-opsz-normal.woff2) format("woff2")}
@font-face{font-family:"Fraunces";font-style:italic;font-weight:100 900;font-display:swap;src:url(fonts/fraunces-latin-opsz-italic.woff2) format("woff2-variations"),url(fonts/fraunces-latin-opsz-italic.woff2) format("woff2")}
@font-face{font-family:"Instrument Sans";font-style:normal;font-weight:400 700;font-display:swap;src:url(fonts/instrument-sans-latin-wght-normal.woff2) format("woff2-variations"),url(fonts/instrument-sans-latin-wght-normal.woff2) format("woff2")}
@font-face{font-family:"Instrument Sans";font-style:italic;font-weight:400 700;font-display:swap;src:url(fonts/instrument-sans-latin-wght-italic.woff2) format("woff2-variations"),url(fonts/instrument-sans-latin-wght-italic.woff2) format("woff2")}
@font-face{font-family:"IBM Plex Mono";font-style:normal;font-weight:400;font-display:swap;src:url(fonts/ibm-plex-mono-latin-400-normal.woff2) format("woff2")}
@font-face{font-family:"IBM Plex Mono";font-style:normal;font-weight:500;font-display:swap;src:url(fonts/ibm-plex-mono-latin-500-normal.woff2) format("woff2")}
'''
GOOGLE = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..600;1,9..144,300..600&family=IBM+Plex+Mono:wght@400;500&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&display=swap">')

def build():
    css = (SRC / 'style.css').read_text()
    js = (SRC / 'app.js').read_text()
    body = page_body()
    # GitHub Pages version: self-hosted fonts, strict CSP with a hash for the one inline script
    sha = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    csp = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; "
           f"script-src 'sha256-{sha}'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests")
    gh = f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{e(TITLE)}</title>
<meta name="description" content="{e(DESC)}">
<meta name="author" content="Dhananjay Singh Madaik">
<meta name="theme-color" content="#6F4E37">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{e(DESC)}">
<link rel="icon" href="{FAVICON}">
<link rel="preload" href="fonts/fraunces-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="fonts/instrument-sans-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>{FONT_FACES}{css}</style>
</head>
<body>
{body}
<script>{js}</script>
</body>
</html>
'''
    (SITE / 'index.html').write_text(gh)
    # artifact version
    art = f'<title>Dhananjay Singh Madaik</title>\n{GOOGLE}\n<style>{css}</style>\n{body}\n<script>{js}</script>\n'
    out = SRC.parent.parent / 'portfolio-artifact'
    out.mkdir(exist_ok=True)
    (out / 'dhananjay-portfolio.html').write_text(art)
    print('built', len(gh), 'bytes; csp sha', sha[:12])

if __name__ == '__main__':
    build()
