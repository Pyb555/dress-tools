"""
FASHN AI Virtual Try-On API Provider

Official API docs: https://docs.fashn.ai
- Base URL: https://api.fashn.ai
- Auth: Bearer token (fa-... format)
- Endpoint: POST /v1/run → poll GET /v1/run/{id}
- Models: tryon-v1.6 (stable, fast), tryon-max (quality)
"""
import os
import base64
import asyncio
from typing import Optional
import httpx
import uuid
from .tryon_engine import TryOnProvider, TryOnResult


class FashnProvider(TryOnProvider):
    """FASHN API 虚拟试穿引擎"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FASHN_API_KEY", "")
        self.base_url = "https://api.fashn.ai"

    async def run(self, clothing_path: str, model_path: str, category: str = "upper_body") -> TryOnResult:
        task_id = uuid.uuid4().hex[:12]

        if not self.api_key:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message="FASHN API Key 未配置。请设置环境变量 FASHN_API_KEY。",
            )

        try:
            # 将图片转为 base64
            clothing_b64 = self._image_to_base64(clothing_path)
            model_b64 = self._image_to_base64(model_path)

            # 映射 category 到 FASHN 格式
            category_map = {
                "upper_body": "tops",
                "lower_body": "bottoms",
                "dresses": "one-pieces",
            }
            fashn_category = category_map.get(category, "auto")

            async with httpx.AsyncClient(timeout=180.0) as client:
                # Step 1: 提交试穿任务
                submit_res = await client.post(
                    f"{self.base_url}/v1/run",
                    json={
                        "model_name": "tryon-v1.6",
                        "inputs": {
                            "product_image": f"data:image/png;base64,{clothing_b64}",
                            "model_image": f"data:image/png;base64,{model_b64}",
                            "category": fashn_category,
                            "mode": "balanced",
                            "num_samples": 1,
                            "output_format": "url",
                        },
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                submit_res.raise_for_status()
                submit_data = submit_res.json()
                prediction_id = submit_data.get("id")

                if not prediction_id:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message=f"FASHN API 返回异常: {submit_data}",
                    )

                # Step 2: 轮询等待结果
                result_url = await self._poll_prediction(client, prediction_id)

                if not result_url:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message="FASHN API 处理超时或失败",
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
                message=f"FASHN API 错误 ({e.response.status_code}): {detail}",
            )
        except httpx.HTTPError as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"网络请求失败: {str(e)}",
            )
        except Exception as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"处理失败: {str(e)}",
            )

    def _image_to_base64(self, file_path: str) -> str:
        """读取图片并转为 base64 字符串"""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def _poll_prediction(self, client: httpx.AsyncClient, prediction_id: str, max_retries: int = 40) -> Optional[str]:
        """轮询获取预测结果，返回结果图片 URL"""
        poll_url = f"{self.base_url}/v1/run/{prediction_id}"
        for attempt in range(max_retries):
            await asyncio.sleep(2)
            response = await client.get(
                poll_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")

            if status == "completed":
                output = data.get("output", [])
                if output and len(output) > 0:
                    return output[0]  # 返回第一张结果图
                return None
            elif status == "failed":
                return None

            # 还在处理中，继续等待
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
