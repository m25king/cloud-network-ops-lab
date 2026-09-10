# 从这里开始：先做通一个最小网络

项目代码和参考配置已经准备好。接下来按“亲手搭建→验证结果→制造故障→定位恢复→保存证据”推进。先用现有eNSP完成这一课，再扩展到完整网络。

## 三个项目的顺序

| 顺序 | 你要做什么 | 完成后展示什么 |
|---|---|---|
| 1 园区网络 | 先跑通本课，再扩展到双核心、分支、OSPF、VRRP/MSTP、ACL与故障演练 | 自己保存的拓扑、运行配置、通信测试和故障记录 |
| 2 云应用部署 | 先跑本机Python程序，再按cloud/README.md部署完整Docker环境并测试故障和恢复 | 业务页面、监控、告警和备份恢复结果 |
| 3 自动巡检 | 读懂并运行automation/probe.py，修改清单、判断失败原因；最后再做SSH扩展 | 正常/失败报告和自己修改过的代码 |

## 今天的目标

让接在不同交换机上的两台PC通过VLAN10通信，再改变端口所属VLAN，观察为什么通信失败。只使用2台交换机和2台PC，预计45—90分钟，环境启动问题另计。

本课在一个新拓扑中执行，另存为learning-01-vlan.topo。它是完整网络之前的练习，不会自动生成最终10台设备的拓扑。不要把完整configs中的全部内容混入本课。

## 1. 放置并连接设备

在eNSP放置：S5700一台，命名CORE1；S3700一台，命名ACC1；PC两台，命名PC-A和PC-B。

| A端 | B端 |
|---|---|
| PC-A的以太网口 | ACC1 Ethernet0/0/1 |
| ACC1 GigabitEthernet0/0/1 | CORE1 GigabitEthernet0/0/1 |
| CORE1 GigabitEthernet0/0/4 | PC-B的以太网口 |

先启动两台交换机，等待启动完成。双击设备进入命令行，执行display interface brief核对端口。若你的镜像端口名称不同，先按实际端口修正接线和命令。

## 2. 配置CORE1

在CORE1命令行逐段输入：

```text
system-view
sysname CORE1
vlan 10
quit
interface GigabitEthernet0/0/1
 port link-type trunk
 port trunk allow-pass vlan 10
quit
interface GigabitEthernet0/0/4
 port link-type access
 port default vlan 10
quit
return
```

连接另一台交换机的口设置为Trunk并允许VLAN10；连接PC-B的口设置为Access并加入VLAN10。不要把本课配置理解成整个园区已经完成。

## 3. 配置ACC1

在ACC1命令行逐段输入：

```text
system-view
sysname ACC1
vlan 10
quit
interface GigabitEthernet0/0/1
 port link-type trunk
 port trunk allow-pass vlan 10
quit
interface Ethernet0/0/1
 port link-type access
 port default vlan 10
quit
return
```

遇到报错先停在该命令，保留完整提示，不要连续粘贴剩下的所有命令。参考语法仍以当前VRP版本接受情况为准。

## 4. 给两台PC配置地址

双击PC，在基础配置中手工设置IPv4：

| PC | IPv4地址 | 子网掩码 | 默认网关 |
|---|---|---|---|
| PC-A | 192.168.10.11 | 255.255.255.0 | 留空；界面若保留0.0.0.0则保持 |
| PC-B | 192.168.10.12 | 255.255.255.0 | 留空；界面若保留0.0.0.0则保持 |

应用配置后，在PC-A命令行运行：

```text
ping 192.168.10.12
```

在PC-B反向测试192.168.10.11。第一次探测可能受ARP建立或端口收敛影响，等待后再测；不能把持续失败都解释成“第一次正常”。

不通时依次检查：设备是否启动→连线端口是否UP→两PC地址/掩码→Access所属VLAN→Trunk是否允许VLAN10。

两台交换机上可查看：

```text
display interface brief
display vlan
display port vlan
display mac-address
```

## 5. 亲手制造并恢复一个故障

正常通信后，在ACC1把PC-A接入口改入VLAN20：

```text
system-view
vlan 20
quit
interface Ethernet0/0/1
 port default vlan 20
quit
return
```

PC地址保持原样，再从PC-A ping 192.168.10.12，预期无法通信。查看display port vlan证明PC-A已经进入不同的二层广播域；不是仅凭ping失败就认定根因。

恢复：

```text
system-view
interface Ethernet0/0/1
 port default vlan 10
quit
return
```

重复双向ping，确认通信恢复。在两台交换机用户视图执行save并按提示确认，随后在eNSP保存拓扑。保存设备配置和保存拓扑是两个动作。

## 6. 今天交付的证据

- 自己保存的learning-01-vlan.topo。
- 一张能看清设备名称、端口和IP的拓扑截图。
- 正常、故障、恢复后三种状态的ping结果。
- 两台交换机display current-configuration的导出文本。
- 一段自己的解释：两PC为什么不需要网关；Access和Trunk有什么区别；地址没改为什么更换VLAN后不通。

这些原始实操文件先保留在本地artifacts/lesson-01目录（Git默认忽略），核对内容后再整理公开证据。本课成功不等于OSPF、VRRP或Docker等后续模块已完成。

## 下一步

本课通过后，按network/README.md的接线表扩展正式拓扑。依次完成多VLAN与三层网关、DHCP、OSPF/默认路由/NAT、MSTP/VRRP、访客ACL，再逐份执行network/faults中的故障演练。每次增加一项功能，就增加对应的正向和失败测试。

GitHub的作用是让别人看到你的代码、配置和证据。先完成这一课，把截图和结果发回当前对话核对，再继续增加功能。
