# Hugging Face Spaces Dockerfile
# 免费部署 FastAPI 后端，无需信用卡
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建上传和结果目录
RUN mkdir -p uploads results

# HF Spaces 默认端口 7860
EXPOSE 7860

# 启动命令：从环境变量读取 PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}
