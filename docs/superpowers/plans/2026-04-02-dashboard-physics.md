# Dashboard Physics Text Effect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dashboard hero with a four-phase physics animation (entry scatter→assemble, idle sine wave, mouse repulsion, gravity fall/return) driven by `@chenglou/pretext` layout and Verlet integration, using a per-project slogan from `VITE_APP_DASHBOARD_SLOGAN`.

**Architecture:** Single Vue 3 SFC (`src/views/dashboard/index.vue`). All physics runs in module-level variables updated by a 120 Hz fixed-timestep RAF loop. State machine has three flags: `physState` (`'entry'|'idle'|'falling'`), `gravityOn`, `elapsed`. `@chenglou/pretext` handles character-level text layout; zig-zag chain ordering connects multi-line text end-to-end.

**Tech Stack:** Vue 3 `<script setup>`, `@chenglou/pretext` (ESM), Verlet integration, CSS `transform: translate()` for rendering, Element Plus for info section.

**Working directory:** `ruoyi-fastapi-frontend/` inside the scaffold template repo. After each task, mirror the change to `~/Desktop/newsCMS/ruoyi-fastapi-frontend/` for live preview.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `package.json` | Modify | Add `@chenglou/pretext` dependency |
| `.env.development` | Modify | Add `VITE_APP_DASHBOARD_SLOGAN` |
| `.env.docker` | Modify | Add `VITE_APP_DASHBOARD_SLOGAN` |
| `src/views/dashboard/index.vue` | Rewrite | Full physics implementation |
| `~/.claude/skills/ruoyi-fastapi-scaffold/SKILL.md` | Modify | Add slogan to init checklist |

---

## Task 1: Install @chenglou/pretext

**Files:**
- Modify: `ruoyi-fastapi-frontend/package.json`

> Note: This project has no frontend unit test framework. Physics correctness is verified visually. Each task ends with a live browser check at http://localhost:12580 (Docker) or the local dev server.

- [ ] **Step 1: Install the package**

```bash
cd /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend
npm install @chenglou/pretext
```

Expected output: `added 1 package` (or similar), no errors.

- [ ] **Step 2: Verify import resolves**

```bash
node --input-type=module <<'EOF'
import { prepareWithSegments, layoutWithLines } from '@chenglou/pretext'
console.log('ok', typeof prepareWithSegments, typeof layoutWithLines)
EOF
```

Expected: `ok function function`

- [ ] **Step 3: Mirror to newsCMS**

```bash
cp /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/package.json \
   ~/Desktop/newsCMS/ruoyi-fastapi-frontend/package.json
cp /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/package-lock.json \
   ~/Desktop/newsCMS/ruoyi-fastapi-frontend/package-lock.json
cp -r /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/node_modules/@chenglou \
      ~/Desktop/newsCMS/ruoyi-fastapi-frontend/node_modules/
```

- [ ] **Step 4: Commit**

```bash
cd /tmp/ruoyi-fastapi-scaffold
git add ruoyi-fastapi-frontend/package.json ruoyi-fastapi-frontend/package-lock.json
git commit -m "chore: add @chenglou/pretext for dashboard physics layout"
```

---

## Task 2: Add VITE_APP_DASHBOARD_SLOGAN to env files

**Files:**
- Modify: `ruoyi-fastapi-frontend/.env.development`
- Modify: `ruoyi-fastapi-frontend/.env.docker`

- [ ] **Step 1: Add to .env.development**

Append to `ruoyi-fastapi-frontend/.env.development`:

```
# 首页 Slogan（物理文字特效文案，\n 表示换行）
VITE_APP_DASHBOARD_SLOGAN = 高效管理 · 智能运营\n让业务在数字化时代加速前行
```

- [ ] **Step 2: Add to .env.docker**

Append to `ruoyi-fastapi-frontend/.env.docker`:

