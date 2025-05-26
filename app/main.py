from fastapi import FastAPI
from api.api_router import router as api_router
from database.session import init_db

init_db()

app = FastAPI(title="Real Estate LLM Agent")

@app.get("/")
def read_root():
    return {"message": "Welcome to Real Estate LLM Agent"}

app.include_router(api_router, prefix="/api")