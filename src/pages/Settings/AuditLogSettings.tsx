import { useState, useEffect } from 'react';
import { api } from '../../utils/api';

export function AuditLogSettings() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');

  const fetchLogs = () => {
    api.get(`/api/v1/audit-logs?page=${page}&action=${search}`)
      .then(res => {
        setLogs(res.data.items);
        setTotalPages(res.data.total_pages);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [page, search]);

  if (loading) return <div>Đang tải...</div>;

  return (
    <div>
      <h1 className="settings-page-title">Nhật ký hoạt động</h1>
      
      <div style={{ marginBottom: '1rem' }}>
        <input 
          className="input" 
          placeholder="Tìm kiếm hành động..." 
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: '300px' }}
        />
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Người thực hiện</th>
              <th>Hành động</th>
              <th>Đối tượng (ID)</th>
              <th>IP</th>
              <th>Chi tiết</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td style={{ whiteSpace: 'nowrap' }}>{new Date(log.created_at).toLocaleString('vi-VN')}</td>
                <td>{log.user_id}</td>
                <td><code style={{ background: '#eee', padding: '2px 4px', borderRadius: '4px' }}>{log.action}</code></td>
                <td>{log.entity_id}</td>
                <td>{log.ip_address}</td>
                <td>
                  <pre style={{ margin: 0, fontSize: '0.75rem', background: '#f8f9fa', padding: '4px' }}>
                    {log.details ? JSON.stringify(log.details, null, 2) : ''}
                  </pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
        <button className="btn btn-outline" disabled={page === 1} onClick={() => setPage(page - 1)}>Trước</button>
        <span style={{ padding: '0.5rem' }}>Trang {page} / {totalPages}</span>
        <button className="btn btn-outline" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Sau</button>
      </div>
    </div>
  );
}