```
# 首页 Slogan（物理文字特效文案，\n 表示换行）
VITE_APP_DASHBOARD_SLOGAN = 高效管理 · 智能运营\n让业务在数字化时代加速前行
```

- [ ] **Step 3: Mirror env files to newsCMS**

```bash
cp /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/.env.development \
   ~/Desktop/newsCMS/ruoyi-fastapi-frontend/.env.development
cp /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/.env.docker \
   ~/Desktop/newsCMS/ruoyi-fastapi-frontend/.env.docker
```

Also add the slogan to newsCMS's own `.env.development` with a project-specific value:

```
VITE_APP_DASHBOARD_SLOGAN = 精准传播，内容为王\n让每一篇文章都触达更多读者
```

- [ ] **Step 4: Commit**

```bash
cd /tmp/ruoyi-fastapi-scaffold
git add ruoyi-fastapi-frontend/.env.development ruoyi-fastapi-frontend/.env.docker
git commit -m "feat: add VITE_APP_DASHBOARD_SLOGAN env var for dashboard slogan"
```

---

## Task 3: Rewrite dashboard index.vue — pretext layout + zig-zag chain

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/dashboard/index.vue`

This task replaces the current `initPhysics()` text layout with pretext-based multi-line layout and zig-zag chain ordering. The template and info section are untouched.

- [ ] **Step 1: Replace the full file with the new implementation**

Write the following to `ruoyi-fastapi-frontend/src/views/dashboard/index.vue`:

```vue
<template>
  <div class="dashboard">
    <div class="hero" ref="heroRef">
      <div class="text-stage" ref="stageRef"></div>
      <transition name="fade">
        <div v-if="!hintHidden" class="hint">
          拖拽末尾字符 · 按 <kbd>F</kbd> 键或
          <span class="hint-btn" @click="triggerRelease">{{ releaseLabel }}</span>
        </div>
      </transition>
    </div>

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

      <el-card class="nav-card" shadow="never" header="快捷导航">
        <div class="nav-grid">
          <router-link v-for="link in quickLinks" :key="link.to" :to="link.to" class="nav-item">
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
import { prepareWithSegments, layoutWithLines } from '@chenglou/pretext'
import useUserStore from '@/store/modules/user'

defineOptions({ name: 'Dashboard' })

const userStore = useUserStore()
const heroRef = ref(null)
const stageRef = ref(null)
const hintHidden = ref(false)
const releaseLabel = ref('点击释放')

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
  { to: '/system/user',  icon: 'peoples',    label: '用户管理' },
  { to: '/system/role',  icon: 'role',       label: '角色管理' },
  { to: '/system/menu',  icon: 'tree-table', label: '菜单管理' },
  { to: '/system/dept',  icon: 'tree',       label: '部门管理' },
  { to: '/system/dict',  icon: 'dict',       label: '字典管理' },
  { to: '/user/profile', icon: 'user',       label: '个人中心' },
]

// ── Physics constants ─────────────────────────────────────────────────────────

const MARGIN = 32
const CONSTRAINT_DIST = 1.25
const UNLOCK_THRESHOLD = 1
const ITERATIONS = 12
const DAMPING_IDLE = 0.97
const DAMPING_ENTRY = 0.88
const GRAVITY = 0.18
const BOUNCE = 0.4
const RADIUS = 9
const FIXED_DT = 1 / 120
const MAX_STEPS = 4

// Entry spring
const ENTRY_K = 0.06
const ENTRY_LOCK_DIST = 2
const ENTRY_LOCK_SPEED = 0.5
const ENTRY_TIMEOUT_MS = 2500

// Idle wave
const WAVE_AMP = 4
const WAVE_FREQ = 1.8      // radians/second
const WAVE_SPREAD = 2.5    // radians per char index

// Mouse repulsion
const REPULSE_RADIUS = 80
const REPULSE_STRENGTH = 3
const REPULSE_SPRING_K = 0.03

// ── Physics state ─────────────────────────────────────────────────────────────

