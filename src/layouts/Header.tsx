import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { IconSearch, IconBell, IconMenu } from '../components/Icon/Icon';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

interface HeaderProps {
  onMenuToggle: () => void;
}

const ROUTE_LABELS: Record<string, string> = {
  '/':                      'Tổng quan',
  '/ban-hang/don-hang':     'Đơn bán hàng',
  '/ban-hang/bang-gia':     'Bảng giá / Báo giá',
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
  '/cai-dat/thong-tin-cong-ty': 'Thông tin công ty',
  '/cai-dat/nguoi-dung': 'Người dùng',
  '/cai-dat/vai-tro': 'Vai trò',
  '/cai-dat/phan-quyen': 'Phân quyền',
  '/cai-dat/nhap-du-lieu': 'Nhập dữ liệu',
  '/cai-dat/nhat-ky': 'Nhật ký hoạt động',
  '/cai-dat/ho-tro': 'Hỗ trợ kỹ thuật',
  '/tai-khoan': 'Tài khoản của tôi',
  '/tai-khoan/doi-mat-khau': 'Đổi mật khẩu',
};

export function Header({ onMenuToggle }: HeaderProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [hasNotif] = useState(0); // real empty state

  const pageTitle = ROUTE_LABELS[location.pathname] ?? 'TradeCore';

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    : 'U';

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
            placeholder="Tìm kiếm..."
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
        <div style={{ position: 'relative' }}>
          <button 
            className="header-user-btn" 
            aria-label="Tài khoản" 
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <div className="header-avatar">{userInitials}</div>
            <span className="header-user-name">{user?.full_name || 'Tài khoản'}</span>
          </button>
          
          {menuOpen && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '0.5rem',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-md)',
              zIndex: 50,
              minWidth: '160px',
              padding: '0.5rem 0'
            }}>
              <div style={{ padding: '0.25rem 1rem', borderBottom: '1px solid var(--color-border)', marginBottom: '0.25rem' }}>
                <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{user?.full_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{user?.roles?.join(', ')}</div>
              </div>
              <button 
                onClick={() => { setMenuOpen(false); navigate('/tai-khoan'); }}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '0.5rem 1rem', background: 'transparent', border: 'none', cursor: 'pointer' }}
              >
                Tài khoản của tôi
              </button>
              <button 
                onClick={() => { setMenuOpen(false); navigate('/tai-khoan/doi-mat-khau'); }}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '0.5rem 1rem', background: 'transparent', border: 'none', cursor: 'pointer' }}
              >
                Đổi mật khẩu
              </button>
              <button 
                onClick={() => { setMenuOpen(false); logout(); }}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '0.5rem 1rem', color: 'var(--color-danger)', background: 'transparent', border: 'none', cursor: 'pointer' }}
              >
                Đăng xuất
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
