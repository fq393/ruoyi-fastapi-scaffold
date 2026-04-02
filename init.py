#!/usr/bin/env python3
"""
Project initialization script. Run once after cloning:

    python init.py

Replaces all ruoyi/vfadmin placeholders with your project name,
and generates a fresh JWT secret key.
"""
import re
import secrets
import sys
from pathlib import Path

ROOT     = Path(__file__).parent
BACKEND  = ROOT / 'ruoyi-fastapi-backend'
FRONTEND = ROOT / 'ruoyi-fastapi-frontend'


def ask(prompt: str, default: str = '') -> str:
    suffix = f' [{default}]' if default else ''
    val = input(f'{prompt}{suffix}: ').strip()
    return val or default


def patch(path: Path, replacements: list) -> bool:
    """Apply a list of (pattern, replacement) to a file.
    pattern can be a plain str or a compiled re.Pattern."""
    if not path.exists():
        return False
    text = path.read_text(encoding='utf-8')
    orig = text
    for pat, rep in replacements:
        text = pat.sub(rep, text) if hasattr(pat, 'sub') else text.replace(pat, rep)
    if text != orig:
        path.write_text(text, encoding='utf-8')
        return True
    return False


def main() -> None:
    print('\n=== RuoYi FastAPI Scaffold — Project Initialization ===\n')

    name = ask('项目英文名 (lowercase, e.g. mycms)').lower().strip()
    if not name:
        print('Error: project name is required'); sys.exit(1)

    cn = ask('项目中文名 (e.g. 内容管理系统)').strip()
    if not cn:
        print('Error: chinese name is required'); sys.exit(1)

    db_pass   = ask('数据库密码', default='mysqlroot')
    jwt_key   = secrets.token_hex(32)

    print(f'\n  英文名  : {name}')
    print(f'  中文名  : {cn}')
    print(f'  DB 密码 : {db_pass}')
    print(f'  JWT key : {jwt_key[:8]}…（已生成）')
    if ask('\n确认? (y/n)', 'y').lower() != 'y':
        print('Aborted.'); sys.exit(0)

    print('\n修改中…')
    changed: list[str] = []

    # ── Compiled patterns ────────────────────────────────────────────────────
    JWT_RE    = re.compile(r"JWT_SECRET_KEY\s*=\s*'[^']*'")
    APP_RE    = re.compile(r"APP_NAME\s*=\s*'[^']*'")
    DB_DB_RE  = re.compile(r"DB_DATABASE\s*=\s*'[^']*'")
    DB_PW_RE  = re.compile(r"DB_PASSWORD\s*=\s*'[^']*'")
    LOG_RE    = re.compile(r"LOG_SERVICE_NAME\s*=\s*'[^']*'")
    HMY_RE    = re.compile(r"DB_HOST\s*=\s*'ruoyi-mysql'")
    HPG_RE    = re.compile(r"DB_HOST\s*=\s*'ruoyi-pg'")
    REDIS_RE  = re.compile(r"REDIS_HOST\s*=\s*'ruoyi-redis'")

    jwt_new  = f"JWT_SECRET_KEY = '{jwt_key}'"
    base_repls = [
        (APP_RE,   f"APP_NAME = '{cn}'"),
        (DB_DB_RE, f"DB_DATABASE = '{name}'"),
        (LOG_RE,   f"LOG_SERVICE_NAME = '{name}-backend'"),
        (JWT_RE,   jwt_new),
    ]

    # ── Frontend .env files ──────────────────────────────────────────────────
    fe_envs = ['.env.development', '.env.docker', '.env.production', '.env.staging']
    for fname in fe_envs:
        if patch(FRONTEND / fname, [('vfadmin管理系统', f'{cn}管理系统'), (JWT_RE, jwt_new)]):
            changed.append(f'ruoyi-fastapi-frontend/{fname}')

    # ── Backend .env files ───────────────────────────────────────────────────
    be_envs = {
        '.env.dev':       base_repls,
        '.env.prod':      base_repls,
        '.env.dockermy':  base_repls + [
            (HMY_RE,  f"DB_HOST = '{name}-mysql'"),
            (DB_PW_RE, f"DB_PASSWORD = '{db_pass}'"),
            (REDIS_RE, f"REDIS_HOST = '{name}-redis'"),
        ],
        '.env.dockerpg':  base_repls + [
            (HPG_RE,   f"DB_HOST = '{name}-pg'"),
            (DB_PW_RE, f"DB_PASSWORD = '{db_pass}'"),
            (REDIS_RE, f"REDIS_HOST = '{name}-redis'"),
        ],
    }
    for fname, repls in be_envs.items():
        if patch(BACKEND / fname, repls):
            changed.append(f'ruoyi-fastapi-backend/{fname}')

    # ── docker-compose files ─────────────────────────────────────────────────
    for fname in ['docker-compose.my.yml', 'docker-compose.pg.yml']:
        if patch(ROOT / fname, [('ruoyi', name)]):
            changed.append(fname)

    # ── Nginx configs ────────────────────────────────────────────────────────
    for fname in ['nginx.dockermy.conf', 'nginx.dockerpg.conf']:
        if patch(FRONTEND / 'bin' / fname, [('ruoyi', name)]):
            changed.append(f'ruoyi-fastapi-frontend/bin/{fname}')

    if changed:
        for f in changed:
            print(f'  ✓ {f}')
    else:
        print('  (no files changed — already initialized?)')

    print('\n✅ 初始化完成！')
    print('\n下一步: 启动服务，成功后执行:')
    print(f'  cd ruoyi-fastapi-backend && python migrate.py --env=dev stamp head\n')


if __name__ == '__main__':
    main()
