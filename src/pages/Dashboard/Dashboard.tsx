// ===================================================
// TRADECORE — DASHBOARD PAGE
// Tổng quan: KPIs, recent orders, shipments, charts
// ===================================================

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../../utils/api';
import type {
  KPISummary, SalesOrder, PurchaseOrder,
  Shipment, StockItem, RevenueDataPoint,
} from '../../types';

// Export these local helpers for formatting
export function formatVND(amount: number, compact = false): string {
  if (amount === undefined || amount === null) return '0đ';
  if (compact) {
    if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(1).replace(/\.0$/, '')} tỷ`;
    if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(0)} tr`;
    return `${amount.toLocaleString('vi-VN')}đ`;
  }
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', minimumFractionDigits: 0 }).format(amount);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear()}`;
  } catch (e) {
    return dateStr;
  }
}
import { OrderStatusBadge, PaymentStatusBadge, ShipmentStatusBadge, StockAlertBadge } from '../../components/Badge/Badge';
import {
  IconTrendUp, IconTrendDown, IconCalendar, IconAlert,
} from '../../components/Icon/Icon';
import './Dashboard.css';

// ─── KPI Card ───────────────────────────────────────
interface KPICardProps {
  label: string;
  value: string;
  trendPct?: number;
  comparisonLabel?: string;
  iconColorClass: string;
  icon: React.ReactNode;
  sub?: string;
}

function KPICard({ label, value, trendPct, comparisonLabel, iconColorClass, icon, sub }: KPICardProps) {
  const isUp   = trendPct !== undefined && trendPct > 0;
  const isDown = trendPct !== undefined && trendPct < 0;

  return (
    <div className="kpi-card">
      <div className="kpi-card-header">
        <span className="kpi-card-label">{label}</span>
        <div className={`kpi-card-icon ${iconColorClass}`}>{icon}</div>
      </div>
      <div className="kpi-card-value">{value}</div>
      {(trendPct !== undefined || sub) && (
        <div className="kpi-card-footer">
          {trendPct !== undefined && (
            <span className={`kpi-trend ${isUp ? 'kpi-trend-up' : isDown ? 'kpi-trend-down' : 'kpi-trend-neutral'}`}>
              {isUp ? <IconTrendUp size={11} /> : isDown ? <IconTrendDown size={11} /> : null}
              {isUp ? '+' : ''}{trendPct.toFixed(1)}%
            </span>
          )}
          {comparisonLabel && (
            <span className="kpi-comparison">{comparisonLabel}</span>
          )}
          {sub && !trendPct && <span className="kpi-comparison">{sub}</span>}
        </div>
      )}
    </div>
  );
}

// ─── Shipment Timeline ──────────────────────────────
const SHIPMENT_STEPS: { key: string; label: string }[] = [
  { key: 'booking',    label: 'Đặt chỗ' },
  { key: 'loading',    label: 'Đóng hàng' },
  { key: 'in_transit', label: 'Vận chuyển' },
  { key: 'arrived',    label: 'Đến cảng' },
  { key: 'customs',    label: 'Hải quan' },
  { key: 'warehoused', label: 'Nhập kho' },
];

const STEP_ORDER = ['booking', 'loading', 'in_transit', 'arrived', 'customs', 'warehoused', 'completed'];

