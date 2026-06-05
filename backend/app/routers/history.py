"""
历史记录管理路由
"""
import os
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

router = APIRouter()

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "history.json")


def _load_history() -> list[dict]:
    """加载历史记录"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(history: list[dict]) -> None:
    """保存历史记录"""
    # 只保留最近 50 条
    history = history[:50]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@router.get("/list")
async def list_history(limit: int = 20):
    """获取历史试穿记录"""
    history = _load_history()
    return {"total": len(history), "items": history[:limit]}


@router.delete("/clear")
async def clear_history():
    """清空历史记录"""
    _save_history([])
    return {"status": "ok", "message": "历史记录已清空"}


@router.delete("/{record_id}")
async def delete_record(record_id: str):
    """删除单条历史记录"""
    history = _load_history()
    history = [h for h in history if h.get("id") != record_id]
    _save_history(history)
    return {"status": "ok", "message": f"记录 {record_id} 已删除"}
