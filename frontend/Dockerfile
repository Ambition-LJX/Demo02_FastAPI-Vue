# ========== 阶段一：构建（build stage）==========
# 用 Node 镜像把 Vue 源码打包成静态文件（HTML/CSS/JS）。
# 这一阶段的镜像很大（含 node_modules），但我们只取它的产物，不进最终镜像。
FROM node:20-alpine AS build

WORKDIR /app

# 先拷贝依赖清单再安装，充分利用 Docker 缓存层：
# 只要 package.json 没变，改源码时就不用重新 npm install。
COPY package.json ./
RUN npm install

# 拷贝其余源码并打包，产物默认输出到 /app/dist
COPY . .
RUN npm run build

# ========== 阶段二：运行（runtime stage）==========
# 用体积极小的 Nginx 镜像只放静态产物，最终镜像干净又小。
FROM nginx:1.27-alpine

# 用我们自定义的 Nginx 配置替换默认配置：
# 负责托管前端静态文件 + 把 /api 反向代理到后端容器。
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从「构建阶段」把打包好的静态文件拷到 Nginx 的网站根目录
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx 默认监听 80 端口
EXPOSE 80

# 前台运行 Nginx（容器里必须前台运行，否则容器会立刻退出）
CMD ["nginx", "-g", "daemon off;"]
