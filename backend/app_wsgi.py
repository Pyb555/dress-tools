"""
Flask 版本 - PythonAnywhere 免费部署
"""
import os
import sys
import json
import logging
from datetime import datetime

# ==== 路径设置 ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ==== 加载环境变量 ====
# 优先从 .env 文件，失败则用系统环境变量
def _load_env():
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

_load_env()

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# 尝试加载 CORS（如果未安装则跳过）
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

app.logger.setLevel(logging.INFO)

# ==== 工具函数 ====
import uuid

def _gen_filename(original):
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "png"
    return f"{uuid.uuid4().hex}.{ext}"

def _validate_image(filepath):
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            img.verify()
        return os.path.getsize(filepath) / (1024*1024) <= 10
    except Exception:
        return False

def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_to_history(record):
    history = _load_history()
    history.insert(0, record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:50], f, ensure_ascii=False, indent=2)

# ==== 任务状态管理（DashScope 异步模式）====

def _load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_task(task):
    tasks = _load_tasks()
    # 去重
    tasks = [t for t in tasks if t.get("task_id") != task["task_id"]]
    tasks.insert(0, task)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks[:100], f, ensure_ascii=False, indent=2)

def _remove_task(task_id):
    tasks = [t for t in _load_tasks() if t.get("task_id") != task_id]
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# ==== 路由 ====

@app.route("/")
def root():
    return jsonify({"service": "dress-tools", "status": "running"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "dress-tools"})

@app.route("/api/images/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"detail": "请上传图片"}), 400
    file = request.files["file"]
    filename = _gen_filename(file.filename or "img.png")
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    if not _validate_image(filepath):
        os.remove(filepath)
        return jsonify({"detail": "无效图片或过大"}), 400
    return jsonify({
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": os.path.getsize(filepath),
    })

@app.route("/api/tryon/run", methods=["POST"])
def run_tryon():
    """提交试穿任务（异步，立即返回 task_id）"""
    data = request.get_json(force=True, silent=True) or {}
    clothing = data.get("clothing_image", "")
    model = data.get("model_image", "")
    category = data.get("category", "upper_body")

    cp = os.path.join(UPLOAD_DIR, clothing)
    mp = os.path.join(UPLOAD_DIR, model)
    if not os.path.exists(cp):
        return jsonify({"detail": "衣服图片不存在"}), 404
    if not os.path.exists(mp):
        return jsonify({"detail": "模特图片不存在"}), 404

    try:
        engine_type = os.getenv("TRYON_ENGINE", "mock")

        if engine_type == "dashscope":
            from app.services.dashscope_provider import DashScopeProvider
            engine = DashScopeProvider()
            result = engine.submit(cp, mp, category)

            if result.get("ok"):
                ds_task_id = result["ds_task_id"]
                task_id = ds_task_id[:12]

                # 保存任务映射
                _save_task({
                    "task_id": task_id,
                    "ds_task_id": ds_task_id,
                    "clothing_image": clothing,
                    "model_image": model,
                    "category": category,
                    "date": datetime.now().isoformat(),
                })

                return jsonify({
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务已提交，请轮询状态",
                })
            else:
                return jsonify({
                    "task_id": "",
                    "status": "failed",
                    "message": result.get("error", "提交失败"),
                })
        else:
            # Mock / 其他引擎：同步处理
            import asyncio
            from app.services.tryon_engine import get_tryon_engine
            engine = get_tryon_engine()
            result = asyncio.run(engine.run(cp, mp, category))
            return jsonify({
                "task_id": result.task_id,
                "status": result.status,
                "result_image": result.result_image,
                "message": result.message,
            })
    except Exception as e:
        app.logger.error(f"TryOn error: {e}")
        return jsonify({"detail": f"试穿失败: {str(e)}"}), 500


@app.route("/api/tryon/status/<task_id>")
def check_status(task_id):
    """查询试穿任务状态"""
    tasks = _load_tasks()
    task = next((t for t in tasks if t.get("task_id") == task_id), None)

    if not task:
        return jsonify({"status": "not_found", "message": "任务不存在"})

    engine_type = os.getenv("TRYON_ENGINE", "mock")

    if engine_type == "dashscope":
        from app.services.dashscope_provider import DashScopeProvider
        engine = DashScopeProvider()
        result = engine.poll(task["ds_task_id"])

        if result["status"] == "SUCCEEDED":
            # 保存到历史
            _save_to_history({
                "id": task_id,
                "date": task.get("date", datetime.now().isoformat()),
                "clothing_image": task["clothing_image"],
                "model_image": task["model_image"],
                "result_image": result["result_image"],
                "category": task.get("category", "upper_body"),
                "status": "completed",
            })
            # 清理任务记录
            _remove_task(task_id)

            return jsonify({
                "task_id": task_id,
                "status": "completed",
                "result_image": result["result_image"],
                "message": "试穿完成",
            })
        elif result["status"] == "FAILED":
            _remove_task(task_id)
            return jsonify({
                "task_id": task_id,
                "status": "failed",
                "message": result.get("error", "处理失败"),
            })
        else:
            return jsonify({
                "task_id": task_id,
                "status": "processing",
                "message": f"AI 处理中... ({result['status']})",
            })

    return jsonify({"status": "completed", "result_image": task.get("result_image")})

@app.route("/api/history/list")
def list_history():
    return jsonify({"total": len(_load_history()), "items": _load_history()[:20]})

@app.route("/api/history/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    history = [h for h in _load_history() if h.get("id") != record_id]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)
    return jsonify({"status": "ok"})

@app.route("/api/history/clear", methods=["DELETE"])
def clear_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})

@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/results/<filename>")
def serve_result(filename):
    return send_from_directory(RESULTS_DIR, filename)
