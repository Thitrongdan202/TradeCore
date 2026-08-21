import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Table, Space, Typography, Card, Descriptions, message, Image } from 'antd';
import { DownloadOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { api } from '../../utils/api';

const { Title, Text } = Typography;

export function PriceListDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/pricing/price-lists/${id}`);
        setData(res.data);
      } catch (err: any) {
        message.error(err.response?.data?.detail || 'Lỗi khi tải chi tiết bảng giá');
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchDetail();
  }, [id]);

  const handleDownloadOriginal = () => {
    window.open(`/api/v1/pricing/price-lists/${id}/download-original`, '_blank');
  };

  const columns = [
    {
      title: 'Nhóm',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 150,
    },
    {
      title: 'Mã Hàng Mới',
      dataIndex: 'product_code',
      key: 'product_code',
      width: 120,
    },
    {
      title: 'Mã Hàng Cũ',
      dataIndex: 'old_code',
      key: 'old_code',
      width: 120,
    },
    {
      title: 'Hình Ảnh',
      dataIndex: 'image_url',
      key: 'image_url',
      width: 100,
      render: (url: string) => url ? <Image src={url} width={50} height={50} style={{objectFit: 'contain'}} /> : null
    },
    {
      title: 'Thông Tin Sản Phẩm',
      dataIndex: 'specifications',
      key: 'specifications',
      width: 250,
    },
    {
      title: 'Giá Đại Lý KM (Chưa VAT)',
      dataIndex: 'price',
      key: 'price',
      width: 150,
      align: 'right' as const,
      render: (val: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val),
    }
  ];

  if (!data) return null;

  return (
    <div>
      <div className="mb-4">
        <Link to="/ban-hang/bang-gia">
          <Button type="link" icon={<ArrowLeftOutlined />}>Quay lại danh sách</Button>
        </Link>
      </div>

      <div className="flex justify-between items-start mb-6">
        <div>
          <Title level={3} className="m-0">{data.name}</Title>
          <Text type="secondary">{data.status || 'Nháp'}</Text>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleDownloadOriginal}>Tải file Excel gốc</Button>
        </Space>
      </div>

      <Card className="mb-6">
        <Descriptions bordered column={{ xxl: 3, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
          <Descriptions.Item label="Số Báo Giá">{data.quotation_number || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Ngày Báo Giá">{data.quotation_date || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Ghi Chú VAT">{data.vat_notes || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Thời Gian Áp Dụng" span={3}>{data.pricing_conditions || 'N/A'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={`Danh sách mặt hàng (${data.items?.length || 0})`}>
        <Table 
          columns={columns} 
          dataSource={data.items || []} 
          rowKey="id" 
          loading={loading}
          pagination={{ pageSize: 50 }}
          scroll={{ x: 'max-content' }}
        />
      </Card>
    </div>
  );
}
