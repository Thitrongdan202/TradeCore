import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Đang tải...</div>;
  }

  if (!user) {
    return <Navigate to="/dang-nhap" replace />;
  }

  return <Outlet />;
}
