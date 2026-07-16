# FastAPI + Vue + Docker 保姆级部署教学

一个"物品管理"增删改查小项目：后端用 **FastAPI**，前端用 **Vue3**，重点演示**如何用 Docker 把「前端 + 后端」两个服务一起部署起来**。
即使你从没用过 Docker，跟着本文档一步步敲命令，也能把整套服务跑起来。

> 如果你还没看过单体后端的部署，建议先看隔壁 `Demo01_FastAPI`（只有一个后端服务）。本篇在它的基础上多了一个前端容器，并讲清楚**两个容器怎么互相通信**。

---

## 一、这个项目长啥样

```
Demo02_FastAPI+Vue/
├── backend/                    # 后端：FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口 + 所有接口（增删改查）
│   │   ├── database.py         # 数据库连接（默认 SQLite）
│   │   ├── models.py           # 数据库表结构
│   │   └── schemas.py          # 请求/响应的数据校验模型
│   ├── data/                   # SQLite 数据库文件（运行后自动生成）
│   ├── requirements.txt        # Python 依赖清单
│   ├── Dockerfile              # 【核心】后端怎么打包成镜像
│   └── .dockerignore
├── frontend/                   # 前端：Vue3 + Vite
│   ├── src/
│   │   ├── App.vue             # 主界面（增删改查 UI）
│   │   ├── api.js              # 封装后端接口调用
│   │   ├── main.js             # Vue 入口
│   │   └── style.css           # 样式
│   ├── index.html
│   ├── package.json            # 前端依赖清单
│   ├── vite.config.js          # 开发服务器 + 代理配置
│   ├── nginx.conf              # 【核心】Nginx 托管静态页 + 反代 /api
│   ├── Dockerfile              # 【核心】前端「打包 + Nginx」多阶段构建
│   └── .dockerignore
├── docker-compose.yml          # 【核心】一条命令启动前端 + 后端
└── README.md                   # 就是你正在看的这份文档
```

后端接口一览（部署后前端会自动调用它们）：

| 方法   | 路径              | 作用             |
| ------ | ----------------- | ---------------- |
| GET    | `/health`         | 健康检查         |
| POST   | `/api/items`      | 新增一个物品     |
| GET    | `/api/items`      | 查询物品列表     |
| GET    | `/api/items/{id}` | 查询单个物品     |
| PUT    | `/api/items/{id}` | 更新物品         |
| DELETE | `/api/items/{id}` | 删除物品         |

---

## 二、准备工作：安装 Docker

Docker 把"应用 + 运行环境"打包成**镜像(image)**，再运行成**容器(container)**。
你不用在电脑上装 Python、Node、Nginx，Docker 会把这些都封在容器里。

1. 到 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载 **Docker Desktop**（Windows / Mac 都有）。
2. 安装后启动它，等右下角小鲸鱼图标不再转圈（表示 Docker 引擎已就绪）。
3. 打开终端（Windows 用 PowerShell），验证安装成功：

```bash
docker --version
docker compose version
```

两条命令都能打印出版本号，就说明装好了。

---

## 三、先搞懂架构：两个容器是怎么配合的

这是本教学最关键的一节。单体项目只有一个容器，而这里有**两个容器**，它们的配合方式如下：

```
                         ┌─────────────────────────────────────────┐
                         │              你的电脑（宿主机）           │
   浏览器                 │                                          │
   http://localhost:8080 │   ┌──────────────┐      ┌──────────────┐ │
   ───────────────────────► │  frontend    │      │  backend     │ │
                         │   │  (Nginx:80)  │      │ (FastAPI:8000)│ │
                         │   │              │      │              │ │
                         │   │  静态页面 /   │      │  /api/items  │ │
                         │   │  /api 反代 ──────────►  增删改查     │ │
                         │   └──────────────┘      └──────────────┘ │
                         │        ▲   两个容器在同一个 Docker 网络里    │
                         │        │   前端用服务名 "backend" 找到后端   │
                         └─────────────────────────────────────────┘
```

关键点，一句话记住：

- **浏览器只和前端容器（Nginx，8080 端口）打交道**，它不知道后端的存在。
- 前端页面发出的 `/api/...` 请求，被 Nginx **反向代理**转发给后端容器。
- 前端能用 `backend` 这个名字找到后端，是因为 **docker-compose 把它们放进了同一个网络，Docker 内置 DNS 会把服务名解析成容器 IP**。
- 后端**不对外暴露端口**，只在内网被前端访问，更安全。

这样设计的好处：浏览器看到的所有请求都是同一个地址（`localhost:8080`），**没有跨域问题**，也不用把后端地址写死在前端代码里。

---

## 四、理解三个核心文件

### 4.1 后端 Dockerfile —— 和单体项目几乎一样

