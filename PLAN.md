# Supersimpel plan — Evaluatie wijkteams op Railway

Een klein webformulier dat je op je telefoon opent en invult. Antwoorden worden
opgeslagen in een CSV-bestand dat jij als beheerder kunt downloaden.

Naam en wijkteam zijn **optioneel** (lage drempel om eerlijk te zijn).

---

## Wat je krijgt

- `/`         → het formulier (mobielvriendelijk, licht + donker)
- `/download` → CSV downloaden (beveiligd met een token)
- `/health`   → statuscheck voor Railway

## Bestanden

| Bestand            | Waarvoor                                  |
|--------------------|-------------------------------------------|
| `app.py`           | Het hele appje (formulier + opslag)       |
| `requirements.txt` | Python-pakketten (Flask + gunicorn)       |
| `Procfile`         | Hoe Railway de app start                  |
| `.gitignore`       | Houdt `data/` en rommel uit git           |

---

## Deploy in 6 stappen (~10 min)

### 1. Zet de code op GitHub
- Maak een lege repo op github.com (bv. `wijkteam-evaluatie`).
- Upload deze map ernaartoe (via GitHub Desktop of de webupload).

### 2. Nieuw project op Railway
- Ga naar https://railway.app → **New Project** → **Deploy from GitHub repo**.
- Kies je repo. Railway herkent Python vanzelf en bouwt de app.

### 3. Stel een geheime token in
- Open het project → tabblad **Variables** → **New Variable**:
  - `ADMIN_TOKEN` = een geheim woord naar keuze (bv. `kerkenraad-x7q2`)
- (Dit token gebruik je straks om de antwoorden te downloaden. Meer variabelen
  zijn niet nodig.)

### 4. Voeg een Volume toe (zodat antwoorden een redeploy overleven)
> Belangrijk: zonder Volume verdwijnt de CSV bij elke redeploy of nieuwe build.
- In het project → **New** → **Volume** → koppel deze aan je service.
- Zet als **Mount path**: `/data`.
- Meer hoef je niet te doen: de app ziet `/data` automatisch en bewaart de
  antwoorden daar. (Geen Volume gekoppeld? Dan werkt de app nog steeds, maar
  gaan antwoorden bij een redeploy verloren.)

### 5. Zet de app publiek
- Tabblad **Settings** → **Networking** → **Generate Domain**.
- Je krijgt een link zoals `https://wijkteam-evaluatie-production.up.railway.app`.

### 6. Delen
- Deel die link (of een QR-code ervan) met de wijkteamleden.
- Op de telefoon: link openen → invullen → **Versturen**. Klaar.

---

## Antwoorden ophalen

Open in je browser:

```
https://JOUW-LINK.up.railway.app/download?token=JOUW_ADMIN_TOKEN
```

Er wordt een `antwoorden.csv` gedownload die je in Excel of Numbers opent.
De CSV heeft een kopregel en per inzending één rij, met een tijdstempel.

> Tip: bewaar de downloadlink privé — met de token kan iedereen de antwoorden ophalen.

---

## Lokaal testen (optioneel, op je pc)

```bash
cd wijkteam-evaluatie
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
pip install -r requirements.txt
python app.py
```

Open daarna http://localhost:8000 in je browser.

---

## Later aanpassen

- **Vragen wijzigen**: pas de lijst `VELDEN` bovenaan `app.py` aan.
- **Kleur/tekst**: bovenin `FORM_HTML` (de `--accent`-kleur en teksten).
- **Naam verplicht maken**: voeg `required` toe aan het naam-`input` in `FORM_HTML`.
