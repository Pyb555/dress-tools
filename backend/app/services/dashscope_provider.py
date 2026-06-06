"""
阿里云百炼 DashScope AI 试穿 Provider

- 免费额度: 400 张
- 价格: 0.50 元/张（超出免费额度）
- 模型: aitryon-plus
- 图片需使用公开 URL（不能 base64）
"""
import os
import asyncio
from typing import Optional
import httpx
import uuid
from .tryon_engine import TryOnProvider, TryOnResult


class DashScopeProvider(TryOnProvider):
    """阿里云百炼 AI 试穿引擎"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        # 图片的基础 URL（上传后对外可访问的地址）
        self.base_url = base_url or os.getenv("IMAGE_BASE_URL", "http://localhost:8000")

    async def run(self, clothing_path: str, model_path: str, category: str = "upper_body") -> TryOnResult:
        task_id = uuid.uuid4().hex[:12]

        if not self.api_key:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message="阿里云 DashScope API Key 未配置。请设置 DASHSCOPE_API_KEY。",
            )

        try:
            # 构建图片公开 URL
            clothing_filename = os.path.basename(clothing_path)
            model_filename = os.path.basename(model_path)
            clothing_url = f"{self.base_url}/uploads/{clothing_filename}"
            model_url = f"{self.base_url}/uploads/{model_filename}"

            # 构建请求体
            inputs = {"person_image_url": model_url}
            if category in ("dresses", "one-pieces"):
                inputs["top_garment_url"] = clothing_url
            elif category == "lower_body":
                inputs["bottom_garment_url"] = clothing_url
            else:
                inputs["top_garment_url"] = clothing_url

            async with httpx.AsyncClient(timeout=180.0) as client:
                # Step 1: 提交任务
                submit_res = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis",
                    json={
                        "model": "aitryon-plus",
                        "input": inputs,
                        "parameters": {
                            "resolution": -1,      # 保持原始分辨率
                            "restore_face": True,   # 保留脸部
                        },
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",
                    },
                )
                submit_res.raise_for_status()
                submit_data = submit_res.json()

                dashscope_task_id = submit_data.get("output", {}).get("task_id")
                if not dashscope_task_id:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message=f"DashScope 返回异常: {submit_data}",
                    )

                # Step 2: 轮询等待结果
                result_url = await self._poll_task(client, dashscope_task_id)

                if not result_url:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message="DashScope 处理超时或失败",
                    )

                # Step 3: 下载结果
                result_filename = await self._download_result(result_url, task_id)
                return TryOnResult(
                    task_id=task_id,
                    status="completed",
                    result_image=result_filename,
                )

        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"DashScope 错误 ({e.response.status_code}): {detail}",
            )
        except Exception as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"处理失败: {str(e)}",
            )

    async def _poll_task(self, client: httpx.AsyncClient, ds_task_id: str, max_retries: int = 30) -> Optional[str]:
        """轮询 DashScope 任务结果"""
        poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{ds_task_id}"
        for _ in range(max_retries):
            await asyncio.sleep(3)
            response = await client.get(
                poll_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("output", {}).get("task_status")

            if status == "SUCCEEDED":
                return data.get("output", {}).get("image_url")
            elif status == "FAILED":
                return None
        return None

    async def _download_result(self, url: str, task_id: str) -> str:
        """下载结果图片到本地"""
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results"
        )
        result_filename = f"result_{task_id}.png"
        result_path = os.path.join(results_dir, result_filename)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(result_path, "wb") as f:
                f.write(response.content)

        return result_filename
