from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Under/Over API (minimal)", version="0.0.1")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*").strip()
allow_origins = ["*"] if FRONTEND_ORIGIN in ("", "*") else [FRONTEND_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "stage": "minimal"}

@app.get("/")
def root():
    return {"ok": True, "routes": ["/", "/health"]}