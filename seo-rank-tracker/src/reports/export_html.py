from pathlib import Path
from html import escape
from ..models import RESULT_COLUMNS

ROOT = Path(__file__).resolve().parents[2]

def export(rows, relative_path="reports/latest-report.html"):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    filters = ["source","language","query","scenario","country","city","device","url"]
    body = ["<html><head><meta charset='utf-8'><title>SEO Rank Tracker</title></head><body>", "<h1>SEO Rank Tracker</h1>", "<p>Datos no disponibles se muestran como No disponible. La posición media no es posición orgánica exacta.</p>"]
    body.append("<h2>Filtros disponibles</h2><ul>" + "".join(f"<li>{escape(f)}</li>" for f in filters + ["category","period"]) + "</ul>")
    for section in [("Google Search Console","google_search_console"),("Bing Webmaster Tools","bing_webmaster"),("Google generative AI importado","google_generative_ai")]:
        title, key = section
        body.append(f"<h2>{escape(title)}</h2><table border='1'><thead><tr>" + "".join(f"<th>{escape(c)}</th>" for c in RESULT_COLUMNS) + "</tr></thead><tbody>")
        selected = [r for r in rows if r.get("source") == key or r.get("surface") == key]
        if not selected:
            body.append(f"<tr><td colspan='{len(RESULT_COLUMNS)}'>No disponible</td></tr>")
        for row in selected:
            body.append("<tr>" + "".join(f"<td>{escape(str(row.get(c) or 'No disponible'))}</td>" for c in RESULT_COLUMNS) + "</tr>")
        body.append("</tbody></table>")
    body.append("</body></html>")
    path.write_text("\n".join(body), encoding="utf-8")
    return path
