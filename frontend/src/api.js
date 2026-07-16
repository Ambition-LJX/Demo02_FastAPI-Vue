import axios from 'axios'

// 所有请求都打到 /api 前缀：
// - 开发模式：Vite 把 /api 代理到 http://localhost:8000
// - 生产模式：Nginx 把 /api 反向代理到后端容器
// 这样前端代码不用写死后端地址，换环境也不用改代码。
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export const itemApi = {
  // 查询列表
  list() {
    return request.get('/items')
  },
  // 新增
  create(data) {
    return request.post('/items', data)
  },
  // 更新（部分字段）
  update(id, data) {
    return request.put(`/items/${id}`, data)
  },
  // 删除
  remove(id) {
    return request.delete(`/items/${id}`)
  },
}
