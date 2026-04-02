"""
Alembic 迁移包装脚本，用法与 app.py 保持一致：

    # 生成迁移文件（改完模型后运行）
    python migrate.py --env=dev revision --autogenerate -m "add news table"

    # 执行迁移（升级到最新）
    python migrate.py --env=dev upgrade head

    # 回滚一步
    python migrate.py --env=dev downgrade -1

    # 查看当前版本
    python migrate.py --env=dev current

    # 查看迁移历史
    python migrate.py --env=dev history

    # 新项目初始化后执行一次，将当前 DB 状态标记为基线
    python migrate.py --env=dev stamp head

--env 默认值为 dev，也可通过 APP_ENV 环境变量指定。
"""

import os
import subprocess
import sys


def main() -> None:
    args = sys.argv[1:]
    env = os.environ.get('APP_ENV', 'dev')

    # 提取 --env / --env=xxx 参数，其余参数原样传给 alembic
    alembic_args: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == '--env' and i + 1 < len(args):
            env = args[i + 1]
            i += 2
        elif args[i].startswith('--env='):
            env = args[i].split('=', 1)[1]
            i += 1
        else:
            alembic_args.append(args[i])
            i += 1

    if not alembic_args:
        print(__doc__)
        sys.exit(0)

    # 通过环境变量传给子进程；config/env.py 在 alembic 模式下会优先读取它
    env_vars = {**os.environ, 'APP_ENV': env}
    result = subprocess.run(['alembic'] + alembic_args, env=env_vars)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
