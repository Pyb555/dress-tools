"""
FASHN AI Virtual Try-On API Provider

FASHN (via Pixazo) — 商业虚拟试穿 API
- 免费试用额度
- 5-19 秒推理时间
- 支持平铺衣服图到模特上身
- Native resolution: 864 × 1296

API 文档: https://www.pixazo.ai/
"""
import os
from typing import Optional
import httpx
import uuid
from .tryon_engine import TryOnProvider, TryOnResult


class FashnProvider(TryOnProvider):
    """FASHN API 虚拟试穿引擎"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FASHN_API_KEY", "")
        self.base_url = "https://api.fashn.ai/v1"

    async def run(self, clothing_path: str, model_path: str, category: str = "upper_body") -> TryOnResult:
        task_id = uuid.uuid4().hex[:12]

        if not self.api_key:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message="FASHN API Key 未配置。请设置环境变量 FASHN_API_KEY。",
            )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Step 1: 上传图片
                clothing_url = await self._upload_image(client, clothing_path)
                model_url = await self._upload_image(client, model_path)

                # Step 2: 创建试穿任务
                task_response = await client.post(
                    f"{self.base_url}/tryon",
                    json={
                        "model_image_url": model_url,
                        "garment_image_url": clothing_url,
                        "category": category,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                task_response.raise_for_status()
                task_data = task_response.json()

                # Step 3: 等待结果 & 下载
                result_url = await self._poll_result(
                    client, task_data.get("task_id", "")
                )

                if not result_url:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message="FASHN API 处理超时",
                    )

                # Step 4: 下载结果图片到本地
                result_filename = await self._download_result(result_url, task_id)
                return TryOnResult(
                    task_id=task_id,
                    status="completed",
                    result_image=result_filename,
                )

        except httpx.HTTPError as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"FASHN API 请求失败: {str(e)}",
            )
        except Exception as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"处理失败: {str(e)}",
            )

    async def _upload_image(self, client: httpx.AsyncClient, file_path: str) -> str:
        """上传图片到 FASHN"""
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            response = await client.post(
                f"{self.base_url}/upload",
                files={"file": (filename, f)},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()["url"]

    async def _poll_result(self, client: httpx.AsyncClient, task_id: str, max_retries: int = 20) -> Optional[str]:
        """轮询获取处理结果"""
        import asyncio
        for _ in range(max_retries):
            response = await client.get(
                f"{self.base_url}/task/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "completed":
                return data.get("result_url")
            elif data.get("status") == "failed":
                return None
            await asyncio.sleep(2)
        return None

    async def _download_result(self, url: str, task_id: str) -> str:
        """下载结果图片到本地"""
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
        result_filename = f"result_{task_id}.png"
        result_path = os.path.join(results_dir, result_filename)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(result_path, "wb") as f:
                f.write(response.content)

        return result_filename
