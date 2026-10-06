# Network Intelligence Platform

A personal relationship-management tool built in Python + Streamlit.
Import your contacts, log interactions, and get a relationship-strength
score and reminders on who to reach out to.

## Setup (MySQL)

This app requires a running MySQL server.

1. Create the database once, using any MySQL client:
   ```sql
   CREATE DATABASE network_intel;
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your connection details as environment variables before running
   (defaults shown — override whichever don't match your setup):

   | Variable | Default |
   |---|---|
   | `MYSQL_HOST` | `localhost` |
   | `MYSQL_PORT` | `3306` |
   | `MYSQL_USER` | `root` |
   | `MYSQL_PASSWORD` | *(empty)* |
   | `MYSQL_DB` | `network_intel` |

   Windows (PowerShell):
   ```powershell
   $env:MYSQL_PASSWORD = "yourpassword"
   ```
   Mac/Linux:
   ```bash
   export MYSQL_PASSWORD="yourpassword"
   ```
4. Run:
   ```bash
   streamlit run app.py
   ```
   Tables (`contacts`, `interactions`, `connections`) are created
   automatically the first time the app starts.

Then open the URL Streamlit prints (usually http://localhost:8501).

## How it works

- **Import** — Upload a CSV. LinkedIn's own export
  ("Connections.csv" from Settings → Data privacy → Get a copy of your data)
  is auto-detected and column-mapped; any other CSV works too, with a
  manual mapping step.
- **Contacts** — Browse/search/edit contacts, set a priority tier
  (Key / Regular / Casual), and see each contact's interaction history.
- **Log Interaction** — Record a call, email, meeting, message, or note
  against a contact. This is what drives the scoring.
- **Dashboard** — Every contact gets a 0-100 relationship strength score:
  - *Recency*: exponential decay since your last interaction. Key contacts
    decay faster (expected touch every ~3 weeks) than Casual ones (~5 months),
    so the model reflects that you *should* be reaching out to important
    people more often.
  - *Frequency*: how many times you've interacted in the last 180 days.
  - Tiers: **Strong** (80+), **Warm** (55-79), **Cooling** (30-54), **Cold** (<30).
  - The Dashboard surfaces everyone in Cooling/Cold as a reminder to reach out.

- **Network Graph** — an egocentric view with you at the center (with a soft
  glow) and every contact placed on a shaded ring by relationship strength —
  Strong closest, Cold furthest out. Rings automatically space out if
  they get crowded, so labels don't overlap. Your **Key** contacts render
  as stars (⭐) so they stand out. Contact-to-contact links come from two
  sources: shared company (auto-detected) and manual connections you add
  yourself (e.g. "X introduced me to Y").

## Data storage

Everything is stored in MySQL, in the database you created (`network_intel`
by default). See the Setup section above for connection configuration.
Your contacts and interactions persist between restarts automatically.

## Tuning the scoring model

Open `scoring.py` — the key knobs are:
- `HALF_LIFE_DAYS`: how fast each priority tier's recency score decays
- `FREQUENCY_WINDOW_DAYS` / `FREQUENCY_CAP`: what counts as "frequent contact"
- `RECENCY_WEIGHT` / `FREQUENCY_WEIGHT`: balance between the two signals
- `TIERS`: score thresholds for Strong/Warm/Cooling/Cold

## Possible next steps

- Email/calendar integration to auto-log interactions
- Export reminders as a weekly digest
- Multi-user support with per-user data isolation (would need auth + a
  shared database like Postgres, or multi-tenant tables in MySQL)
