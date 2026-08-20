import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';
<<<<<<< Updated upstream

export function UsersSettings() {
=======
import { useAuth } from '../../contexts/AuthContext';

export function UsersSettings() {
  const { user: currentUser } = useAuth();
>>>>>>> Stashed changes
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [effectivePerms, setEffectivePerms] = useState<any[] | null>(null);
  const [viewingUser, setViewingUser] = useState<string | null>(null);
  
<<<<<<< Updated upstream
=======
  // Password viewing state
  const [revealedPasswords, setRevealedPasswords] = useState<Record<string, string>>({});
  
  // Form eye icon state
  const [showPassword, setShowPassword] = useState(false);
  
  // Check if current user has password_view permission
  const canViewPassword = currentUser?.permissions?.includes('user:password_view');

>>>>>>> Stashed changes
  // New user form state
  const [formData, setFormData] = useState({
    username: '', full_name: '', email: '', password: '', confirm_password: '', role_ids: [] as string[], is_active: true
  });

  const fetchUsers = () => {
    api.get('/api/v1/users')
      .then(res => setUsers(res.data.items))
      .catch(console.error);
  };

  useEffect(() => {
    fetchUsers();
    api.get('/api/v1/users/roles')
      .then(res => setRoles(res.data))
      .finally(() => setLoading(false));
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) {
      alert('Mật khẩu xác nhận không khớp');
      return;
    }
    try {
      await api.post('/api/v1/users', formData);
      setShowForm(false);
      fetchUsers();
      setFormData({ username: '', full_name: '', email: '', password: '', confirm_password: '', role_ids: [], is_active: true });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi thêm người dùng');
    }
  };

  const toggleStatus = async (user: any) => {
    try {
      await api.put(`/api/v1/users/${user.id}`, { is_active: !user.is_active });
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể cập nhật trạng thái');
    }
  };

  const resetPassword = async (user: any) => {
    const newPassword = prompt(`Nhập mật khẩu mới cho tài khoản ${user.username}:`);
    if (!newPassword) return;
    try {
      await api.put(`/api/v1/users/${user.id}/reset-password`, { new_password: newPassword });
      alert('Đã đặt lại mật khẩu thành công');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể đặt lại mật khẩu');
    }
  };

  const viewPermissions = async (user: any) => {
    if (viewingUser === user.id) {
      setViewingUser(null);
      setEffectivePerms(null);
      return;
    }
    try {
      const res = await api.get(`/api/v1/users/${user.id}/effective-permissions`);
      setEffectivePerms(res.data);
      setViewingUser(user.id);
    } catch (err: any) {
      alert('Lỗi tải danh sách quyền');
    }
  };

<<<<<<< Updated upstream
=======
  const handleViewPassword = async (user: any) => {
    if (revealedPasswords[user.id]) {
      setRevealedPasswords(prev => {
        const next = { ...prev };
        delete next[user.id];
        return next;
      });
      return;
    }

    try {
      const res = await api.get(`/api/v1/users/${user.id}/password`);
      const pwd = res.data.password;
      setRevealedPasswords(prev => ({ ...prev, [user.id]: pwd }));
      
      // Auto-hide after 10 seconds
      setTimeout(() => {
        setRevealedPasswords(prev => {
          const next = { ...prev };
          delete next[user.id];
          return next;
        });
      }, 10000);
      
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xem mật khẩu');
    }
  };

>>>>>>> Stashed changes
  if (loading) return <div>Đang tải...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="settings-page-title" style={{ margin: 0 }}>Người dùng</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Hủy' : '+ Thêm người dùng'}
        </button>
      </div>

      {showForm && (
        <form className="settings-form" onSubmit={handleAdd} style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Họ và tên</label>
              <input className="input" value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} required />
            </div>
            <div className="form-group">
              <label>Tên đăng nhập</label>
              <input className="input" value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input className="input" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} required />
            </div>
            <div className="form-group">
              <label>Số điện thoại</label>
              <input className="input" type="text" placeholder="Tùy chọn" />
            </div>
            <div className="form-group">
<<<<<<< Updated upstream
              <label>Mật khẩu khởi tạo</label>
              <input className="input" type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} required minLength={6} />
            </div>
            <div className="form-group">
              <label>Xác nhận mật khẩu</label>
              <input className="input" type="password" value={formData.confirm_password} onChange={e => setFormData({...formData, confirm_password: e.target.value})} required minLength={6} />
=======
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                Mật khẩu khởi tạo
                <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontSize: '12px' }}>
                  {showPassword ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
                </button>
              </label>
              <input className="input" type={showPassword ? 'text' : 'password'} value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} required minLength={6} />
            </div>
            <div className="form-group">
              <label>Xác nhận mật khẩu</label>
              <input className="input" type={showPassword ? 'text' : 'password'} value={formData.confirm_password} onChange={e => setFormData({...formData, confirm_password: e.target.value})} required minLength={6} />
>>>>>>> Stashed changes
            </div>
          </div>
          <div className="form-group">
            <label>Vai trò</label>
            <select className="input" multiple value={formData.role_ids} onChange={e => {
              const opts = Array.from(e.target.selectedOptions, option => option.value);
              setFormData({...formData, role_ids: opts});
            }} style={{ height: '100px' }}>
              {roles.filter(r => r.is_active).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <small style={{ color: 'var(--color-text-muted)' }}>Nhấn giữ Ctrl/Cmd để chọn nhiều vai trò</small>
          </div>
          <button type="submit" className="btn btn-primary">Lưu người dùng</button>
        </form>
      )}

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Họ và tên</th>
              <th>Tên đăng nhập</th>
              <th>Email</th>
              <th>Vai trò</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <React.Fragment key={u.id}>
                <tr>
                  <td>{u.full_name}</td>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.roles?.map((r: any) => r.name).join(', ')}</td>
                  <td>
                    <span style={{ color: u.is_active ? 'green' : 'red' }}>
                      {u.is_active ? 'Hoạt động' : 'Đã khóa'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                      <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => viewPermissions(u)}>Quyền</button>
                      <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => resetPassword(u)}>Đặt lại MK</button>
                      <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: '12px', color: u.is_active ? 'red' : 'green', borderColor: u.is_active ? 'red' : 'green' }} onClick={() => toggleStatus(u)}>
                        {u.is_active ? 'Khóa' : 'Mở khóa'}
                      </button>
<<<<<<< Updated upstream
                    </div>
=======
                      {canViewPassword && (
                        <button className="btn btn-outline" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => handleViewPassword(u)}>
                          {revealedPasswords[u.id] ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
                        </button>
                      )}
                    </div>
                    {revealedPasswords[u.id] && (
                       <div style={{ marginTop: '0.5rem', background: '#fff9c4', padding: '0.25rem 0.5rem', borderRadius: '4px', border: '1px solid #fbc02d', display: 'inline-block' }}>
                          Mật khẩu: <strong>{revealedPasswords[u.id]}</strong>
                       </div>
                    )}
>>>>>>> Stashed changes
                  </td>
                </tr>
                {viewingUser === u.id && effectivePerms && (
                  <tr>
                    <td colSpan={6} style={{ background: '#f9fafb', padding: '1rem' }}>
                      <strong>Quyền được cấp ({u.username}):</strong>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                        {effectivePerms.length === 0 ? <span style={{ color: 'var(--color-text-muted)' }}>Không có quyền nào</span> : effectivePerms.map(p => (
                          <span key={p.id} style={{ background: '#e0e7ff', color: '#3730a3', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>
                            {p.resource}:{p.action}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
