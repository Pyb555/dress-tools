"""
OOTDiffusion Provider

通过 Colab 或其他 GPU 后端运行 OOTDiffusion 开源模型。
- Apache 2.0 开源协议
- 支持半身/全身虚拟试穿
- 需要 GPU 服务器（可免费使用 Google Colab）
"""
import os
from typing import Optional
import httpx
import uuid
from .tryon_engine import TryOnProvider, TryOnResult


class OOTDProvider(TryOnProvider):
    """OOTDiffusion 开源模型引擎"""

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.getenv("OOTD_API_URL", "http://localhost:7860")

    async def run(self, clothing_path: str, model_path: str, category: str = "upper_body") -> TryOnResult:
        task_id = uuid.uuid4().hex[:12]

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 通过 Gradio API 调用 OOTDiffusion
                # 参考 OOTDiffusion Gradio demo 的 API 格式
                with open(clothing_path, "rb") as cloth_file, open(model_path, "rb") as model_file:
                    response = await client.post(
                        f"{self.api_url}/api/predict",
                        files={
                            "cloth": cloth_file,
                            "model": model_file,
                        },
                        data={
                            "category": category,
                        },
                    )
                    response.raise_for_status()
                    result_data = response.json()

                # 下载结果
                result_url = result_data.get("data", [None])[0]
                if not result_url:
                    return TryOnResult(
                        task_id=task_id,
                        status="failed",
                        message="OOTDiffusion 返回结果为空",
                    )

                result_filename = f"result_{task_id}.png"
                results_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results"
                )
                result_path = os.path.join(results_dir, result_filename)

                img_response = await client.get(result_url)
                with open(result_path, "wb") as f:
                    f.write(img_response.content)

                return TryOnResult(
                    task_id=task_id,
                    status="completed",
                    result_image=result_filename,
                )

        except httpx.ConnectError:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message="无法连接 OOTDiffusion 服务。请确保 GPU 服务器已启动。",
            )
        except Exception as e:
            return TryOnResult(
                task_id=task_id,
                status="failed",
                message=f"OOTDiffusion 处理失败: {str(e)}",
            )
