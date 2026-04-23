"""
generate_site.py
Reads data/articles.json and writes a self-contained index.html.
"""

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Visual identity: one color pair per category
# ---------------------------------------------------------------------------
CATEGORY_COLORS = {
    "AI & Knowledge Management":        {"bg": "#DBEAFE", "text": "#1D4ED8", "border": "#93C5FD"},
    "Records Management & AI":          {"bg": "#FFEDD5", "text": "#C2410C", "border": "#FED7AA"},
    "Information Retrieval & Search":   {"bg": "#EDE9FE", "text": "#6D28D9", "border": "#C4B5FD"},
    "Libraries & Archives":             {"bg": "#D1FAE5", "text": "#065F46", "border": "#6EE7B7"},
    "Information Behavior":             {"bg": "#CCFBF1", "text": "#0F766E", "border": "#99F6E4"},
    "AI Training & Literacy":           {"bg": "#FEF3C7", "text": "#B45309", "border": "#FDE68A"},
    "Enterprise Information Management":{"bg": "#E0E7FF", "text": "#4338CA", "border": "#A5B4FC"},
    "AI & Information Governance":      {"bg": "#FEE2E2", "text": "#B91C1C", "border": "#FCA5A5"},
    "AI & Information Sciences":        {"bg": "#F1F5F9", "text": "#475569", "border": "#CBD5E1"},
}

FALLBACK_COLOR = {"bg": "#F1F5F9", "text": "#475569", "border": "#CBD5E1"}


def fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso[:10]


