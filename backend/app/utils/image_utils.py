"""
图片处理工具
"""
import os
import uuid
from PIL import Image


def ensure_dirs(dirs: list[str]) -> None:
    """确保目录存在"""
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def generate_filename(original_name: str) -> str:
    """生成唯一文件名，保留扩展名"""
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "png"
    return f"{uuid.uuid4().hex}.{ext}"


def validate_image(file_path: str, max_size_mb: int = 10) -> bool:
    """验证图片文件"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False
        return True
    except Exception:
        return False


def get_image_info(file_path: str) -> dict:
    """获取图片基本信息"""
    with Image.open(file_path) as img:
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
        }
