import { useState } from 'react';
import { api } from '../../utils/api';

export function ChangePassword() {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
        new_password: formData.new_password,
      });

      setMessage('Đổi mật khẩu thành công');

      setFormData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err: any) {
      setMessage(
        err.response?.data?.detail || 'Lỗi khi đổi mật khẩu',
      );
    } finally {
      setLoading(false);
    }
  };

  const isSuccess = message === 'Đổi mật khẩu thành công';

  return (
    <div>
      <h1 className="settings-page-title">Đổi mật khẩu</h1>

      {message && (
        <div
          style={{
            padding: '1rem',
            marginBottom: '1.5rem',
            borderRadius: '4px',
            backgroundColor: isSuccess ? '#e8f5e9' : '#ffebee',
            color: isSuccess ? '#2e7d32' : '#c62828',
          }}
        >
          {message}
        </div>
      )}

      <form
        className="settings-form"
        onSubmit={handleSubmit}
        style={{ maxWidth: '400px' }}
      >
        <div className="form-group">
          <label
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Mật khẩu hiện tại</span>

            <button
              type="button"
              onClick={() =>
                setShowCurrentPassword(!showCurrentPassword)
              }
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              {showCurrentPassword ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
            </button>
          </label>

          <input
            className="input"
            type={showCurrentPassword ? 'text' : 'password'}
            value={formData.current_password}
            onChange={(e) =>
              setFormData({
                ...formData,
                current_password: e.target.value,
              })
            }
            required
          />
        </div>

        <div className="form-group">
          <label
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Mật khẩu mới</span>

            <button
              type="button"
              onClick={() =>
                setShowNewPassword(!showNewPassword)
              }
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              {showNewPassword ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
            </button>
          </label>

          <input
            className="input"
            type={showNewPassword ? 'text' : 'password'}
            value={formData.new_password}
            onChange={(e) =>
              setFormData({
                ...formData,
                new_password: e.target.value,
              })
            }
            required
            minLength={6}
          />
        </div>

        <div className="form-group">
          <label
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>Xác nhận mật khẩu mới</span>

            <button
              type="button"
              onClick={() =>
                setShowConfirmPassword(!showConfirmPassword)
              }
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              {showConfirmPassword ? 'Ẩn mật khẩu' : 'Xem mật khẩu'}
            </button>
          </label>

          <input
            className="input"
            type={showConfirmPassword ? 'text' : 'password'}
            value={formData.confirm_password}
            onChange={(e) =>
              setFormData({
                ...formData,
                confirm_password: e.target.value,
              })
            }
            required
            minLength={6}
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Đang xử lý...' : 'Lưu mật khẩu mới'}
          </button>
        </div>
      </form>
    </div>
  );
}