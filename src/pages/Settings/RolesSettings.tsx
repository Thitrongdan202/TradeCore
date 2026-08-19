import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function RolesSettings() {
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: '', code: '', description: '', is_active: true });

  const fetchRoles = () => {
    api.get('/api/v1/users/roles')
      .then(res => setRoles(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleOpenAdd = () => {
    setEditId(null);
    setFormData({ name: '', code: '', description: '', is_active: true });
    setShowForm(true);
  };

  const handleOpenEdit = (role: any) => {
    setEditId(role.id);
    setFormData({ name: role.name, code: role.code, description: role.description || '', is_active: role.is_active });
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await api.put(`/api/v1/users/roles/${editId}`, {
          name: formData.name,
          description: formData.description,
          is_active: formData.is_active
        });
      } else {
        await api.post('/api/v1/users/roles', formData);
      }
      setShowForm(false);
      fetchRoles();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi lưu vai trò');
    }
  };

  const handleDelete = async (role: any) => {
    if (role.is_system) {
      alert('Không thể xóa vai trò hệ thống.');
      return;
    }
    if (!window.confirm(`Bạn có chắc chắn muốn xóa vai trò "${role.name}" không?`)) return;
    try {
      await api.delete(`/api/v1/users/roles/${role.id}`);
      fetchRoles();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi xóa vai trò');
    }
  };

  if (loading) return <div>Đang tải...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="settings-page-title" style={{ margin: 0 }}>Vai trò</h1>
        <button className="btn btn-primary" onClick={() => showForm ? setShowForm(false) : handleOpenAdd()}>
          {showForm ? 'Hủy' : '+ Tạo vai trò'}
        </button>
      </div>

      {showForm && (
        <form className="settings-form" onSubmit={handleSubmit} style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
          <div className="form-group">
            <label>Tên vai trò</label>
            <input className="input" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
          </div>
          <div className="form-group">
            <label>Mã vai trò (VD: ACCOUNTANT)</label>
            <input className="input" value={formData.code} onChange={e => setFormData({...formData, code: e.target.value.toUpperCase()})} required disabled={!!editId} />
          </div>
          <div className="form-group">
            <label>Mô tả</label>
            <input className="input" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input type="checkbox" checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} />
              Kích hoạt
            </label>
          </div>
          <button type="submit" className="btn btn-primary">Lưu vai trò</button>
        </form>
      )}

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tên vai trò</th>
              <th>Mã</th>
              <th>Mô tả</th>
              <th>Loại</th>
              <th>Trạng thái</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {roles.map(r => (
              <tr key={r.id}>
                <td style={{ fontWeight: 500 }}>{r.name}</td>
                <td><code style={{ background: '#eee', padding: '2px 4px', borderRadius: '4px' }}>{r.code}</code></td>
                <td>{r.description}</td>
                <td>{r.is_system ? <span style={{ color: '#f57c00' }}>Hệ thống</span> : 'Tùy chỉnh'}</td>
                <td>
                  <span style={{ color: r.is_active ? 'green' : 'red' }}>
                    {r.is_active ? 'Hoạt động' : 'Đã tắt'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn btn-outline" style={{ padding: '2px 8px', fontSize: '12px' }} onClick={() => handleOpenEdit(r)}>Chỉnh sửa</button>
                    {!r.is_system && (
                      <button className="btn btn-outline" style={{ padding: '2px 8px', fontSize: '12px', color: 'red', borderColor: 'red' }} onClick={() => handleDelete(r)}>Xóa</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