function ShipmentTimeline({ status }: { status: string }) {
  const currentIdx = STEP_ORDER.indexOf(status);
  return (
    <div className="shipment-progress">
      {SHIPMENT_STEPS.map((step, i) => {
        const stepIdx = STEP_ORDER.indexOf(step.key);
        const isDone    = stepIdx < currentIdx;
        const isCurrent = stepIdx === currentIdx;
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: '3px', flex: 1, minWidth: 0 }}>
            <div className={`progress-step ${isDone ? 'done' : isCurrent ? 'current' : ''}`}>
              <div className="progress-step-dot" />
              <span className="progress-step-label">{step.label}</span>
            </div>
            {i < SHIPMENT_STEPS.length - 1 && (
              <div className={`progress-line ${isDone ? 'done' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Recharts custom tooltip ───────────────────────
function RevenueTooltip({ active, payload, label }: {
  active?: boolean; payload?: { value: number; name: string; color: string }[]; label?: string
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontSize: 'var(--font-size-sm)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--color-text-primary)' }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, color: 'var(--color-text-secondary)' }}>
          <span style={{ color: p.color }}>{p.name === 'revenue' ? 'Doanh thu' : p.name === 'cost' ? 'Chi phí' : 'Lợi nhuận'}</span>
          <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{formatVND(p.value, true)}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Dashboard ─────────────────────────────────────
export function Dashboard() {
  const [kpi, setKpi]           = useState<KPISummary | null>(null);
  const [salesOrders, setSales]  = useState<SalesOrder[]>([]);
  const [purchaseOrders, setPO]  = useState<PurchaseOrder[]>([]);
  const [shipments]              = useState<Shipment[]>([]);
  const [stockAlerts, setStock]  = useState<StockItem[]>([]);
  const [revenueData, setRevenue] = useState<RevenueDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [
          kpiRes, revenueRes, ordersRes, lowStockRes
        ] = await Promise.all([
          api.get('/api/v1/dashboard/summary'),
          api.get('/api/v1/dashboard/revenue-chart'),
          api.get('/api/v1/dashboard/recent-orders'),
          api.get('/api/v1/dashboard/low-stock'),
        ]);

        setKpi(kpiRes.data);
        setRevenue(revenueRes.data);
        setSales(ordersRes.data.sales_orders || []);
        setPO(ordersRes.data.purchase_orders || []);
        setStock(lowStockRes.data || []);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', padding: 'var(--space-8)' }}>Đang tải dữ liệu...</div>;
  }

  const revenuePct = kpi
    ? ((kpi.revenueThisMonth - kpi.revenueLastMonth) / (kpi.revenueLastMonth || 1)) * 100
    : 0;
  const ordersPct = kpi
    ? ((kpi.ordersThisMonth - kpi.ordersLastMonth) / (kpi.ordersLastMonth || 1)) * 100
    : 0;

  // Today in Vietnamese locale
  const today = new Date().toLocaleDateString('vi-VN', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <div>
      {/* ── Page header ── */}
      <div className="dashboard-header">
        <div className="page-header-left">
          <h1 className="page-title">Tổng quan</h1>
          <p className="page-subtitle">Tình trạng hoạt động kinh doanh hôm nay</p>
        </div>
        <div className="dashboard-date">
          <IconCalendar size={13} />
          {today}
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div className="kpi-grid">
        <KPICard
          label="Doanh thu tháng này"
          value={formatVND(kpi?.revenueThisMonth ?? 0, true)}
          trendPct={revenuePct}
          comparisonLabel="so tháng trước"
          iconColorClass="kpi-card-icon-purple"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
            </svg>
          }
        />
        <KPICard
          label="Đơn hàng tháng này"
          value={String(kpi?.ordersThisMonth ?? 0)}
          trendPct={ordersPct}
          comparisonLabel="so tháng trước"
          iconColorClass="kpi-card-icon-blue"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/>
            </svg>
          }
        />
        <KPICard
          label="Giá trị tồn kho"
          value={formatVND(kpi?.inventoryValue ?? 0, true)}
          iconColorClass="kpi-card-icon-green"
          sub="Cập nhật hôm nay"
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          }
        />
        <KPICard
          label="Công nợ phải thu"
          value={formatVND(kpi?.receivable ?? 0, true)}
          iconColorClass="kpi-card-icon-amber"
          sub={`Phải trả: ${formatVND(kpi?.payable ?? 0, true)}`}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>
            </svg>
          }
        />
      </div>

      {/* ── Recent orders (2 columns) ── */}
      <div className="dashboard-grid-2">
        {/* Sales orders */}
        <div className="section-card">
          <div className="section-card-header">
            <div>
              <div className="section-card-title">Đơn bán hàng gần đây</div>
              <div className="section-card-subtitle">{salesOrders.length} đơn trong 7 ngày qua</div>
            </div>
            <Link to="/ban-hang/don-hang" className="see-all-link">Xem tất cả →</Link>
          </div>
          <div className="section-card-body-flush">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mã đơn</th>
                  <th>Khách hàng</th>
                  <th className="th-right">Tổng tiền</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {salesOrders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <span className="order-number">{order.orderNumber}</span>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                        {formatDate(order.date)}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 500 }}>{order.customerName}</div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{order.customerCode}</div>
                    </td>
                    <td className="td-right">
                      <div className="amount-vnd">{formatVND(order.total, true)}</div>
                      <div style={{ marginTop: 2 }}><PaymentStatusBadge status={order.paymentStatus} /></div>
                    </td>
                    <td><OrderStatusBadge status={order.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Purchase orders */}
        <div className="section-card">
          <div className="section-card-header">
            <div>
              <div className="section-card-title">Đơn mua hàng gần đây</div>
              <div className="section-card-subtitle">{purchaseOrders.length} đơn trong 7 ngày qua</div>
            </div>
            <Link to="/mua-hang/don-hang" className="see-all-link">Xem tất cả →</Link>
          </div>
          <div className="section-card-body-flush">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mã đơn</th>
                  <th>Nhà cung cấp</th>
                  <th className="th-right">Tổng tiền</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {purchaseOrders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <span className="order-number">{order.orderNumber}</span>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                        {formatDate(order.date)}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 140 }}>
                        {order.supplierName}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{order.country}</div>
                    </td>
                    <td className="td-right">
                      <div className="amount-vnd">{formatVND(order.total, true)}</div>
                      <div style={{ marginTop: 2 }}><PaymentStatusBadge status={order.paymentStatus} /></div>
                    </td>
                    <td><OrderStatusBadge status={order.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Active Shipments ── */}
      <div className="dashboard-row">
        <div className="section-card">
          <div className="section-card-header">
            <div>
              <div className="section-card-title">Lô hàng đang vận chuyển</div>
              <div className="section-card-subtitle">{shipments.length} lô hàng đang theo dõi</div>
            </div>
            <Link to="/xnk/lo-hang" className="see-all-link">Xem tất cả →</Link>
          </div>
          <div className="section-card-body-flush">
            {shipments.map((sh) => (
              <div key={sh.id}>
                <div className="shipment-row">
                  {/* Info */}
                  <div>
                    <div className="shipment-code">{sh.shipmentNumber}</div>
                    <div className="shipment-desc">{sh.description}</div>
                    <div className="shipment-route">
                      <span>{sh.portOrigin}</span>
                      <span className="shipment-route-arrow">→</span>
                      <span>{sh.portDestination}</span>
                    </div>
                  </div>
                  {/* ETA */}
                  <div>
                    <div className="shipment-eta-label">ETA</div>
                    <div className="shipment-eta-value">{formatDate(sh.eta)}</div>
                  </div>
                  {/* Containers */}
                  <div className="shipment-containers">
                    <strong>{sh.containers}</strong>
                    container
                  </div>
                  {/* Status */}
                  <div><ShipmentStatusBadge status={sh.status} /></div>
                </div>
                {/* Timeline */}
                <div style={{ paddingBottom: 'var(--space-4)', borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <ShipmentTimeline status={sh.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Chart + Stock alerts ── */}
      <div className="dashboard-grid-chart">
        {/* Revenue bar chart */}
        <div className="section-card">
          <div className="section-card-header">
            <div>
              <div className="section-card-title">Doanh thu 6 tháng gần nhất</div>
              <div className="section-card-subtitle">Doanh thu, chi phí và lợi nhuận theo tháng</div>
            </div>
          </div>
          <div className="chart-wrapper">
            <div className="chart-legend">
              <div className="chart-legend-item">
                <div className="chart-legend-dot" style={{ background: '#5B3FD8' }} />
                <span>Doanh thu</span>
              </div>
              <div className="chart-legend-item">
                <div className="chart-legend-dot" style={{ background: '#E0D9FF' }} />
                <span>Chi phí</span>
              </div>
              <div className="chart-legend-item">
                <div className="chart-legend-dot" style={{ background: '#15803D' }} />
                <span>Lợi nhuận</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={revenueData} barGap={3} barCategoryGap="30%">
                <CartesianGrid vertical={false} stroke="var(--color-border-subtle)" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v: number) => `${(v / 1_000_000_000).toFixed(1)}tỷ`}
                  tick={{ fontSize: 10, fill: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip content={<RevenueTooltip />} cursor={{ fill: 'var(--color-surface-raised)' }} />
                <Bar dataKey="revenue" name="revenue" fill="#5B3FD8" radius={[3, 3, 0, 0]} />
                <Bar dataKey="cost"    name="cost"    fill="#DDD6FE" radius={[3, 3, 0, 0]} />
                <Bar dataKey="profit"  name="profit"  fill="#15803D" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stock alerts */}
        <div className="section-card">
          <div className="section-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--color-warning)', display: 'flex' }}>
                <IconAlert size={15} />
              </span>
              <div>
                <div className="section-card-title">Cảnh báo tồn kho</div>
                <div className="section-card-subtitle">{stockAlerts.length} mặt hàng cần chú ý</div>
              </div>
            </div>
            <Link to="/kho/ton-kho" className="see-all-link">Xem kho →</Link>
          </div>
          <div className="section-card-body-flush">
            {stockAlerts.map((item) => (
              <div key={item.id} className="stock-alert-row">
                <div className="stock-alert-info">
                  <div className="stock-alert-name" title={item.name}>{item.name}</div>
                  <div className="stock-alert-code">{item.code} · {item.category}</div>
                </div>
                <div>
                  <div className="stock-alert-qty">
                    {item.currentStock} {item.unit}
                  </div>
                  <div className="stock-alert-min">Tối thiểu: {item.minStock}</div>
                </div>
                <div style={{ flexShrink: 0 }}>
                  <StockAlertBadge level={item.alertLevel} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
