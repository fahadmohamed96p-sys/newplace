from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import create_tables
from database.seed import seed_database
from routers import auth, aptitude, coding, communication, dashboard, assistant, profile, company
import os

app = FastAPI(title="PlacementPro API", version="3.0.0")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(aptitude.router)
app.include_router(coding.router)
app.include_router(communication.router)
app.include_router(dashboard.router)
app.include_router(assistant.router)
app.include_router(profile.router)
app.include_router(company.router)


@app.on_event("startup")
async def startup():
    print("🚀 PlacementPro starting...")
    create_tables()
    seed_database()
    print("✅ Ready!")


@app.get("/")
async def root():
    return {"message": "PlacementPro API v3 running ✅", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
