"""
图片上传和管理路由
"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.image_utils import generate_filename, validate_image, get_image_info
from app.models.schemas import ImageUploadResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """上传图片"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    filename = generate_filename(file.filename or "image.png")
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 验证图片
    if not validate_image(file_path):
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="无效的图片文件或文件过大（最大10MB）")

    info = get_image_info(file_path)
    size = os.path.getsize(file_path)

    return ImageUploadResponse(
        filename=filename,
        url=f"/uploads/{filename}",
        width=info["width"],
        height=info["height"],
        size=size,
    )
