import { useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Button, Card, Descriptions, Drawer, Segmented, Table, Tag } from 'antd';
import { DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { getJson } from '../lib/api';
import { reportSchema, type Probe, type Report } from '../lib/contracts';
import { downloadCsv } from '../lib/csv';
import { ErrorNotice, Loading, PageTitle, StateTag } from '../components/Shared';
export default function Inspections() {
  const query = useQuery({ queryKey: ['sample-report'], queryFn: ({ signal }) => getJson('/samples/probe-report.json', reportSchema, signal), staleTime: Infinity });
  const [imported, setImported] = useState<Report | null>(null);
  const [filename, setFilename] = useState('仓库内的历史实验报告');
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('全部');
  const [selected, setSelected] = useState<Probe | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const report = imported || query.data;
  async function importFile(file?: File) {
    setError(''); if (!file) return;
    if (file.size > 1024 * 1024) { setError('文件超过 1 MB，请先缩小报告。'); return; }
    try {
      const result = reportSchema.safeParse(JSON.parse(await file.text()));
      if (!result.success) throw new Error('invalid');
      setImported(result.data); setFilename(file.name); setSelected(null);
    } catch { setError('报告格式不正确，请选择本项目 Python 巡检工具生成的 JSON 文件。'); }
  }
  const rows = report?.results.filter(row => filter === '全部' || (filter === '仅异常' && row.state !== 'OK')) || [];
  return <><PageTitle title="巡检报告" subtitle="回看逐次 HTTP / TCP 探测，定位失败原因。这里展示历史采样，不代表当前在线状态。" action={<Button icon={<UploadOutlined />} onClick={() => input.current?.click()}>导入报告</Button>} />
    <input ref={input} className="visually-hidden" type="file" accept=".json,application/json" aria-label="选择巡检 JSON 文件" onChange={e => { void importFile(e.target.files?.[0]); e.target.value = ''; }} />
    {error && <Alert type="error" showIcon title={error} />}
    {query.isError && !imported && <ErrorNotice error={query.error} retry={() => void query.refetch()} />}
    {!report && query.isPending ? <Loading /> : report && <><div className="report-meta"><Tag color="gold">历史报告</Tag><span>来源：{filename}</span><span>采样时间：{new Date(report.generated_at_utc).toLocaleString('zh-CN')}</span>{imported && <Button size="small" onClick={() => { setImported(null); setFilename('仓库内的历史实验报告'); }}>恢复示例</Button>}</div>
    <div className="report-stats"><Card><span>探测目标</span><b>{report.results.length}</b></Card><Card><span>全部采样成功</span><b className="success">{report.results.filter(v => v.state === 'OK').length}</b></Card><Card><span>含失败采样</span><b className="danger">{report.results.filter(v => v.state !== 'OK').length}</b></Card></div>
    <Card><div className="table-toolbar"><Segmented value={filter} onChange={v => setFilter(String(v))} options={['全部', '仅异常']} aria-label="巡检结果筛选" /><Button icon={<DownloadOutlined />} onClick={() => downloadCsv('inspection-filtered.csv', [['目标', '协议', '状态', '尝试', '成功', '请求失败比例'], ...rows.map(v => [v.name, v.kind, v.state, v.attempts, v.successes, v.request_failure_ratio])])}>导出筛选结果</Button></div><Table<Probe> rowKey={row => `${row.kind}:${row.name}:${row.target}`} dataSource={rows} pagination={{ pageSize: 10, hideOnSinglePage: true }} scroll={{ x: 760 }} columns={[
      { title: '探测目标', dataIndex: 'name', render: (name, row) => <Button type="link" className="asset-link" onClick={() => setSelected(row)}>{name}</Button> },
      { title: '协议', dataIndex: 'kind', render: v => <Tag>{String(v).toUpperCase()}</Tag> },
      { title: '检查结果', dataIndex: 'state', render: v => <StateTag ok={v === 'OK'} /> },
      { title: '成功 / 尝试', render: (_, row) => `${row.successes} / ${row.attempts}` },
      { title: '请求失败比例', dataIndex: 'request_failure_ratio', render: v => `${(Number(v) * 100).toFixed(0)}%` },
    ]} /></Card><p className="updated">{report.note || '报告由用户导入。'} 本地导入仅在当前页面会话解析，文件不会上传服务器。</p></>}
    <Drawer title="逐次采样详情" open={!!selected} onClose={() => setSelected(null)} size="large">{selected && <><Descriptions column={1} items={[{ key: 'name', label: '目标名称', children: selected.name }, { key: 'target', label: '探测地址', children: <span className="break-all">{selected.target}</span> }, { key: 'protocol', label: '协议', children: selected.kind.toUpperCase() }]} /><Table dataSource={selected.samples.map((sample, index) => ({ ...sample, key: index, attempt: index + 1 }))} size="small" pagination={false} columns={[{ title: '次数', dataIndex: 'attempt' }, { title: '结果', dataIndex: 'ok', render: ok => <StateTag ok={ok} /> }, { title: 'HTTP', dataIndex: 'http_status', render: value => value ?? '—' }, { title: '耗时 (ms)', dataIndex: 'latency_ms' }, { title: '原因', dataIndex: 'reason' }]} /><p className="updated">请求失败比例不能解释为 ICMP 丢包率，也不能外推全年可用率。</p></>}</Drawer></>;
}