// physState: 'entry' | 'idle' | 'falling'
let physState = 'entry'
let gravityOn = false
let unraveling = false
let unravelIdx = -1
let elapsed = 0          // seconds, incremented each fixed tick
let entryStartTime = 0   // performance.now() when entry began

let FONT = 'bold 40px system-ui, sans-serif'
let LINE_HEIGHT = 56
let letters = []
let restLengths = []
let els = []
let rafId = null
let lastTime = -1
let accumulator = 0
let mouseX = -9999
let mouseY = -9999

const drags = new Map()
function isDragged(idx) {
  for (const d of drags.values()) if (d.idx === idx) return true
  return false
}

// ── pretext layout + zig-zag chain ───────────────────────────────────────────

function pickFont(width) {
  if (width < 500) return 'bold 28px system-ui, sans-serif'
  if (width < 800) return 'bold 34px system-ui, sans-serif'
  return 'bold 40px system-ui, sans-serif'
}

function buildLayout(container) {
  // Parse slogan: \n in env var becomes literal backslash-n
  const raw = import.meta.env.VITE_APP_DASHBOARD_SLOGAN || '高效管理 · 智能运营\n让业务在数字化时代加速前行'
  const text = raw.replace(/\\n/g, '\n')

  FONT = pickFont(container.clientWidth)
  LINE_HEIGHT = Math.round(parseInt(FONT) * 1.4)

  const maxW = container.clientWidth - MARGIN * 2

  // Measure each grapheme width via canvas (same as pretext internally)
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = FONT
  const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' })
  const allGraphemes = [...segmenter.segment(text)].map(s => s.segment)
  const graphemeWidths = allGraphemes.map(g => ctx.measureText(g).width)

  // Use pretext to get line breaks
  const prepared = prepareWithSegments(text, FONT)
  const { lines } = layoutWithLines(prepared, maxW, LINE_HEIGHT)

  // Map grapheme index → line index
  const lineGraphemeIndices = []
  let gi = 0
  for (const line of lines) {
    const lineGS = [...segmenter.segment(line.text)].map(s => s.segment)
    const indices = []
    for (let j = 0; j < lineGS.length; j++) indices.push(gi++)
    lineGraphemeIndices.push(indices)
  }

  // Zig-zag chain: reverse alternating lines so chain is end-to-end continuous
  const lastLineIdx = lineGraphemeIndices.length - 1
  const needFlip = lastLineIdx % 2 === 1
  const chainOrder = []
  for (let li = 0; li < lineGraphemeIndices.length; li++) {
    const reversed = needFlip ? (li % 2 === 0) : (li % 2 === 1)
    if (reversed) chainOrder.push(...[...lineGraphemeIndices[li]].reverse())
    else chainOrder.push(...lineGraphemeIndices[li])
  }

  // Compute rest positions: layout each grapheme left-to-right per line
  const restPos = new Array(allGraphemes.length)
  for (let li = 0; li < lineGraphemeIndices.length; li++) {
    const lineIndices = lineGraphemeIndices[li]
    // total height centred vertically
    const totalH = lines.length * LINE_HEIGHT
    const offsetY = Math.max(0, (container.clientHeight - totalH) * 0.38)
    const lineY = li * LINE_HEIGHT + offsetY
    let x = MARGIN
    for (const idx of lineIndices) {
      restPos[idx] = { x, y: lineY, w: graphemeWidths[idx] }
      x += graphemeWidths[idx]
    }
  }

  return { allGraphemes, graphemeWidths, chainOrder, restPos }
}

// ── initPhysics ───────────────────────────────────────────────────────────────

