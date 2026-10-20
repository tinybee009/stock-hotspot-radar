# A股热点雷达 · Stock Hotspot Radar

FastAPI + React / TypeScript 的个人行情观察台，支持热点板块排行、领涨股、自选股增删及更新时间。当前价格与涨幅均为**模拟数据**，不代表实时行情，不构成投资建议。

## 免费在线方案

**Render 免费 Web Service + Turso 免费数据库**。FastAPI 在同一个 HTTPS 网址提供编译后的 React 页面和业务接口，Turso 独立保存自选股。GitHub 仓库保持私有，不需要在自己的电脑运行。

- Render 选择 **Free**，不添加付费磁盘。免费实例可能休眠，第一次打开会等待冷启动；额度及可用性以注册时的官方页面为准。
- Turso 选择当时提供的免费套餐，数据使用独立数据库保存。不要升级付费套餐或启用自动付费；如果控制台不再提供免费选项，先停止创建。
- 免费不等于无限量或永久保证。达到额度、令牌失效或数据库暂停时，程序返回错误，**不会退回临时 SQLite 保存数据**。
- 免费服务的本地文件可能随发布丢失，因此线上镜像默认 `RADAR_STORAGE=turso`，不使用本地磁盘保存自选。
- 尚未部署外部网站。官方套餐信息请在 <https://render.com/pricing> 和 <https://turso.tech/pricing> 核对，当前环境未能在线核实最新免费额度。

## 第一步：在 Turso 创建数据库（仅需网页）

进入你的组织控制台，例如 <https://app.turso.tech/bobchen>。组织页面链接不是数据库连接地址。

1. 在 Databases 页面选择创建数据库（界面可能显示 Create Database / New Database）。名称可用 `stock-hotspot-radar`，选择免费套餐支持的区域。
2. 打开数据库详情，在连接信息中找到 **Database URL**，一般类似 `libsql://数据库名-组织名.turso.io`。此地址不含密码，可以单独提供用于配置检查。
3. 在该数据库的连接/令牌区域生成 **数据库 Auth Token**。应用需要建表和读写权限；不要使用只能读的令牌，也不需要组织管理员 API 令牌。
4. 将令牌暂存在自己的密码管理器，随后直接填入 Render 的 Secret 环境变量 `TURSO_AUTH_TOKEN`。不要发到聊天、粘贴到源码或上传 GitHub。
5. 不用手工创建表，应用首次成功连接后会执行 `CREATE TABLE IF NOT EXISTS`，不会删除已有列表。选择有明确有效期的令牌时，记录到期时间并提前轮换。

## 第二步：准备 Render 服务（创建前先核对配置）

注册/登录 Render，通过 GitHub 授权只允许访问私有仓库 `tinybee009/stock-hotspot-radar`。新建 Web Service：

| 项目 | 配置 |
| --- | --- |
| Repository | `tinybee009/stock-hotspot-radar` |
| Branch | `feat/stock-hotspot-radar-v1` |
| Runtime | Docker |
| Dockerfile | 仓库根目录的 `./Dockerfile` |
| Instance Type | **Free** |
| Persistent Disk | **不添加** |
| Auto Deploy | 关闭，后续由你手动确认更新 |
| Instances / Workers | 1 / 1（Dockerfile 已指定） |
| Start Command | 使用 Dockerfile 默认值，不要运行 Vite 开发服务器 |
| Health Check | 默认 TCP 检查；不要添加无需登录的业务健康检查 |

环境变量如下，密码和令牌仅在平台设置中输入，不提交到 Git：

| 名称 | 值/说明 |
| --- | --- |
| `RADAR_STORAGE` | `turso`（镜像默认值） |
| `TURSO_DATABASE_URL` | 从 Turso 复制的数据库 URL，支持 `libsql://` 或 `https://`，域名为 `*.turso.io` |
| `TURSO_AUTH_TOKEN` | 该数据库的读写令牌，设为 Secret |
| `RADAR_USERNAME` | 你选择的唯一用户名，不包含冒号 |
| `RADAR_PASSWORD` | 密码管理器生成的随机长密码，建议至少24字符，程序最低要求16字符，设为 Secret |
| `RADAR_ORIGIN` | 最终站点源地址，如 `https://你的服务名.onrender.com`，不要包含路径 |

