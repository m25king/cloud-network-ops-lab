# Python自动巡检与设备配置差异检查

两个可独立使用的入口：HTTP/TCP服务巡检不需要额外依赖；华为SSH采集需要Netmiko、设备SSH服务、已验证的主机密钥和实验账号。默认不执行任何设备配置更改。

## HTTP/TCP巡检

先在一个终端运行python cloud/app.py，再在仓库根目录执行：

```sh
python automation/probe.py --inventory automation/inventory.example.csv --live --out artifacts/inspection
```

输出JSON、CSV和可浏览HTML。每目标默认请求3次、单次套接字超时2秒、最多4个并发任务；上限为256目标、8并发、每目标10次请求。超时约束不等同严格端到端deadline：系统DNS解析耗时可能不受socket超时完整覆盖。三次请求默认连续发生，不是按秒采样的可用性监控。

结果区分OK、DEGRADED和FAILED；非全通过退出码1，便于后续作业判断。HTTP支持预期状态码、拒绝自动重定向；TCP仅证明握手成功，不证明SSH认证或业务可用。JSON保留每次请求的原因和耗时；请求失败比例不是ICMP丢包率，不能写成“测量网络丢包”。

CSV/HTML对输入作展示转义。凭据不放进URL。真实目标只来自明确指定的清单；程序没有扫描网段功能。

## SSH采集与差异

网络基础配置没有默认账号。先通过设备本地控制台配置专用实验SSH账号、VTY仅SSH、管理来源ACL，并在你使用的VRP版本上验证。核对设备主机密钥指纹后建立known_hosts文件；不得简单把未知密钥自动信任。

```sh
python -m pip install -r automation/requirements-ssh.txt
python automation/collect_ssh.py --inventory automation/ssh-inventory.example.json --known-hosts 本地已核验的known_hosts文件
```

先在本地设置LAB_SSH_USER、LAB_SSH_PASSWORD环境变量；不把值写进脚本或截图。本次未实连SSH设备，不能声称完成批量设备巡检部署。

适配器采集display version、display ip interface brief、display ip routing-table、display current-configuration；Netmiko可能为读取完整输出执行终端分页设置。不会调用send_config_set或改变业务配置。

接口解析只支持fixtures示例表格。expected_up列出实际应该UP的接口，未使用端口DOWN不自动报警；缺少预期接口或未知格式均不算通过。版本与路由保留为文本，未实现CPU/内存或路由策略的自动语义判断。

配置逐行屏蔽常见凭据后生成差异；屏蔽是辅助措施，不能保证所有厂商密钥格式都覆盖。artifacts全目录默认不提交，公开任何现场输出前仍需人工检查资产地址、账号与商业数据。只保存最新配置和上一次差异，尚无加密历史版本库。

## 复现实验与追问

1. 正常启动应用：HTTP/TCP均成功。
2. 停止应用：握手/HTTP连接失败，保存失败报告。
3. /readyz依赖失败但/healthz成功：说明检测层次不同；项目测试通过临时本地服务复现此场景。
4. 修改CSV预期状态码为201：HTTP检查应失败，即使端口可达。
5. 执行测试套件，覆盖HTML注入转义、未知VRP格式、缺少接口和配置秘密屏蔽。

规则分类和固定阈值属于自动化运维，未使用训练模型、LLM根因诊断或自动修复。后续智能化扩展需要标注数据、基线比较、误报统计和人工处置入口，不能把脚本包装成AI模型项目。
