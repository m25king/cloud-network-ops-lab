import React, { Suspense, lazy, Component, type ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, NavLink, Route, Routes, Navigate } from 'react-router-dom';
import { ConfigProvider, Result, Button } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { DashboardOutlined, DatabaseOutlined, AuditOutlined, HistoryOutlined, CloudServerOutlined, GithubOutlined } from '@ant-design/icons';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { retryRequest } from './lib/api';
import { Loading } from './components/Shared';
import 'antd/dist/reset.css';
import './styles.css';
const Overview = lazy(() => import('./pages/Overview'));
const Assets = lazy(() => import('./pages/Assets'));
const Inspections = lazy(() => import('./pages/Inspections'));
const Incidents = lazy(() => import('./pages/Incidents'));
const client = new QueryClient({ defaultOptions: { queries: { staleTime: 10000, retry: retryRequest, refetchOnWindowFocus: true } } });
class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <Result status="error" title="页面暂时无法显示" subTitle="可以重新加载页面恢复。" extra={<Button onClick={() => window.location.reload()}>重新加载</Button>} /> : this.props.children; }
}
function Shell() {
  const links = [{ path: '/', label: '运行概览', icon: <DashboardOutlined /> }, { path: '/assets', label: '资产目录', icon: <DatabaseOutlined /> }, { path: '/inspections', label: '巡检报告', icon: <AuditOutlined /> }, { path: '/incidents', label: '故障记录', icon: <HistoryOutlined /> }];
  return <div className="shell">
    <a className="skip-link" href="#main">跳转到主内容</a>
    <aside className="sidebar"><div className="brand"><span className="brand-icon"><CloudServerOutlined /></span><div>云网运维<span>OPS CONSOLE</span></div></div><div className="nav-label">工作空间</div><nav aria-label="主导航">{links.map(link => <NavLink key={link.path} aria-label={link.label} end={link.path === '/'} to={link.path}>{link.icon}<span>{link.label}</span></NavLink>)}</nav><div className="sidebar-foot"><span className="env-dot"/>个人实验环境<p>所有资产均为合成数据</p></div></aside>
    <div className="workspace"><header className="topbar"><span>工作台 <span className="slash">/</span> 运维协作</span><div className="topbar-right"><span className="read-only">只读访问</span><a href="https://github.com/m25king/cloud-network-ops-lab" target="_blank" rel="noreferrer"><GithubOutlined /> 项目仓库</a></div></header><main id="main" className="main" tabIndex={-1}><Boundary><Suspense fallback={<Loading />}><Routes><Route path="/" element={<Overview />} /><Route path="/assets" element={<Assets />} /><Route path="/inspections" element={<Inspections />} /><Route path="/incidents" element={<Incidents />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></Suspense></Boundary><footer>Cloud Network Ops Lab · 个人学习项目 · 展示范围以实际接口与记录为准</footer></main></div>
  </div>;
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#126d72', borderRadius: 8, fontFamily: 'Inter, "Microsoft YaHei", system-ui, sans-serif', colorText: '#203545' } }}><QueryClientProvider client={client}><BrowserRouter><Shell /></BrowserRouter></QueryClientProvider></ConfigProvider></React.StrictMode>);
