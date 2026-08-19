import { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function PermissionsSettings() {
  const [roles, setRoles] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [rolePerms, setRolePerms] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/api/v1/users/roles'),
      api.get('/api/v1/users/permissions')
    ]).then(([rolesRes, permsRes]) => {
      setRoles(rolesRes.data);
      setPermissions(permsRes.data);
      if (rolesRes.data.length > 0) {
        handleSelectRole(rolesRes.data[0].id);
      }
    });
  }, []);

  const handleSelectRole = async (roleId: string) => {
    setSelectedRole(roleId);
    try {
      const res = await api.get(`/api/v1/users/roles/${roleId}`);
      setRolePerms(res.data.permissions?.map((p: any) => p.id) || []);
    } catch (err) {
      console.error(err);
    }
  };

  const togglePermission = (permId: string) => {
    setRolePerms(prev => prev.includes(permId) ? prev.filter(p => p !== permId) : [...prev, permId]);
  };

  const handleSave = async () => {
    if (!selectedRole) return;
    setSaving(true);
    try {
      await api.put(`/api/v1/users/roles/${selectedRole}`, { permission_ids: rolePerms });
      alert('Đã lưu phân quyền!');
    } catch (err) {
      alert('Lỗi khi lưu phân quyền');
    } finally {
      setSaving(false);
    }
  };

  // Group permissions by resource
  const groupedPerms = permissions.reduce((acc, p) => {
    acc[p.resource] = acc[p.resource] || [];
    acc[p.resource].push(p);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div>
      <h1 className="settings-page-title">Phân quyền</h1>
      
      <div style={{ display: 'flex', gap: '2rem' }}>
        <div style={{ width: '250px' }}>
          <h3 style={{ marginBottom: '1rem' }}>Chọn vai trò</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {roles.map(r => (
              <button
                key={r.id}
                onClick={() => handleSelectRole(r.id)}
                style={{
                  padding: '0.5rem 1rem',
                  textAlign: 'left',
                  border: '1px solid var(--color-border)',
                  borderRadius: '4px',
                  background: selectedRole === r.id ? 'var(--color-primary-light)' : 'transparent',
                  color: selectedRole === r.id ? 'var(--color-primary)' : 'inherit',
                  fontWeight: selectedRole === r.id ? 600 : 400,
                  cursor: 'pointer'
                }}
              >
                {r.name}
              </button>
            ))}
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Ma trận quyền</h3>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving || !selectedRole}>
              {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
            {Object.entries(groupedPerms).map(([resource, perms]) => (
              <div key={resource} style={{ border: '1px solid var(--color-border)', borderRadius: '4px', padding: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', textTransform: 'capitalize', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>
                  {resource}
                </div>
                {(perms as any[]).map((p: any) => (
                  <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0', cursor: 'pointer' }}>
                    <input 
                      type="checkbox" 
                      checked={rolePerms.includes(p.id)}
                      onChange={() => togglePermission(p.id)}
                    />
                    <span style={{ fontSize: '0.875rem' }}>{p.action}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
