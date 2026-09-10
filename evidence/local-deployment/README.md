# 本机部署与数据库查询故障恢复

环境：Windows、Python、SQLite，只监听127.0.0.1:8081。3条资产数据由程序生成，均为实验数据。

2026-09-08实际启动服务后，将SQLite中的assets表临时重命名为assets_drill_paused，使真实查询失败，再恢复原表名。操作前通过SQLite backup接口保留本地备份，恢复放在finally中执行。备份数据库不公开。

| 状态 | /healthz | /readyz | lab_db_up |
|---|---|---|---|
| 正常 | 200 | 200 | 1 |
| 数据库查询故障 | 200 | 503 | 0 |
| 恢复 | 200 | 200 | 1 |

原始结果见[drill.json](drill.json)。[故障巡检](fault-inspection/report.json)中HTTP检查失败、TCP仍可连接；[恢复巡检](healthy-inspection/report.json)中两项均恢复正常。HTML和CSV版本保存在相同目录，HTML下载后打开。

这些结果说明：进程存活、TCP端口可连接，并不代表应用依赖健康。/healthz检查进程，/readyz通过实际数据库查询判断能否提供服务。

本次是短时功能验证，不能据此声称故障恢复时延、生产可用性或性能指标。没有运行Docker、MySQL、Prometheus、Grafana或华为设备。这组历史结果不会在新启动的演示实例中被冒充为当前实例的实测记录。
