from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.api.routes.remove_background import router as remove_background_router
from app.services.model_registry import model_manager
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.images import router as images_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting AI Background Remover backend...")

    print("Loading BiRefNet model...")

    model = model_manager.get_model("birefnet")
    model.load_model()

    print("Backend is ready!")

    yield

    print("Shutting down AI Background Remover backend...")


app = FastAPI(
    title="AI Background Remover API",
    description="Backend API for AI-powered background removal.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Image-ID"],
)


@app.get("/")
def home():
    return {
        "message": "AI Background Remover backend is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(
    remove_background_router,
    prefix="/api/v1",
    tags=["Background Removal"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(images_router)