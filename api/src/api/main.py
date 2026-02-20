import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from infrastructure.db.postgres.database import init_db  # noqa: E402 (must be after load_dotenv)

from api.routers import auth, grocery, household, plan, preferences, template  # noqa: E402

app = FastAPI(title="Dinner Solved API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Household-ID"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(household.router, prefix="/api/household", tags=["household"])
app.include_router(template.router, prefix="/api/template", tags=["template"])
app.include_router(plan.router, prefix="/api/plan", tags=["plan"])
app.include_router(grocery.router, prefix="/api/grocery", tags=["grocery"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])


@app.on_event("startup")
async def startup() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        init_db(database_url)


@app.get("/health")
async def health():
    return {"status": "ok"}
