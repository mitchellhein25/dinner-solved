# Dinner Solved

AI-powered meal planning that eliminates the weekly mental load of figuring out what to cook and what to buy.

## What it does

Set up your household and meal template once. Each week the app suggests recipes, lets you refine via chat, and generates a scaled, merged grocery list ready to export.

## Architecture

Clean Architecture with a Python FastAPI backend as the system brain and a Vue 3 frontend as a thin client.

```
dinner-solved/
├── api/      # Python FastAPI backend (all business logic)
└── web/      # Vue 3 frontend (presentation only)
```

See [dinner-solved-brief.md](./dinner-solved-brief.md) for full architecture documentation.

## Local Development

```bash
# Copy environment files
cp api/.env.example api/.env
# Edit api/.env with your ANTHROPIC_API_KEY

# Start all services
docker compose up
```

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Web: http://localhost:5173

## Build Order

Steps completed so far: 1–4 (domain layer only — no DB, API, or UI yet).

See brief for full 16-step build order.
