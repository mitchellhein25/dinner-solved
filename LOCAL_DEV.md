# Local Dev Setup

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be running)
- Python 3.12+
- Node.js 18+

---

## First-time setup

```powershell
cp api/.env.example api/.env
# Fill in your ANTHROPIC_API_KEY in api/.env

npm install           # installs concurrently (root dev tool)
npm run install:api   # installs Python dependencies
```

---

## Daily dev

```powershell
npm run dev
```

Starts Postgres, runs any pending migrations, then runs the API and frontend in parallel.

- API: http://localhost:8000
- Frontend: http://localhost:5173

Press `Ctrl+C` to stop both servers.

---

## Individual commands

| Command              | What it does                        |
|----------------------|-------------------------------------|
| `npm run dev`        | Start everything                    |
| `npm run api`        | Start the API server (port 8000)    |
| `npm run web`        | Start the frontend (port 5173)      |
| `npm run db`         | Start Postgres (detached)           |
| `npm run migrate`    | Run Alembic migrations              |
| `npm run install:api`| Install Python deps (editable mode) |
| `npm run down`       | Stop Docker containers              |
| `npm run reset`      | Stop containers + delete DB volume  |
