"""
AI 虚拟试穿 - FastAPI 后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import tryon, images, history
from app.utils.image_utils import ensure_dirs

# 确保上传和结果目录存在
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
ensure_dirs([UPLOAD_DIR, RESULTS_DIR])

app = FastAPI(
    title="Dress Tools API",
    description="AI 虚拟试穿服务",
    version="0.1.0",
)

# CORS: 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tryon.router, prefix="/api/tryon", tags=["试穿"])
app.include_router(images.router, prefix="/api/images", tags=["图片"])
app.include_router(history.router, prefix="/api/history", tags=["历史"])

# 静态文件服务（上传图片和结果可访问）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "dress-tools"}
