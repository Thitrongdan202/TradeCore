// ===================================================
// TRADECORE — BADGE COMPONENT
// Status-semantic pill badges
// ===================================================

import type { OrderStatus, PaymentStatus, ShipmentStatus, StockAlertLevel } from '../../types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple';
  dot?: boolean;
  className?: string;
}

export function Badge({ children, variant = 'neutral', dot = true, className }: BadgeProps) {
  return (
    <span className={`badge badge-${variant} ${className ?? ''}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  );
}

// ─── Domain-specific badge helpers ───
export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const map: Record<OrderStatus, { variant: BadgeProps['variant']; label: string }> = {
    draft:      { variant: 'neutral',  label: 'Nháp' },
    pending:    { variant: 'purple',   label: 'Chờ xác nhận' },
    confirmed:  { variant: 'info',     label: 'Đã xác nhận' },
    processing: { variant: 'warning',  label: 'Đang xử lý' },
    shipping:   { variant: 'info',     label: 'Đang giao' },
    completed:  { variant: 'success',  label: 'Hoàn thành' },
    cancelled:  { variant: 'danger',   label: 'Đã hủy' },
    returned:   { variant: 'danger',   label: 'Đã trả hàng' },
  };
  const { variant, label } = map[status] ?? { variant: 'neutral', label: status };
  return <Badge variant={variant}>{label}</Badge>;
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const map: Record<PaymentStatus, { variant: BadgeProps['variant']; label: string }> = {
    unpaid:   { variant: 'warning', label: 'Chưa TT' },
    partial:  { variant: 'purple',  label: 'TT một phần' },
    paid:     { variant: 'success', label: 'Đã TT' },
    overdue:  { variant: 'danger',  label: 'Quá hạn' },
    refunded: { variant: 'neutral', label: 'Đã hoàn' },
  };
  const { variant, label } = map[status] ?? { variant: 'neutral', label: status };
  return <Badge variant={variant}>{label}</Badge>;
}

export function ShipmentStatusBadge({ status }: { status: ShipmentStatus }) {
  const map: Record<ShipmentStatus, { variant: BadgeProps['variant']; label: string }> = {
    booking:    { variant: 'neutral', label: 'Đặt chỗ' },
    loading:    { variant: 'warning', label: 'Đang đóng hàng' },
    in_transit: { variant: 'info',    label: 'Đang vận chuyển' },
    arrived:    { variant: 'purple',  label: 'Đã đến cảng' },
    customs:    { variant: 'warning', label: 'Đang thông quan' },
    warehoused: { variant: 'success', label: 'Đã nhập kho' },
    completed:  { variant: 'success', label: 'Hoàn thành' },
  };
  const { variant, label } = map[status] ?? { variant: 'neutral', label: status };
  return <Badge variant={variant}>{label}</Badge>;
}

export function StockAlertBadge({ level }: { level: StockAlertLevel }) {
  const map: Record<StockAlertLevel, { variant: BadgeProps['variant']; label: string }> = {
    low:      { variant: 'warning', label: 'Sắp hết' },
    critical: { variant: 'danger',  label: 'Nguy hiểm' },
    out:      { variant: 'danger',  label: 'Hết hàng' },
  };
  const { variant, label } = map[level];
  return <Badge variant={variant}>{label}</Badge>;
}
