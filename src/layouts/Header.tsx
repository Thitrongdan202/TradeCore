// ===================================================
// TRADECORE — HEADER COMPONENT
// Top navigation bar with search, notifications, breadcrumb
// ===================================================

import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { IconSearch, IconBell, IconMenu } from '../components/Icon/Icon';
import './Header.css';

interface HeaderProps {
  onMenuToggle: () => void;
}

const ROUTE_LABELS: Record<string, string> = {
  '/':                      'Tổng quan',
  '/ban-hang/don-hang':     'Đơn bán hàng',
  '/ban-hang/bao-gia':      'Báo giá',
  '/ban-hang/hoa-don':      'Hóa đơn',
  '/mua-hang/don-hang':     'Đơn mua hàng',
  '/mua-hang/de-nghi':      'Đề nghị mua',
  '/kho/ton-kho':           'Tồn kho',
  '/kho/nhap-kho':          'Nhập kho',
  '/kho/xuat-kho':          'Xuất kho',
  '/xnk/nhap-khau':         'Nhập khẩu',
  '/xnk/xuat-khau':         'Xuất khẩu',
  '/xnk/lo-hang':           'Lô hàng',
  '/xnk/container':         'Container',
  '/doi-tac/khach-hang':    'Khách hàng',
  '/doi-tac/nha-cung-cap':  'Nhà cung cấp',
  '/bao-cao':               'Báo cáo',
  '/cai-dat':               'Cài đặt',
};

export function Header({ onMenuToggle }: HeaderProps) {
  const location = useLocation();
  const [hasNotif] = useState(3); // mock notification count

  const pageTitle = ROUTE_LABELS[location.pathname] ?? 'TradeCore';

  return (
    <header className="header">
      {/* Mobile menu toggle */}
      <button
        className="header-menu-btn"
        onClick={onMenuToggle}
        aria-label="Mở menu"
      >
        <IconMenu size={18} />
      </button>

      {/* Page title (mobile-visible breadcrumb) */}
      <div className="header-title">{pageTitle}</div>

      {/* Search — desktop */}
      <div className="header-search-wrapper">
        <div className="search-wrapper">
          <span className="search-icon">
            <IconSearch size={14} color="var(--color-text-muted)" />
          </span>
          <input
            className="input input-sm header-search"
            type="search"
            placeholder="Tìm kiếm đơn hàng, khách hàng..."
            aria-label="Tìm kiếm"
          />
        </div>
      </div>

      {/* Right actions */}
      <div className="header-actions">
        {/* Notification bell */}
        <button className="header-icon-btn" aria-label="Thông báo">
          <IconBell size={17} />
          {hasNotif > 0 && (
            <span className="header-notif-dot" aria-label={`${hasNotif} thông báo`}>{hasNotif}</span>
          )}
        </button>

        {/* User avatar */}
        <button className="header-user-btn" aria-label="Tài khoản">
          <div className="header-avatar">NV</div>
          <span className="header-user-name">Nguyễn Văn An</span>
        </button>
      </div>
    </header>
  );
}
