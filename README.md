# Tracking Success 📊

Persönliche Kennzahlen-Tracking Web-App mit FastAPI Backend und React Frontend.

## Features

- **Authentifizierung**: Registrierung mit E-Mail-Bestätigung, Login, Passwort-Zurücksetzung
- **Tägliches Tracking**: Gewicht, Sport, Schlaf, Stimmung, etc.
- **Erfolgs-Animationen**: Visuelles Feedback bei Erfolg/Misserfolg
- **Streaks**: Fortlaufende Erfolgsserien mit Meilenstein-Animationen
- **Liniendiagramme**: Performance über 7, 30 oder 365 Tage
- **YAML-Konfiguration**: Kennzahlen als YAML exportieren/importieren

## Auth Flows

1. **Registrierung**: POST `/api/auth/register` → erstellt inaktiven User, sendet Bestätigungs-E-Mail via Sweego
2. **E-Mail bestätigen**: GET `/api/auth/confirm/{token}` → aktiviert den User
3. **Login**: POST `/api/auth/login` → prüft `is_active`, gibt JWT zurück
4. **Passwort vergessen**: POST `/api/auth/forgot-password` → sendet Reset-E-Mail (404 wenn E-Mail nicht existiert)
5. **Passwort zurücksetzen**: POST `/api/auth/reset-password/confirm` → setzt neues Passwort mit Token
6. **Bestätigung erneut senden**: POST `/api/auth/resend-confirmation` → sendet neue Bestätigungs-E-Mail

Tokens werden als SHA-256 Hash in der DB gespeichert (nie als Klartext). TTL: Bestätigung 24h, Reset 1h.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **Infra**: Docker Compose, Traefik, Let's Encrypt
- **Email**: Sweego API (transaktionale E-Mails via `support.jonaskrauss.de`)

## Development

### Backend

```bash
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]" aiosqlite
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Tests

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="sqlite+aiosqlite:///tmp/test_auth.db"
export JWT_SECRET="test-secret"
export SWEEGO_API_KEY="test-key"
export APP_BASE_URL="http://test"
python -m pytest
```

## Deployment

Die App wird über Hermine auf den Hetzner VPS deployed:

```bash
# Staging
scripts/staging-up.sh tracking-success

# Production
scripts/prod-up.sh tracking-success
```

## URLs

- **Production**: https://tracking-success.jonaskrauss.de
- **Staging**: https://tracking-success.stage.jonaskrauss.de

## Kennzahlen

| Kennzahl | Typ | Berechnung | Ziel |
|----------|-----|------------|------|
| Schlaf | sleep | Aufstehzeit - Bettzeit - 1h | ≥ 7h |
| Einstellarbeit | bool | - | Erledigt |
| Morgenrunde | bool | - | Erledigt |
| Sport | bool | - | Erledigt |
| 2h Fokus | bool | - | Erledigt |
| Plan für Morgen | bool | - | Erledigt |
| Kein Youtube | bool | - | Erledigt |
| Stimmung | float | - | - |
| Fokus | float | - | - |
| Gewicht | weight | Heute < Gestern | Abgenommen |
| Fastenzeit | fasting | Abendessen → Frühstück | ≥ 15h |

## Streak-Meilensteine

Bei Erreichen dieser Streak-Längen wird eine Animation abgespielt:
3, 7, 14, 30, 60, 90, 183, 365 Tage