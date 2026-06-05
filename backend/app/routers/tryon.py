"""
试穿相关路由
"""
import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.schemas import TryOnRequest, TryOnResponse
from app.services.tryon_engine import get_tryon_engine

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")


def _save_to_history(record: dict) -> None:
    """保存试穿记录到历史"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []
    except (json.JSONDecodeError, IOError):
        history = []

    history.insert(0, record)
    # 只保留最近 50 条
    history = history[:50]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


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

        # 保存到历史记录
        if result.status == "completed":
            _save_to_history({
                "id": result.task_id,
                "date": datetime.now().isoformat(),
                "clothing_image": req.clothing_image,
                "model_image": req.model_image,
                "result_image": result.result_image,
                "category": req.category,
                "status": "completed",
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试穿处理失败: {str(e)}")
