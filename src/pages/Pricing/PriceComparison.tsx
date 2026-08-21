import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Button, Table, Tag, Typography, Card, message, Image } from 'antd';
import { ArrowLeftOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import { api } from '../../utils/api';

const { Title, Text } = Typography;

export function PriceComparison() {
  const [searchParams] = useSearchParams();
  const listA = searchParams.get('a');
  const listB = searchParams.get('b');
  
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchComparison = async () => {
      if (!listA || !listB) return;
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/pricing/price-lists/compare?list_a=${listA}&list_b=${listB}`);
        setData(res.data.data || []);
      } catch (err: any) {
        message.error(err.response?.data?.detail || 'Lỗi khi so sánh bảng giá');
      } finally {
        setLoading(false);
      }
    };
    fetchComparison();
  }, [listA, listB]);

  const columns = [
    {
      title: 'Mã Sản Phẩm',
      dataIndex: 'product_code',
      key: 'product_code',
    },
    {
      title: 'Tên / Nhóm',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: 'Hình Ảnh',
      dataIndex: 'image_url',
      key: 'image_url',
      render: (url: string) => url ? <Image src={url} width={40} height={40} style={{objectFit: 'contain'}} /> : null
    },
    {
      title: 'Giá Cũ (Kỳ trước)',
      dataIndex: 'price_a',
      key: 'price_a',
      align: 'right' as const,
      render: (val: number) => val ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val) : '-',
    },
    {
      title: 'Giá Mới (Kỳ này)',
      dataIndex: 'price_b',
      key: 'price_b',
      align: 'right' as const,
      render: (val: number) => val ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val) : '-',
    },
    {
      title: 'Chênh Lệch',
      dataIndex: 'diff',
      key: 'diff',
      align: 'right' as const,
      render: (val: number) => {
        if (!val) return '-';
        const color = val > 0 ? 'text-red-500' : 'text-green-500';
        const sign = val > 0 ? '+' : '';
        return (
          <span className={color}>
            {sign}{new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val)}
          </span>
        );
      },
    },
    {
      title: 'Trạng Thái',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'default';
        let icon = null;
        if (status === 'Tăng giá') { color = 'red'; icon = <ArrowUpOutlined />; }
        if (status === 'Giảm giá') { color = 'green'; icon = <ArrowDownOutlined />; }
        if (status === 'Không đổi') { color = 'blue'; icon = <MinusOutlined />; }
        if (status === 'Sản phẩm mới') color = 'cyan';
        if (status === 'Ngừng áp dụng') color = 'gray';
        
        return <Tag color={color} icon={icon}>{status}</Tag>;
      }
    }
  ];

  return (
    <div>
      <div className="mb-4">
        <Link to="/ban-hang/bang-gia">
          <Button type="link" icon={<ArrowLeftOutlined />}>Quay lại danh sách</Button>
        </Link>
      </div>

      <div className="mb-6">
        <Title level={3} className="m-0">So Sánh Bảng Giá</Title>
        <Text type="secondary">Phân tích biến động giá giữa hai kỳ</Text>
      </div>

      <Card>
        <Table 
          columns={columns} 
          dataSource={data} 
          rowKey="product_code" 
          loading={loading}
          pagination={{ pageSize: 50 }}
        />
      </Card>
    </div>
  );
}
