# A股热点雷达 · Stock Hotspot Radar

首个可运行版本：Python FastAPI + React / TypeScript + SQLite。界面为简体中文，明显标注“模拟数据”。所有股票价格和涨幅都是虚构示例，不是实时行情，不构成投资建议。

## 功能

- 热点板块按涨幅排序，点击板块查看领涨股。
- 从领涨股列表或输入六位股票代码添加自选，支持删除；SQLite 保存，刷新页面或重启后端仍保留。
- 显示本次模拟快照的生成时间（北京时间）；点击“刷新数据”重新获取，模拟价格固定。
- 提供加载、失败重试、重复添加保护和窄屏布局。

## 本地启动

需要 Python 3.12+、Node.js 22+。在仓库根目录执行：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci --cache /tmp/stock-radar-npm-cache
cd ..
```

两个终端分别运行：

```bash
# 终端一：从仓库根目录进入后端
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# 终端二：从仓库根目录进入前端
cd frontend
npm run dev -- --host 127.0.0.1
```

在你自己的电脑浏览器访问 `http://127.0.0.1:5173`。后端接口文档在 `http://127.0.0.1:8000/docs`。Vite 将 `/api` 代理到本机 8000 端口，无需配置 CORS。云环境内的回环地址不等于电脑上的地址；在电脑克隆仓库启动，或使用受控的 SSH 端口转发查看，不需要公开部署。开发服务器仅供开发使用。

默认数据库为后端工作目录下的 `data/radar.sqlite3`，不纳入 Git。可通过 `RADAR_DB_PATH` 指定持久化文件路径。删除数据库会清空自选。当前无登录，所有访问同一实例的用户共享自选列表；请仅在私有开发环境使用。

## 测试和构建

```bash
cd backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run build
```

核心测试覆盖行情结构及排序、自选添加、去重、重新创建应用后的持久化、删除及无效代码。前端构建包含 TypeScript 严格检查；尚未配置浏览器自动化测试。

## API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务及数据库检查 |
| GET | `/api/market` | 模拟板块、领涨股、来源与更新时间 |
| GET | `/api/watchlist` | 自选股列表 |
| POST | `/api/watchlist` | `{"code":"002230"}` 添加；重复请求不重复保存 |
| DELETE | `/api/watchlist/{code}` | 删除自选股 |

模拟版本仅接受行情列表中已有的八只股票；未知代码返回 404，无效格式返回 422。添加成功返回 201，删除返回 204。

## 接入真实行情

`backend/app/market.py` 定义 `MarketProvider` 协议。实现 `snapshot()` 返回同样的 `source`、ISO 时间 `updated_at` 及 `sectors` 结构，再通过 `create_app(provider=...)` 注入。真实接入时需处理交易时段、超时、限流、缓存和行情源授权，并将时间设置为行情实际更新时间。密钥通过环境设置注入，不提交到仓库；前端的模拟标签也需要随数据来源调整，当前版本始终使用模拟提供器。

## 保存到私有 GitHub 仓库

本次实现保留在工作区，未自动提交或推送。检查后在仓库根目录执行：

```bash
git status
git add .gitignore README.md backend frontend
git commit -m "feat: add runnable mock stock hotspot radar"
git push origin HEAD:main
```

如 main 受保护，请推送到功能分支后创建 PR。继续使用现有私有仓库，不更改可见性，不启用 Pages 或公开部署。不需要提交 `.venv`、`node_modules`、数据库或任何密钥。
