# 项目约定

本项目基于 [ruoyi-fastapi-scaffold](https://github.com/fq393/ruoyi-fastapi-scaffold) 脚手架构建，
使用 FastAPI（后端）+ Vue3 + Element Plus（前端）。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+, FastAPI, SQLAlchemy (async), Pydantic v2 |
| 前端 | Vue3, Vite, Element Plus, Pinia |
| 数据库 | MySQL 或 PostgreSQL（项目初始化时选定） |
| 缓存 | Redis |
| 认证 | OAuth2 + JWT |

---

## 后端模块结构

每个业务模块放在 `ruoyi-fastapi-backend/module_<name>/`，固定四层：

```
module_<name>/
  controller/   # 路由层 —— 放这里才会被自动注册
  service/      # 业务逻辑
  dao/          # 数据库查询
  entity/
    do/         # SQLAlchemy ORM 模型
    vo/         # Pydantic 请求/响应模型
```

**自动路由注册**：`controller/` 目录下所有文件中的 `APIRouterPro` 实例会被自动扫描注册，无需手动修改 `server.py`。

### Controller 模板

```python
from common.router import APIRouterPro
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.annotation.log_annotation import Log
from common.enums import BusinessType

news_controller = APIRouterPro(
    prefix='/cms/news',
    order_num=20,          # 业务模块从 20 开始，内置模块用 1-10
    tags=['CMS-新闻管理'],
    dependencies=[PreAuthDependency()]   # 路由级：仅需登录
)

@news_controller.get('/list',
    dependencies=[UserInterfaceAuthDependency('cms:news:list')])  # 接口级权限
async def get_news_list(...): ...

@news_controller.post('',
    dependencies=[UserInterfaceAuthDependency('cms:news:add')])
@Log(title='新闻管理', business_type=BusinessType.INSERT)
async def add_news(...): ...
```

### 权限码命名规范

格式：`<模块前缀>:<资源>:<操作>`

- **内置前缀（禁止使用）**：`system:`, `monitor:`, `tool:`
- **业务模块自定义前缀**：如 `cms:`, `shop:`, `crm:`
- **标准操作**：`list`, `add`, `edit`, `remove`, `query`, `export`

### Pydantic VO 约定

所有 VO 必须加 camelCase 转换配置，API JSON 与前端交互用 camelCase，Python 代码内部用 snake_case：

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class NewsModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    news_id: int | None = None
    news_title: str | None = None   # API 传输为 newsTitle
```

### SQLAlchemy Model 约定

继承 `Base` 即可，启动时自动建表（`init_create_table()` 调用 `create_all`），无需写 Alembic migration：

```python
from config.database import Base
from sqlalchemy import Column, BigInteger, String

class CmsNews(Base):
    __tablename__ = 'cms_news'
    news_id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_title = Column(String(200), nullable=False)
```

---

## 前端模块结构

每个业务模块对应：

```
src/api/<module>/          # 接口定义，如 src/api/cms/news.js
src/views/<module>/        # 页面组件，如 src/views/cms/news/index.vue
```

**组件路径必须与 `sys_menu.component` 字段完全一致。**

例如 `sys_menu.component = 'cms/news/index'` 对应文件 `src/views/cms/news/index.vue`。路径不匹配时路由静默失败，不报错。

---

## 菜单与权限 SQL

新增模块必须向 `sys_menu` 插入三层记录：

```sql
-- 1. 目录（menu_type='M'）
INSERT INTO sys_menu VALUES
(2000, '内容管理', 0, 10, 'cms', NULL, '', '', 1, 0, 'M', '0', '0', '', 'table', 'admin', NOW(), '', NULL, '');

-- 2. 菜单（menu_type='C'，component 必须与 src/views/ 路径一致）
INSERT INTO sys_menu VALUES
(2001, '新闻管理', 2000, 1, 'news', 'cms/news/index', '', 'CmsNews', 1, 0, 'C', '0', '0', 'cms:news:list', 'documentation', 'admin', NOW(), '', NULL, '');

-- 3. 按钮（menu_type='F'）
INSERT INTO sys_menu VALUES
(2100, '新闻查询', 2001, 1, '', NULL, '', '', 1, 0, 'F', '0', '0', 'cms:news:query', '#', 'admin', NOW(), '', NULL, ''),
(2101, '新闻新增', 2001, 2, '', NULL, '', '', 1, 0, 'F', '0', '0', 'cms:news:add', '#', 'admin', NOW(), '', NULL, ''),
(2102, '新闻修改', 2001, 3, '', NULL, '', '', 1, 0, 'F', '0', '0', 'cms:news:edit', '#', 'admin', NOW(), '', NULL, ''),
(2103, '新闻删除', 2001, 4, '', NULL, '', '', 1, 0, 'F', '0', '0', 'cms:news:remove', '#', 'admin', NOW(), '', NULL, '');
```

menu_id 从 2000 开始（内置模块用 1-1999）。

---

## 动态配置使用规则

### sys_dict（字典）—— 枚举型选项

适用场景：字段有固定可选值（状态、分类、类型等）。

```
dict_type 命名：<模块前缀>_<字段名>
示例：cms_news_status（草稿=0, 已发布=1, 下线=2）
```

前端用 `<dict-tag>` 组件渲染，不硬编码文字。

### sys_config（参数）—— 单值配置

适用场景：运行时可修改的单一配置值（文件上传大小、站点名称等）。

```
config_key 命名：<模块前缀>.<参数名>
示例：cms.news.maxTitleLength
```

**判断规则：有多个选项 → sys_dict；单一可变值 → sys_config；固定不变 → 代码常量。**

---

## 项目初始化后必须修改的配置

### 本地开发 / 混合模式

| 文件 | 字段 | 说明 |
|------|------|------|
| `ruoyi-fastapi-backend/.env.dev` | `APP_NAME` | 改为项目名 |
| `ruoyi-fastapi-backend/.env.dev` | `JWT_SECRET_KEY` | 必须重新生成（默认值是公开的） |
| `ruoyi-fastapi-backend/.env.dev` | `LOG_SERVICE_NAME` | 改为项目名 |
| `ruoyi-fastapi-backend/.env.dev` | `DB_DATABASE` | 改为项目数据库名 |
| `ruoyi-fastapi-frontend/.env.development` | `VITE_APP_TITLE` | 改为项目名（注意：默认值是 `vfadmin` 不是 `ruoyi`） |

### Docker 全量模式（额外需要）

| 文件 | 需改内容 |
|------|---------|
| `docker-compose.my.yml` / `.pg.yml` | 所有 `ruoyi-*` service名、container_name、network名、MYSQL_DATABASE/POSTGRES_DB 改为项目名；**image名必须全小写**（如 `newscms-frontend:latest`） |
| `ruoyi-fastapi-backend/.env.dockermy` / `.env.dockerpg` | `APP_NAME`、`LOG_SERVICE_NAME`、`DB_DATABASE`、`DB_PASSWORD`、`JWT_SECRET_KEY` |
| `ruoyi-fastapi-frontend/bin/nginx.dockermy.conf` / `nginx.dockerpg.conf` | `proxy_pass` 里的 `ruoyi-backend-my` / `ruoyi-backend-pg` 改为 `<project_name>-backend-my/pg`（文件内有 ⚠️ 注释提示） |

混合模式下 Docker 容器映射端口：MySQL → `127.0.0.1:13306`，Redis → `127.0.0.1:16379`，在 `.env.dev` 中对应填写。
