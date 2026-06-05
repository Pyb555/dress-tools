"""
Flask 版本 - 用于 PythonAnywhere 免费部署
与 FastAPI 版本共享相同的 services/ 层
"""
import os
import json
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 加载 .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# 确保路径可用
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.image_utils import ensure_dirs, generate_filename, validate_image, get_image_info
from app.services.tryon_engine import get_tryon_engine

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
ensure_dirs([UPLOAD_DIR, RESULTS_DIR])

app = Flask(__name__)
CORS(app)

# ============ 健康检查 ============
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "dress-tools"})


@app.route("/")
def root():
    return jsonify({"message": "Dress Tools API", "docs": "https://github.com/Pyb555/dress-tools"})


# ============ 图片上传 ============
@app.route("/api/images/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"detail": "请上传图片文件"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"detail": "文件名为空"}), 400

    filename = generate_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    if not validate_image(filepath):
        os.remove(filepath)
        return jsonify({"detail": "无效图片或文件过大（最大10MB）"}), 400

    info = get_image_info(filepath)
    return jsonify({
        "filename": filename,
        "url": f"/uploads/{filename}",
        "width": info["width"],
        "height": info["height"],
        "size": os.path.getsize(filepath),
    })


# ============ 虚拟试穿 ============
@app.route("/api/tryon/run", methods=["POST"])
def run_tryon():
    data = request.get_json()
    if not data:
        return jsonify({"detail": "请求体为空"}), 400

    clothing_image = data.get("clothing_image")
    model_image = data.get("model_image")
    category = data.get("category", "upper_body")

    clothing_path = os.path.join(UPLOAD_DIR, clothing_image)
    model_path = os.path.join(UPLOAD_DIR, model_image)

    if not os.path.exists(clothing_path):
        return jsonify({"detail": "衣服图片不存在"}), 404
    if not os.path.exists(model_path):
        return jsonify({"detail": "模特图片不存在"}), 404

    try:
        import asyncio
        engine = get_tryon_engine()
        result = asyncio.run(engine.run(clothing_path, model_path, category))

        # 保存到历史
        if result.status == "completed":
            _save_to_history({
                "id": result.task_id,
                "date": datetime.now().isoformat(),
                "clothing_image": clothing_image,
                "model_image": model_image,
                "result_image": result.result_image,
                "category": category,
                "status": "completed",
            })

        return jsonify({
            "task_id": result.task_id,
            "status": result.status,
            "result_image": result.result_image,
            "message": result.message,
        })
    except Exception as e:
        return jsonify({"detail": f"试穿失败: {str(e)}"}), 500


# ============ 历史记录 ============
def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_to_history(record):
    history = _load_history()
    history.insert(0, record)
    history = history[:50]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@app.route("/api/history/list")
def list_history():
    history = _load_history()
    return jsonify({"total": len(history), "items": history[:20]})


@app.route("/api/history/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    history = _load_history()
    history = [h for h in history if h.get("id") != record_id]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"})


@app.route("/api/history/clear", methods=["DELETE"])
def clear_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"status": "ok"})


# ============ 静态文件 ============
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/results/<filename>")
def result_file(filename):
    return send_from_directory(RESULTS_DIR, filename)
