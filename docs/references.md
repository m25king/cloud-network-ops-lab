# 官方参考与适用范围

整理日期：2026-09-08。下面资料用于理解原理及工具行为；具体eNSP镜像、容器标签和招聘岗位需要分别核验。阅读官方资料不等于对应环境已运行成功。

1. [中国电信2027年度校园招聘公告](https://www.chinatelecom.com.cn/ct/zp/168256.html)：该轮网申从2026年8月24日开始，各单位具体岗位和资格分别确定。用户上次讨论的云网智能工程师为中国电信岗位背景。
2. [中国电信招聘平台](https://job.chinatelecom.com.cn/)：查询具体单位、岗位及截止时间。
3. [南方电网官方招聘平台](https://zhaopin.csg.cn/)：本次未获得用户拟投岗位的正式JD，页面动态内容也未能完整读取；不能据此声称已核实2027年某岗位的专业、分数或面试要求。
4. [华为S5700系列VRRP网关备份说明](https://support.huawei.com/enterprise/en/doc/EDOC1000178176/42622a3e/using-vrrp-to-implement-next-hop-gateway-backup)：理解网关备份及上联故障检测的作用。
5. [华为VRRP切换说明](https://info.support.huawei.com/enterprise/zh/doc/EDOC1100305532/96f5a1a0)：理解优先级、抢占和跟踪接口；文档平台不必然与实验镜像一致。
6. [Docker Compose启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)：依赖启动和依赖健康是不同概念，service_healthy可作为启动条件。
7. [Prometheus告警规则](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)：for对应持续满足条件的等待时间，规则进入firing后由告警组件处理通知。
8. [Nginx upstream模块](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)：理解upstream、失败重试和相关参数。请按所用版本核对resolve等选项。
9. [Python HTTP服务文档](https://docs.python.org/3/library/http.server.html)：理解本机测试服务器的用途和边界；Compose业务进程使用Gunicorn。

本项目的面试题是根据实现整理的练习题，不是南方电网内部题库或已验证真题。
