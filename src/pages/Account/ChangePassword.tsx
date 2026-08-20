import { useState } from 'react';
import { api } from '../../utils/api';

export function ChangePassword() {
  const [formData, setFormData] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
<<<<<<< Updated upstream
=======
  const [showPassword, setShowPassword] = useState(false);
>>>>>>> Stashed changes

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.new_password !== formData.confirm_password) {
      setMessage('Mật khẩu mới không khớp');
      return;
    }
    
    setLoading(true);
    setMessage('');
    try {
      await api.put('/api/v1/account/password', {
        current_password: formData.current_password,
        new_password: formData.new_password
      });
      setMessage('Đổi mật khẩu thành công');
      setFormData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Lỗi khi đổi mật khẩu');
    } finally {
      setLoading(false);
    }
  };

  const isSuccess = message === 'Đổi mật khẩu thành công';

  return (
    <div>
      <h1 className="settings-page-title">Đổi mật khẩu</h1>
      
      {message && (
        <div style={{ padding: '1rem', marginBottom: '1.5rem', borderRadius: '4px', backgroundColor: isSuccess ? '#e8f5e9' : '#ffebee', color: isSuccess ? '#2e7d32' : '#c62828' }}>
          {message}
        </div>
      )}

<<<<<<< Updated upstream
      <form className="settings-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Mật khẩu hiện tại</label>
          <input className="input" type="password" value={formData.current_password} onChange={e => setFormData({...formData, current_password: e.target.value})} required />
        </div>
        <div className="form-group">
          <label>Mật khẩu mới</label>
          <input className="input" type="password" value={formData.new_password} onChange={e => setFormData({...formData, new_password: e.target.value})} required minLength={6} />
        </div>
        <div className="form-group">
          <label>Xác nhận mật khẩu mới</label>
          <input className="input" type="password" value={formData.confirm_password} onChange={e => setFormData({...formData, confirm_password: e.target.value})} required minLength={6} />
=======
      <form className="settings-form" onSubmit={handleSubmit} style={{ maxWidth: '400px' }}>
        <div className="form-group">
          <label style={{ display: 'flex', justifyContent: 'space-between' }}>
            Mật khẩu hiện tại
            <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontSize: '12px' }}>
              {showPassword ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
            </button>
          </label>
          <input className="input" type={showPassword ? 'text' : 'password'} value={formData.current_password} onChange={e => setFormData({...formData, current_password: e.target.value})} required />
        </div>
        <div className="form-group">
          <label>Mật khẩu mới</label>
          <input className="input" type={showPassword ? 'text' : 'password'} value={formData.new_password} onChange={e => setFormData({...formData, new_password: e.target.value})} required minLength={6} />
        </div>
        <div className="form-group">
          <label>Xác nhận mật khẩu mới</label>
          <input className="input" type={showPassword ? 'text' : 'password'} value={formData.confirm_password} onChange={e => setFormData({...formData, confirm_password: e.target.value})} required minLength={6} />
>>>>>>> Stashed changes
        </div>
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Lưu mật khẩu mới'}
          </button>
        </div>
      </form>
    </div>
  );
}
