<template>
  <div class="dashboard">
    <!-- Physics animation hero -->
    <div class="hero" ref="heroRef">
      <div class="text-stage" ref="stageRef"></div>
      <transition name="fade">
        <div v-if="!hintHidden" class="hint">
          拖拽末尾字符 · 按 <kbd>F</kbd> 键或
          <span class="hint-btn" @click="triggerRelease">点击释放</span>
        </div>
      </transition>
    </div>

    <!-- Info section -->
    <div class="info-section">
      <!-- Welcome card -->
      <el-card class="welcome-card" shadow="never">
        <div class="welcome-inner">
          <img :src="userStore.avatar" class="user-avatar" />
          <div class="welcome-text">
            <div class="greeting">{{ greeting }}，{{ userStore.nickName }}</div>
            <div class="sub-info">
              <span>{{ datetimeStr }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Quick nav -->
      <el-card class="nav-card" shadow="never" header="快捷导航">
        <div class="nav-grid">
          <router-link
            v-for="link in quickLinks"
            :key="link.to"
            :to="link.to"
            class="nav-item"
          >
            <svg-icon :icon-class="link.icon" class="nav-icon" />
            <span>{{ link.label }}</span>
          </router-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import useUserStore from '@/store/modules/user'

defineOptions({ name: 'Dashboard' })

const userStore = useUserStore()
const heroRef = ref(null)
const stageRef = ref(null)
const hintHidden = ref(false)

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
  datetimeStr.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

// ── Quick links ───────────────────────────────────────────────────────────────

const quickLinks = [
  { to: '/system/user',   icon: 'peoples',  label: '用户管理' },
  { to: '/system/role',   icon: 'role',     label: '角色管理' },
  { to: '/system/menu',   icon: 'tree-table', label: '菜单管理' },
  { to: '/system/dept',   icon: 'tree',     label: '部门管理' },
  { to: '/system/dict',   icon: 'dict',     label: '字典管理' },
  { to: '/user/profile',  icon: 'user',     label: '个人中心' },
]

// ── Physics simulation ────────────────────────────────────────────────────────

const CONSTRAINT_DIST = 1.25
const UNLOCK_THRESHOLD = 1
const ITERATIONS = 12
const DAMPING = 0.97
const GRAVITY = 0.18
const BOUNCE = 0.4
const RADIUS = 9
const FIXED_DT = 1 / 120
const MAX_STEPS = 4

let FONT = 'bold 56px system-ui, sans-serif'
let LINE_HEIGHT = 68

let letters = []
let restLengths = []
let els = []
let gravityOn = false
let unraveling = false
let unravelIdx = -1
let rafId = null
let lastTime = -1
let accumulator = 0
const drags = new Map()

function isDragged(idx) {
  for (const d of drags.values()) if (d.idx === idx) return true
  return false
}

function pickFont(width) {
  if (width < 400) return 'bold 28px system-ui, sans-serif'
  if (width < 700) return 'bold 40px system-ui, sans-serif'
  return 'bold 56px system-ui, sans-serif'
}

function initPhysics() {
  const container = stageRef.value
  if (!container) return

  container.innerHTML = ''
  els = []
  letters = []
  drags.clear()
  gravityOn = false
  unraveling = false
  unravelIdx = -1
  hintHidden.value = false

  FONT = pickFont(container.clientWidth)
  LINE_HEIGHT = Math.round(parseInt(FONT) * 1.25)

  const title = import.meta.env.VITE_APP_TITLE || '管理系统'
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = FONT

  const chars = [...title]
  const widths = chars.map(ch => ctx.measureText(ch).width)
  const totalW = widths.reduce((a, b) => a + b, 0)
  const startX = Math.max(0, (container.clientWidth - totalW) / 2)
  const startY = Math.max(0, (container.clientHeight - LINE_HEIGHT) / 2)

  let x = startX
  letters = chars.map((ch, i) => {
    const w = widths[i]
    const l = { ch, w, x, y: startY, ox: x, oy: startY, px: x, py: startY, locked: true }
    x += w
    return l
  })

  restLengths = []
  for (let i = 0; i < letters.length - 1; i++) {
    const a = letters[i], b = letters[i + 1]
    const dist = Math.hypot(
      (b.ox + b.w / 2) - (a.ox + a.w / 2),
      (b.oy + LINE_HEIGHT / 2) - (a.oy + LINE_HEIGHT / 2)
    )
    restLengths.push(dist * CONSTRAINT_DIST)
  }

  for (const l of letters) {
    const span = document.createElement('span')
    span.className = 'phys-letter'
    span.textContent = l.ch
    span.style.cssText = `position:absolute;top:0;left:0;font:${FONT};line-height:${LINE_HEIGHT}px;user-select:none;cursor:default;will-change:transform;transform:translate(${l.x}px,${l.y}px)`
    container.appendChild(span)
    els.push(span)
  }

  // Unlock last few chars as draggable entry points
  const n = Math.min(5, letters.length)
  const lastIdx = letters.length - 1
  for (let i = lastIdx; i > lastIdx - n; i--) {
    if (i < 0) break
    letters[i].locked = false
    els[i].style.cursor = 'grab'
  }
}

function simulate() {
  const container = stageRef.value
  if (!container) return

  // Progressively unlock chars via unravel sequence
  if (unraveling) {
    if (!gravityOn || unravelIdx < 0) {
      unraveling = false
    } else if (letters[unravelIdx].locked) {
      letters[unravelIdx].locked = false
      letters[unravelIdx].px = letters[unravelIdx].x
      letters[unravelIdx].py = letters[unravelIdx].y - 0.5
      unravelIdx--
    } else {
      unravelIdx--
    }
  }

  // Chain tension unlocks neighbours
  for (let i = letters.length - 2; i >= 0; i--) {
    if (letters[i].locked && !letters[i + 1].locked) {
      const a = letters[i], b = letters[i + 1]
      const dx = (b.x + b.w / 2) - (a.ox + a.w / 2)
      const dy = (b.y + LINE_HEIGHT / 2) - (a.oy + LINE_HEIGHT / 2)
      if (Math.hypot(dx, dy) > restLengths[i] + UNLOCK_THRESHOLD) {
        a.locked = false
        a.px = a.x
        a.py = a.y
        hintHidden.value = true
      }
    }
  }

  // Verlet integration
  for (let i = 0; i < letters.length; i++) {
    const l = letters[i]
    if (l.locked || isDragged(i)) continue
    const vx = (l.x - l.px) * DAMPING
    const vy = (l.y - l.py) * DAMPING
    l.px = l.x
    l.py = l.y
    l.x += vx
    l.y += vy + (gravityOn ? GRAVITY : 0)
  }

  // Distance constraints (Jakobsen iterations)
  for (let iter = 0; iter < ITERATIONS; iter++) {
    for (let i = 0; i < letters.length - 1; i++) {
      const a = letters[i], b = letters[i + 1]
      if (a.locked && b.locked) continue
      const ax = a.x + a.w / 2, ay = a.y + LINE_HEIGHT / 2
      const bx = b.x + b.w / 2, by = b.y + LINE_HEIGHT / 2
      const dx = bx - ax, dy = by - ay
      const dist = Math.hypot(dx, dy) || 0.001
      const diff = (dist - restLengths[i]) / dist
      const aF = a.locked || isDragged(i)
      const bF = b.locked || isDragged(i + 1)
      if (aF && !bF) {
        b.x -= dx * diff; b.y -= dy * diff
      } else if (!aF && bF) {
        a.x += dx * diff; a.y += dy * diff
      } else {
        a.x += dx * diff * 0.5; a.y += dy * diff * 0.5
        b.x -= dx * diff * 0.5; b.y -= dy * diff * 0.5
      }
    }
  }

  // Soft collision between non-adjacent chars
  for (let i = 0; i < letters.length; i++) {
    if (letters[i].locked) continue
    const a = letters[i]
    const acx = a.x + a.w / 2, acy = a.y + LINE_HEIGHT / 2
    for (let j = i + 2; j < letters.length; j++) {
      if (letters[j].locked) continue
      const b = letters[j]
      const dx = (b.x + b.w / 2) - acx
      const dy = (b.y + LINE_HEIGHT / 2) - acy
      const dist = Math.hypot(dx, dy) || 0.001
      if (dist < RADIUS * 2) {
        const ov = (RADIUS * 2 - dist) / dist * 0.5
        if (isDragged(i)) { b.x += dx * ov; b.y += dy * ov }
        else if (isDragged(j)) { a.x -= dx * ov; a.y -= dy * ov }
        else { a.x -= dx * ov; a.y -= dy * ov; b.x += dx * ov; b.y += dy * ov }
      }
    }
  }

  // Boundary bounce
  const cw = container.clientWidth
  const ch = container.clientHeight
  for (let i = 0; i < letters.length; i++) {
    const l = letters[i]
    if (l.locked || isDragged(i)) continue
    if (l.x < 0) { l.x = 0; l.px = l.x + (l.x - l.px) * BOUNCE }
    if (l.x + l.w > cw) { l.x = cw - l.w; l.px = l.x + (l.x - l.px) * BOUNCE }
    if (l.y < 0) { l.y = 0; l.py = l.y + (l.y - l.py) * BOUNCE }
    if (l.y + LINE_HEIGHT > ch) { l.y = ch - LINE_HEIGHT; l.py = l.y + (l.y - l.py) * BOUNCE }
  }
}

function renderFrame(now) {
  if (lastTime < 0) { lastTime = now; rafId = requestAnimationFrame(renderFrame); return }
  const dt = Math.min((now - lastTime) / 1000, MAX_STEPS * FIXED_DT)
  lastTime = now
  accumulator += dt
  while (accumulator >= FIXED_DT) { simulate(); accumulator -= FIXED_DT }
  for (let i = 0; i < letters.length; i++) {
    if (!letters[i].locked) els[i].style.cursor = els[i].style.cursor === 'grabbing' ? 'grabbing' : 'grab'
    els[i].style.transform = `translate(${letters[i].x}px,${letters[i].y}px)`
  }
  rafId = requestAnimationFrame(renderFrame)
}

function triggerRelease() {
  if (!gravityOn) {
    gravityOn = true
    unraveling = true
    hintHidden.value = true
    unravelIdx = letters.length - 1
    while (unravelIdx >= 0 && !letters[unravelIdx].locked) unravelIdx--
  } else {
    // Second click: restore
    gravityOn = false
    initPhysics()
  }
}

// ── Event handlers ────────────────────────────────────────────────────────────

function onKeydown(e) {
  if (e.key === 'f' || e.key === 'F') triggerRelease()
}

function onPointerDown(e) {
  const idx = els.indexOf(e.target)
  if (idx === -1 || letters[idx].locked) return
  if (isDragged(idx)) return
  const rect = stageRef.value.getBoundingClientRect()
  drags.set(e.pointerId, {
    idx,
    offX: e.clientX - rect.left - letters[idx].x,
    offY: e.clientY - rect.top - letters[idx].y,
  })
  els[idx].style.cursor = 'grabbing'
  e.target.setPointerCapture(e.pointerId)
  e.preventDefault()
}

function onPointerMove(e) {
  const d = drags.get(e.pointerId)
  if (!d) return
  const rect = stageRef.value.getBoundingClientRect()
  const l = letters[d.idx]
  l.x = e.clientX - rect.left - d.offX
  l.y = e.clientY - rect.top - d.offY
  l.px = l.x; l.py = l.y
  l.locked = false
}

function onPointerUp(e) {
  const d = drags.get(e.pointerId)
  if (!d) return
  els[d.idx].style.cursor = 'grab'
  drags.delete(e.pointerId)
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

let resizeObs = null
let resizeTimer = null

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)

  initPhysics()
  lastTime = -1
  accumulator = 0
  rafId = requestAnimationFrame(renderFrame)

  window.addEventListener('keydown', onKeydown)
  stageRef.value?.addEventListener('pointerdown', onPointerDown)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerUp)

  resizeObs = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      cancelAnimationFrame(rafId)
      lastTime = -1
      accumulator = 0
      initPhysics()
      rafId = requestAnimationFrame(renderFrame)
    }, 150)
  })
  resizeObs.observe(heroRef.value)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  clearInterval(clockTimer)
  clearTimeout(resizeTimer)
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  window.removeEventListener('pointercancel', onPointerUp)
  resizeObs?.disconnect()
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 84px);
  padding: 16px;
  box-sizing: border-box;
  gap: 16px;
}

