# Cloud Network Ops Lab

**云网运维个人实验项目集：网络方案、云应用监控、Python巡检。**

[![verify-lab](https://github.com/m25king/cloud-network-ops-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/m25king/cloud-network-ops-lab/actions/workflows/verify.yml)

面向云网运维、信息通信与系统运行维护方向。可用于学习、复现实验和讲解设计取舍。非中国电信或南方电网生产项目，无内部资料、真实资产清单或商业数据。

## 从这里开始

第一次动手请看[分步开工指南：两台交换机、两台PC](START_HERE.md)，先在eNSP跑通一个最小网络，再做下面三个完整模块。

| 模块 | 交付内容 | 当前证据 |
|---|---|---|
| [园区网络](network/README.md) | 10台设备参考配置、5个业务/管理VLAN、双核心、2个分支、8份演练方案 | S5700/S3700最小VLAN通信已实测；完整园区方案及切换待验证 |
| [云应用部署](cloud/README.md) | Nginx双应用实例、MySQL、Prometheus、Grafana、Blackbox、告警、备份恢复脚本 | 本机SQLite及GitHub Linux完整Compose验收通过；见下方运行记录 |
| [Python巡检](automation/README.md) | HTTP/TCP清单巡检、CSV/HTML报告、可选华为SSH采集及配置差异 | 本机真实请求测试；VRP合成样本解析；SSH待验证 |

```sh
python scripts/verify.py
python cloud/app.py
```

需要Python 3.11+。第一条执行测试并重新生成evidence；第二条启动本机只读演示，访问 http://127.0.0.1:8081/ 。Windows也可以双击根目录的`start-local.cmd`，自动打开网页；保持运行窗口开启，按Ctrl+C停止。本机方式只使用Python和SQLite。另开终端：

```sh
python automation/probe.py --inventory automation/inventory.example.csv --live --out artifacts/inspection
```

查看[实测范围及结果](evidence/verification.json)、[测试原始输出](evidence/test-output.txt)、[本机巡检报告](evidence/local-probe/report.html)。GitHub网页会展示HTML源文件；下载后用浏览器打开。这些报告来自本机临时服务，不是网络设备运行截图。

另有[本机部署与数据库故障恢复记录](evidence/local-deployment/README.md)：针对持续运行的SQLite演示服务，记录正常、查询故障和恢复三种状态，并保留实际HTTP/TCP巡检结果。

[eNSP最小VLAN实测](evidence/ensp-vlan10/README.md)保留实际型号、命令与探测结果：CORE1到两台PC、ACC1到CORE1的3组ICMP检查均收到全部3个响应。测试范围及尚未完成的验收项目均在记录中标明。

## 阅读导航

- [架构与关键取舍](docs/architecture.md)：哪些故障受保护，哪些仍会中断。
- [验收清单](docs/acceptance.md)：什么证据齐备后能写哪些简历表述。
- [巡检、变更与回退](docs/operations.md)：操作前后如何保留证据。
- [面试技术追问](docs/interview.md)：从原理、实现、验证、局限回答。
- [官方参考资料](docs/references.md)：协议和工具依据，不包含面试真题承诺。

## 工程状态

本仓库是AI辅助生成、经过本机和GitHub Linux环境验证的个人实验材料。使用者需要亲自执行、修改并理解后，才能在简历中陈述自己的实现和故障处理经验。没有伪造项目时间、提交历史、运行截图、丢包率或企业落地经历。

### 2026-09-09 实际验收

[通过的GitHub Actions运行记录](https://github.com/m25king/cloud-network-ops-lab/actions/runs/34333935389)，对应代码提交`c624ef3f22b3a8a812dfb6ee5725a8071629327f`：

- 22项Python自动化测试通过；完整Compose栈在临时Ubuntu运行器启动。
- Nginx配置、Prometheus配置及7条告警规则通过语法检查。Grafana健康接口、MySQL模拟资产查询通过。
- 停止一个应用实例后入口恢复可用，应用实例告警触发并在启动后消退。
- 停止数据库后业务就绪返回503，进程存活仍返回200；数据库和入口业务告警触发，并在数据库启动后消退。
- 停止Nginx后入口业务告警触发，启动后就绪检查和告警恢复。
- MySQL逻辑备份完成，校验SHA-256后恢复到新建独立库；3条合成资产与源库逐行比对一致。

验收中发现并修复了两个实际问题：上传包遗漏`nginx.conf`；将应用503列为Nginx上游重试条件会把共享数据库故障误判为实例故障，影响进程检查。现在保留应用503，仅对连接错误、超时及502/504尝试其他实例。语义依据见[Nginx官方说明](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream)。

这是临时CI环境的实际部署验收，运行结束会清理容器；GitHub仓库不是持续在线的业务服务。本机持续演示使用Python/SQLite。没有验证完整10设备园区切换、真实设备SSH、宿主机资源告警或外部通知送达，也没有性能压测、全年可用率或面试通过结论。早期`evidence/verification.json`保留当时本机验证边界，后续进展以上述记录为准。

未实跑功能不会放“已完成”徽章。个人联系方式、成绩、求职简历和备份文件不属于此公开项目仓库。
