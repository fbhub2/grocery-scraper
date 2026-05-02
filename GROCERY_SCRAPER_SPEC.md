# GROCERY-SCRAPER — Komplett Spec & Designdokument
# Fil: C:\mittprosjekt\GROCERY_SCRAPER_SPEC.md
# Sist oppdatert: 2026-05-01
# Formål: Claude Code CLI — planlegging, implementasjon, branching, testing og logging

---

## INNHOLDSFORTEGNELSE

1. [Prosjektkontekst](#1-prosjektkontekst)
2. [Arkitektur & tekniske valg](#2-arkitektur--tekniske-valg)
3. [Databaseskjema — komplett oversikt](#3-databaseskjema--komplett-oversikt)
4. [Feature Spec v2.0 — Normalisering, Prishistorikk & UI](#4-feature-spec-v20)
5. [Feature Spec v2.1 — Google Auth & Per-bruker data](#5-feature-spec-v21)
6. [Feature Spec v2.2 — Brukerintensjon, Handlelister & Varsling](#6-feature-spec-v22)
7. [Bug & UX Issues — App-test 2026-05-01](#7-bug--ux-issues)
8. [Implementasjonsrekkefølge & branches](#8-implementasjonsrekkefølge--branches)
9. [Testplan](#9-testplan)
10. [Logging & lokale MD-filer](#10-logging--lokale-md-filer)
11. [Claude Code CLI — oppstartsprompter](#11-claude-code-cli--oppstartsprompter)

---

## 1. PROSJEKTKONTEKST

**Prosjekt:** grocery-scraper
**Plassering:** `C:\mittprosjekt\grocery-scraper`
**GitHub:** `fbhub2/grocery-scraper`
**Stack:** Python, Streamlit, SQLite (sqlite3), aiosqlite (valgfritt)
**Scrapers:** Oda og Meny — direkte HTTP, ingen API-nøkler
**OS:** Windows 11, alltid PowerShell-syntax (ikke bash)
**Python-kommando:** `python` (ikke `python3`)

### Hva appen gjør (nå)
- Søker etter produkter på tvers av Oda og Meny i sanntid
- Sammenligner priser, viser prisfall
- Enkel handleliste med flervalgstabell
- Handlelisteprissammenligning med "optimal sum" (splitt mellom butikker)

### Hva appen skal gjøre (etter denne speccen)
- Persistent lagring av produkter, priser og brukere i SQLite
- Normalisering av produktnavn på tvers av butikker
- Google OAuth — innlogging med Google-konto
- Per-bruker data: egne handlelister, varslingsliste, custom-normalisering
- Prisovervåkning via scheduled tasks med notifikasjon
- Prishistorikk-visualisering per produkt
- Redesignet seleksjonsmodell: kategori-nivå, ikke SKU-nivå

---

## 2. ARKITEKTUR & TEKNISKE VALG

### Designprinsipper
- **sqlite3 only** — ikke SQLAlchemy, ikke aiosqlite i db.py
- **Synkrone DB-kall** — enklere, tilstrekkelig for Streamlit
- **CREATE TABLE IF NOT EXISTS** — ingen migrasjoner
- **grocery.db** opprettes automatisk ved første kjøring
- **resolve_name()** er eneste funksjon som leverer produktnavn til UI — aldri rå navn
- **tasks.py** kjøres direkte fra PowerShell — ingen daemon-prosess

### Filstruktur (mål)
```
C:\mittprosjekt\grocery-scraper\
├── .env                   ← GOOGLE_CLIENT_ID, SECRET, REDIRECT_URI
├── .gitignore             ← .env, grocery.db, __pycache__
├── CLAUDE.md              ← oppdateres av Claude Code ved decisions
├── DECISIONS.md           ← arkitekturvalg og begrunnelser
├── BACKLOG.md             ← neste features og ideer
├── CHANGELOG.md           ← hva som er gjort per branch/PR
├── auth.py                ← Google OAuth (Feature 8)
├── db.py                  ← ALL DB-logikk
├── normalize.py           ← auto_normalize + resolve_name
├── tasks.py               ← scheduled tasks
├── main.py                ← Streamlit UI
├── grocery.db             ← SQLite, ikke i git
├── scrapers/
│   ├── oda.py             ← + fetch_price(product_id)
│   └── meny.py            ← + fetch_price(product_id)
├── tests/
│   ├── test_db.py
│   ├── test_normalize.py
│   ├── test_scrapers.py
│   ├── test_tasks.py
│   └── test_auth.py
└── requirements.txt
```

### Abstraksjonsnivåer (viktig for UI-design)
```
Nivå 1 — Kategori:     "Lett melk"          ← bruker tenker her
Nivå 2 — Produkt:      "Tine Lettmelk 1L"   ← normalisert, ett merke/volum
Nivå 3 — SKU:          Oda × Tine × 1L      ← butikk-spesifikt
```
UI opererer på Nivå 1 for handleliste og varsling.
UI opererer på Nivå 2/3 for prissammenligning og historikk.

---

## 3. DATABASESKJEMA — KOMPLETT OVERSIKT

```sql
-- Butikker
CREATE TABLE IF NOT EXISTS store (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE   -- 'oda', 'meny'
);

-- Normalisering (global)
CREATE TABLE IF NOT EXISTS normal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_name   TEXT NOT NULL,
    auto_name       TEXT,        -- generert av tasks.py normalize
    UNIQUE(original_name)
);

-- Per-bruker custom-navn (erstatter custom_name i normal)
CREATE TABLE IF NOT EXISTS user_normal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id),
    normal_id   INTEGER NOT NULL REFERENCES normal(id),
    custom_name TEXT NOT NULL,
    UNIQUE(user_id, normal_id)
);

-- Produkter (global katalog)
CREATE TABLE IF NOT EXISTS product (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    TEXT NOT NULL,       -- ekstern ID fra scraper
    original_name TEXT NOT NULL,
    store_id      INTEGER NOT NULL REFERENCES store(id),
    UNIQUE(product_id, store_id)
);

-- Prishistorikk (global)
CREATE TABLE IF NOT EXISTS price_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id),
    store_id   INTEGER NOT NULL REFERENCES store(id),
    date       TEXT NOT NULL,          -- ISO 8601: '2026-05-01'
    price      REAL NOT NULL,
    UNIQUE(product_id, store_id, date)
);

-- Brukere
CREATE TABLE IF NOT EXISTS user (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    google_sub TEXT NOT NULL UNIQUE,   -- Google sin stabile bruker-ID (ikke e-post)
    email      TEXT NOT NULL,
    name       TEXT,
    created_at TEXT DEFAULT (date('now'))
);

-- Produkter som skal prisovervåkes (per bruker)
CREATE TABLE IF NOT EXISTS price_fetch (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES user(id),
    product_id INTEGER NOT NULL REFERENCES product(id),
    UNIQUE(user_id, product_id)
);

-- Handlelister (per bruker)
CREATE TABLE IF NOT EXISTS shopping_list (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES user(id),
    name       TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    archived   INTEGER DEFAULT 0
);

-- Handlelisteprodukter (kategori-nivå, ikke SKU)
CREATE TABLE IF NOT EXISTS shopping_list_item (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id        INTEGER NOT NULL REFERENCES shopping_list(id),
    original_name  TEXT NOT NULL,   -- kobling til normal-tabellen
    quantity       INTEGER DEFAULT 1,
    note           TEXT,
    checked        INTEGER DEFAULT 0,
    added_at       TEXT DEFAULT (datetime('now'))
);

-- Varslingsliste (per bruker)
CREATE TABLE IF NOT EXISTS watchlist (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES user(id),
    original_name   TEXT NOT NULL,
    threshold_type  TEXT NOT NULL,   -- 'absolute' | 'relative' | 'sale'
    threshold_value REAL,
    status          TEXT DEFAULT 'waiting',  -- 'waiting'|'triggered'|'ignored'
    triggered_at    TEXT,
    triggered_price REAL,
    triggered_store TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, original_name)
);

-- Søkehistorikk (per bruker, valgfritt)
CREATE TABLE IF NOT EXISTS search_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id),
    query       TEXT NOT NULL,
    searched_at TEXT DEFAULT (datetime('now'))
);
```

### Prioritetslogikk for visningsnavn
```
custom_name (user_normal) > auto_name (normal) > original_name
```
Implementert i `get_display_name(original_name, user_id=None)` i db.py.

---

## 4. FEATURE SPEC v2.0 — NORMALISERING, PRISHISTORIKK & UI

### Bakgrunn & motivasjon
Meny og Oda bruker ulike produktnavn for samme vare:
- "Lettmelk 0,5% Tine" (Meny) = "Tine Lettmelk" (Oda) = "TINE Lett Melk 1L" (Oda)
Uten normalisering oppstår dataduplisering i alle deler av appen.

### Feature 1 — Normaliseringstabellen

**db.py:**
```python
def upsert_normal(original_name: str, auto_name: str = None) -> int:
    """Insert or ignore. Returnerer normal.id."""

def get_display_name(original_name: str, user_id: int = None) -> str:
    """
    Prioritet: user_normal.custom_name > normal.auto_name > original_name.
    user_id=None → hopp over user_normal-oppslag.
    """

def list_normals(filter: str = None) -> list[dict]:
    """Alle rader i normal med alle tre navn-kolonner."""
```

**normalize.py:**
```python
def resolve_name(original_name: str, user_id: int = None) -> str:
    """Eneste funksjon UI skal kalle for å vise produktnavn."""
```

**Krav:** Alle produktnavn i UI bruker resolve_name() — aldri rå original_name.

### Feature 2 — Lagre produkter

**db.py:**
```python
def ensure_store(name: str) -> int
def upsert_product(product_id: str, original_name: str, store_id: int) -> int
def get_products(store_id: int = None) -> list[dict]
```

**Scrapers — påkrevd endring:**
```python
store_id = db.ensure_store("oda")
for p in products:
    pid = db.upsert_product(p["id"], p["name"], store_id)
    db.upsert_normal(p["name"])
```

### Feature 3 — Auto-normalisering (scheduled task)

**normalize.py:**
```python
COMPOUND_SPLITS = {
    "lettmelk": "lett melk",
    "helmelk": "hel melk",
    "skummetmelk": "skummet melk",
    "kremfløte": "krem fløte",
    "havregryn": "havre gryn",
    "fullkornbrød": "fullkorn brød",
    "knekkebrød": "knekke brød",
    "jordbærsyltetøy": "jordbær syltetøy",
}

def auto_normalize(original_name: str) -> str:
    """
    1. Lowercase
    2. Splitt CamelCase
    3. Kjente sammensetninger via COMPOUND_SPLITS
    4. Normaliser volum/vekt: '1L'/'1 liter' → '1l', '1000g' → '1kg'
    5. Strip mellomrom
    """
```

**tasks.py:**
```python
def run_auto_normalize():
    """Hent alle normal-rader der auto_name IS NULL. Kjør auto_normalize(). Oppdater DB."""

if __name__ == "__main__":
    import sys
    if "normalize" in sys.argv: run_auto_normalize()
    if "fetch"     in sys.argv: run_price_fetch()
```

**PowerShell:** `python tasks.py normalize`

### Feature 4 — UI: Custom normalisering

**db.py:**
```python
def set_custom_name(original_name: str, custom_name: str, user_id: int) -> None:
    """Lagre i user_normal. Tom streng → NULL."""
```

**UI (Streamlit):**
```
Tab: "Normalisering"
├── Søkefelt (filter på original_name)
├── Tabell: original_name | auto_name | custom_name (text_input per rad)
└── [Lagre endringer]
```

### Feature 5 — price_fetch-tabell

**db.py:**
```python
def add_to_price_fetch(product_id: int, user_id: int) -> None
def remove_from_price_fetch(product_id: int, user_id: int) -> None
def get_price_fetch_products(user_id: int) -> list[dict]
```

**UI:** Checkbox "Overvåk" per rad i produkttabell.

### Feature 6 — Scheduled task: hent priser

**Scraper-interface (påkrevd):**
```python
async def fetch_price(product_id: str) -> float | None:
    """Hent gjeldende pris for ett produkt. None ved feil."""
```

**tasks.py:**
```python
def run_price_fetch():
    """
    For alle (user_id, product_id) i price_fetch:
    1. Hent pris via riktig scraper
    2. Lagre i price_history (UNIQUE constraint forhindrer duplikater)
    3. Sjekk watchlist-terskel → varsle hvis truffet
    Logger: "Fetched X prices, Y errors"
    """
```

**Windows Task Scheduler:** `python C:\mittprosjekt\grocery-scraper\tasks.py fetch` daglig kl. 07:00

### Feature 7 — UI: Prishistorikk-graf

**db.py:**
```python
def get_price_history(product_id: int) -> list[dict]:
    """[{"date": "2026-05-01", "price": 29.9, "store": "oda"}, ...]"""
```

**Streamlit:**
```python
def show_price_history(product_db_id: int, display_name: str):
    rows = db.get_price_history(product_db_id)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    st.line_chart(df.pivot(index="date", columns="store", values="price"))
```

**UI:** Knapp "Historikk" per produkt → expander med linjegraf.
En linje per butikk. X: dato, Y: pris (NOK).

---

## 5. FEATURE SPEC v2.1 — GOOGLE AUTH & PER-BRUKER DATA

### Bakgrunn & designvalg
- Ingen passordlagring — kun Google OAuth 2.0
- `google_sub` (ikke e-post) er stabil bruker-ID — e-post kan endres
- `authlib` fremfor `streamlit-google-auth` (sistnevnte er ikke vedlikeholdt)
- `.env` skal aldri committes — legg til `.gitignore` fra dag 1

### Feature 8 — Google OAuth

**Google Cloud Console (engangsjobb, manuell):**
```
1. console.cloud.google.com → prosjekt "grocery-scraper"
2. APIs & Services → Credentials → OAuth 2.0 Client ID
3. Application type: Web application
4. Authorized redirect URIs:
   http://localhost:8501/oauth/callback
5. Noter Client ID og Client Secret
```

**.env:**
```
GOOGLE_CLIENT_ID=din_client_id
GOOGLE_CLIENT_SECRET=din_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8501/oauth/callback
```

**requirements.txt — legg til:**
```
authlib>=1.3
httpx>=0.27
python-dotenv>=1.0
```

**auth.py:**
```python
def get_auth_url() -> str:
    """Generer Google OAuth URL. Lagrer state i session."""

def exchange_code_for_user(code: str) -> dict:
    """Bytt OAuth-kode mot {sub, email, name, picture}."""

def get_current_user() -> dict | None:
    """Returner innlogget bruker fra st.session_state."""

def require_login() -> dict:
    """
    Kall øverst i main.py.
    - Håndterer ?code= callback
    - Viser login-knapp hvis ikke innlogget
    - st.stop() hvis ikke autentisert
    - Returnerer bruker-dict hvis innlogget
    """
```

**main.py — øverst:**
```python
import auth
user = auth.require_login()
user_db_id = db.get_user_id(user["sub"])

with st.sidebar:
    st.image(user["picture"], width=40)
    st.write(f"**{user['name']}**")
    st.caption(user["email"])
    if st.button("Logg ut"):
        del st.session_state["user"]
        st.rerun()
```

**db.py:**
```python
def ensure_user(google_sub: str, email: str, name: str) -> int
def get_user_id(google_sub: str) -> int
```

### Feature 9 — Per-bruker isolasjon

**Hva er delt vs. per-bruker:**

| Data            | Scope      | Begrunnelse                              |
|-----------------|------------|------------------------------------------|
| store           | Global     | Samme butikker for alle                  |
| product         | Global     | Produktkatalogen deles                   |
| price_history   | Global     | Historikk er felles fakta                |
| normal.auto_name| Global     | Auto-normalisering er felles             |
| user_normal     | Per bruker | Personlig preferanse for navn            |
| price_fetch     | Per bruker | Hver bruker overvåker sine produkter     |
| shopping_list   | Per bruker | Private handlelister                     |
| watchlist       | Per bruker | Private varslingsønsker                  |

**Mønster for alle bruker-spesifikke kall:**
```python
user = auth.require_login()
user_db_id = db.get_user_id(user["sub"])

db.get_price_fetch_products(user_id=user_db_id)
db.add_to_price_fetch(product_id, user_id=user_db_id)
db.set_custom_name(original_name, custom_name, user_id=user_db_id)
db.get_display_name(original_name, user_id=user_db_id)
```

**tasks.py — price_fetch itererer per bruker:**
```python
# price_history er global — UNIQUE constraint hindrer dobbeltlagring
# selv om to brukere overvåker samme produkt
```

**Breaking change fra v2.0 Feature 4:**
`custom_name` i `normal`-tabellen fjernes til fordel for `user_normal`.
Migrering: flytt eksisterende custom_name-verdier til user_normal under en "default"-bruker.

---

## 6. FEATURE SPEC v2.2 — BRUKERINTENSJON, HANDLELISTER & VARSLING

### Kjerneobservasjon: abstraksjonsnivåer i brukerens hode
Når bruker sier "jeg skal kjøpe lettmelk":
- Bryr seg IKKE om: merke (TINE vs Q), butikk (Oda vs Meny), volum (1L vs 1,75L)
- Bryr seg OM: behovet og prisen

### Intensjonsmodell — to dimensjoner

**Dimensjon A — Hastegrad:**
| Verdi    | Betydning                     | Brukerens ord          |
|----------|-------------------------------|------------------------|
| nå       | Kjøper ved neste handletur    | "Vi er tomme"          |
| snart    | Fleksibel, innen X dager      | "Vi begynner å gå tom" |
| ingen    | Ren prisjakt                  | "Hadde vært fint å ha" |

**Dimensjon B — Pristerskel:**
| Verdi    | Betydning                        | Eksempel          |
|----------|----------------------------------|-------------------|
| ingen    | Kjøper til normalpris            | —                 |
| absolutt | Kjøper hvis pris < X kr          | "Under 20 kr"     |
| relativ  | Kjøper hvis Y% under snitt       | "Hvis på tilbud"  |

**De fire reelle use casene:**
```
                 Ingen terskel    Med terskel
Hastegrad: nå    → Handleliste    → Ikke meningsfullt
Hastegrad: flex  → Vurder varsling → KJERNECASE: Varslingsliste
```

**Brukerreise:**
```
Søk: "lettmelk"
├── "Jeg trenger det nå"
│         └── [+ Legg i handleliste] → ferdig
└── "Vil ha det hvis prisen er riktig"
          └── [⭐ Legg til varsling] + sett terskel
                    └── Scheduled task → pris matcher
                              └── Varsling → bruker bestemmer:
                                        ├── [+ Legg i handleliste]
                                        └── [Ignorer]
```

### De tre listene

| Liste | Navn              | Formål                                              |
|-------|-------------------|-----------------------------------------------------|
| 1     | Handlelister      | Oversikt over aktive lister (én per handletur)      |
| 2     | Varslingsliste    | Produkter bruker vil kjøpe VIS prisen treffer       |
| 3     | Handleliste (innhold) | Konkrete produkter i én valgt handleliste       |

### Feature 10 — Handleliste (DB + UI)

**db.py:**
```python
def create_shopping_list(user_id: int, name: str) -> int
def get_shopping_lists(user_id: int) -> list[dict]
def get_shopping_list_items(list_id: int) -> list[dict]
def add_to_shopping_list(list_id: int, original_name: str,
                          quantity: int = 1, note: str = None) -> int
def toggle_item_checked(item_id: int) -> None
def delete_shopping_list(list_id: int) -> None
def archive_shopping_list(list_id: int) -> None
```

**UI-layout:**
```
"Mine handlelister"
├── [Ukeshandel]   5 varer  → åpne
├── [Fredagsmat]   2 varer  → åpne
└── [+ Ny liste]

Handleliste-visning:
├── [ ] Lettmelk     1 stk   19,30 kr (Oda)   [⭐]
├── [ ] Havregryn    2 stk   34,00 kr (Meny)  [⭐]
├── [x] Smør         ← grå/gjennomstrek
└── [+ Legg til produkt]  ← søkefelt
```

### Feature 11 — Varslingsliste (DB + logic + UI)

**Terskel-typer:**
- `sale` — "på tilbud" (default, enklest): pris < 90% av 30-dagers snitt
- `absolute` — "under X kr": pris < threshold_value
- `relative` — "Y% under snitt": pris < snitt × (1 - threshold_value/100)

**db.py:**
```python
def add_to_watchlist(user_id: int, original_name: str,
                      threshold_type: str, threshold_value: float = None) -> int
def remove_from_watchlist(user_id: int, original_name: str) -> None
def get_watchlist(user_id: int) -> list[dict]
def get_all_watchlist_items() -> list[dict]   # brukes av tasks.py
def mark_watchlist_triggered(watchlist_id: int, price: float, store: str) -> None
def reset_watchlist_item(watchlist_id: int) -> None   # tilbake til 'waiting'
def is_on_watchlist(user_id: int, original_name: str) -> bool
```

**Terskellogikk (tasks.py / normalize.py):**
```python
def check_threshold(item: dict, current_price: float, avg_price: float) -> bool:
    if item["threshold_type"] == "absolute":
        return current_price < item["threshold_value"]
    if item["threshold_type"] == "relative":
        return current_price < avg_price * (1 - item["threshold_value"] / 100)
    if item["threshold_type"] == "sale":
        return current_price < avg_price * 0.90
```

**UI — varslingsliste:**
```
⭐ Varslingsliste  (2 aktive)
🟡 Lettmelk     < 18 kr       Nå: 22 kr   [Endre terskel]  [Fjern]
🟢 Havregryn    på tilbud     Nå: 29 kr ← TRUFFET!         [+ Liste] [Ignorer]
```
Fargestatus: 🟡 venter | 🟢 truffet | ⚫ ignorert/inaktiv

**add_to_watchlist() bør auto-kalle add_to_price_fetch()** — sikrer at prisdata samles inn.

### Feature 12 — Stjerne-knapp og beslutningsflyt

**Stjernen (⭐) = "Varsle meg om dette"**

Terskel-dialog ved klikk (radio-buttons, ikke fritekst):
```
"Varsle meg om Lettmelk når..."
  ○ Prisen er på tilbud  (anbefalt, default)
  ○ Prisen er under  [18] kr
  ○ Prisen er mer enn [15] % billigere enn vanlig
[Lagre varsel]   [Avbryt]
```

**Etter varsling — beslutningsflyt:**
```
🔔 Varsling:
"Lettmelk er nå 17,90 kr hos Oda — 19% under normalt!"
  [+ Legg i handleliste ▾]    [Ignorer]
   └── velg liste:
       • Ukeshandel
       • + Ny liste
```

Etter valg:
- "Legg i liste" → legger til, setter watchlist status = 'ignored', ⭐ forblir aktiv for neste gang
- "Ignorer" → status = 'ignored', auto-reset til 'waiting' etter 7 dager

### Feature 13 — UI-navigasjon

**Sidebar:**
```
🔍  Søk              ← primær inngangspunkt
🛒  Handlelister
⭐  Varslingsliste
📈  Prishistorikk
⚙️  Normalisering
👤  [Bilde + navn]   | Logg ut
```

**Søk — UI-layout:**
```
[ Søk etter produkt... ]

Resultater for "lettmelk":
┌─────────────────────────────────────────────────┐
│  Lett melk                   (normalisert navn) │
│  TINE Lett Melk 1L  — 22,90 kr  Oda   ▲ +1,20  │
│  Q Lett 1L          — 21,50 kr  Meny  → stabil │
│                                                 │
│  [+ Legg i liste ▾]      [⭐ Varsle meg]        │
└─────────────────────────────────────────────────┘
```
- Sort etter beste pris automatisk
- ▲ dyrere, ▼ billigere, → stabil (siste 7 dager)
- [+ Legg i liste ▾] åpner volume-velger + antall + liste-valg

---

## 7. BUG & UX ISSUES — APP-TEST 2026-05-01

### Sammendrag
Analysert 6 skjermbilder fra live app. Identifisert 7 issues: 3 kritiske (strukturelle), 4 moderate/lave.

### ISSUE-01 — Manglende normalisering (Kritisk)
**Symptom:** Samme produkt vises som 3–5 rader: "Q Melk Lett", "Lettmelk 0,5% Q", "Lettmelk 0,5% q"
**Konsekvens:** Dataduplisering i søk, handleliste, varsler og prissammenligning
**Fix:** Feature 1 + Feature 3 (normalisering + auto-normalisering)
**Branch:** `feature/normalization`

### ISSUE-02 — Antall på søk-nivå er semantisk feil (Moderat)
**Symptom:** Antall-felt (5) i søkeskjema — men man vet ikke hva man vil ha 5 av før man ser resultater
**Konsekvens:** Antall propagerer som 5 separate produktlinjer, ikke "5 × billigste"
**Fix:** Fjern antall fra søkskjema. Flytt til "Legg til"-dialogboksen.
**Branch:** `fix/search-ux`

### ISSUE-03 — Prisendring-baseline er feil (Moderat)
**Symptom:** "Q melk lett 19,30 kr (var 35,80 kr)" — 35,80 er 1,75L-prisen, ikke 1L-baseline
**Konsekvens:** Besparelsesbeløp er meningsløst og misvisende
**Fix:** Baseline må alltid være fra SAMME product_id + store_id. Aldri blande volum.
**Branch:** `fix/price-baseline`

### ISSUE-04 — Varsler er ikke gruppert (Moderat)
**Symptom:** 6 separate varselbokser for "lettmelk" — én per produkt-SKU
**Forventet:** Én varselboks per normalisert kategori med beste pris
**Fix:** Grupper varsler per resolve_name(). Følger automatisk av ISSUE-01-fix.
**Branch:** Dekkes av `feature/normalization`

### ISSUE-05 — Handleliste mangler avkryssing og pris (Moderat)
**Symptom:** Handleliste viser navn, volum og X-knapp. Ingen checkbox, ingen pris.
**Forventet:** Checkbox per rad, siste pris, gjennomstreket ved kjøpt
**Fix:** Feature 10 (handleliste DB + UI)
**Branch:** `feature/shopping-list`

### ISSUE-06 — Prisendring-pil er visuelt inkonsistent (Lav)
**Symptom:** "↑ 16.50 kr" brukes for besparelse (ikke prisstigning) — forvirrende
**Fix:** ↑ = dyrere (rødt), ↓ = billigere (grønt). Eller bruk farge uten pil.
**Branch:** `fix/price-arrow-semantics`

### ISSUE-07 — Seleksjonsmodell er på feil abstraksjonsnivå (Kritisk)
**Symptom:** Checkbox-tabell lar bruker velge individuelle SKU-er.
Resulterte i handleliste med:
- 3 × 1L lettmelk (3L totalt — brukeren ville ha 1L)
- Blandet 1L + 1,75L Q-melk (2,75L totalt)
- 5 separate produktlinjer, ikke "5 × billigste lettmelk"
- Optimal sum kr 124,80 beregnet på feil produktsett

**Rotårsak:** Checkboxmodellen opererer på SKU-nivå (butikk × merke × volum).
Brukeren tenker på kategori-nivå ("lettmelk").

**Fix:**
- Fjern multi-select checkboxer fra handleliste-flyten
- Introduser gruppe-kort per normalisert navn:
  - Volum-velger (dropdown)
  - Antall (+/-)
  - Automatisk beste pris
  - Én "Legg til"-knapp
- Behold tabellen som ren PRISSAMMENLIGNING (informasjonsvisning)
- Skill tydelig mellom "se priser" og "legg til i liste"

**Branch:** `feature/shopping-list` (del av redesign)

### Prioritert tiltaksliste

| Prioritet | Issue   | Branch                         | Estimat |
|-----------|---------|--------------------------------|---------|
| 🔴 1      | ISSUE-01| `feature/normalization`        | Stor    |
| 🔴 2      | ISSUE-07| `feature/shopping-list`        | Stor    |
| 🟠 3      | ISSUE-02| `fix/search-ux`                | Liten   |
| 🟠 4      | ISSUE-04| Dekkes av normalisering        | —       |
| 🟠 5      | ISSUE-05| `feature/shopping-list`        | Middels |
| 🟡 6      | ISSUE-03| `fix/price-baseline`           | Middels |
| 🟡 7      | ISSUE-06| `fix/price-arrow-semantics`    | Liten   |

---

## 8. IMPLEMENTASJONSREKKEFØLGE & BRANCHES

### Overordnet strategi
Én branch per feature/fix. Ingen branch merger til main uten at:
1. Testene i `tests/` passerer
2. CHANGELOG.md er oppdatert
3. DECISIONS.md er oppdatert med evt. nye valg

### Branch-oversikt

```
main
├── feature/db-foundation          ← STEG 1: db.py med alle tabeller
├── feature/normalization          ← STEG 2+3: Feature 1+3 (normal, auto)
├── feature/product-persistence    ← STEG 4: Feature 2 (lagre produkter)
├── feature/price-fetch-task       ← STEG 5: Feature 5+6 (price_fetch + task)
├── feature/google-auth            ← STEG 6: Feature 8 (.env, auth.py)
├── feature/per-user-isolation     ← STEG 7: Feature 9 (user_normal, price_fetch per user)
├── feature/shopping-list          ← STEG 8: Feature 10+12+13 (ISSUE-07 inkludert)
├── feature/watchlist              ← STEG 9: Feature 11+12 (varsling)
├── feature/price-history-ui       ← STEG 10: Feature 7 (graf)
├── feature/normalization-ui       ← STEG 11: Feature 4 (custom navn UI)
├── fix/search-ux                  ← ISSUE-02 (fjern antall fra søk)
├── fix/price-baseline             ← ISSUE-03
└── fix/price-arrow-semantics      ← ISSUE-06
```

### Detaljert rekkefølge

**STEG 1 — `feature/db-foundation`**
- Opprett `db.py` med alle `CREATE TABLE IF NOT EXISTS`
- `grocery.db` opprettes automatisk
- Test: alle tabeller eksisterer etter `import db`

**STEG 2 — `feature/normalization`**
- `normalize.py`: `auto_normalize()`, `resolve_name()`
- `db.py`: `upsert_normal()`, `get_display_name()`, `list_normals()`
- `tasks.py` (grunnstruktur): `run_auto_normalize()`
- Fikser også ISSUE-01 og ISSUE-04

**STEG 3 — `feature/product-persistence`**
- `db.py`: `ensure_store()`, `upsert_product()`, `get_products()`
- Koble `oda.py` og `meny.py` til DB etter scraping

**STEG 4 — `feature/price-fetch-task`**
- `db.py`: `add_to_price_fetch()`, `remove_from_price_fetch()`, `get_price_fetch_products()`
- Scrapers: `fetch_price(product_id: str) -> float | None`
- `tasks.py`: `run_price_fetch()`

**STEG 5 — `feature/google-auth`**
- `.env` + `.gitignore`
- `requirements.txt` oppdatering
- `db.py`: `ensure_user()`, `get_user_id()`
- `auth.py`: full OAuth-flyt
- `main.py`: `require_login()` + sidebar

**STEG 6 — `feature/per-user-isolation`**
- `db.py`: `user_normal`-tabell, migrer ev. `custom_name`
- Oppdater `price_fetch` med `user_id`-kolonne
- Oppdater alle bruker-spesifikke funksjoner

**STEG 7 — `feature/shopping-list`**
- `db.py`: `shopping_list` + `shopping_list_item` + alle funksjoner
- `main.py`: ny seleksjonsmodell (gruppe-kort, ikke checkboxer)
- Fikser ISSUE-05 og ISSUE-07

**STEG 8 — `feature/watchlist`**
- `db.py`: `watchlist` + alle funksjoner
- `normalize.py`: `check_threshold()`
- `tasks.py`: watchlist-sjekk i `run_price_fetch()`
- `main.py`: varslingsliste UI med fargestatus

**STEG 9 — `feature/price-history-ui`**
- `db.py`: `get_price_history()`
- `main.py`: linjegraf med `st.line_chart()`

**STEG 10 — `feature/normalization-ui`**
- `main.py`: custom-normalisering tab

**Parallelle fixes (kan tas når som helst):**
- `fix/search-ux` — ISSUE-02: fjern antall fra søk
- `fix/price-baseline` — ISSUE-03: korrekt baseline per product_id
- `fix/price-arrow-semantics` — ISSUE-06: konsistent pil-semantikk

---

## 9. TESTPLAN

### Teststrategi
- **Unit-tester:** Isolerte funksjoner i db.py, normalize.py, tasks.py
- **Integrasjonstester:** DB-operasjoner mot ekte SQLite (test-DB i minne)
- **Scraper-tester:** Mock HTTP-svar — aldri kall ekte API i CI
- **Auth-tester:** Mock OAuth-flyt
- **UI-tester:** Ikke prioritert (Streamlit er vanskelig å teste automatisk)

### Testoppsett
```python
# tests/conftest.py
import pytest
import sqlite3
import db

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Opprett isolert SQLite-DB i minne for hver test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    db.init_db()
    return db_path
```

### tests/test_db.py
```python
def test_ensure_store(test_db):
    sid = db.ensure_store("oda")
    assert isinstance(sid, int)
    assert db.ensure_store("oda") == sid  # idempotent

def test_upsert_product(test_db):
    sid = db.ensure_store("oda")
    pid = db.upsert_product("ext-123", "Tine Lettmelk", sid)
    assert isinstance(pid, int)
    assert db.upsert_product("ext-123", "Tine Lettmelk", sid) == pid  # idempotent

def test_upsert_normal(test_db):
    db.upsert_normal("Tine Lettmelk")
    rows = db.list_normals()
    assert any(r["original_name"] == "Tine Lettmelk" for r in rows)

def test_price_history_no_duplicates(test_db):
    sid = db.ensure_store("oda")
    pid = db.upsert_product("ext-123", "Tine Lettmelk", sid)
    db.save_price(pid, sid, "2026-05-01", 19.90)
    db.save_price(pid, sid, "2026-05-01", 20.00)  # skal ikke duplikere
    rows = db.get_price_history(pid)
    assert len([r for r in rows if r["date"] == "2026-05-01"]) == 1

def test_get_display_name_priority(test_db):
    uid = db.ensure_user("sub-123", "test@example.com", "Test User")
    db.upsert_normal("Tine Lettmelk", auto_name="lett melk")
    # Uten custom: skal returnere auto_name
    assert db.get_display_name("Tine Lettmelk") == "lett melk"
    # Med custom: skal returnere custom_name
    nid = db.get_normal_id("Tine Lettmelk")
    db.set_custom_name_by_id(nid, "Lettmelk", uid)
    assert db.get_display_name("Tine Lettmelk", user_id=uid) == "Lettmelk"

def test_shopping_list_crud(test_db):
    uid = db.ensure_user("sub-123", "test@example.com", "Test")
    lid = db.create_shopping_list(uid, "Ukeshandel")
    assert lid is not None
    iid = db.add_to_shopping_list(lid, "Tine Lettmelk", quantity=2)
    items = db.get_shopping_list_items(lid)
    assert len(items) == 1
    assert items[0]["quantity"] == 2
    db.toggle_item_checked(iid)
    items = db.get_shopping_list_items(lid)
    assert items[0]["checked"] == 1

def test_watchlist_add_and_trigger(test_db):
    uid = db.ensure_user("sub-123", "test@example.com", "Test")
    db.add_to_watchlist(uid, "Tine Lettmelk", "absolute", 18.0)
    items = db.get_watchlist(uid)
    assert len(items) == 1
    assert items[0]["status"] == "waiting"
    db.mark_watchlist_triggered(items[0]["id"], 17.50, "oda")
    items = db.get_watchlist(uid)
    assert items[0]["status"] == "triggered"
```

### tests/test_normalize.py
```python
from normalize import auto_normalize, check_threshold

def test_compound_split():
    assert auto_normalize("lettmelk") == "lett melk"
    assert auto_normalize("helmelk") == "hel melk"
    assert auto_normalize("LETTMELK") == "lett melk"

def test_volume_normalization():
    assert auto_normalize("Tine 1L") == "tine 1l"
    assert auto_normalize("Tine 1 liter") == "tine 1l"
    assert auto_normalize("Tine 1000g") == "tine 1kg"

def test_threshold_absolute():
    item = {"threshold_type": "absolute", "threshold_value": 20.0}
    assert check_threshold(item, 19.90, 25.0) is True
    assert check_threshold(item, 20.10, 25.0) is False

def test_threshold_sale():
    item = {"threshold_type": "sale", "threshold_value": None}
    assert check_threshold(item, 20.0, 25.0) is True   # 80% av snitt
    assert check_threshold(item, 23.0, 25.0) is False  # 92% av snitt

def test_threshold_relative():
    item = {"threshold_type": "relative", "threshold_value": 15.0}
    assert check_threshold(item, 21.0, 25.0) is True   # 16% under snitt
    assert check_threshold(item, 22.0, 25.0) is False  # 12% under snitt
```

### tests/test_scrapers.py
```python
from unittest.mock import patch, AsyncMock
from scrapers.oda import fetch_price as oda_fetch_price

def test_oda_fetch_price_returns_float():
    mock_response = {"price": 19.90}
    with patch("scrapers.oda.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=type("R", (), {"json": lambda self: mock_response, "raise_for_status": lambda self: None})()
        )
        import asyncio
        price = asyncio.run(oda_fetch_price("ext-123"))
        assert price == 19.90

def test_fetch_price_returns_none_on_error():
    with patch("scrapers.oda.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Network error"))
        import asyncio
        price = asyncio.run(oda_fetch_price("ext-123"))
        assert price is None
```

### tests/test_tasks.py
```python
from unittest.mock import patch, MagicMock
import tasks

def test_run_auto_normalize_updates_db(test_db):
    import db
    db.upsert_normal("lettmelk")
    tasks.run_auto_normalize()
    rows = db.list_normals()
    row = next(r for r in rows if r["original_name"] == "lettmelk")
    assert row["auto_name"] == "lett melk"

def test_run_auto_normalize_skips_existing(test_db):
    import db
    db.upsert_normal("lettmelk", auto_name="eksisterende")
    tasks.run_auto_normalize()
    rows = db.list_normals()
    row = next(r for r in rows if r["original_name"] == "lettmelk")
    assert row["auto_name"] == "eksisterende"  # ikke overskrevet
```

### tests/test_auth.py
```python
from unittest.mock import patch, MagicMock
import auth

def test_exchange_code_returns_user_dict():
    mock_userinfo = {"sub": "123", "email": "a@b.com", "name": "Test", "picture": "http://img"}
    with patch("auth.OAuth2Client") as MockClient:
        instance = MockClient.return_value
        instance.fetch_token.return_value = {"access_token": "tok"}
        instance.get.return_value.json.return_value = mock_userinfo
        result = auth.exchange_code_for_user("fake-code")
        assert result["sub"] == "123"
        assert result["email"] == "a@b.com"
```

### Kjøre tester
```powershell
cd C:\mittprosjekt\grocery-scraper
python -m pytest tests/ -v
python -m pytest tests/ -v --tb=short   # kortere traceback
python -m pytest tests/test_db.py -v    # kun DB-tester
```

### requirements for testing
```
pytest>=8.0
pytest-asyncio>=0.23
```

---

## 10. LOGGING & LOKALE MD-FILER

Claude Code CLI skal holde disse filene oppdatert gjennom arbeidet.

### CLAUDE.md — Prosjektstatus for Claude Code

```markdown
# CLAUDE.md — grocery-scraper

## Prosjektbeskrivelse
Prissammenligner for Oda og Meny. Python + Streamlit + SQLite.

## Kjøre appen
    python -m streamlit run main.py

## Kjøre tasks
    python tasks.py normalize
    python tasks.py fetch

## Kjøre tester
    python -m pytest tests/ -v

## Aktiv branch
[oppdateres av Claude Code]

## Siste beslutning
[oppdateres av Claude Code]

## Viktige constraints
- sqlite3 (standard lib) — ikke SQLAlchemy
- python (ikke python3) på denne maskinen
- PowerShell-syntax alltid
- grocery.db ikke i git
- .env ikke i git
- resolve_name() er eneste funksjon for produktnavn i UI
```

### DECISIONS.md — Arkitekturvalg

Claude Code oppdaterer denne filen ved hvert arkitekturvalg:

```markdown
# DECISIONS.md

## 2026-05-01 — sqlite3 over SQLAlchemy
**Beslutning:** Bruker sqlite3 (standard lib)
**Begrunnelse:** Enklere, ingen dependencies, tilstrekkelig for prosjektets størrelse
**Konsekvenser:** Ingen ORM, manuelle SQL-queries i db.py

## 2026-05-01 — google_sub som bruker-ID
**Beslutning:** Bruker Google sub-claim, ikke e-post
**Begrunnelse:** E-post kan endres av bruker. sub er stabil livstid.
**Konsekvenser:** Må alltid hente sub fra ID-token, ikke email

## 2026-05-01 — price_history er global
**Beslutning:** price_history deles på tvers av brukere
**Begrunnelse:** Ingen grunn til å lagre samme pris/dato dobbelt for to brukere
**Konsekvenser:** UNIQUE(product_id, store_id, date) hindrer duplikater automatisk

## 2026-05-01 — user_normal over custom_name i normal
**Beslutning:** Per-bruker custom-navn i egen tabell user_normal
**Begrunnelse:** normal-tabellen er global. Custom-navn er personlig preferanse.
**Konsekvenser:** Breaking change fra v2.0 Feature 4. Migrer ved å flytte
  eksisterende custom_name til user_normal under "default"-bruker.

## 2026-05-01 — Kategori-nivå i handleliste
**Beslutning:** Handleliste lagrer original_name (normalisert kategori), ikke product_id (SKU)
**Begrunnelse:** Brukeren tenker "lettmelk", ikke "Tine Lettmelk 1L fra Oda"
**Konsekvenser:** Shopping_list_item.original_name kobler til normal-tabellen.
  Best-pris-visning gjøres ved oppslag mot siste price_history for alle matchende produkter.

## 2026-05-01 — authlib over streamlit-google-auth
**Beslutning:** Bruker authlib direkte for OAuth
**Begrunnelse:** streamlit-google-auth er ikke vedlikeholdt på PyPI
**Konsekvenser:** Mer kode i auth.py, men stabilt og produksjonsklar
```

### BACKLOG.md — Neste features og ideer

```markdown
# BACKLOG.md

## Fase 3 — Notifikasjoner
- [ ] E-post-varsling via SMTP (bruk Google-e-post fra OAuth)
- [ ] Push-notifikasjon (krever native app eller PWA)
- [ ] SMS via Twilio (fase 3+)

## Fase 3 — Flere scrapers
- [ ] Rema 1000 (API ikke-funksjonell pr. 2026-05-01 — følg med)
- [ ] Kiwi
- [ ] Coop

## Fase 3 — Forbedret normalisering
- [ ] ML-basert normalisering (embedding-similarity mellom produktnavn)
- [ ] Brukerforslag til compound splits

## Fase 4 — Analyse
- [ ] Prisutvikling per kategori over tid
- [ ] "Beste butikk for min handleliste"-analyse
- [ ] Spar X kr ved å handle hos Y i stedet for Z
```

### CHANGELOG.md — Hva som er gjort

Claude Code appender til denne etter hver branch:

```markdown
# CHANGELOG.md

## [Unreleased]

## [branch: feature/db-foundation]
- Opprettet db.py med alle tabeller
- grocery.db opprettes automatisk
- Lagt til tests/conftest.py

## [branch: feature/normalization]
...
```

---

## 11. CLAUDE CODE CLI — OPPSTARTSPROMPTER

### Generell oppstart (les alltid dette først)
```
Les C:\mittprosjekt\GROCERY_SCRAPER_SPEC.md i sin helhet.
Les deretter CLAUDE.md hvis den finnes.
Sjekk faktisk filstruktur:
  Get-ChildItem -Recurse -Include *.py | Select-Object FullName
  Get-Content requirements.txt
Bekreft hvilken branch som er aktiv:
  git branch
```

### STEG 1 — DB-foundation
```
Les spec seksjon 3 (databaseskjema) og seksjon 9 (testplan).
Oppgave: Implementer db.py med alle CREATE TABLE IF NOT EXISTS.
- grocery.db skal opprettes automatisk ved import
- Eksporter DB_PATH som konstant slik at tester kan override den
- Skriv tests/conftest.py med test_db fixture
- Skriv tests/test_db.py med tester fra spec seksjon 9
Kjør tester etter: python -m pytest tests/test_db.py -v
Oppdater CHANGELOG.md og CLAUDE.md.
Branch: feature/db-foundation
```

### STEG 2 — Normalisering
```
Les spec seksjon 4 (Feature 1 og 3).
Oppgave: Implementer normalize.py og run_auto_normalize() i tasks.py.
- COMPOUND_SPLITS ordliste skal ligge i normalize.py
- auto_normalize() håndterer lowercase, CamelCase, sammensetninger, volum/vekt
- resolve_name() er eneste eksponerte funksjon til UI
- Skriv tests/test_normalize.py fra spec seksjon 9
Kjør tester: python -m pytest tests/test_normalize.py -v
Branch: feature/normalization
```

### STEG 5 — Google Auth
```
Les spec seksjon 5 (Feature 8 og 9).
FORUTSETNING: .env finnes med GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
Oppgave:
1. Legg til .env og grocery.db i .gitignore
2. Oppdater requirements.txt med authlib, httpx, python-dotenv
3. Implementer auth.py (get_auth_url, exchange_code_for_user, require_login)
4. Legg til ensure_user() og get_user_id() i db.py
5. Legg til require_login() øverst i main.py med sidebar
Skriv tests/test_auth.py fra spec seksjon 9.
Branch: feature/google-auth
```

### STEG 7 — Handleliste + seleksjonsmodell
```
Les spec seksjon 6 (Feature 10, 12, 13) og seksjon 7 (ISSUE-05, ISSUE-07).
Kritisk: Ny seleksjonsmodell — IKKE multi-select checkboxer.
- Gruppe-kort per normalisert navn
- Volum-velger (dropdown) + antall (+/-) + automatisk beste pris
- Tabellen er kun informasjonsvisning for prissammenligning
Implementer shopping_list + shopping_list_item i db.py.
Skriv tester.
Branch: feature/shopping-list
```

### Fix-brancher (kan tas parallelt)
```
fix/search-ux:
  Fjern antall-feltet fra søkeskjema i main.py.
  Flytt antall-velger til "Legg til"-dialog.
  Ingen DB-endringer. Liten endring.

fix/price-baseline:
  I prisfall-beregning: baseline (var-pris) må hentes fra
  SAMME product_id + store_id kombinasjon.
  Aldri blande volum-varianter i baseline-beregning.

fix/price-arrow-semantics:
  ↑ = prisen har gått opp (rødt, negativt for bruker)
  ↓ = prisen har gått ned (grønt, positivt for bruker)
  Gjennomgå alle steder der prisendring vises i main.py.
```

---

## APPENDIKS — CONSTRAINTS OPPSUMMERT

```
- sqlite3 (standard lib) — ikke SQLAlchemy
- python (ikke python3) — Windows 11
- PowerShell-syntax alltid (ikke bash)
- grocery.db ikke i git
- .env ikke i git
- resolve_name() eneste funksjon for produktnavn i UI
- google_sub (ikke e-post) er stabil bruker-ID
- price_history er global (deles på tvers av brukere)
- user_normal er per-bruker (ikke custom_name i normal)
- Handleliste lagrer original_name (kategori), ikke product_id (SKU)
- add_to_watchlist() auto-kaller add_to_price_fetch()
- tasks.py kjøres direkte: python tasks.py normalize / fetch
- Ingen migrasjoner — bare CREATE TABLE IF NOT EXISTS
```