function initPhysics() {
  const container = stageRef.value
  if (!container) return

  container.innerHTML = ''
  els = []
  letters = []
  drags.clear()
  physState = 'entry'
  gravityOn = false
  unraveling = false
  unravelIdx = -1
  elapsed = 0
  entryStartTime = performance.now()
  hintHidden.value = false
  releaseLabel.value = '点击释放'

  const { allGraphemes, graphemeWidths, chainOrder, restPos } = buildLayout(container)

  const cw = container.clientWidth
  const ch = container.clientHeight

  // Build letters array in chain order
  letters = chainOrder.map(ri => {
    const rp = restPos[ri]
    // Random spawn position
    const sx = Math.random() * cw
    const sy = Math.random() * ch
    // Initial velocity roughly toward target, magnitude 2-6 px/tick
    const angle = Math.atan2(rp.y - sy, rp.x - sx) + (Math.random() - 0.5) * (Math.PI / 1.5)
    const speed = 2 + Math.random() * 4
    return {
      ch: allGraphemes[ri],
      w: graphemeWidths[ri],
      x: sx, y: sy,
      px: sx - Math.cos(angle) * speed,
      py: sy - Math.sin(angle) * speed,
      ox: rp.x, oy: rp.y,
      locked: false,
      readingIdx: ri,
    }
  })

  // Rest lengths between adjacent chain members
  restLengths = []
  for (let i = 0; i < letters.length - 1; i++) {
    const a = letters[i], b = letters[i + 1]
    const dist = Math.hypot(
      (b.ox + b.w / 2) - (a.ox + a.w / 2),
      (b.oy + LINE_HEIGHT / 2) - (a.oy + LINE_HEIGHT / 2)
    )
    restLengths.push(dist * CONSTRAINT_DIST)
  }

  // Create DOM spans
  for (const l of letters) {
    const span = document.createElement('span')
    span.className = 'phys-letter'
    span.textContent = l.ch
    span.style.cssText = `position:absolute;top:0;left:0;font:${FONT};line-height:${LINE_HEIGHT}px;user-select:none;cursor:default;will-change:transform;`
    container.appendChild(span)
    els.push(span)
  }
}

// ── simulate ──────────────────────────────────────────────────────────────────

