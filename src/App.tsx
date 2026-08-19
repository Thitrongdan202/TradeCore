// ===================================================
// TRADECORE — APP ROUTER
// React Router v6 route configuration
// ===================================================

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { Dashboard } from './pages/Dashboard/Dashboard';
import { PlaceholderPage } from './pages/Placeholder/PlaceholderPage';
import { Login } from './pages/Auth/Login';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

import { SettingsLayout } from './pages/Settings/SettingsLayout';
import { CompanySettings } from './pages/Settings/CompanySettings';
import { UsersSettings } from './pages/Settings/UsersSettings';
import { RolesSettings } from './pages/Settings/RolesSettings';
import { PermissionsSettings } from './pages/Settings/PermissionsSettings';
import { AuditLogSettings } from './pages/Settings/AuditLogSettings';
import { SupportSessionsSettings } from './pages/Settings/SupportSessionsSettings';
import { ImportSettings } from './pages/Settings/ImportSettings';

import { AccountLayout } from './pages/Account/AccountLayout';
import { Profile } from './pages/Account/Profile';
import { ChangePassword } from './pages/Account/ChangePassword';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/dang-nhap" element={<Login />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              {/* Dashboard */}
              <Route index element={<Dashboard />} />

              {/* Bán hàng */}
              <Route path="ban-hang/don-hang" element={<PlaceholderPage />} />
              <Route path="ban-hang/bao-gia"  element={<PlaceholderPage />} />
              <Route path="ban-hang/hoa-don"  element={<PlaceholderPage />} />

              {/* Mua hàng */}
              <Route path="mua-hang/don-hang" element={<PlaceholderPage />} />
              <Route path="mua-hang/de-nghi"  element={<PlaceholderPage />} />

              {/* Kho hàng */}
              <Route path="kho/ton-kho"  element={<PlaceholderPage />} />
              <Route path="kho/nhap-kho" element={<PlaceholderPage />} />
              <Route path="kho/xuat-kho" element={<PlaceholderPage />} />

              {/* Xuất nhập khẩu */}
              <Route path="xnk/nhap-khau"  element={<PlaceholderPage />} />
              <Route path="xnk/xuat-khau"  element={<PlaceholderPage />} />
              <Route path="xnk/lo-hang"    element={<PlaceholderPage />} />
              <Route path="xnk/container"  element={<PlaceholderPage />} />

              {/* Đối tác */}
              <Route path="doi-tac/khach-hang"   element={<PlaceholderPage />} />
              <Route path="doi-tac/nha-cung-cap" element={<PlaceholderPage />} />

              {/* Others */}
              <Route path="bao-cao" element={<PlaceholderPage />} />
              
              {/* Cài đặt */}
              <Route path="cai-dat" element={<SettingsLayout />}>
                <Route path="thong-tin-cong-ty" element={<CompanySettings />} />
                <Route path="nguoi-dung" element={<UsersSettings />} />
                <Route path="vai-tro" element={<RolesSettings />} />
                <Route path="phan-quyen" element={<PermissionsSettings />} />
                <Route path="nhap-du-lieu" element={<ImportSettings />} />
                <Route path="nhat-ky" element={<AuditLogSettings />} />
                <Route path="ho-tro" element={<SupportSessionsSettings />} />
              </Route>
              
              {/* Tài khoản */}
              <Route path="tai-khoan" element={<AccountLayout />}>
                <Route index element={<Profile />} />
                <Route path="doi-mat-khau" element={<ChangePassword />} />
              </Route>

              {/* 404 */}
              <Route path="*" element={<PlaceholderPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
