"""
AI 虚拟试穿 - FastAPI 后端入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用，生产环境直接设环境变量）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.routers import tryon, images, history
from app.utils.image_utils import ensure_dirs

# 确保上传和结果目录存在
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
ensure_dirs([UPLOAD_DIR, RESULTS_DIR])

# CORS origins（支持环境变量配置，逗号分隔）
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

app = FastAPI(
    title="Dress Tools API",
    description="AI 虚拟试穿服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tryon.router, prefix="/api/tryon", tags=["试穿"])
app.include_router(images.router, prefix="/api/images", tags=["图片"])
app.include_router(history.router, prefix="/api/history", tags=["历史"])

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "dress-tools"}


@app.get("/")
async def root():
    return {"message": "Dress Tools API", "docs": "/docs"}