function simulate() {
  const container = stageRef.value
  if (!container) return

  elapsed += FIXED_DT

  // ── Entry: spring toward rest position ──────────────────────────────────────
  if (physState === 'entry') {
    let allLocked = true
    for (let i = 0; i < letters.length; i++) {
      const l = letters[i]
      if (l.locked) continue

      const targetX = l.ox, targetY = l.oy
      const dx = targetX - l.x, dy = targetY - l.y

      // Spring force
      const fx = dx * ENTRY_K, fy = dy * ENTRY_K

      const vx = (l.x - l.px) * DAMPING_ENTRY + fx
      const vy = (l.y - l.py) * DAMPING_ENTRY + fy
      l.px = l.x; l.py = l.y
      l.x += vx; l.y += vy

      const dist = Math.hypot(dx, dy)
      const speed = Math.hypot(vx, vy)
      if (dist < ENTRY_LOCK_DIST && speed < ENTRY_LOCK_SPEED) {
        l.x = l.ox; l.y = l.oy
        l.px = l.ox; l.py = l.oy
        l.locked = true
      } else {
        allLocked = false
      }
    }

    const timedOut = (performance.now() - entryStartTime) > ENTRY_TIMEOUT_MS
    if (allLocked || timedOut) {
      // Force-lock any stragglers, then unlock last 6 as rope end
      for (const l of letters) {
        l.locked = true; l.x = l.ox; l.y = l.oy; l.px = l.ox; l.py = l.oy
      }
      const n = Math.min(6, letters.length)
      const lastIdx = letters.length - 1
      for (let i = lastIdx; i > lastIdx - n; i--) {
        if (i < 0) break
        letters[i].locked = false
        els[i].style.cursor = 'grab'
      }
      physState = 'idle'
    }
    return  // skip Verlet / constraints during entry
  }

  // ── Falling: unravel sequence ────────────────────────────────────────────────
  if (physState === 'falling' && unraveling) {
    if (unravelIdx < 0) {
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

  // ── Chain tension unlock (idle + falling) ────────────────────────────────────
  if (physState !== 'entry') {
    for (let i = letters.length - 2; i >= 0; i--) {
      if (letters[i].locked && !letters[i + 1].locked) {
        const a = letters[i], b = letters[i + 1]
        const dx = (b.x + b.w / 2) - (a.ox + a.w / 2)
        const dy = (b.y + LINE_HEIGHT / 2) - (a.oy + LINE_HEIGHT / 2)
        if (Math.hypot(dx, dy) > restLengths[i] + UNLOCK_THRESHOLD) {
          a.locked = false; a.px = a.x; a.py = a.y
          hintHidden.value = true
        }
      }
    }
  }

  // ── Verlet integration ────────────────────────────────────────────────────────
  for (let i = 0; i < letters.length; i++) {
    const l = letters[i]
    if (l.locked || isDragged(i)) continue

    let fx = 0, fy = 0

    // Mouse repulsion (idle only, unlocked chars)
    if (physState === 'idle') {
      const cx = l.x + l.w / 2, cy = l.y + LINE_HEIGHT / 2
      const mdx = cx - mouseX, mdy = cy - mouseY
      const mdist = Math.hypot(mdx, mdy)
      if (mdist < REPULSE_RADIUS && mdist > 0.1) {
        const t = 1 - mdist / REPULSE_RADIUS
        const mag = REPULSE_STRENGTH * t * t
        fx += (mdx / mdist) * mag
        fy += (mdy / mdist) * mag
      }
      // Soft spring back toward rest when not dragged
      if (!isDragged(i)) {
        fx += (l.ox - l.x) * REPULSE_SPRING_K
        fy += (l.oy - l.y) * REPULSE_SPRING_K
      }
    }

    const vx = (l.x - l.px) * DAMPING_IDLE + fx
    const vy = (l.y - l.py) * DAMPING_IDLE + fy
    l.px = l.x; l.py = l.y
    l.x += vx
    l.y += vy + (gravityOn ? GRAVITY : 0)
  }

  // ── Distance constraints ──────────────────────────────────────────────────────
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
      if (aF && !bF)       { b.x -= dx * diff;         b.y -= dy * diff }
      else if (!aF && bF)  { a.x += dx * diff;         a.y += dy * diff }
      else                 { a.x += dx*diff*0.5; a.y += dy*diff*0.5; b.x -= dx*diff*0.5; b.y -= dy*diff*0.5 }
    }
  }

  // ── Soft collision ────────────────────────────────────────────────────────────
  for (let i = 0; i < letters.length; i++) {
    if (letters[i].locked) continue
    const a = letters[i]
    const acx = a.x + a.w / 2, acy = a.y + LINE_HEIGHT / 2
    for (let j = i + 2; j < letters.length; j++) {
      if (letters[j].locked) continue
      const b = letters[j]
      const dx = (b.x + b.w / 2) - acx, dy = (b.y + LINE_HEIGHT / 2) - acy
      const dist = Math.hypot(dx, dy) || 0.001
      if (dist < RADIUS * 2) {
        const ov = (RADIUS * 2 - dist) / dist * 0.5
        if (isDragged(i))      { b.x += dx * ov; b.y += dy * ov }
        else if (isDragged(j)) { a.x -= dx * ov; a.y -= dy * ov }
        else { a.x -= dx * ov; a.y -= dy * ov; b.x += dx * ov; b.y += dy * ov }
      }
    }
  }

  // ── Boundary bounce ───────────────────────────────────────────────────────────
  const cw = container.clientWidth, ch = container.clientHeight
  for (let i = 0; i < letters.length; i++) {
    const l = letters[i]
    if (l.locked || isDragged(i)) continue
    if (l.x < 0)           { l.x = 0;              l.px = l.x + (l.x - l.px) * BOUNCE }
    if (l.x + l.w > cw)    { l.x = cw - l.w;       l.px = l.x + (l.x - l.px) * BOUNCE }
    if (l.y < 0)            { l.y = 0;              l.py = l.y + (l.y - l.py) * BOUNCE }
    if (l.y + LINE_HEIGHT > ch) { l.y = ch - LINE_HEIGHT; l.py = l.y + (l.y - l.py) * BOUNCE }
  }
}

