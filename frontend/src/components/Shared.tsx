import { Alert, Button, Skeleton, Tag } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
export function ErrorNotice({ error, retry }: { error: Error; retry: () => void }) {
  return <div><Alert type="error" showIcon title="数据读取失败" description={error.message} action={<Button size="small" aria-label="重试" onClick={retry}>重试</Button>} /></div>;
}
export function Loading() { return <div role="status" aria-label="正在加载数据"><Skeleton active paragraph={{ rows: 5 }} /></div>; }
export function Refresh({ onClick, busy }: { onClick: () => void; busy: boolean }) { return <Button icon={<ReloadOutlined />} loading={busy} onClick={onClick}>刷新数据</Button>; }
export function StateTag({ ok, unknown = false }: { ok: boolean; unknown?: boolean }) { return <Tag color={unknown ? 'default' : ok ? 'success' : 'error'}>{unknown ? '待确认' : ok ? '正常' : '异常'}</Tag>; }
export function PageTitle({ title, subtitle, action }: { title: string; subtitle: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>;
}