// ── Hero ──────────────────────────────────────────────────────────────────────

.hero {
  position: relative;
  flex: 0 0 38vh;
  min-height: 200px;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.text-stage {
  position: absolute;
  inset: 0;

  :deep(.phys-letter) {
    color: var(--el-text-color-primary);
    white-space: pre;
  }
}

.hint {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
  pointer-events: none;

  kbd {
    display: inline-block;
    padding: 1px 5px;
    border: 1px solid var(--el-border-color);
    border-radius: 3px;
    font-size: 12px;
    background: var(--el-fill-color);
  }

  .hint-btn {
    pointer-events: auto;
    cursor: pointer;
    color: var(--el-color-primary);

    &:hover {
      text-decoration: underline;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.6s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// ── Info section ──────────────────────────────────────────────────────────────

.info-section {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.welcome-card {
  flex: 0 0 320px;

  .welcome-inner {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .user-avatar {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
  }

  .greeting {
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
  }

  .sub-info {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

.nav-card {
  flex: 1;
  min-width: 280px;

  .nav-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
  }

  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 8px;
    border-radius: 8px;
    text-decoration: none;
    color: var(--el-text-color-regular);
    font-size: 13px;
    transition: background 0.2s, color 0.2s;
    border: 1px solid transparent;

    &:hover {
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-color: var(--el-color-primary-light-7);
    }

    .nav-icon {
      font-size: 24px;
    }
  }
}

// ── Responsive ────────────────────────────────────────────────────────────────

@media (max-width: 768px) {
  .hero {
    flex: 0 0 30vh;
  }

  .welcome-card {
    flex: 1 1 100%;
  }
}
</style>
