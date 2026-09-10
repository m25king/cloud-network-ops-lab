import { useQuery } from '@tanstack/react-query';
import { Alert, Card, Empty, Table, Tag, Timeline } from 'antd';
import { getJson } from '../lib/api';
import { drillSchema } from '../lib/contracts';
import { ErrorNotice, Loading, PageTitle, Refresh } from '../components/Shared';
export default function Incidents() {
  const query = useQuery({ queryKey: ['drill'], queryFn: ({ signal }) => getJson('/api/drill', drillSchema, signal) });
  const data = query.data;
  return <><PageTitle title="故障记录" subtitle="按实际保存的记录复盘正常、故障与恢复过程。" action={<Refresh busy={query.isFetching} onClick={() => void query.refetch()} />} />
    {query.isError ? <ErrorNotice error={query.error} retry={() => void query.refetch()} /> : query.isPending ? <Loading /> : data && !data.stages.length ? <Card><Empty description="当前后端未加载演练记录" /><p className="empty-hint">完成本机演练并为后端设置记录文件后，这里会展示真实时间线。页面不会自动生成成功记录。</p></Card> : data && <><Alert type="info" showIcon title="历史演练 · 本机 Python / SQLite" description="记录只证明当次实验中的请求结果。当前服务状态请回到运行概览查看。" /><div className="incident-grid"><Card title="演练时间线" extra={<Tag color={data.state === 'passed' ? 'success' : 'gold'}>{data.state === 'passed' ? '已执行并恢复' : '已记录'}</Tag>}><Timeline items={data.stages.map(stage => ({ color: stage.readyz === 200 ? '#126d72' : '#bd513e', title: stage.label, content: <><p>{new Date(stage.utc).toLocaleString('zh-CN')}</p><p>进程 {stage.healthz} · 业务 {stage.readyz} · 数据库指标 {stage.db_up}</p></> }))} /></Card><Card title="这次实验说明什么"><h3>健康检查需要分层</h3><p>进程响应正常，只能证明应用还能够处理请求。数据库查询失败时，业务就绪检查应明确返回异常。</p><h3>恢复需要重新检查</h3><p>修复操作完成后，要重新确认业务查询成功，并保留当次请求的时间与结果。</p><p className="muted">当前记录不证明高可用切换、生产 RTO 或端到端通知送达。</p></Card></div><Card title="原始状态对照"><Table rowKey="utc" pagination={false} dataSource={data.stages} scroll={{ x: 650 }} columns={[{ title: '阶段', dataIndex: 'label' }, { title: '时间', dataIndex: 'utc', render: v => new Date(v).toLocaleString('zh-CN') }, { title: '进程检查', dataIndex: 'healthz' }, { title: '业务就绪', dataIndex: 'readyz', render: v => <Tag color={v === 200 ? 'success' : 'error'}>{v}</Tag> }, { title: '数据库指标', dataIndex: 'db_up' }]} /></Card></>}
  </>;
}
