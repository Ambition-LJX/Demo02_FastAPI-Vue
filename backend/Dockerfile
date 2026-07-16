# ---------- 第一步：选择基础镜像 ----------
# 使用官方 Python 精简镜像（slim 体积小、够用）。
FROM python:3.12-slim

# ---------- 第二步：设置环境变量 ----------
# PYTHONDONTWRITEBYTECODE=1  不生成 .pyc 文件，保持镜像干净
# PYTHONUNBUFFERED=1         日志实时输出，不被缓冲，方便 docker logs 查看
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------- 第三步：设置工作目录 ----------
# 之后的命令都在容器内的 /app 目录下执行
WORKDIR /app

# ---------- 第四步：先装依赖（利用 Docker 缓存层）----------
# 单独先拷贝 requirements.txt 再安装，这样只要依赖没变，
# 后续改代码时这一层缓存就能复用，构建更快。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 第五步：拷贝项目代码 ----------
COPY ./app ./app

# ---------- 第六步：声明端口 ----------
# 仅作说明用途，真正对外暴露端口靠 docker run -p 或 compose 的 ports
EXPOSE 8000

# ---------- 第七步：启动命令 ----------
# 用 uvicorn 启动 FastAPI，监听 0.0.0.0 才能被容器外访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