// ── renderFrame ───────────────────────────────────────────────────────────────

function renderFrame(now) {
  if (lastTime < 0) { lastTime = now; rafId = requestAnimationFrame(renderFrame); return }
  const dt = Math.min((now - lastTime) / 1000, MAX_STEPS * FIXED_DT)
  lastTime = now
  accumulator += dt
  while (accumulator >= FIXED_DT) { simulate(); accumulator -= FIXED_DT }

  const t = elapsed  // current elapsed in seconds (updated in simulate)
  for (let i = 0; i < letters.length; i++) {
    const l = letters[i]
    let x = l.x, y = l.y

    // Idle wave: offset locked chars
    if (physState === 'idle' && l.locked) {
      y = l.oy + WAVE_AMP * Math.sin(i / WAVE_SPREAD + t * WAVE_FREQ)
      x = l.ox
    }

    if (!l.locked && physState !== 'entry') {
      els[i].style.cursor = isDragged(i) ? 'grabbing' : 'grab'
    }
    els[i].style.transform = `translate(${x}px,${y}px)`
  }

  rafId = requestAnimationFrame(renderFrame)
}

// ── Controls ──────────────────────────────────────────────────────────────────

function triggerRelease() {
  if (physState === 'idle') {
    physState = 'falling'
    gravityOn = true
    unraveling = true
    hintHidden.value = true
    releaseLabel.value = '归位'
    unravelIdx = letters.length - 1
    while (unravelIdx >= 0 && !letters[unravelIdx].locked) unravelIdx--
  } else if (physState === 'falling') {
    cancelAnimationFrame(rafId)
    lastTime = -1; accumulator = 0
    initPhysics()
    rafId = requestAnimationFrame(renderFrame)
  }
}

// ── Event handlers ────────────────────────────────────────────────────────────

function onKeydown(e) {
  if (e.key === 'f' || e.key === 'F') triggerRelease()
}

function onMouseMove(e) {
  const rect = stageRef.value?.getBoundingClientRect()
  if (!rect) return
  mouseX = e.clientX - rect.left
  mouseY = e.clientY - rect.top
}

function onMouseLeave() {
  mouseX = -9999; mouseY = -9999
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
  lastTime = -1; accumulator = 0
  rafId = requestAnimationFrame(renderFrame)

  window.addEventListener('keydown', onKeydown)
  stageRef.value?.addEventListener('pointerdown', onPointerDown)
  stageRef.value?.addEventListener('mousemove', onMouseMove)
  stageRef.value?.addEventListener('mouseleave', onMouseLeave)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerUp)

  resizeObs = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      cancelAnimationFrame(rafId)
      lastTime = -1; accumulator = 0
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
  min-height: calc(100vh - 84px);
  padding: 16px;
  box-sizing: border-box;
  gap: 16px;
}

.hero {
  position: relative;
  flex: 0 0 45vh;
  min-height: 220px;
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
    &:hover { text-decoration: underline; }
  }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.6s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

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

.nav-card {
  flex: 1;
  min-width: 280px;
  .nav-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 12px; }
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

@media (max-width: 768px) {
  .hero { flex: 0 0 35vh; }
  .welcome-card { flex: 1 1 100%; }
}
</style>
```

- [ ] **Step 2: Mirror to newsCMS**

```bash
cp /tmp/ruoyi-fastapi-scaffold/ruoyi-fastapi-frontend/src/views/dashboard/index.vue \
   ~/Desktop/newsCMS/ruoyi-fastapi-frontend/src/views/dashboard/index.vue
