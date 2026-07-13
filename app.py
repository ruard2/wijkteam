import csv
import os
from datetime import datetime

from flask import Flask, request, render_template_string, redirect, url_for, Response, abort

app = Flask(__name__)

# Waar de CSV wordt opgeslagen.
#  - Op Railway: koppel een Volume met mount path /data. Die map overleeft
#    elke redeploy en nieuwe build. De app pakt 'm dan automatisch.
#  - Lokaal (of zonder Volume): valt terug op een map ./data naast dit bestand.
# Je kunt dit desgewenst overrulen met de omgevingsvariabele DATA_DIR.
def _kies_data_dir():
    override = os.environ.get("DATA_DIR")
    if override:
        return override
    # Railway-Volume aanwezig en schrijfbaar? Gebruik die -> data blijft bewaard.
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data"
    return os.path.join(os.path.dirname(__file__), "data")


DATA_DIR = _kies_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "antwoorden.csv")

# Simpel wachtwoord voor de downloadpagina. Zet dit in Railway als ADMIN_TOKEN.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "wijkteam2026")

VELDEN = [
    ("ingediend_op", None),
    ("naam", "Naam (optioneel)"),
    ("wijkteam", "Wijkteam (optioneel)"),
    ("toerusting", "1. Hoe heb je de gezamenlijke toerustingsmomenten ervaren? Wat vond je waardevol en wat zou je anders willen zien?"),
    ("versterking", "2. Hoe heb je de onderlinge versterking, bemoediging en het samen bidden binnen jouw wijkteam ervaren? Wat zou dit verder kunnen versterken?"),
    ("functioneren", "3. Hoe functioneert jullie wijkteam (samenwerking, communicatie, taakverdeling, sfeer)? Hebben jullie voldoende mensen? Zo nee, wat ontbreekt er?"),
    ("vooruitblik", "4. Wat moeten we in 2026–2027 behouden, anders doen of toevoegen? Zijn er nog andere dingen die je aan de kerkenraad wilt meegeven?"),
]

FORM_HTML = """
<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluatie wijkteams 2025–2026</title>
<style>
  :root { --accent:#2f6b4f; --bg:#f6f7f5; --card:#fff; --line:#e2e5e0; --text:#1e2420; --muted:#5c6660; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { max-width:640px; margin:0 auto; padding:20px 16px 60px; }
  header h1 { font-size:1.5rem; margin:.2em 0 .1em; }
  header p { color:var(--muted); margin:.2em 0 1.2em; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:16px; margin-bottom:16px; }
  label { display:block; font-weight:600; margin-bottom:8px; }
  .hint { font-weight:400; color:var(--muted); font-size:.92rem; }
  input[type=text], textarea { width:100%; padding:12px 13px; border:1px solid var(--line);
    border-radius:10px; font:inherit; background:#fff; color:var(--text);
    -webkit-text-fill-color:var(--text); opacity:1; }
  input::placeholder, textarea::placeholder { color:var(--muted); -webkit-text-fill-color:var(--muted); opacity:1; }
  textarea { min-height:120px; resize:vertical; }
  input:focus, textarea:focus { outline:2px solid var(--accent); outline-offset:1px; border-color:var(--accent); }
  button { width:100%; padding:15px; font-size:1.05rem; font-weight:700; color:#fff;
    background:var(--accent); border:0; border-radius:12px; cursor:pointer; }
  button:active { filter:brightness(.94); }
  .intro { font-size:.98rem; color:var(--muted); }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#141815; --card:#1c221e; --line:#2c332e; --text:#e7ece8; --muted:#9aa49d; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Evaluatie wijkteams 2025–2026</h1>
    <p>Seizoensevaluatie</p>
  </header>
  <p class="intro">We horen graag hoe je het afgelopen seizoen hebt ervaren. Je antwoorden helpen ons om de
  wijkteams in het seizoen 2026–2027 verder te ontwikkelen. We stellen een eerlijke en concrete reactie op prijs.</p>

  <form method="post" action="{{ url_for('verstuur') }}">
    {% for key, vraag in velden %}
      {% if key not in ('ingediend_op',) %}
      <div class="card">
        <label for="{{ key }}">{{ vraag }}</label>
        {% if key in ('naam','wijkteam') %}
          <input type="text" id="{{ key }}" name="{{ key }}" autocomplete="off">
        {% else %}
          <textarea id="{{ key }}" name="{{ key }}"></textarea>
        {% endif %}
      </div>
      {% endif %}
    {% endfor %}
    <button type="submit">Versturen</button>
  </form>
</div>
</body>
</html>
"""

BEDANKT_HTML = """
<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bedankt</title>
<style>
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
    background:#f6f7f5; color:#1e2420; text-align:center; padding:24px;
    font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .box { max-width:420px; }
  h1 { color:#2f6b4f; }
  a { color:#2f6b4f; }
  @media (prefers-color-scheme: dark){ body{background:#141815;color:#e7ece8;} }
</style>
</head>
<body>
  <div class="box">
    <h1>Hartelijk dank!</h1>
    <p>Je reactie is opgeslagen. Fijn dat je de tijd hebt genomen om mee te denken over de wijkteams.</p>
    <p><a href="{{ url_for('formulier') }}">Nog een reactie invullen</a></p>
  </div>
</body>
</html>
"""


def zorg_voor_header():
    """Zorg dat de CSV bestaat met een kopregel."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow([k for k, _ in VELDEN])


@app.route("/")
def formulier():
    return render_template_string(FORM_HTML, velden=VELDEN, url_for=url_for)


@app.route("/verstuur", methods=["POST"])
def verstuur():
    zorg_voor_header()
    rij = [datetime.now().strftime("%Y-%m-%d %H:%M")]
    for key, _ in VELDEN[1:]:
        rij.append((request.form.get(key) or "").strip())
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow(rij)
    return redirect(url_for("bedankt"))


@app.route("/bedankt")
def bedankt():
    return render_template_string(BEDANKT_HTML, url_for=url_for)


@app.route("/download")
def download():
    if request.args.get("token") != ADMIN_TOKEN:
        abort(403, "Ongeldige of ontbrekende token. Gebruik ?token=...")
    if not os.path.exists(CSV_PATH):
        return "Nog geen antwoorden binnen.", 404
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        data = f.read()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=antwoorden.csv"},
    )


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
