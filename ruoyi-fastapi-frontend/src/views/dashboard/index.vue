<template>
  <div class="dashboard">
    <div class="info-section">
      <el-card class="welcome-card" shadow="never">
        <div class="welcome-inner">
          <img :src="userStore.avatar" class="user-avatar" />
          <div class="welcome-text">
            <div class="greeting">{{ greeting }}，{{ userStore.nickName }}</div>
            <div class="sub-info">{{ datetimeStr }}</div>
          </div>
        </div>
      </el-card>

      <div class="stat-group">
        <div class="stat-card" v-for="s in stats" :key="s.label">
          <div class="stat-icon" :style="{ background: s.color }">
            <el-icon :size="20"><component :is="s.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ s.value ?? '—' }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="nav-card" header="快捷功能">
      <div class="nav-grid">
        <router-link v-for="link in quickLinks" :key="link.to" :to="link.to" class="nav-item">
          <svg-icon :icon-class="link.icon" class="nav-icon" />
          <span>{{ link.label }}</span>
        </router-link>
      </div>
    </el-card>

    <el-row :gutter="16" class="desc-row">
      <el-col :xs="24" :sm="12">
        <el-card shadow="never" header="平台功能">
          <ul class="desc-list">
            <li>用户、角色与权限管理，灵活配置访问控制</li>
            <li>动态菜单，支持多级目录结构</li>
            <li>字典与参数管理，运行时配置无需重启</li>
            <li>操作日志与登录日志，完整审计追踪</li>
            <li>部门组织架构管理</li>
          </ul>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="never" header="系统接口">
          <ul class="desc-list">
            <li><router-link to="/tool/swagger" class="api-link">Swagger UI</router-link> — 在线接口调试与文档</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import useUserStore from '@/store/modules/user'
import { listUser } from '@/api/system/user'
import { listRole } from '@/api/system/role'
import { listDept } from '@/api/system/dept'
import { listType as listDictType } from '@/api/system/dict/type'

defineOptions({ name: 'Dashboard' })

const userStore = useUserStore()

// ── Greeting & clock ─────────────────────────────────────────────────────────

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const datetimeStr = ref('')
let clockTimer = null
function updateClock() {
  const now = new Date()
  const pad = n => String(n).padStart(2, '0')
  datetimeStr.value = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

// ── Quick links ───────────────────────────────────────────────────────────────

const quickLinks = [
  { to: '/tool/swagger',    icon: 'swagger',  label: '系统接口' },
  { to: '/system/user',     icon: 'peoples',  label: '用户管理' },
  { to: '/system/dept',     icon: 'tree',     label: '部门管理' },
  { to: '/system/dict',     icon: 'dict',     label: '字典管理' },
  { to: '/system/config',   icon: 'system',   label: '参数管理' },
  { to: '/monitor/operlog', icon: 'log',      label: '操作日志' },
]

// ── Stats cards ───────────────────────────────────────────────────────────────

const stats = ref([
  { label: '注册用户数', value: null, color: 'linear-gradient(135deg,#a855f7,#7c3aed)', icon: 'User' },
  { label: '角色总数',   value: null, color: 'linear-gradient(135deg,#ec4899,#db2777)', icon: 'UserFilled' },
  { label: '部门总数',   value: null, color: 'linear-gradient(135deg,#3b82f6,#2563eb)', icon: 'OfficeBuilding' },
  { label: '字典总数',   value: null, color: 'linear-gradient(135deg,#10b981,#059669)', icon: 'List' },
])

async function loadStats() {
  const [users, roles, depts, dicts] = await Promise.allSettled([
    listUser({ pageNum: 1, pageSize: 1 }),
    listRole({ pageNum: 1, pageSize: 1 }),
    listDept({}),
    listDictType({ pageNum: 1, pageSize: 1 }),
  ])
  if (users.status  === 'fulfilled') stats.value[0].value = users.value.total  ?? null
  if (roles.status  === 'fulfilled') stats.value[1].value = roles.value.total  ?? null
  if (depts.status  === 'fulfilled') stats.value[2].value = depts.value.data?.length ?? null
  if (dicts.status  === 'fulfilled') stats.value[3].value = dicts.value.total  ?? null
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadStats()
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 84px);
  padding: 16px;
  box-sizing: border-box;
  gap: 16px;
}

.info-section {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.welcome-card {
  flex: 0 0 320px;
  .welcome-inner { display: flex; align-items: center; gap: 16px; }
  .user-avatar { width: 56px; height: 56px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
  .greeting { font-size: 18px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 4px; }
  .sub-info { font-size: 13px; color: var(--el-text-color-secondary); }
}

.stat-group {
  flex: 1;
  min-width: 280px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-value { font-size: 22px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }

.nav-card {
  .nav-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
  }
  .nav-item {
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    padding: 12px 8px; border-radius: 8px; text-decoration: none;
    color: var(--el-text-color-regular); font-size: 13px;
    transition: background 0.2s, color 0.2s;
    border: 1px solid transparent;
    &:hover { background: var(--el-color-primary-light-9); color: var(--el-color-primary); border-color: var(--el-color-primary-light-7); }
    .nav-icon { font-size: 24px; }
  }
}

.desc-row {
  .desc-list {
    margin: 0;
    padding-left: 18px;
    font-size: 13px;
    line-height: 2;
    color: var(--el-text-color-regular);
  }
  .api-link {
    color: var(--el-color-primary);
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }
}

@media (max-width: 768px) {
  .welcome-card { flex: 1 1 100%; }
  .stat-group { min-width: 100%; }
  .nav-card .nav-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
