FROM python:3.12-slim

WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制项目代码
COPY . .

# 日志目录
RUN mkdir -p logs

EXPOSE 8501

# 默认 dev 环境，生产部署时用 --env APP_ENV=prod
ENV APP_ENV=dev

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
