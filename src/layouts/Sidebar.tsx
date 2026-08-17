// ===================================================
// TRADECORE — SIDEBAR COMPONENT
// Dark left navigation with grouped Vietnamese routes
// ===================================================

import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';
import {
  IconDashboard, IconSales, IconPurchase, IconWarehouse,
  IconShipping, IconCustomers, IconSuppliers, IconReports,
  IconSettings, IconGlobe, IconQuote, IconInvoice,
  IconContainer, IconPackage,
} from '../components/Icon/Icon';

interface NavGroup {
  label: string;
  items: NavItem[];
}

interface NavItem {
  label: string;
  path: string;
  icon?: React.ReactNode;
}

const NAV_TOP: NavItem[] = [
  { label: 'Tổng quan', path: '/', icon: <IconDashboard size={15} /> },
];

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Bán hàng',
    items: [
      { label: 'Đơn bán hàng', path: '/ban-hang/don-hang', icon: <IconSales size={14} /> },
      { label: 'Báo giá', path: '/ban-hang/bao-gia', icon: <IconQuote size={14} /> },
      { label: 'Hóa đơn', path: '/ban-hang/hoa-don', icon: <IconInvoice size={14} /> },
    ],
  },
  {
    label: 'Mua hàng',
    items: [
      { label: 'Đơn mua hàng', path: '/mua-hang/don-hang', icon: <IconPurchase size={14} /> },
      { label: 'Đề nghị mua', path: '/mua-hang/de-nghi', icon: <IconQuote size={14} /> },
    ],
  },
  {
    label: 'Kho hàng',
    items: [
      { label: 'Tồn kho', path: '/kho/ton-kho', icon: <IconWarehouse size={14} /> },
      { label: 'Nhập kho', path: '/kho/nhap-kho', icon: <IconPackage size={14} /> },
      { label: 'Xuất kho', path: '/kho/xuat-kho', icon: <IconPackage size={14} /> },
    ],
  },
  {
    label: 'Xuất nhập khẩu',
    items: [
      { label: 'Nhập khẩu', path: '/xnk/nhap-khau', icon: <IconGlobe size={14} /> },
      { label: 'Xuất khẩu', path: '/xnk/xuat-khau', icon: <IconGlobe size={14} /> },
      { label: 'Lô hàng', path: '/xnk/lo-hang', icon: <IconShipping size={14} /> },
      { label: 'Container', path: '/xnk/container', icon: <IconContainer size={14} /> },
    ],
  },
  {
    label: 'Đối tác',
    items: [
      { label: 'Khách hàng', path: '/doi-tac/khach-hang', icon: <IconCustomers size={14} /> },
      { label: 'Nhà cung cấp', path: '/doi-tac/nha-cung-cap', icon: <IconSuppliers size={14} /> },
    ],
  },
];

const NAV_BOTTOM: NavItem[] = [
  { label: 'Báo cáo', path: '/bao-cao', icon: <IconReports size={15} /> },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className={`sidebar ${isOpen ? 'open' : ''}`} aria-label="Navigation chính">
        {/* Logo */}
        <NavLink to="/" className="sidebar-logo" onClick={onClose}>
          <div className="sidebar-logo-mark">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div className="sidebar-logo-text">TradeCore</div>
            <div className="sidebar-logo-sub">Quản lý thương mại</div>
          </div>
        </NavLink>

        {/* Main navigation */}
        <nav className="sidebar-nav">
          {/* Top direct items */}
          {NAV_TOP.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={onClose}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}

          {/* Grouped items */}
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className="sidebar-group">
              <div className="sidebar-group-label">{group.label}</div>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`sidebar-subitem ${isActive(item.path) ? 'active' : ''}`}
                  onClick={onClose}
                >
                  <span className="sidebar-subitem-dot" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}

          {/* Bottom direct items */}
          <div className="sidebar-divider" style={{ marginTop: 'var(--space-3)' }} />
          {NAV_BOTTOM.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={onClose}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <NavLink
            to="/cai-dat"
            className={`sidebar-item ${isActive('/cai-dat') ? 'active' : ''}`}
            onClick={onClose}
          >
            <span className="sidebar-item-icon"><IconSettings size={15} /></span>
            Cài đặt
          </NavLink>

          <div className="sidebar-user">
            <div className="sidebar-user-avatar">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'NV'}
            </div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.full_name || 'Đang tải...'}</div>
              <div className="sidebar-user-role">{user?.role || '---'}</div>
            </div>
            <button onClick={logout} className="sidebar-logout-btn" title="Đăng xuất">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
