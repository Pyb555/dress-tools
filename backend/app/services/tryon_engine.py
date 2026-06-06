"""
AI 虚拟试穿引擎 - 抽象接口

通过 TryOnProvider 抽象基类统一不同 AI 引擎的调用方式：
- FASHN API (商业服务)
- OOTDiffusion (开源模型)
- 未来: IDM-VTON, CatVTON 等
"""
import uuid
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TryOnResult:
    task_id: str
    status: str       # pending | processing | completed | failed
    result_image: Optional[str] = None
    message: Optional[str] = None


class TryOnProvider(ABC):
    """AI 试穿引擎抽象基类"""

    @abstractmethod
    async def run(
        self,
        clothing_path: str,
        model_path: str,
        category: str = "upper_body",
    ) -> TryOnResult:
        """执行虚拟试穿

        Args:
            clothing_path: 衣服图片本地路径
            model_path: 模特/人物图片本地路径
            category: 类别 (upper_body | lower_body | dresses)

        Returns:
            TryOnResult 包含任务状态和结果图片路径
        """
        ...


class MockProvider(TryOnProvider):
    """
    模拟引擎 - 用于开发调试，无需调用任何外部 API。
    直接返回模特原图作为"结果"，方便前端开发。
    """

    async def run(self, clothing_path: str, model_path: str, category: str = "upper_body") -> TryOnResult:
        import shutil
        import os

        task_id = uuid.uuid4().hex[:12]
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "results")
        result_filename = f"result_{task_id}.png"
        result_path = os.path.join(results_dir, result_filename)

        # 模拟延迟
        import asyncio
        await asyncio.sleep(2)

        # 简单复制模特图作为模拟结果
        shutil.copy(model_path, result_path)

        return TryOnResult(
            task_id=task_id,
            status="completed",
            result_image=result_filename,
            message="模拟试穿成功（Mock）",
        )


# ============================================
# 工厂方法：根据配置选择 AI 引擎
# ============================================

_engine: Optional[TryOnProvider] = None
_engine_type: Optional[str] = None


def get_tryon_engine(engine_type: Optional[str] = None) -> TryOnProvider:
    """获取 AI 试穿引擎实例（单例模式）

    Args:
        engine_type: "mock" | "fashn" | "ootd" | "dashscope"，为空时读取环境变量 TRYON_ENGINE

    Returns:
        TryOnProvider 实例
    """
    global _engine, _engine_type
    import os

    if engine_type is None:
        engine_type = os.getenv("TRYON_ENGINE", "mock")

    # 缓存：同类型引擎复用实例
    if _engine is not None and _engine_type == engine_type:
        return _engine

    if engine_type == "fashn":
        from .fashn_provider import FashnProvider
        _engine = FashnProvider()
    elif engine_type == "ootd":
        from .ootd_provider import OOTDProvider
        _engine = OOTDProvider()
    elif engine_type == "dashscope":
        from .dashscope_provider import DashScopeProvider
        _engine = DashScopeProvider()
    else:
        _engine = MockProvider()

    _engine_type = engine_type
    return _engine
