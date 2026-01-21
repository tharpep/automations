# Automations Dashboard

Simple frontend for managing and monitoring automations.

## Features (Planned)

- [ ] View integration status from api-gateway
- [ ] List all automations with enable/disable toggles
- [ ] Manual trigger buttons ("Run Now")
- [ ] View recent run history
- [ ] Pause/resume schedules
- [ ] Mobile-friendly for phone access

## Tech Stack

- **Package Manager**: pnpm
- **Framework**: Vite + React or Vue (TBD)
- **Styling**: Minimal, dark mode
- **Auth**: Simple password (single-user) or OAuth later
- **API**: Calls api-gateway directly

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Dashboard home - status overview |
| `/automations` | List all automations with toggles |
| `/logs` | Recent run history |

## API Endpoints Used

From api-gateway:
- `GET /health` — Gateway status
- `GET /health/integrations` — Integration status
- `GET /context/now` — Current context

From automations backend (to be added):
- `GET /automations` — List all automations
- `POST /automations/:id/run` — Trigger manually
- `PATCH /automations/:id` — Enable/disable

## Development

```bash
cd frontend
pnpm install
pnpm dev
```

## Deployment

- Local: `pnpm build && pnpm preview`
- Cloud: Static files on Cloud Storage or bundled with automations container
