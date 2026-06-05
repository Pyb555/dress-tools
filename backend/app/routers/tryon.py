"""
试穿相关路由
"""
import os
from fastapi import APIRouter, HTTPException
from app.models.schemas import TryOnRequest, TryOnResponse
from app.services.tryon_engine import get_tryon_engine

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")


@router.post("/run", response_model=TryOnResponse)
async def run_tryon(req: TryOnRequest):
    """执行虚拟试穿"""
    # 检查衣服图片是否存在
    clothing_path = os.path.join(UPLOAD_DIR, req.clothing_image)
    if not os.path.exists(clothing_path):
        raise HTTPException(status_code=404, detail="衣服图片不存在")

    # 检查模特图片是否存在
    model_path = os.path.join(UPLOAD_DIR, req.model_image)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="模特图片不存在")

    # 调用 AI 引擎
    try:
        engine = get_tryon_engine()
        result = await engine.run(
            clothing_path=clothing_path,
            model_path=model_path,
            category=req.category,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试穿处理失败: {str(e)}")
