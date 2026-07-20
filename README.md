# Tracking Success 📊

Persönliche Kennzahlen-Tracking Web-App mit FastAPI Backend und React Frontend.

## Features

- **Authentifizierung**: Registrierung, Login, Passwort-Reset
- **Tägliches Tracking**: Gewicht, Sport, Schlaf, Stimmung, etc.
- **Erfolgs-Animationen**: Visuelles Feedback bei Erfolg/Misserfolg
- **Streaks**: Fortlaufende Erfolgsserien mit Meilenstein-Animationen
- **Liniendiagramme**: Performance über 7, 30 oder 365 Tage
- **YAML-Konfiguration**: Kennzahlen als YAML exportieren/importieren

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **Infra**: Docker Compose, Traefik, Let's Encrypt

## Development

### Backend

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
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
pytest
```

## Deployment

Die App wird über Hermine auf den Hetzner VPS deployed:

```bash
# Staging
scripts/staging-up.sh tracking-success

# Production
scripts/prod-up.sh tracking-success
```

## URL

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
