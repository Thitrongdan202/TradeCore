import { NavLink, Outlet, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Settings.css';

export function SettingsLayout() {
  const { user } = useAuth();
  const location = useLocation();

  const hasPerm = (resource: string) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(`${resource}:view`);
  };

  const menu = [
    { label: 'Thông tin công ty', path: '/cai-dat/thong-tin-cong-ty', resource: 'company_setting' },
    { label: 'Người dùng', path: '/cai-dat/nguoi-dung', resource: 'user' },
    { label: 'Vai trò', path: '/cai-dat/vai-tro', resource: 'role' },
    { label: 'Phân quyền', path: '/cai-dat/phan-quyen', resource: 'permission' },
    { label: 'Nhật ký hoạt động', path: '/cai-dat/nhat-ky', resource: 'audit_log' },
    { label: 'Hỗ trợ kỹ thuật', path: '/cai-dat/ho-tro', resource: 'tech_support' },
  ].filter(m => hasPerm(m.resource));

  // Redirect to first available if on root /cai-dat
  if (location.pathname === '/cai-dat' && menu.length > 0) {
    return <Navigate to={menu[0].path} replace />;
  }

  return (
    <div className="settings-layout">
      <aside className="settings-sidebar">
        <h2 className="settings-title">Cài đặt</h2>
        <nav className="settings-nav">
          {menu.map(m => (
            <NavLink
              key={m.path}
              to={m.path}
              className={({ isActive }) => `settings-nav-item ${isActive ? 'active' : ''}`}
            >
              {m.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="settings-content">
        <Outlet />
      </main>
    </div>
  );
}