```

- [ ] **Step 3: Verify dev server compiles without errors**

If running a local dev server: check browser console for import errors.

For Docker mode, check that `@chenglou/pretext` is in `node_modules`:
```bash
ls ~/Desktop/newsCMS/ruoyi-fastapi-frontend/node_modules/@chenglou/pretext/dist/layout.js
```
Expected: file exists.

- [ ] **Step 4: Commit**

```bash
cd /tmp/ruoyi-fastapi-scaffold
git add ruoyi-fastapi-frontend/src/views/dashboard/index.vue
git commit -m "feat: dashboard physics hero — entry scatter, idle wave, mouse repulsion, gravity fall"
```

---

## Task 4: Rebuild Docker frontend and verify visually

**Files:** none (build only)

- [ ] **Step 1: Rebuild newsCMS frontend container**

```bash
cd ~/Desktop/newsCMS
docker-compose -f docker-compose.pg.yml up -d --build newsCMS-frontend
```

Wait for build to complete (~2-3 min). Expected: `newsCMS-frontend` container restarts.

- [ ] **Step 2: Open browser and verify all four phases**

Open http://localhost:12580, log in.

Check:
1. **Entry**: Characters fly in from random positions and converge into 2-line text ✓
2. **Idle**: Sine wave visibly ripples through the settled text ✓
3. **Repulsion**: Move mouse slowly across the hero — unlocked end chars push away then spring back ✓
4. **Fall**: Press F or click "点击释放" — chars fall with bounce ✓
5. **Return**: Click "归位" — entry animation replays ✓
6. **Drag**: Drag the last few chars — chain unravels ✓

- [ ] **Step 3: Check dark mode**

Toggle dark mode via the sun/moon button in navbar. Text color should remain legible (uses `var(--el-text-color-primary)`).

---

## Task 5: Update SKILL.md init checklist

**Files:**
- Modify: `~/.claude/skills/ruoyi-fastapi-scaffold/SKILL.md`

- [ ] **Step 1: Add VITE_APP_DASHBOARD_SLOGAN to Step 3 rename table**

Find the table in the "Mode A & B & C — edit `ruoyi-fastapi-frontend/.env.development`" section and add the slogan row:

```
VITE_APP_TITLE = <中文项目名>
VITE_APP_DASHBOARD_SLOGAN = <项目一句话 Slogan>   # 物理文字特效文案，\n 表示换行
```

- [ ] **Step 2: Commit**

```bash
cd /tmp/ruoyi-fastapi-scaffold
git add .
git commit -m "docs: add VITE_APP_DASHBOARD_SLOGAN to scaffold init checklist"
```

- [ ] **Step 3: Push template repo**

```bash
cd /tmp/ruoyi-fastapi-scaffold
git push
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| pretext `prepareWithSegments + layoutWithLines` for layout | Task 3 |
| Zig-zag chain ordering | Task 3 (`buildLayout`) |
| Entry: random spawn + spring attractor, ENTRY_K=0.06, damping=0.88 | Task 3 (`simulate` entry block) |
| Lock condition: dist < 2 AND speed < 0.5 | Task 3 |
| 2.5s timeout | Task 3 (`ENTRY_TIMEOUT_MS`) |
| Idle sine wave: amp=4, freq=1.8, spread=2.5 | Task 3 (`renderFrame`) |
| Mouse repulsion: radius=80, strength=3, spring k=0.03 | Task 3 (`simulate` idle block) |
| Falling: gravity + unravel sequence | Task 3 (`triggerRelease` + `simulate` falling block) |
| Returning: re-run initPhysics | Task 3 (`triggerRelease` falling→idle) |
| Button label toggle 释放/归位 | Task 3 (`releaseLabel`) |
| VITE_APP_DASHBOARD_SLOGAN env var | Task 2 |
| Skill init checklist update | Task 5 |
| Docker rebuild | Task 4 |

All spec requirements covered. No TBDs or placeholders in the plan.
