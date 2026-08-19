import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function SupportSessionsSettings() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  const [formData, setFormData] = useState({ user_id: '', duration_hours: 24, reason: '' });

  const fetchData = () => {
    Promise.all([
      api.get('/api/v1/support-sessions'),
      api.get('/api/v1/users')
    ]).then(([sessionsRes, usersRes]) => {
      setSessions(sessionsRes.data);
      setUsers(usersRes.data.items);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/support-sessions', formData);
      setShowForm(false);
      fetchData();
    } catch (err) {
      alert('Lỗi khi kích hoạt phiên hỗ trợ');
    }
  };

  const handleCancel = async (id: string) => {
    if (!window.confirm('Hủy phiên hỗ trợ này sẽ khóa ngay lập tức tài khoản tương ứng. Tiếp tục?')) return;
    try {
      await api.delete(`/api/v1/support-sessions/${id}`);
      fetchData();
    } catch (err) {
      alert('Lỗi khi hủy phiên');
    }
  };

  const getStatusText = (s: any) => {
    if (!s.is_active) return <span style={{ color: 'red' }}>Đã kết thúc / Đã hủy</span>;
    if (new Date(s.expires_at) < new Date()) return <span style={{ color: 'orange' }}>Đã hết hạn</span>;
    return <span style={{ color: 'green' }}>Đang hoạt động</span>;
  };

  if (loading) return <div>Đang tải...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="settings-page-title" style={{ margin: 0 }}>Hỗ trợ kỹ thuật</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Hủy' : '+ Kích hoạt phiên hỗ trợ'}
        </button>
      </div>

      {showForm && (
        <form className="settings-form" onSubmit={handleCreate} style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid var(--color-border)', borderRadius: '4px', background: '#fff9c4' }}>
          <p style={{ marginBottom: '1rem', color: '#f57f17', fontWeight: 600 }}>Cảnh báo: Tính năng này sẽ cấp quyền truy cập tạm thời cho tài khoản kỹ thuật.</p>
          <div className="form-group">
            <label>Tài khoản được cấp quyền</label>
            <select className="input" value={formData.user_id} onChange={e => setFormData({...formData, user_id: e.target.value})} required>
              <option value="">-- Chọn tài khoản --</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.username} - {u.full_name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Thời gian (Giờ)</label>
            <input type="number" className="input" value={formData.duration_hours} onChange={e => setFormData({...formData, duration_hours: Number(e.target.value)})} required />
          </div>
          <div className="form-group">
            <label>Lý do / Số ticket</label>
            <input className="input" value={formData.reason} onChange={e => setFormData({...formData, reason: e.target.value})} required />
          </div>
          <button type="submit" className="btn btn-primary">Kích hoạt ngay</button>
        </form>
      )}

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID Tài khoản (Kỹ thuật)</th>
              <th>Người cấp quyền</th>
              <th>Thời gian bắt đầu</th>
              <th>Hết hạn</th>
              <th>Lý do</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map(s => (
              <tr key={s.id}>
                <td>{s.user_id}</td>
                <td>{s.activated_by_id}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{new Date(s.created_at).toLocaleString('vi-VN')}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{new Date(s.expires_at).toLocaleString('vi-VN')}</td>
                <td>{s.reason}</td>
                <td style={{ fontWeight: 600 }}>{getStatusText(s)}</td>
                <td>
                  {s.is_active && new Date(s.expires_at) > new Date() && (
                    <button className="btn btn-outline" style={{ color: 'red', borderColor: 'red', padding: '4px 8px' }} onClick={() => handleCancel(s.id)}>
                      Hủy & Khóa
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
