<script setup>
import { ref, reactive, onMounted } from 'vue'
import { itemApi } from './api'

const items = ref([])
const error = ref('')
const editingId = ref(null)

// 表单初始值
const emptyForm = () => ({
  name: '',
  description: '',
  price: 0,
  in_stock: true,
})

const form = reactive(emptyForm())

// 加载列表
async function loadItems() {
  error.value = ''
  try {
    const res = await itemApi.list()
    items.value = res.data
  } catch (e) {
    error.value = '加载列表失败：' + (e.response?.data?.detail || e.message)
  }
}

// 重置表单，退出编辑状态
function resetForm() {
  Object.assign(form, emptyForm())
  editingId.value = null
}

// 提交表单：根据 editingId 判断是新增还是更新
async function submitForm() {
  error.value = ''
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || null,
    price: Number(form.price),
    in_stock: form.in_stock,
  }
  if (!payload.name) {
    error.value = '物品名称不能为空'
    return
  }
  try {
    if (editingId.value === null) {
      await itemApi.create(payload)
    } else {
      await itemApi.update(editingId.value, payload)
    }
    resetForm()
    await loadItems()
  } catch (e) {
    error.value = '保存失败：' + (e.response?.data?.detail || e.message)
  }
}

// 点击编辑：把该行数据填回表单
function startEdit(item) {
  editingId.value = item.id
  form.name = item.name
  form.description = item.description || ''
  form.price = item.price
  form.in_stock = item.in_stock
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 删除
async function removeItem(id) {
  if (!confirm('确定删除这个物品吗？')) return
  error.value = ''
  try {
    await itemApi.remove(id)
    if (editingId.value === id) resetForm()
    await loadItems()
  } catch (e) {
    error.value = '删除失败：' + (e.response?.data?.detail || e.message)
  }
}

onMounted(loadItems)
</script>

<template>
  <div class="container">
    <h1>物品管理</h1>
    <p class="subtitle">FastAPI + Vue3 + Docker 部署演示 · 简单增删改查</p>

    <div v-if="error" class="error">{{ error }}</div>

    <!-- 新增 / 编辑表单 -->
    <div class="card">
      <div class="form-grid">
        <div>
          <label>物品名称</label>
          <input type="text" v-model="form.name" placeholder="例如：机械键盘" />
        </div>
        <div>
          <label>价格</label>
          <input type="number" v-model="form.price" min="0" step="0.01" />
        </div>
        <div class="full">
          <label>描述</label>
          <input type="text" v-model="form.description" placeholder="选填" />
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="in_stock" v-model="form.in_stock" />
          <label for="in_stock" style="margin: 0">有库存</label>
        </div>
      </div>
      <div class="actions">
        <button class="btn-primary" @click="submitForm">
          {{ editingId === null ? '新增物品' : '保存修改' }}
        </button>
        <button v-if="editingId !== null" class="btn-ghost" @click="resetForm">
          取消编辑
        </button>
      </div>
    </div>

    <!-- 列表 -->
    <div class="card">
      <table v-if="items.length">
        <thead>
          <tr>
            <th style="width: 48px">ID</th>
            <th>名称</th>
            <th>描述</th>
            <th style="width: 90px">价格</th>
            <th style="width: 80px">库存</th>
            <th style="width: 130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.description || '—' }}</td>
            <td>¥{{ item.price }}</td>
            <td>
              <span :class="['tag', item.in_stock ? 'tag-in' : 'tag-out']">
                {{ item.in_stock ? '有货' : '缺货' }}
              </span>
            </td>
            <td>
              <div class="row-actions">
                <button class="btn-edit" @click="startEdit(item)">编辑</button>
                <button class="btn-danger" @click="removeItem(item.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">还没有数据，先在上面添加一个物品吧</div>
    </div>
  </div>
</template>
