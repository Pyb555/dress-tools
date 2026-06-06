"""
阿里云百炼 DashScope AI 试穿 Provider

两步异步模式（适配 PythonAnywhere 超时限制）:
  1. submit() → 提交到 DashScope，返回 ds_task_id
  2. poll()  → 查询状态，完成后下载结果
"""
import os
import json
from typing import Optional
import httpx


class DashScopeProvider:
    """阿里云百炼 AI 试穿引擎（两步异步）"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = base_url or os.getenv("IMAGE_BASE_URL", "http://localhost:8000")

    def submit(self, clothing_path: str, model_path: str, category: str = "upper_body") -> dict:
        """
        提交试穿任务到 DashScope，立即返回
        Returns: {"ok": True, "ds_task_id": "xxx"} or {"ok": False, "error": "..."}
        """
        if not self.api_key:
            return {"ok": False, "error": "DashScope API Key 未配置"}

        try:
            clothing_filename = os.path.basename(clothing_path)
            model_filename = os.path.basename(model_path)
            clothing_url = f"{self.base_url}/uploads/{clothing_filename}"
            model_url = f"{self.base_url}/uploads/{model_filename}"

            inputs = {"person_image_url": model_url}
            if category in ("dresses", "one-pieces"):
                inputs["top_garment_url"] = clothing_url
            elif category == "lower_body":
                inputs["bottom_garment_url"] = clothing_url
            else:
                inputs["top_garment_url"] = clothing_url

            with httpx.Client(timeout=30) as client:
                res = client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis",
                    json={
                        "model": "aitryon-plus",
                        "input": inputs,
                        "parameters": {"resolution": -1, "restore_face": True},
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",
                    },
                )
                res.raise_for_status()
                data = res.json()

            ds_task_id = data.get("output", {}).get("task_id")
            if not ds_task_id:
                return {"ok": False, "error": f"DashScope 返回异常: {data}"}

            return {"ok": True, "ds_task_id": ds_task_id}

        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            return {"ok": False, "error": f"DashScope 错误 ({e.response.status_code}): {detail}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def poll(self, ds_task_id: str) -> dict:
        """
        查询 DashScope 任务状态，完成时下载结果
        Returns: {"status": "PENDING"|"SUCCEEDED"|"FAILED", "result_image": "xxx.png", "error": "..."}
        """
        try:
            with httpx.Client(timeout=15) as client:
                res = client.get(
                    f"https://dashscope.aliyuncs.com/api/v1/tasks/{ds_task_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                res.raise_for_status()
                data = res.json()

            status = data.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                result_url = data.get("output", {}).get("image_url")
                if result_url:
                    result_filename = self._download(result_url, ds_task_id)
                    return {"status": "SUCCEEDED", "result_image": result_filename}
                return {"status": "FAILED", "error": "无结果图片"}
            elif status == "FAILED":
                return {"status": "FAILED", "error": str(data.get("output", {}))}
            else:
                return {"status": status or "PENDING"}

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

    def _download(self, url: str, ds_task_id: str) -> str:
        """下载结果图片到本地，返回文件名"""
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results"
        )
        filename = f"result_{ds_task_id[:12]}.png"
        filepath = os.path.join(results_dir, filename)

        with httpx.Client(timeout=30) as client:
            res = client.get(url)
            res.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(res.content)

        return filename
