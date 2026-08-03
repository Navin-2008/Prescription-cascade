from fastapi import FastAPI
from app.routers import cascade, ingest

app = FastAPI(title="Prescription Cascade Detector")
app.include_router(ingest.router)
app.include_router(cascade.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
