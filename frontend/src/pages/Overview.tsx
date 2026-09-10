import { useQuery } from '@tanstack/react-query';
import { Alert, Card, Tag, Button } from 'antd';
import { ArrowRightOutlined, CheckCircleOutlined, DatabaseOutlined, ApartmentOutlined, CloudServerOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { getJson } from '../lib/api';
import { processSchema, statusSchema } from '../lib/contracts';
import { ErrorNotice, PageTitle, Refresh } from '../components/Shared';
export default function Overview() {
  const process = useQuery({ queryKey: ['process'], queryFn: ({ signal }) => getJson('/healthz', processSchema, signal), refetchInterval: 10000 });
  const service = useQuery({ queryKey: ['service'], queryFn: ({ signal }) => getJson('/api/status', statusSchema, signal), refetchInterval: 10000 });
  const ready = !!service.data && !service.isError;
  const metrics = [
    { label: '应用进程', value: process.isPending ? '检测中' : process.isError ? '不可达' : '运行中', caption: '独立检查应用是否响应', icon: <CloudServerOutlined />, good: !process.isError },
    { label: '业务依赖', value: service.isPending ? '检测中' : ready ? '查询正常' : '查询异常', caption: '通过真实数据库查询确认', icon: <CheckCircleOutlined />, good: ready },
    { label: '登记资产', value: ready ? service.data.asset_count : '—', caption: '合成资产，不代表在线设备', icon: <ApartmentOutlined />, good: true },
    { label: '数据存储', value: ready ? service.data.driver === 'mysql' ? 'MySQL' : 'SQLite' : '—', caption: ready && service.data.driver === 'mysql' ? '当前连接容器数据库' : '当前环境以接口返回为准', icon: <DatabaseOutlined />, good: true },
  ];
  return <><PageTitle title="运行概览" subtitle="先确认服务现状，再查看资产与巡检证据。" action={<Refresh busy={service.isFetching || process.isFetching} onClick={() => { void service.refetch(); void process.refetch(); }} />} />
    {service.isError && <ErrorNotice error={service.error} retry={() => void service.refetch()} />}
    {process.isError && <ErrorNotice error={process.error} retry={() => void process.refetch()} />}
    <div className="metric-grid">{metrics.map(item => <Card key={item.label} className="metric"><div className="metric-label">{item.label}<span>{item.icon}</span></div><div className={'metric-value ' + (!item.good ? 'danger' : '')}>{item.value}</div><p>{item.caption}</p></Card>)}</div>
    <div className="overview-grid"><Card title="服务访问链路" extra={<Tag color="cyan">实时请求</Tag>}><div className="service-flow">{['浏览器工作台', 'Python 应用', ready ? service.data.driver.toUpperCase() : '数据库依赖'].map((name, i) => <div className="flow-part" key={name}><div className="flow-node"><span className="flow-number">0{i + 1}</span><b>{name}</b><span>{['展示与交互', '接口与健康检查', '查询合成资产'][i]}</span></div>{i < 2 && <ArrowRightOutlined className="flow-arrow" />}</div>)}</div><Alert type="info" showIcon title="进程存活不等于业务可用" description="数据库故障时，应用仍可能返回健康响应；业务就绪检查会返回 503。两个状态需要分别判断。" /></Card>
    <Card title="常用入口" className="quick-links"><Link to="/assets"><DatabaseOutlined /><div><b>查看资产目录</b><span>搜索、分区筛选与明细</span></div><ArrowRightOutlined /></Link><Link to="/inspections"><CheckCircleOutlined /><div><b>分析巡检报告</b><span>导入结果，检查失败采样</span></div><ArrowRightOutlined /></Link><Link to="/incidents"><ApartmentOutlined /><div><b>回看故障恢复</b><span>正常、故障与恢复时间线</span></div><ArrowRightOutlined /></Link></Card></div>
    <Card className="scope-card"><div><Tag>环境说明</Tag><span>本机演示与云端临时验收分别留有记录；此页面仅报告当前连接的后端状态。</span></div><Button type="link" href="https://github.com/m25king/cloud-network-ops-lab/actions" target="_blank" rel="noreferrer">查看云端验收 <ArrowRightOutlined /></Button></Card>
    <p className="updated">最近成功读取：{service.dataUpdatedAt ? new Date(service.dataUpdatedAt).toLocaleString('zh-CN') : '尚无成功结果'} · 每 10 秒更新，后台标签页暂停轮询</p></>;
}