Render 若在创建后才分配网址，可先将 `RADAR_ORIGIN` 留空：程序会拒绝启动，而不会开放无认证页面。取得最终网址后补齐变量，再手动部署。所有必要配置正确后，只有在你决定上线时才点击创建/部署；这一步会产生外部网址。若页面要求购买服务或不提供 Free，请停止，不要选择付费替代。

平台若要求 HTTP 健康检查成功而不能使用 TCP，请先确认其认证检查能力；不要为健康检查移除业务认证。

## 登录保护与上线验证

- 浏览器首次打开 HTTPS 网址会弹出账号密码框，只有站点唯一账号可用，没有注册入口。页面、JS/CSS、业务 API 及文档入口全部经过身份校验。
- 仅通过 HTTPS 使用。Basic 认证本身是编码，不是加密；不要把凭据写在 URL 中，也不要记录 Authorization 请求头。
- 浏览器缓存 Basic 凭据，没有自定义退出按钮或 MFA。建议通过独立隐私窗口使用，用完关闭全部隐私窗口；更换密码并重新部署会使旧密码失效。
- 缺少凭据会拒绝启动；写请求校验 Origin；响应禁止缓存、嵌入和外部脚本。每进程每分钟20次错误密码后临时限流，重启会重置。
- 发布后先用新隐私窗口确认未登录无法读取页面；登录后确认模拟标签、切换板块、自选添加和删除。
- 添加一只自选股后，保留同一个 Turso 数据库，手动更新/重启 Render，确认自选仍在。只有完成这一步，才算验证实际云端持久化。

## 持久化、备份及迁移

更新镜像、重启或更换 Render 实例不会重置独立的 Turso 数据库。但**删除 Turso 数据库、换数据库 URL 或账户问题仍可能丢失访问或数据**。不要在每次发布时创建新数据库。

在 Turso 控制台查看当前免费套餐可用的备份/导出功能，定期导出 SQL 并保存在你控制的私有位置；不要假定免费套餐包含自动备份，不要把备份提交 GitHub。旧版本本地 SQLite 的自选不会自动复制到 Turso；当前仅有代码测试数据。若已有个人数据，迁移前先备份并另外安排导入。

## 实现与开发测试

`backend/app/storage.py` 封装存储：`RADAR_STORAGE=sqlite` 用于本地测试，`turso` 通过 HTTPS `/v2/pipeline` 使用参数化 SQL、认证令牌和请求超时。上游错误转换为不包含令牌或响应正文的 503；不会把失败读写当作成功。

Python 3.12、Node.js 22+，从仓库根目录执行（仅供开发者，不要求使用者本机运行）：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci --cache /tmp/stock-radar-npm-cache
npm run build
cd ../backend
../.venv/bin/python -m pytest -q
```

测试包含登录隔离、来源校验、缺少配置拒绝启动、本地持久化、Turso HTTP 协议模拟、参数绑定与去重、跨存储实例持久化、网络/SQL/认证错误脱敏、禁止临时文件回退。

**验证边界：**Turso 测试使用模拟 HTTP 传输和独立 SQLite 文件，不等同于真实 Turso 连通验证。真实数据库、正式 HTTPS 登录、Render 更新后的数据保存仍需配置后验证。此前 Docker 构建受当前云环境容器 DNS 故障阻塞；前端构建和 Python 测试可以在当前机器执行。

行情接入边界在 `backend/app/market.py` 的 `MarketProvider.snapshot()`。行情 API 密钥只能通过服务端环境变量注入，不能放进 `VITE_` 前端变量。

所有 API 均需认证：`GET /api/health`、`GET /api/market`、`GET /api/watchlist`、`POST /api/watchlist`（`{"code":"002230"}`）、`DELETE /api/watchlist/{code}`。非浏览器写操作还须携带与 `RADAR_ORIGIN` 相同的 Origin 请求头。模拟版本只支持页面列出的八只股票。
