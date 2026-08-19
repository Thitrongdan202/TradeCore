import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function CompanySettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState({
    name: '',
    trade_name: '',
    tax_code: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    logo_url: ''
  });
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.get('/api/v1/settings')
      .then(res => {
        setData({
          name: res.data.name || '',
          trade_name: res.data.trade_name || '',
          tax_code: res.data.tax_code || '',
          address: res.data.address || '',
          phone: res.data.phone || '',
          email: res.data.email || '',
          website: res.data.website || '',
          logo_url: res.data.logo_url || ''
        });
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      await api.put('/api/v1/settings', data);
      setMessage('Lưu thay đổi thành công!');
    } catch (err: any) {
      setMessage('Lỗi khi lưu thay đổi.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Đang tải...</div>;

  return (
    <div>
      <h1 className="settings-page-title">Thông tin công ty</h1>
      {message && <div style={{ padding: '1rem', marginBottom: '1rem', backgroundColor: message.includes('Lỗi') ? '#ffebee' : '#e8f5e9', color: message.includes('Lỗi') ? '#c62828' : '#2e7d32', borderRadius: '4px' }}>{message}</div>}
      <form className="settings-form" onSubmit={handleSave}>
        <div className="form-group">
          <label>Tên công ty</label>
          <input className="input" name="name" value={data.name} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label>Tên giao dịch</label>
          <input className="input" name="trade_name" value={data.trade_name} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Mã số thuế</label>
          <input className="input" name="tax_code" value={data.tax_code} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Địa chỉ</label>
          <input className="input" name="address" value={data.address} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Điện thoại</label>
          <input className="input" name="phone" value={data.phone} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Email</label>
          <input className="input" type="email" name="email" value={data.email} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Website</label>
          <input className="input" name="website" value={data.website} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Logo URL</label>
          <input className="input" name="logo_url" value={data.logo_url} onChange={handleChange} />
        </div>
        
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
          </button>
          <button type="button" className="btn btn-outline" onClick={() => window.location.reload()}>Hủy</button>
        </div>
      </form>
    </div>
  );
}
