from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router, search_engine
from core.config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pre-warm browser
    await search_engine.warmup()
    yield
    # Shutdown: cleanup
    await search_engine._cleanup()


app = FastAPI(
    title="LinkedIn LeadGen API",
    description="AI-powered LinkedIn lead generation engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