`backend/Dockerfile` 就是标准的 Python 应用打包，从上往下一行行执行：

```dockerfile
FROM python:3.12-slim              # 选一个自带 Python 的精简 Linux
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1             # 日志实时输出，方便看 docker logs
WORKDIR /app                       # 容器内工作目录
COPY requirements.txt .            # 先拷依赖清单（利用缓存层）
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app                   # 再拷代码
EXPOSE 8000
# --host 0.0.0.0 才能被容器外（其它容器）访问，写 127.0.0.1 会访问不到
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 前端 Dockerfile —— 多阶段构建（本篇重点）

前端和后端最大的不同：**Vue 代码不能直接运行，要先"打包"成一堆静态文件（HTML/CSS/JS），再交给 Nginx 托管**。
如果把庞大的 Node 环境也塞进最终镜像会又大又慢，所以用**多阶段构建**：第一阶段用 Node 打包，第二阶段只把打包产物放进小巧的 Nginx 镜像。

```dockerfile
# ===== 阶段一：用 Node 打包 =====
FROM node:20-alpine AS build       # 起个别名叫 build
WORKDIR /app
COPY package.json ./               # 先拷依赖清单（利用缓存）
RUN npm install
COPY . .
RUN npm run build                  # 产物输出到 /app/dist

# ===== 阶段二：只用 Nginx 跑静态文件 =====
FROM nginx:1.27-alpine             # 换一个极小的 Nginx 镜像
COPY nginx.conf /etc/nginx/conf.d/default.conf          # 自定义配置
COPY --from=build /app/dist /usr/share/nginx/html       # 只从阶段一拷产物
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] # 前台运行，否则容器会立刻退出
```

> 记住这句话：**`COPY --from=build` 就是"只要打包结果，不要打包用的一大堆工具"**。最终镜像里没有 Node、没有源码，只有几百 KB 的静态文件 + Nginx。

配套的 `frontend/nginx.conf` 做两件事：

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA 兜底：刷新任意路径都返回首页，避免 404
    }

    location /api/ {
        proxy_pass http://backend:8000/api/; # 把 /api 转发给后端容器（backend 是服务名）
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4.3 docker-compose.yml —— 一键编排两个容器

有了两个 Dockerfile，如果手动部署你得 `docker build` 两次、`docker network create` 建网络、`docker run` 两次还要挂参数。compose 把这些都写进一个文件，一条命令搞定：

```yaml
services:
  backend:                         # 服务名就是容器在网络里的"域名"
    build: ./backend               # 用 ./backend/Dockerfile 构建
    container_name: demo02-backend
    volumes:
      - ./backend/data:/app/data   # 数据卷：数据库文件存到宿主机，容器重建不丢
    environment:
      - DATA_DIR=/app/data
    restart: unless-stopped
    healthcheck:                   # 定期探活
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
    # 故意不写 ports：后端不对外暴露，只给前端内部访问，更安全

  frontend:
    build: ./frontend
    container_name: demo02-frontend
    ports:
      - "8080:80"                  # 宿主机 8080 -> 容器 80（Nginx）
    depends_on:
      - backend                    # 等后端先启动
    restart: unless-stopped
```

三个最关键的概念：

- **服务名即域名**：`backend`、`frontend` 这两个名字，compose 会自动建一个网络让它们互相能用名字访问。前端 nginx.conf 里写的 `http://backend:8000` 就是靠这个生效的。
- **端口映射 `ports`**：只有 `frontend` 映射了 `8080:80`，所以你只能从 `8080` 进来。后端没映射，从宿主机直接访问不到它（这是故意的）。
- **数据卷 `volumes`**：容器"用完即弃"，删掉数据就没了。把 `./backend/data` 挂出来，SQLite 数据库存在你电脑上，容器删了重建数据还在。

---

## 五、开始部署（推荐方式：docker compose）

在项目根目录（有 `docker-compose.yml` 的 `Demo02_FastAPI+Vue/` 这一层）打开终端。

### 步骤 1：构建并启动

```bash
docker compose up -d --build
```

- `--build` 先按两个 Dockerfile 分别构建镜像
- `-d` 后台运行（detached），不占用当前终端

第一次运行要下载 Python、Node、Nginx 基础镜像并装依赖，会比较慢，耐心等待。

### 步骤 2：确认两个容器都在跑

```bash
docker compose ps
```

能看到 `demo02-backend` 和 `demo02-frontend` 状态都是 `Up`（后端稍等会变成 `healthy`）就 OK。

### 步骤 3：访问服务

浏览器打开：**<http://localhost:8080>**

你会看到物品管理界面，可以直接增删改查。数据是真的存进了后端的 SQLite 数据库。

### 步骤 4：查看日志（排查问题必备）

