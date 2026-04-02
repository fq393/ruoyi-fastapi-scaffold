# Dashboard Physics Text Effect — Design Spec

**Date:** 2026-04-02  
**File:** `ruoyi-fastapi-frontend/src/views/dashboard/index.vue`

---

## Overview

Replace the current static-title hero with a four-phase physics animation driven by `@chenglou/pretext`. Text content is a per-project slogan configured via `VITE_APP_DASHBOARD_SLOGAN`. The effect combines an auto-play entry animation with an always-on interactive state.

---

## Layout

```
┌─────────────────────────────────────────┐  ← Hero 45vh, position:relative, overflow:hidden
│  physics text stage (absolute fill)     │
│  hint bar (absolute bottom)             │
└─────────────────────────────────────────┘
┌───────────────┐ ┌───────────────────────┐
│  welcome card │ │  quick nav grid        │
└───────────────┘ └───────────────────────┘
```

Info section (welcome + quick nav) is unchanged from current implementation.

---

## Text Content

### Environment variable

```
VITE_APP_DASHBOARD_SLOGAN = 高效管理 · 智能运营\n让业务在数字化时代加速前行
```

Added to `.env.development` and `.env.dockermy` / `.env.dockerpg` templates.  
Scaffold init checklist: update `VITE_APP_DASHBOARD_SLOGAN` alongside `VITE_APP_TITLE`.

### Layout

- Font: `bold 40px system-ui, sans-serif` (desktop); `bold 28px system-ui, sans-serif` (< 600px)
- Line height: `font-size × 1.4`
- Use `prepareWithSegments(text, font)` + `layoutWithLines(prepared, containerWidth - 2×MARGIN, lineHeight)` from `@chenglou/pretext` to get per-character positions
- Build zig-zag chain: reverse alternating lines so chain is continuous end-to-end (identical to textstring demo)
- Last 6 characters start `unlocked` (free rope end)

---

## Physics State Machine

```
[entry] ──all locked──► [idle] ◄──returning──[returning]
                           │                      ▲
                      user interaction            │
                           │                  trigger reset
                           ▼                      │
                      [interactive] ──F/btn──► [falling]
```

### State: `entry` (~1.8s)

- Each character spawns at a random position within the hero bounds
- Random initial velocity (magnitude 2-6 px/tick, direction roughly toward target ± 60°)
- Per-tick spring force toward rest position: `F = k × (ox - x, oy - y)`, `k = 0.06`
- Damping: `0.88` (faster convergence than idle)
- Lock condition: `dist_to_target < 2px AND speed < 0.5px/tick`
- Characters lock in natural order (earlier chars converge first due to shorter travel distances from staggered random spawn)
- After all chars locked (or 2.5s timeout): transition to `idle`

### State: `idle`

- Locked chars get a sine-wave Y offset each frame:
  ```
  Δy = 4 × sin(charIndex / 2.5 + elapsed × 1.8)
  ```
- Unlocked chars run normal Verlet integration (no gravity, DAMPING=0.97)
- Mouse repulsion active (see interactive section)

### State: `interactive` (subset of idle)

No separate state — mouse repulsion runs every frame while in `idle`.

**Mouse repulsion:**
- Radius: 80px
- Applied only to `unlocked` characters
- Force magnitude: `strength × (1 - dist/radius)²`, `strength = 3`
- Direction: away from mouse
- Characters spring back naturally via Verlet + soft constraint to rest position (spring `k = 0.03` toward `ox/oy` when no drag active)

**Rope drag:** existing Verlet distance-constraint chain (unchanged from current implementation).

**Chain unlock:** existing tension-threshold propagation (unchanged).

### State: `falling`

- Triggered by: F key OR "释放" button click
- `gravityOn = true`, run existing unravel sequence (unlock chars from end toward start, one per tick)
- Boundary bounce: `BOUNCE = 0.4`
- Button label changes to "归位"

### State: `returning`

- Triggered by: second click of button (or second F press) while in `falling`
- `gravityOn = false`; re-run `initPhysics()` which restarts `entry` animation
- Hint reappears

---

## Component Architecture

Single file: `src/views/dashboard/index.vue`

**Module-level physics vars** (same pattern as current): `letters[]`, `restLengths[]`, `els[]`, state flags, RAF id.

**Key functions:**
| Function | Role |
|---|---|
| `initPhysics()` | Build char array from pretext layout, create spans, set state=entry |
| `simulate()` | One physics tick: entry spring / idle wave / falling gravity / constraints / collision / bounds |
| `renderFrame(now)` | Fixed-timestep accumulator at 120Hz, apply transforms |
| `triggerRelease()` | Toggle falling ↔ returning |
| `onPointerDown/Move/Up` | Drag handling |

**Dependencies added:**
- `@chenglou/pretext` (npm install, already exists in template)

---

## Environment Files to Update

| File | Key | Default |
|---|---|---|
| `.env.development` | `VITE_APP_DASHBOARD_SLOGAN` | `高效管理 · 智能运营\n让业务在数字化时代加速前行` |
| `.env.dockermy` | same | same |
| `.env.dockerpg` | same | same |

Skill (`SKILL.md`) init checklist: add `VITE_APP_DASHBOARD_SLOGAN` to rename step.

---

## What Does NOT Change

- Info section (welcome card + quick nav) — identical to current
- Dark mode support via CSS variables — identical to current
- ResizeObserver debounced reinit — identical to current
- Pointer drag multi-touch handling — identical to current
