import { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function Profile() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/v1/account/me')
      .then(res => setProfile(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Đang tải...</div>;
  if (!profile) return <div>Không thể tải hồ sơ</div>;

  return (
    <div>
      <h1 className="settings-page-title">Hồ sơ cá nhân</h1>
      
      <div style={{ maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <strong style={{ color: 'var(--color-text-muted)' }}>Họ và tên:</strong>
          <span>{profile.full_name}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <strong style={{ color: 'var(--color-text-muted)' }}>Tên đăng nhập:</strong>
          <span>{profile.username}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <strong style={{ color: 'var(--color-text-muted)' }}>Email:</strong>
          <span>{profile.email}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <strong style={{ color: 'var(--color-text-muted)' }}>Trạng thái:</strong>
          <span style={{ color: profile.is_active ? 'green' : 'red', fontWeight: 500 }}>
            {profile.is_active ? 'Đang hoạt động' : 'Đã khóa'}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
          <strong style={{ color: 'var(--color-text-muted)' }}>Vai trò hiện tại:</strong>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {profile.roles?.map((r: any) => (
              <span key={r.id} style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.875rem' }}>
                {r.name}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
