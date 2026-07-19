from pathlib import Path
from html import escape
from ..models import RESULT_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
FILTERS = ["source","language","query","category","scenario","country","city","device","url","period","status","row_type","endpoint"]
SECTIONS = [
    ("Google Search Console", lambda r: r.get("source") == "google_search_console" and r.get("surface") == "search_console"),
    ("Bing Webmaster Tools", lambda r: r.get("source") == "bing_webmaster" and r.get("surface") == "bing_webmaster"),
    ("Google generative AI importado", lambda r: r.get("surface") == "google_generative_ai"),
]

def indicator(row):
    if row.get("status") == "dry_run": return "dry-run"
    if row.get("status") == "error": return "error"
    change = row.get("position_change")
    if change in (None, ""): return "datos insuficientes"
    try: value = float(change)
    except (TypeError, ValueError): return "datos insuficientes"
    if value < 0: return "mejora"
    if value > 0: return "empeoramiento"
    return "sin cambio"

def export(rows, relative_path="reports/latest-report.html"):
    path = ROOT / relative_path; path.parent.mkdir(parents=True, exist_ok=True)
    body = ["<html><head><meta charset='utf-8'><title>SEO Rank Tracker</title>", "<style>.mejora{color:green}.empeoramiento{color:#b00}.error{color:#b00;font-weight:bold}.dry-run{color:#06c}.insuficiente{color:#777}</style></head><body>", "<h1>SEO Rank Tracker</h1>", "<p>Datos no disponibles se muestran como No disponible. La posición media no es posición orgánica exacta.</p>"]
    body.append("<div id='filters'>" + "".join(f"<label>{escape(f)} <input data-filter='{escape(f)}' oninput='filterRows()'></label> " for f in FILTERS) + "</div>")
    for title, predicate in SECTIONS:
        body.append(f"<h2>{escape(title)}</h2><table border='1'><thead><tr><th>indicator</th>" + "".join(f"<th>{escape(c)}</th>" for c in RESULT_COLUMNS) + "</tr></thead><tbody>")
        selected = [r for r in rows if predicate(r)]
        if not selected: body.append(f"<tr><td colspan='{len(RESULT_COLUMNS)+1}'>No disponible</td></tr>")
        for row in selected:
            ind = indicator(row); cls = "insuficiente" if ind == "datos insuficientes" else ind
            attrs = " ".join(f"data-{f.replace('_','-')}='{escape(str(row.get(f) or '').casefold())}'" for f in FILTERS)
            body.append(f"<tr {attrs}><td class='{escape(cls)}'>{escape(ind)}</td>" + "".join(f"<td>{escape(str(row.get(c) or 'No disponible'))}</td>" for c in RESULT_COLUMNS) + "</tr>")
        body.append("</tbody></table>")
    body.append("""<script>
function filterRows(){
 const filters = Array.from(document.querySelectorAll('[data-filter]')).map(i => [i.dataset.filter.replaceAll('_','-'), i.value.toLowerCase().trim()]).filter(x => x[1]);
 document.querySelectorAll('tbody tr').forEach(row => {
   if (!row.dataset.source && row.children.length === 1) return;
   row.style.display = filters.every(([key, value]) => (row.dataset[key] || '').includes(value)) ? '' : 'none';
 });
}
</script>""")
    body.append("</body></html>"); path.write_text("\n".join(body), encoding="utf-8"); return path