```bash
docker compose logs -f              # 看全部
docker compose logs -f backend      # 只看后端
docker compose logs -f frontend     # 只看前端
```

`-f` 是持续跟踪，按 `Ctrl + C` 退出查看（不会停掉容器）。

### 步骤 5：停止 / 删除

```bash
docker compose stop      # 只停止，不删除
docker compose down      # 停止并删除容器（宿主机 ./backend/data 里的数据保留）
```

---

## 六、验证一下"前后端真的通了"

1. 在页面上**新增**一个物品，列表立刻出现它 → 说明前端成功调到了后端的 `POST /api/items`。
2. 刷新浏览器，数据还在 → 说明数据存进了后端数据库（不是前端内存）。
3. `docker compose down` 再 `docker compose up -d`，数据依然在 → 说明数据卷挂载生效了。

想直接调后端接口验证，可以临时打开后端端口：把 `docker-compose.yml` 里 `backend` 服务的 `ports` 注释去掉（改成映射 `8000:8000`），重启后访问 <http://localhost:8000/docs> 用交互式文档测试。

---

## 七、本地开发模式（不打包，改代码实时生效）

部署是"打包上线"，开发时你会想改代码立即看到效果，这时不走 Docker：

**开一个终端跑后端：**

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload       # --reload 改代码自动重启
```

**再开一个终端跑前端：**

```bash
cd frontend
npm install
npm run dev                          # 打开提示的 http://localhost:5173
```

开发模式下，前端跑在 `5173`，`vite.config.js` 里配了代理把 `/api` 转发到 `localhost:8000` 的后端，所以同样没有跨域问题。

---

## 八、常见问题 FAQ

**Q1：8080 端口被占用怎么办？**
改 `docker-compose.yml` 里 `frontend` 的 `ports`，比如 `"9000:80"`，然后访问 `http://localhost:9000`。冒号左边是你电脑的端口（随便改），右边是容器内 Nginx 的 80（保持不变）。

**Q2：页面打开了，但数据加载失败 / 新增报错？**
多半是前端没能连到后端。依次排查：
1. `docker compose ps` 看 `demo02-backend` 是不是 `Up`。
2. `docker compose logs backend` 看后端有没有报错。
3. 确认 `nginx.conf` 里 `proxy_pass` 写的是 `http://backend:8000/api/`，`backend` 必须和 compose 里的服务名一致。

**Q3：改了代码怎么生效？**
重新构建：`docker compose up -d --build`。只改了前端就等前端重新打包，改了后端就重装依赖并重启。

**Q4：数据存在哪？会丢吗？**
存在 `backend/data/app.db`。因为做了数据卷挂载，容器删了数据也在。想清空，把 `backend/data` 删掉重启即可。

**Q5：构建很慢 / 拉镜像失败（`failed to fetch oauth token` 或 `dial tcp ... timeout`）？**
国内访问 Docker Hub 网络不通导致，跟代码无关。给 Docker 配国内镜像加速器：

1. Docker Desktop → 设置(齿轮) → `Docker Engine`。
2. 在 JSON 里加上 `registry-mirrors`（其它别动）：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

3. `Apply & restart`，等重启后再 `docker compose up -d --build`。

> 镜像源会失效/变动，拉不动就搜"Docker 镜像加速器 最新可用"换一个。也可先手动 `docker pull node:20-alpine` 等把基础镜像拉下来再构建。

**Q6：`npm install` 阶段很慢？**
同样是网络问题。可以在 `frontend/Dockerfile` 的 `RUN npm install` 前加一行设置淘宝镜像：
`RUN npm config set registry https://registry.npmmirror.com`。

**Q7：为什么后端不映射端口也能用？**
因为访问后端的是**前端容器**，不是你的浏览器。两个容器在同一 Docker 网络里，用服务名内部通信，根本不需要经过宿主机端口。只有需要从你电脑直接访问后端时才需要映射。

---

## 九、部署命令速查表

| 目的              | 命令                                    |
| ----------------- | --------------------------------------- |
| 构建并后台启动    | `docker compose up -d --build`          |
| 查看状态          | `docker compose ps`                     |
| 查看全部日志      | `docker compose logs -f`                |
| 查看后端日志      | `docker compose logs -f backend`        |
| 停止              | `docker compose stop`                   |
| 停止并删除        | `docker compose down`                   |
| 重新构建生效      | `docker compose up -d --build`          |
| 进入后端容器      | `docker compose exec backend bash`      |
| 进入前端容器      | `docker compose exec frontend sh`       |

到这里，你已经完整走完了"写前后端代码 → 各自打包镜像 → 用 compose 编排两个容器 → 让它们在内网通信 → 浏览器访问"的全流程。这正是真实项目里前后端分离部署的标准姿势，祝玩得开心！
