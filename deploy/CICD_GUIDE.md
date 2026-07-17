# CI/CD 自动化部署 - 通俗易懂版

## 这套流程是干嘛的？

**一句话：代码 push 到 GitHub → 自动构建 Docker 镜像 → 服务器自动更新**

```
你改代码 → git push → GitHub 自动构建镜像 → 服务器自动拉取 → 网站自动更新
     ↑              ↑                    ↑                    ↑
   你手动        GitHub Actions        Watchtower           无感知
```

---

## 完整流程（7步走）

### 第一步：把代码上传到 GitHub（如果没有的话）

1. 去 [github.com](https://github.com) 创建新仓库，名字叫 `demo02`
2. 本地关联并推送代码：

```bash
cd Demo02_FastAPI+Vue
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/你的用户名/demo02.git
git push -u origin main
```

### 第二步：修改配置文件（3秒钟）

修改这两个文件里的 `YOUR_USERNAME`：


| 文件                               | 改什么                                           |
| -------------------------------- | --------------------------------------------- |
| `deploy/docker-compose.prod.yml` | `ghcr.io/YOUR_USERNAME/...` → 改成你的 GitHub 用户名 |
| `deploy/scripts/deploy.sh`       | `USERNAME="YOUR_USERNAME"` → 改成你的 GitHub 用户名  |




### 第三步：生成 GitHub 访问令牌

1. GitHub 右上角头像 → **Settings**
2. 左边菜单最下面 → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token (classic)**
5. 勾选这两个权限：
  - ✅ `packages: write` （推送镜像用）
  - ✅ `repo: status` （可选，提交状态用）
6. 点击 **Generate token**，**立刻复制保存**（关掉页面就看不见了）



### 第四步：在服务器上安装 Docker

```bash
# Ubuntu/Debian 一键安装
curl -fsSL https://get.docker.com | sh

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证
docker --version
```



### 第五步：在服务器上创建部署目录

```bash
# 创建项目目录
sudo mkdir -p /opt/demo02
cd /opt/demo02

# 复制 docker-compose.prod.yml 到这里
# 方法1：如果服务器能访问 GitHub
git clone https://github.com/你的用户名/demo02.git .
rm -rf .git  # 删掉 .git（避免污染主仓库）

# 方法2：用 scp 从本地上传
# scp deploy/docker-compose.prod.yml root@你的服务器:/opt/demo02/
```



### 第六步：设置 GitHub Token（让服务器能拉取镜像）

在**服务器终端**执行：

```bash
# 登录 GitHub 镜像仓库
docker login ghcr.io -u 你的GitHub用户名
# 然后粘贴刚才生成的 token 作为密码

# 或者一行命令
echo "你的token" | docker login ghcr.io -u 你的GitHub用户名 --password-stdin
```



### 第七步：首次部署

```bash
cd /opt/demo02

# 拉取镜像
docker compose -f docker-compose.prod.yml pull

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看状态
docker compose -f docker-compose.prod.yml ps
```

看到三个容器都是 `Up` 状态就成功了！

---



## 验证整个流程（测试自动化）

现在来测试"改代码 → 自动部署"：

1. **本地改一点代码**（比如在 README 里加一行字）
2. **提交并推送**：

```bash
git add .
git commit -m "测试 CI/CD"
git push
```

1. **去 GitHub 看构建过程**：
  - 打开你的仓库 → 点击 **Actions** 标签
  - 看到一条 workflow 正在运行（有个绿转蓝的圈圈在转）
  - 等 2-3 分钟，变成绿色勾勾就成功了
2. **去服务器看日志**：

```bash
# 等待 Watchtower 检测到新镜像（最多5分钟）
# 或者手动触发
docker compose -f /opt/demo02/docker-compose.prod.yml restart

# 看日志
docker compose -f /opt/demo02/docker-compose.prod.yml logs -f
```

1. **打开网站验证**：
  - 浏览器访问 `http://你的服务器IP`
  - 看到改动的效果就说明成功了！

---



## 常用命令



### 服务器上

```bash
# 查看所有容器
docker compose -f /opt/demo02/docker-compose.prod.yml ps

# 查看日志
docker compose -f /opt/demo02/docker-compose.prod.yml logs -f

# 只看某个服务
docker compose -f /opt/demo02/docker-compose.prod.yml logs -f backend

# 重启所有服务
docker compose -f /opt/demo02/docker-compose.prod.yml restart

# 停止所有服务
docker compose -f /opt/demo02/docker-compose.prod.yml down

# 强制拉取最新镜像并重启（跳过 Watchtower）
docker compose -f /opt/demo02/docker-compose.prod.yml pull
docker compose -f /opt/demo02/docker-compose.prod.yml up -d
```



### 本地查看 GitHub Actions

```
https://github.com/你的用户名/demo02/actions
```

---



## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          GitHub 仓库                             │
│   你 push 代码 ────────────────────────────────────────────────►│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions（云端）                        │
│                                                                 │
│   1. 拉取代码                                                   │
│   2. 构建后端镜像 ──► 推送到 ghcr.io/backend:latest             │
│   3. 构建前端镜像 ──► 推送到 ghcr.io/frontend:latest            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Watchtower 每5分钟轮询
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       你的服务器                                  │
│                                                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │   backend   │  │  frontend   │  │ watchtower  │            │
│   │   容器       │  │   容器       │  │   容器       │            │
│   └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                ▲                 │
│                         检测到新镜像 ────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                        浏览器访问网站
```

---



## 故障排查



### 1. GitHub Actions 构建失败

- 检查 Actions 日志，看哪一步报错
- 常见问题：Dockerfile 路径不对、依赖安装失败



### 2. 服务器拉取镜像失败

```bash
# 在服务器上测试登录
docker login ghcr.io
# 如果失败，说明 token 过期了，重新生成并设置
```



### 3. Watchtower 没更新

```bash
# 检查 Watchtower 日志
docker logs watchtower

# 确认镜像确实变了
docker images | grep demo02

# 手动触发一次
docker compose -f /opt/demo02/docker-compose.prod.yml pull
docker compose -f /opt/demo02/docker-compose.prod.yml up -d
```



### 4. 网站打不开

```bash
# 检查容器状态
docker compose -f /opt/demo02/docker-compose.prod.yml ps

# 看日志
docker compose -f /opt/demo02/docker-compose.prod.yml logs
```

---



## 原理总结（可以跳过）


| 组件                          | 作用                        |
| --------------------------- | ------------------------- |
| **GitHub Actions**          | push 代码后自动在云端构建 Docker 镜像 |
| **ghcr.io**                 | GitHub 的免费镜像仓库，存构建好的镜像    |
| **Watchtower**              | 服务器上的"巡逻兵"，定期检查新镜像并自动更新   |
| **docker-compose.prod.yml** | 生产环境编排文件，从镜像启动容器，不做本地构建   |


---



## 费用

- GitHub Actions：免费（每月 2000 分钟）
- ghcr.io 镜像仓库：免费（无限制）
- 服务器：自备

全程不用花一分钱！