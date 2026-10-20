# A股热点雷达 · Stock Hotspot Radar

FastAPI + React / TypeScript + SQLite 的个人行情观察台。当前所有行情均为**模拟数据**，页面明确标注，不代表实时行情，不构成投资建议。

支持热点板块排行、板块领涨股、自选股增删和持久化、北京时间更新提示。真实行情可实现 `backend/app/market.py` 中的 `MarketProvider.snapshot()` 并注入 `create_app(provider=...)`。

## 推荐在线方案：Render 单个付费 Web Service + 持久磁盘

前后端打包为一个 Docker 服务：FastAPI 同时提供 React 构建文件和 `/api`，同一个 HTTPS 域名。无需单独购买数据库或配置跨域。

| 方案 | 费用估算 | SQLite 持久化 | 配置难度 |
| --- | --- | --- | --- |
| Render 付费 Web Service + 磁盘（推荐） | Starter 约 US$7/月，1 GB 磁盘约 US$0.25/月，另可能有税费/超额用量 | 将磁盘挂载到 `/var/data` | 低，GitHub 私有仓库集成及托管 HTTPS |
| Railway 服务 + Volume | 通常从约 US$5/月套餐起，计算与存储按用量，可能超出包含额度 | 必须挂载 Volume | 较低，费用随使用变化 |
| 自管 VPS | 常见约 US$5–10/月起，备份/域名可能另计 | 云主机磁盘及独立备份 | 高，需管理 HTTPS、系统补丁及防火墙 |

以上为预算参考，当前环境无法访问官方页面核实最新价格，请以购买页面为准。官方资料：<https://render.com/pricing>、<https://render.com/docs/disks>、<https://docs.railway.com/reference/pricing/plans>。

不推荐无持久磁盘的免费实例，也不适合把此 SQLite 文件放到会随发布重置的文件系统。当前必须单实例、单 worker；磁盘方案更新时可能短暂中断。暂未执行任何外部部署。

## 访问保护

- 所有页面、JS/CSS 静态资源、API、健康检查和接口文档入口统一经过服务器端 HTTP Basic 身份校验；没有公开业务接口，没有注册入口。
- 首次打开网站，浏览器弹出用户名/密码输入框。只有知道站点唯一账号密码的人能使用。建议使用密码管理器生成至少 24 字符随机密码；程序最低要求 16 字符。
- 凭据仅通过环境变量读取，没有默认账号密码；缺少配置会拒绝启动。测试密码每次随机生成，不是真实凭据。
- 正式访问必须使用平台提供的 HTTPS。Basic 认证是编码而非加密，依赖 TLS；不要在 URL 中拼接用户名密码，不把 Authorization 请求头写入日志。
- 浏览器会缓存 Basic 凭据；此版本没有自定义登录页面、退出按钮或 MFA。推荐在个人电脑的独立隐私窗口使用，用完关闭全部隐私窗口。改密码并重新部署可使旧密码失效。
- 写操作校验 Origin，拒绝跨站或缺失来源的请求；响应禁止缓存、嵌入和外部脚本。每个进程一分钟最多允许 20 次错误密码尝试，之后临时返回 429。限流保存在内存，重启会重置；它不是平台级防攻击服务。

## 部署前需要在 Render 设置的环境变量

| 名称 | 配置方式 |
| --- | --- |
| `RADAR_USERNAME` | 你选择的唯一用户名，不能包含冒号 |
| `RADAR_PASSWORD` | 在平台 Secret/环境变量编辑器输入随机长密码，不要在聊天或 Git 提交中填写 |
| `RADAR_ORIGIN` | 平台分配的正式源地址，例如 `https://你的服务名.onrender.com`，无路径；修改域名后同步修改 |
| `RADAR_DB_PATH` | `/var/data/radar.sqlite3`（镜像默认值） |
| `RADAR_STATIC_DIR` | `/app/static`（镜像默认值） |

当前模拟行情不需要任何行情 API 密钥。未来密钥同样只在平台环境变量中设置，不要使用会暴露给浏览器的 `VITE_` 变量保存密钥。

## 由你操作的 Render 部署步骤（会产生费用，尚未执行）

