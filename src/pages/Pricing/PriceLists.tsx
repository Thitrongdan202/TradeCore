import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button, Table, Space, Tag, Upload, message, Typography, Select, Card, Modal } from 'antd';
import { UploadOutlined, EyeOutlined, SwapOutlined } from '@ant-design/icons';
import { api } from '../../utils/api';

const { Title, Text } = Typography;

export function PriceLists() {
  const [lists, setLists] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fetchLists = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/pricing/price-lists');
      setLists(res.data.items || []);
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Lỗi khi tải danh sách bảng giá');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLists();
  }, []);

  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/api/v1/pricing/price-lists/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success('Tải lên và xử lý thành công!');
      onSuccess(res.data);
      fetchLists();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Lỗi tải lên');
      onError(err);
    } finally {
      setUploading(false);
    }
  };

  // State cho Compare Modal
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [selectedListA, setSelectedListA] = useState<string | null>(null);
  const [selectedListB, setSelectedListB] = useState<string | null>(null);

  const handleCompare = () => {
    if (!selectedListA || !selectedListB) {
      message.warning('Vui lòng chọn 2 bảng giá để so sánh');
      return;
    }
    window.location.href = `/ban-hang/bang-gia/so-sanh?a=${selectedListA}&b=${selectedListB}`;
  };

  const columns = [
    {
      title: 'Mã Bảng Giá / Số Báo Giá',
      dataIndex: 'code',
      key: 'code',
      render: (text: string, record: any) => (
        <Link to={`/ban-hang/bang-gia/${record.id}`}>
          {record.quotation_number || text || record.name}
        </Link>
      ),
    },
    {
      title: 'Tên Bảng Giá',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Ngày Báo Giá',
      dataIndex: 'quotation_date',
      key: 'quotation_date',
      render: (val: string, record: any) => val || record.created_at?.split('T')[0],
    },
    {
      title: 'Số Mặt Hàng',
      dataIndex: 'items_count',
      key: 'items_count',
    },
    {
      title: 'Trạng Thái',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'Đang áp dụng' ? 'green' : 'default'}>
          {status || 'Nháp'}
        </Tag>
      ),
    },
    {
      title: 'Thao Tác',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Link to={`/ban-hang/bang-gia/${record.id}`}>
            <Button icon={<EyeOutlined />} type="link">Xem</Button>
          </Link>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={3} className="m-0">Quản Lý Bảng Giá & Báo Giá</Title>
          <Text type="secondary">Cập nhật và tra cứu lịch sử giá đại lý, nhà phân phối</Text>
        </div>
        <Space>
          <Button icon={<SwapOutlined />} onClick={() => setIsCompareModalOpen(true)}>So sánh giá</Button>
          <Upload customRequest={handleUpload} showUploadList={false} accept=".xlsx,.xls">
            <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
              Tải Lên Bảng Giá (Excel)
            </Button>
          </Upload>
        </Space>
      </div>

      <Card>
        <Table 
          columns={columns} 
          dataSource={lists} 
          rowKey="id" 
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal 
        title="So sánh bảng giá" 
        open={isCompareModalOpen} 
        onCancel={() => setIsCompareModalOpen(false)}
        onOk={handleCompare}
        okText="So sánh"
        cancelText="Đóng"
      >
        <div className="flex flex-col gap-4 py-4">
          <div>
            <div className="mb-2">Bảng giá gốc (Kỳ trước)</div>
            <Select 
              className="w-full"
              placeholder="Chọn bảng giá" 
              options={lists.map(l => ({label: l.name, value: l.id}))} 
              value={selectedListA}
              onChange={setSelectedListA}
            />
          </div>
          <div>
            <div className="mb-2">Bảng giá mới (Kỳ này)</div>
            <Select 
              className="w-full"
              placeholder="Chọn bảng giá" 
              options={lists.map(l => ({label: l.name, value: l.id}))}
              value={selectedListB}
              onChange={setSelectedListB}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
