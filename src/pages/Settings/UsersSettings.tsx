import React, { useEffect, useState } from 'react';
import { api } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';

export function UsersSettings() {
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [effectivePerms, setEffectivePerms] = useState<any[] | null>(null);
  const [viewingUser, setViewingUser] = useState<string | null>(null);

  // Password viewing state
  const [revealedPasswords, setRevealedPasswords] = useState<
    Record<string, string>
  >({});

  // Form password visibility
  const [showPassword, setShowPassword] = useState(false);

  // Check current user's permission
  const canViewPassword =
    currentUser?.permissions?.includes('user:password_view') ?? false;

  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    role_ids: [] as string[],
    is_active: true,
  });

  const fetchUsers = async () => {
    try {
      const res = await api.get('/api/v1/users');
      setUsers(res.data.items ?? []);
    } catch (error) {
      console.error('Không thể tải danh sách người dùng', error);
    }
  };

  const fetchRoles = async () => {
    try {
      const res = await api.get('/api/v1/users/roles');
      setRoles(res.data ?? []);
    } catch (error) {
      console.error('Không thể tải danh sách vai trò', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);

      try {
        await Promise.all([fetchUsers(), fetchRoles()]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const resetForm = () => {
    setFormData({
      username: '',
      full_name: '',
      email: '',
      password: '',
      confirm_password: '',
      role_ids: [],
      is_active: true,
    });

    setShowPassword(false);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirm_password) {
      alert('Mật khẩu xác nhận không khớp');
      return;
    }

    try {
      await api.post('/api/v1/users', formData);

      setShowForm(false);
      resetForm();
      await fetchUsers();

      alert('Đã tạo người dùng thành công');
    } catch (err: any) {
      alert(
        err.response?.data?.detail || 'Lỗi khi thêm người dùng',
      );
    }
  };

  const toggleStatus = async (user: any) => {
    try {
      await api.put(`/api/v1/users/${user.id}`, {
        is_active: !user.is_active,
      });

      await fetchUsers();
    } catch (err: any) {
      alert(
        err.response?.data?.detail ||
          'Không thể cập nhật trạng thái tài khoản',
      );
    }
  };

  const resetPassword = async (user: any) => {
    const newPassword = window.prompt(
      `Nhập mật khẩu mới cho tài khoản ${user.username}:`,
    );

    if (!newPassword) {
      return;
    }

    if (newPassword.length < 6) {
      alert('Mật khẩu phải có ít nhất 6 ký tự');
      return;
    }

    try {
      await api.put(
        `/api/v1/users/${user.id}/reset-password`,
        {
          new_password: newPassword,
        },
      );

      alert('Đã đặt lại mật khẩu thành công');
    } catch (err: any) {
      alert(
        err.response?.data?.detail ||
          'Không thể đặt lại mật khẩu',
      );
    }
  };

  const viewPermissions = async (user: any) => {
    if (viewingUser === user.id) {
      setViewingUser(null);
      setEffectivePerms(null);
      return;
    }

    try {
      const res = await api.get(
        `/api/v1/users/${user.id}/effective-permissions`,
      );

      setEffectivePerms(res.data ?? []);
      setViewingUser(user.id);
    } catch (err: any) {
      alert(
        err.response?.data?.detail ||
          'Lỗi tải danh sách quyền',
      );
    }
  };

  const handleViewPassword = async (user: any) => {
    if (!canViewPassword) {
      return;
    }

    if (revealedPasswords[user.id]) {
      setRevealedPasswords((prev) => {
        const next = { ...prev };
        delete next[user.id];
        return next;
      });

      return;
    }

    try {
      const res = await api.get(
        `/api/v1/users/${user.id}/password`,
      );

      const password = res.data.password;

      setRevealedPasswords((prev) => ({
        ...prev,
        [user.id]: password,
      }));

      window.setTimeout(() => {
        setRevealedPasswords((prev) => {
          const next = { ...prev };
          delete next[user.id];
          return next;
        });
      }, 10000);
    } catch (err: any) {
      alert(
        err.response?.data?.detail ||
          'Không thể xem mật khẩu',
      );
    }
  };

  if (loading) {
    return <div>Đang tải...</div>;
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
        }}
      >
        <h1
          className="settings-page-title"
          style={{ margin: 0 }}
        >
          Người dùng
        </h1>

        <button
          className="btn btn-primary"
          onClick={() => {
            setShowForm((prev) => !prev);

            if (showForm) {
              resetForm();
            }
          }}
        >
          {showForm ? 'Hủy' : '+ Thêm người dùng'}
        </button>
      </div>

      {showForm && (
        <form
          className="settings-form"
          onSubmit={handleAdd}
          style={{
            marginBottom: '2rem',
            padding: '1rem',
            border: '1px solid var(--color-border)',
            borderRadius: '4px',
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns:
                'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1rem',
            }}
          >
            <div className="form-group">
              <label>Họ và tên</label>

              <input
                className="input"
                value={formData.full_name}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    full_name: e.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>Tên đăng nhập</label>

              <input
                className="input"
                value={formData.username}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    username: e.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>Email</label>

              <input
                className="input"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    email: e.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>Số điện thoại</label>

              <input
                className="input"
                type="text"
                placeholder="Tùy chọn"
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
                <span>Mật khẩu khởi tạo</span>

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((prev) => !prev)
                  }
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-primary)',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                >
                  {showPassword
                    ? 'Ẩn mật khẩu'
                    : 'Xem mật khẩu'}
                </button>
              </label>

              <input
                className="input"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    password: e.target.value,
                  })
                }
                required
                minLength={6}
              />
            </div>

            <div className="form-group">
              <label>Xác nhận mật khẩu</label>

              <input
                className="input"
                type={showPassword ? 'text' : 'password'}
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
          </div>

          <div className="form-group">
            <label>Vai trò</label>

            <select
              className="input"
              multiple
              value={formData.role_ids}
              onChange={(e) => {
                const selectedRoles = Array.from(
                  e.target.selectedOptions,
                  (option) => option.value,
                );

                setFormData({
                  ...formData,
                  role_ids: selectedRoles,
                });
              }}
              style={{
                minHeight: '120px',
                width: '100%',
              }}
            >
              {roles
                .filter((role) => role.is_active)
                .map((role) => (
                  <option
                    key={role.id}
                    value={role.id}
                  >
                    {role.name}
                  </option>
                ))}
            </select>

            <small
              style={{
                color: 'var(--color-text-muted)',
              }}
            >
              Nhấn giữ Ctrl/Cmd để chọn nhiều vai trò
            </small>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
          >
            Lưu người dùng
          </button>
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
            {users.map((user) => (
              <React.Fragment key={user.id}>
                <tr>
                  <td>{user.full_name}</td>

                  <td>{user.username}</td>

                  <td>{user.email}</td>

                  <td>
                    {user.roles
                      ?.map((role: any) => role.name)
                      .join(', ') || 'Chưa phân vai trò'}
                  </td>

                  <td>
                    <span
                      style={{
                        color: user.is_active
                          ? 'green'
                          : 'red',
                      }}
                    >
                      {user.is_active
                        ? 'Hoạt động'
                        : 'Đã khóa'}
                    </span>
                  </td>

                  <td>
                    <div
                      style={{
                        display: 'flex',
                        gap: '0.25rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      <button
                        className="btn btn-outline"
                        style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                        }}
                        onClick={() =>
                          viewPermissions(user)
                        }
                      >
                        Quyền
                      </button>

                      <button
                        className="btn btn-outline"
                        style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                        }}
                        onClick={() =>
                          resetPassword(user)
                        }
                      >
                        Đặt lại MK
                      </button>

                      <button
                        className="btn btn-outline"
                        style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                          color: user.is_active
                            ? 'red'
                            : 'green',
                          borderColor: user.is_active
                            ? 'red'
                            : 'green',
                        }}
                        onClick={() =>
                          toggleStatus(user)
                        }
                      >
                        {user.is_active
                          ? 'Khóa'
                          : 'Mở khóa'}
                      </button>

                      {canViewPassword && (
                        <button
                          className="btn btn-outline"
                          style={{
                            padding: '4px 8px',
                            fontSize: '12px',
                          }}
                          onClick={() =>
                            handleViewPassword(user)
                          }
                        >
                          {revealedPasswords[user.id]
                            ? 'Ẩn mật khẩu'
                            : 'Xem mật khẩu'}
                        </button>
                      )}
                    </div>

                    {revealedPasswords[user.id] && (
                      <div
                        style={{
                          marginTop: '0.5rem',
                          background: '#fff9c4',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          border: '1px solid #fbc02d',
                          display: 'inline-block',
                        }}
                      >
                        Mật khẩu:{' '}
                        <strong>
                          {revealedPasswords[user.id]}
                        </strong>
                      </div>
                    )}
                  </td>
                </tr>

                {viewingUser === user.id &&
                  effectivePerms && (
                    <tr>
                      <td
                        colSpan={6}
                        style={{
                          background: '#f9fafb',
                          padding: '1rem',
                        }}
                      >
                        <strong>
                          Quyền được cấp ({user.username}):
                        </strong>

                        <div
                          style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '0.5rem',
                            marginTop: '0.5rem',
                          }}
                        >
                          {effectivePerms.length === 0 ? (
                            <span
                              style={{
                                color:
                                  'var(--color-text-muted)',
                              }}
                            >
                              Không có quyền nào
                            </span>
                          ) : (
                            effectivePerms.map(
                              (permission) => (
                                <span
                                  key={permission.id}
                                  style={{
                                    background:
                                      '#e0e7ff',
                                    color: '#3730a3',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                  }}
                                >
                                  {permission.resource}:
                                  {permission.action}
                                </span>
                              ),
                            )
                          )}
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