1. 注册/登录 Render，连接 GitHub，仅授权私有仓库 `tinybee009/stock-hotspot-radar`；保持 GitHub 仓库 Private。
2. 新建 Web Service，选择该仓库和开发分支 `feat/stock-hotspot-radar-v1`。使用 Docker，仓库根目录为构建上下文，Dockerfile 路径为 `./Dockerfile`，选择可挂载磁盘的付费规格，实例数为 1。
3. 在首次启动之前添加持久磁盘：挂载路径 `/var/data`，初始容量 1 GB。设置上表环境变量。不要选择临时目录。平台若先显示源地址，用它填写 `RADAR_ORIGIN`；不确定时先不触发创建/部署。
4. 关闭自动部署，后续由你手动确认更新。启动命令使用 Dockerfile 默认值：一个 Uvicorn worker，监听平台 `PORT`。
5. 健康检查使用平台默认 TCP 检查，不配置未经认证的 HTTP `/api/health` 检查，因为该接口也需要登录。若平台界面不支持 TCP 检查，请先确认该平台的健康检查认证能力，不要移除业务认证来绕过检查。
6. 核对月费、磁盘、环境变量后，再点击创建/部署。此步骤才会创建外部可访问地址；没有登录不能读取页面或业务数据。
7. 部署成功后访问平台提供的 **HTTPS** 地址，在浏览器提示中输入你设置的账号密码。验证模拟数据标签、添加自选并刷新、删除自选。
8. 验证一次更新：保留一只自选股，手动重新部署同一个服务、保留同一块磁盘，然后确认该自选股仍在。未经这一步不能宣称云端持久化已验证。

## 数据持久化与备份

SQLite 仅保存自选股票代码和名称，不保存登录密码。程序只会 `CREATE TABLE IF NOT EXISTS`，不会在启动时删除或初始化已有列表。更新镜像不会覆盖挂载磁盘。

必须持续保留**同一服务及同一持久磁盘**。删除服务/磁盘、换挂载路径或换平台都可能丢失数据；磁盘持久化不等于备份。建议定期在平台私有 Shell 使用 SQLite 在线备份 API 生成一致性备份，再下载到你控制的私有位置：

```bash
python - <<'PY'
import os
import sqlite3
from datetime import datetime, timezone
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
with sqlite3.connect(os.environ['RADAR_DB_PATH']) as source:
    with sqlite3.connect('/var/data/radar-backup-' + stamp + '.sqlite3') as target:
        source.backup(target)
PY
```

同盘备份不能抵御磁盘删除，务必保留盘外副本。恢复前停止服务，备份当前文件，再用已验证的备份替换数据库，启动后检查自选。不要把备份上传 GitHub。

## 开发与测试

Python 3.12、Node.js 22+。从仓库根目录执行：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci --cache /tmp/stock-radar-npm-cache
npm run build
cd ../backend
../.venv/bin/python -m pytest -q
```

测试覆盖认证拦截（页面/静态资源/API）、错误密码限流、来源检查、缺少凭据拒绝启动、行情排序、自选去重/删除及重建应用后的数据保留。已通过 7 项核心测试、前端类型检查和构建，并验证实际进程重启后的 SQLite 持久化。当前云环境的 Docker 容器无法解析依赖站点域名，完整镜像构建未通过验证；需在有正常构建网络的平台复核。浏览器 UI 自动化、正式 HTTPS 登录及真实云端发布/挂载磁盘尚未验证。

生产使用 Dockerfile 构建镜像；本地调试也需要配置认证环境变量，并用受控 HTTPS 代理提供与 `RADAR_ORIGIN` 一致的入口。旧版本的无认证 Vite 开发页面不应作为部署入口，禁止将 Vite dev/preview 暴露到公网。

API：`GET /api/health`、`GET /api/market`、`GET /api/watchlist`、`POST /api/watchlist`（请求体 `{"code":"002230"}`）、`DELETE /api/watchlist/{code}`，均需认证。非浏览器写请求还须携带与 `RADAR_ORIGIN` 一致的 `Origin` 请求头。模拟版本只支持页面中的八只股票。

代码存于 GitHub 私有开发分支，不要提交 `.env*`、数据库、依赖目录、备份或密钥。不会自动更改仓库可见性或启用公开部署。
