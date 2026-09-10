import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { Button, Card, Descriptions, Drawer, Empty, Input, Select, Space, Table, Tag } from 'antd';
import { DownloadOutlined, SearchOutlined } from '@ant-design/icons';
import { getJson } from '../lib/api';
import { assetsSchema, zoneLabels, type Asset } from '../lib/contracts';
import { downloadCsv } from '../lib/csv';
import { ErrorNotice, PageTitle, Refresh } from '../components/Shared';
export default function Assets() {
  const [params, setParams] = useSearchParams();
  const q = (params.get('q') || '').slice(0, 80);
  const rawZone = params.get('zone') || '';
  const zone = Object.hasOwn(zoneLabels, rawZone) ? rawZone : '';
  const page = Math.min(10000, Math.max(1, Math.floor(Number(params.get('page'))) || 1));
  const size = [2, 10, 20, 50].includes(Number(params.get('size'))) ? Number(params.get('size')) : 10;
  const sort = params.get('sort') === 'name' ? 'name' : 'id';
  const [draft, setDraft] = useState(q);
  const [selected, setSelected] = useState<Asset | null>(null);
  useEffect(() => { setDraft(q); }, [q]);
  useEffect(() => {
    if (draft === q) return;
    const timer = setTimeout(() => setParams(previous => { const next = new URLSearchParams(previous); next.set('q', draft); next.delete('page'); return next; }, { replace: true }), 300);
    return () => clearTimeout(timer);
  }, [draft, q, setParams]);
  function change(key: string, value: string) { setParams(previous => { const next = new URLSearchParams(previous); value ? next.set(key, value) : next.delete(key); if (key !== 'page') next.delete('page'); return next; }); }
  const query = useQuery({ queryKey: ['assets', { q, zone, page, size, sort }], queryFn: ({ signal }) => getJson('/api/assets?' + new URLSearchParams({ q, zone, page: String(page), page_size: String(size), sort }), assetsSchema, signal), placeholderData: keepPreviousData });
  const data = query.data;
  return <><PageTitle title="资产目录" subtitle="从数据库读取资产，按名称与分区查找。目录登记不代表设备实时在线。" action={<Refresh busy={query.isFetching} onClick={() => void query.refetch()} />} />
    <Card className="table-card"><div className="filter-bar"><div className="filter"><label htmlFor="asset-search">资产名称</label><Input id="asset-search" prefix={<SearchOutlined />} placeholder="搜索资产名称" allowClear maxLength={80} value={draft} onChange={e => setDraft(e.target.value)} /></div><div className="filter small-filter"><label htmlFor="zone-filter">所属分区</label><Select id="zone-filter" aria-label="所属分区" value={zone} onChange={v => change('zone', v)} options={[{ value: '', label: '全部分区' }, ...Object.entries(zoneLabels).map(([value, label]) => ({ value, label }))]} /></div><div className="filter small-filter"><label htmlFor="sort-filter">排序</label><Select id="sort-filter" aria-label="排序" value={sort} onChange={v => change('sort', v)} options={[{ value: 'id', label: '按资产编号' }, { value: 'name', label: '按名称' }]} /></div><Button onClick={() => { setDraft(''); setParams({}); }}>重置筛选</Button></div>
      <div className="table-toolbar"><span>{query.isFetching ? '正在读取最新结果…' : `共 ${data?.total ?? 0} 条资产`} <Tag>合成数据</Tag></span><Button icon={<DownloadOutlined />} disabled={!data?.items.length || query.isFetching || query.isError} onClick={() => downloadCsv('assets-current-page.csv', [['编号', '名称', '分区'], ...(data?.items.map(v => [v.id, v.name, zoneLabels[v.zone]]) || [])])}>导出当前页</Button></div>
      {query.isError ? <ErrorNotice error={query.error} retry={() => void query.refetch()} /> : <Table<Asset> rowKey="id" loading={query.isFetching} dataSource={data?.items} scroll={{ x: 620 }} locale={{ emptyText: <Empty description="没有匹配的资产，试试调整筛选条件。" /> }} columns={[
        { title: '资产编号', dataIndex: 'id', width: 120, render: id => <span className="mono">AS-{String(id).padStart(3, '0')}</span> },
        { title: '资产名称', dataIndex: 'name', render: (name, row) => <Button className="asset-link" type="link" onClick={() => setSelected(row)}>{name}</Button> },
        { title: '所属分区', dataIndex: 'zone', render: (value: Asset['zone']) => <Tag color="cyan">{zoneLabels[value]}</Tag> },
        { title: '记录类型', render: () => <span className="muted">实验资产</span> },
      ]} pagination={{ current: page, pageSize: size, total: data?.total || 0, showSizeChanger: true, pageSizeOptions: [2, 10, 20, 50], showTotal: total => `共 ${total} 条`, onChange: (nextPage, nextSize) => setParams(previous => { const next = new URLSearchParams(previous); next.set('page', String(nextSize === size ? nextPage : 1)); next.set('size', String(nextSize)); return next; }) }} />}
    </Card><Drawer title="资产详情" open={!!selected} onClose={() => setSelected(null)}><Space orientation="vertical" size="large" style={{ width: '100%' }}>{selected && <Descriptions column={1} items={[{ key: 'id', label: '编号', children: `AS-${String(selected.id).padStart(3, '0')}` }, { key: 'name', label: '名称', children: selected.name }, { key: 'zone', label: '分区', children: zoneLabels[selected.zone] }, { key: 'source', label: '来源', children: '当前后端数据库的合成资产表' }]} />}<p className="muted">此项目提供只读资产查询，不采集这台资产的实时在线状态。</p></Space></Drawer></>;
}
