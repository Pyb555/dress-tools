"""
Pydantic 数据模型
"""
from typing import Optional
from pydantic import BaseModel


class TryOnRequest(BaseModel):
    """试穿请求"""
    clothing_image: str   # 衣服图片文件名
    model_image: str      # 模特图片文件名
    category: str = "upper_body"  # upper_body | lower_body | dresses


class TryOnResponse(BaseModel):
    """试穿响应"""
    task_id: str
    status: str           # pending | processing | completed | failed
    result_image: Optional[str] = None
    message: Optional[str] = None


class ImageUploadResponse(BaseModel):
    """图片上传响应"""
    filename: str
    url: str
    width: int
    height: int
    size: int
