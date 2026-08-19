import React, { useState, useEffect } from 'react';
import { api } from '../../utils/api';
import './Settings.css';

export function ImportSettings() {
  const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Upload State
  const [entityType, setEntityType] = useState('product');
  const [file, setFile] = useState<File | null>(null);
  const [uploadRun, setUploadRun] = useState<any>(null);
  const [dryRunResult, setDryRunResult] = useState<any>(null);

  const fetchHistory = () => {
    setLoading(true);
    api.get('/api/v1/imports')
      .then(res => setHistory(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('entity_type', entityType);
    formData.append('file', file);

    try {
      const res = await api.post('/api/v1/imports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadRun(res.data);
      setDryRunResult(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi tải tệp lên');
    } finally {
      setLoading(false);
    }
  };

  const handleDryRun = async () => {
    if (!uploadRun) return;
    setLoading(true);
    try {
      const res = await api.post(`/api/v1/imports/${uploadRun.id}/dry-run`);
      setDryRunResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi chạy thử');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!uploadRun) return;
    setLoading(true);
    try {
      await api.post(`/api/v1/imports/${uploadRun.id}/confirm`);
      alert('Đã xác nhận nhập dữ liệu thành công!');
      setUploadRun(null);
      setDryRunResult(null);
      setFile(null);
      setActiveTab('history');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi khi xác nhận');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="settings-page-title">Nhập dữ liệu</h1>
      
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--color-border)', marginBottom: '2rem' }}>
        <button 
          onClick={() => setActiveTab('upload')} 
          style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'upload' ? '2px solid var(--color-primary)' : '2px solid transparent', color: activeTab === 'upload' ? 'var(--color-primary)' : 'inherit', cursor: 'pointer', fontWeight: activeTab === 'upload' ? 600 : 400 }}
        >
          Tải tệp lên
        </button>
        <button 
          onClick={() => setActiveTab('history')} 
          style={{ padding: '0.5rem 1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'history' ? '2px solid var(--color-primary)' : '2px solid transparent', color: activeTab === 'history' ? 'var(--color-primary)' : 'inherit', cursor: 'pointer', fontWeight: activeTab === 'history' ? 600 : 400 }}
        >
          Lịch sử nhập
        </button>
      </div>

      {activeTab === 'upload' && (
        <div style={{ maxWidth: '600px' }}>
          {!uploadRun ? (
            <form className="settings-form" onSubmit={handleUpload}>
              <div className="form-group">
                <label>Loại dữ liệu</label>
                <select className="input" value={entityType} onChange={e => setEntityType(e.target.value)}>
                  <option value="product">Sản phẩm</option>
                  <option value="customer">Khách hàng</option>
                  <option value="supplier">Nhà cung cấp</option>
                  <option value="inventory">Tồn kho</option>
                  <option value="price_item">Bảng giá</option>
                </select>
              </div>
              <div className="form-group">
                <label>Tệp Excel/CSV</label>
                <input type="file" className="input" accept=".xlsx,.xls,.csv" onChange={handleFileChange} required />
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading || !file}>
                {loading ? 'Đang tải...' : 'Tải tệp lên'}
              </button>
            </form>
          ) : (
            <div style={{ padding: '1.5rem', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
              <h3 style={{ marginTop: 0 }}>Tệp đã tải lên: {uploadRun.source_file}</h3>
              <p>Trạng thái: <strong>{uploadRun.status}</strong></p>
              
              {!dryRunResult ? (
                <div style={{ marginTop: '1.5rem' }}>
                  <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }}>Vui lòng chạy thử (dry-run) để hệ thống kiểm tra dữ liệu trước khi lưu chính thức.</p>
                  <button className="btn btn-outline" onClick={handleDryRun} disabled={loading}>
                    {loading ? 'Đang kiểm tra...' : 'Kiểm tra dữ liệu (Chạy thử)'}
                  </button>
                  <button className="btn btn-outline" style={{ marginLeft: '1rem', color: 'red', borderColor: 'red' }} onClick={() => {setUploadRun(null); setFile(null);}}>Hủy</button>
                </div>
              ) : (
                <div style={{ marginTop: '1.5rem' }}>
                  <div style={{ background: '#f9fafb', padding: '1rem', borderRadius: '4px', marginBottom: '1rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0' }}>Kết quả kiểm tra</h4>
                    <div>Tổng số dòng: <strong>{dryRunResult.total_rows}</strong></div>
                    <div style={{ color: 'red' }}>Lỗi: <strong>{dryRunResult.errors}</strong></div>
                    <div style={{ color: '#f57c00' }}>Cảnh báo: <strong>{dryRunResult.warnings}</strong></div>
                  </div>
                  <button className="btn btn-primary" onClick={handleConfirm} disabled={loading}>
                    {loading ? 'Đang xử lý...' : 'Xác nhận nhập dữ liệu chính thức'}
                  </button>
                  <button className="btn btn-outline" style={{ marginLeft: '1rem', color: 'red', borderColor: 'red' }} onClick={() => {setUploadRun(null); setFile(null); setDryRunResult(null)}}>Hủy</button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div>
          {loading ? <div>Đang tải...</div> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>Người tải lên</th>
                    <th>Loại dữ liệu</th>
                    <th>Tên tệp</th>
                    <th>Trạng thái</th>
                    <th>Tổng số</th>
                    <th>Lỗi</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <tr key={h.id}>
                      <td>{new Date(h.started_at).toLocaleString('vi-VN')}</td>
                      <td>{h.created_by}</td>
                      <td>{h.entity_type}</td>
                      <td>{h.source_file}</td>
                      <td>
                        <span style={{ 
                          padding: '2px 6px', borderRadius: '4px', fontSize: '12px',
                          background: h.status === 'completed' ? '#e8f5e9' : h.status === 'running' ? '#fff3e0' : '#ffebee',
                          color: h.status === 'completed' ? '#2e7d32' : h.status === 'running' ? '#f57c00' : '#c62828'
                        }}>
                          {h.status === 'completed' ? 'Hoàn tất' : h.status === 'running' ? 'Đang xử lý' : h.status === 'partial' ? 'Chờ xác nhận' : 'Lỗi'}
                        </span>
                      </td>
                      <td>{h.total_rows}</td>
                      <td style={{ color: h.error_rows > 0 ? 'red' : 'inherit' }}>{h.error_rows}</td>
                    </tr>
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>Chưa có lịch sử nhập dữ liệu</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