def host(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def build_card(a: dict) -> str:
    colors = CATEGORY_COLORS.get(a["category"], FALLBACK_COLOR)
    cat_escaped = a["category"].replace('"', "&quot;")
    title_escaped = a["title"].replace("<", "&lt;").replace(">", "&gt;")
    summary_escaped = a["summary"].replace("<", "&lt;").replace(">", "&gt;")
    return f"""<article class="card" data-category="{cat_escaped}" data-text="{title_escaped.lower()} {summary_escaped.lower()} {a['source'].lower()}">
  <div class="card-inner">
    <span class="badge" style="background:{colors['bg']};color:{colors['text']};border:1px solid {colors['border']}">{a['category']}</span>
    <h3 class="card-title"><a href="{a['url']}" target="_blank" rel="noopener noreferrer">{title_escaped}</a></h3>
    <p class="card-excerpt">{summary_escaped}</p>
    <div class="card-meta">
      <span class="card-source">{a['source']}</span>
      <span class="sep">·</span>
      <span class="card-date">{fmt_date(a['date'])}</span>
    </div>
  </div>
</article>"""


def build_filter_btn(label: str, value: str, active: bool = False) -> str:
    cls = "filter-btn active" if active else "filter-btn"
    escaped = value.replace('"', "&quot;")
    return f'<button class="{cls}" data-filter="{escaped}">{label}</button>'


# ---------------------------------------------------------------------------
# Full HTML template (CSS + JS inline, no external dependencies except Google Fonts)
# ---------------------------------------------------------------------------
PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI & Information Sciences Watch</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background:#F8FAFC;color:#1E293B;min-height:100vh}

/* ── Header ── */
header{background:linear-gradient(135deg,#0F172A 0%,#1A3356 100%);color:#fff;padding:2.5rem 1.5rem}
.header-inner{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:flex-end;gap:1.5rem;flex-wrap:wrap}
.header-eyebrow{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#60A5FA;margin-bottom:.5rem}
header h1{font-size:1.875rem;font-weight:700;line-height:1.2;margin-bottom:.4rem}
.header-subtitle{color:#94A3B8;font-size:.875rem;max-width:520px;line-height:1.5}
.header-stats{display:flex;gap:2rem;align-items:flex-end}
.stat{text-align:right}
.stat-value{display:block;font-size:1.75rem;font-weight:700;line-height:1}
.stat-label{font-size:.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:.05em}

/* ── Main ── */
main{max-width:1200px;margin:0 auto;padding:2rem 1.5rem}

/* ── Controls ── */
.controls{margin-bottom:2rem;display:flex;flex-direction:column;gap:.875rem}
.search-wrap{position:relative}
.search-icon{position:absolute;left:.875rem;top:50%;transform:translateY(-50%);color:#94A3B8;pointer-events:none}
.search-input{width:100%;padding:.75rem 1rem .75rem 2.5rem;border:1px solid #E2E8F0;border-radius:10px;font-size:.9375rem;font-family:inherit;background:#fff;color:#1E293B;outline:none;box-shadow:0 1px 3px rgba(0,0,0,.05);transition:border-color .2s,box-shadow .2s}
.search-input:focus{border-color:#3B82F6;box-shadow:0 0 0 3px rgba(59,130,246,.12)}
.search-input::placeholder{color:#94A3B8}
.filters{display:flex;flex-wrap:wrap;gap:.4rem}
.filter-btn{padding:.35rem .875rem;border-radius:20px;border:1px solid #E2E8F0;background:#fff;color:#64748B;font-size:.78rem;font-weight:500;cursor:pointer;font-family:inherit;transition:all .15s;line-height:1.5}
.filter-btn:hover{border-color:#94A3B8;color:#1E293B}
.filter-btn.active{background:#0F172A;color:#fff;border-color:#0F172A}

/* ── Grid ── */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.125rem}

/* ── Card ── */
.card{background:#fff;border-radius:12px;border:1px solid #E2E8F0;box-shadow:0 1px 4px rgba(0,0,0,.04);transition:box-shadow .2s,transform .2s;display:flex}
.card:hover{box-shadow:0 8px 28px rgba(0,0,0,.1);transform:translateY(-2px)}
.card-inner{padding:1.125rem 1.25rem;display:flex;flex-direction:column;gap:.625rem;width:100%}
.badge{display:inline-block;padding:.2rem .625rem;border-radius:20px;font-size:.68rem;font-weight:700;letter-spacing:.03em;align-self:flex-start;line-height:1.5}
.card-title{font-size:.9rem;font-weight:600;line-height:1.45}
.card-title a{color:#1E293B;text-decoration:none;transition:color .15s}
.card-title a:hover{color:#3B82F6}
.card-excerpt{font-size:.8rem;line-height:1.65;color:#64748B;flex:1;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.card-meta{display:flex;align-items:center;gap:.35rem;font-size:.72rem;color:#94A3B8;padding-top:.625rem;border-top:1px solid #F1F5F9;margin-top:auto}
.card-source{font-weight:600;color:#64748B}
.sep{opacity:.5}

/* ── Empty state ── */
.no-results{display:none;text-align:center;padding:5rem 2rem;color:#94A3B8;font-size:.9375rem}

/* ── Footer ── */
footer{text-align:center;padding:2rem 1.5rem;color:#94A3B8;font-size:.78rem;border-top:1px solid #E2E8F0;line-height:2}

@media(max-width:640px){
  header h1{font-size:1.4rem}
  .header-inner{flex-direction:column;align-items:flex-start}
  .header-stats{flex-direction:row;gap:1.5rem}
  .stat{text-align:left}
  .grid{grid-template-columns:1fr}
}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <div>
      <div class="header-eyebrow">Strategic Intelligence</div>
      <h1>AI &amp; Information Sciences Watch</h1>
      <p class="header-subtitle">Daily intelligence on AI in libraries, archives, records management &amp; knowledge management</p>
    </div>
    <div class="header-stats">
      <div class="stat">
        <span class="stat-value">ARTICLE_COUNT</span>
        <span class="stat-label">articles</span>
      </div>
      <div class="stat">
        <span class="stat-value">CATEGORY_COUNT</span>
        <span class="stat-label">categories</span>
      </div>
    </div>
  </div>
</header>

<main>
  <div class="controls">
    <div class="search-wrap">
      <svg class="search-icon" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" id="search" class="search-input" placeholder="Search articles by title, source or keyword&hellip;" autocomplete="off">
    </div>
    <div class="filters" id="filters">
FILTER_BUTTONS
    </div>
  </div>

  <div class="grid" id="grid">
CARDS
  </div>
  <div class="no-results" id="no-results">No articles match your search.</div>
</main>

<footer>
  <div>Refreshed automatically every day via GitHub Actions &mdash; Last update: LAST_UPDATED</div>
  <div>AI &amp; Information Sciences Watch &mdash; Pierre-Luc Cauchon</div>
</footer>

<script>
(function(){
  var cards = Array.from(document.querySelectorAll('.card'));
  var searchEl = document.getElementById('search');
  var noResults = document.getElementById('no-results');
  var activeFilter = 'all';

  function apply(){
    var q = searchEl.value.toLowerCase().trim();
    var visible = 0;
    cards.forEach(function(c){
      var matchCat = activeFilter === 'all' || c.dataset.category === activeFilter;
      var matchQ = !q || c.dataset.text.indexOf(q) !== -1;
      var show = matchCat && matchQ;
      c.style.display = show ? '' : 'none';
      if(show) visible++;
    });
    noResults.style.display = visible === 0 ? 'block' : 'none';
  }

  document.getElementById('filters').addEventListener('click', function(e){
    var btn = e.target.closest('.filter-btn');
    if(!btn) return;
    document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    apply();
  });

  searchEl.addEventListener('input', apply);
})();
</script>
</body>
</html>
"""


def generate():
    data_path = os.path.join("data", "articles.json")
    if not os.path.exists(data_path):
        print("No articles.json found — run fetch_articles.py first.")
        return

    with open(data_path, encoding="utf-8") as f:
        articles = json.load(f)

    categories = sorted({a["category"] for a in articles})
    now = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    cards_html = "\n".join(build_card(a) for a in articles)

    filters = ["  " + build_filter_btn("All", "all", active=True)]
    for cat in categories:
        filters.append("  " + build_filter_btn(cat, cat))
    filters_html = "\n".join(filters)

    html = (PAGE
            .replace("ARTICLE_COUNT", str(len(articles)))
            .replace("CATEGORY_COUNT", str(len(categories)))
            .replace("LAST_UPDATED", now)
            .replace("FILTER_BUTTONS", filters_html)
            .replace("CARDS", cards_html))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html generated — {len(articles)} articles, {len(categories)} categories.")


if __name__ == "__main__":
    generate()
