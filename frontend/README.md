# 云网运维管理台

React 19、TypeScript、Vite、Ant Design、TanStack Query 与 Zod 实现的只读运维控制台。包含实时服务概览、资产查询、历史巡检报告和故障记录。

## 本机启动

需要 Node.js 24、pnpm 11.19.0 和 Python 3.11+。在仓库根目录启动后端：

```sh
python cloud/app.py
```

另开终端：

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

访问 http://127.0.0.1:5173 。开发代理默认连接 http://127.0.0.1:8081 ，可通过 API_TARGET 环境变量调整。数据库自动创建三条合成资产。

## 功能与数据来源

- 概览分别读取 `/healthz` 和 `/api/status`，每 10 秒刷新；依赖查询失败不显示为业务正常。
- 资产页调用 `/api/assets`，支持后端分页、名称搜索、分区筛选和白名单排序；筛选保存在 URL 中。
- 巡检页默认读取 `public/samples/probe-report.json` 的历史采样；可本地导入 Python 工具生成的报告。支持 OK、DEGRADED、FAILED，校验统计值与逐次采样一致，限制文件为 1 MB。导入不会上传服务器。
- 故障页读取 `/api/drill`；后端没有配置记录时显示空状态。启动后端前设置 LOCAL_DRILL_REPORT 为 `evidence/local-deployment/drill.json` 的绝对路径可加载已有历史记录。
- 导出仅包含当前资产页或当前筛选的巡检记录，CSV 对公式前缀做保护。

## 验证

```sh
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e
```

浏览器测试自动启动独立 SQLite 后端（18081）和构建预览（4174），需先执行 build。测试覆盖真实查询、刷新保留筛选、导出、无结果、报告格式错误、503 后重试与移动端布局。503 场景使用浏览器路由注入，其余资产请求使用实际后端。

## 容器部署

在 cloud 目录生成环境配置后执行：

```sh
python scripts/init_env.py
docker compose -f compose.yaml -f compose.frontend.yaml up -d --build --wait
```

访问 http://127.0.0.1:4174 。前端 Nginx 提供静态文件及 SPA 路由回退，并将 API 转发到原应用入口。此扩展的本机容器运行仍需验证。

## 当前范围

系统只读，不包含登录、RBAC、资产增删改、工单流转或后台报告归档。当前适合本机实验；对外服务前需明确认证与访问控制需求。故障记录是历史证据，登记资产不是实时在线设备清单。
