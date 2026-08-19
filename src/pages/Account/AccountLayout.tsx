import { NavLink, Outlet } from 'react-router-dom';
import '../Settings/Settings.css';

export function AccountLayout() {
  const menu = [
    { label: 'Hồ sơ cá nhân', path: '/tai-khoan', exact: true },
    { label: 'Đổi mật khẩu', path: '/tai-khoan/doi-mat-khau', exact: false },
  ];

  return (
    <div className="settings-layout">
      <aside className="settings-sidebar">
        <h2 className="settings-title">Tài khoản của tôi</h2>
        <nav className="settings-nav">
          {menu.map(m => (
            <NavLink
              key={m.path}
              to={m.path}
              end={m.exact}
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
