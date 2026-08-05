from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.routers import cascade, ingest, parse, knowledge, patients

app = FastAPI(title="Prescription Cascade Detector")
app.include_router(ingest.router)
app.include_router(parse.router)
app.include_router(cascade.router)
app.include_router(knowledge.router)
app.include_router(patients.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
