// ===================================================
// TRADECORE — MOCK DATA LAYER
//
// This module is the isolated data layer for Phase 1.
// Replace these functions with API calls (FastAPI) in Phase 2
// without touching any UI components.
// ===================================================

import type {
  SalesOrder,
  PurchaseOrder,
  Shipment,
  StockItem,
  RevenueDataPoint,
  KPISummary,
} from '../types';

// ─── KPI Summary ───────────────────────────────────
export async function fetchKPISummary(): Promise<KPISummary> {
  return {
    revenueThisMonth: 4_280_000_000,
    revenueLastMonth: 3_812_000_000,
    ordersThisMonth: 134,
    ordersLastMonth: 118,
    inventoryValue: 8_740_000_000,
    receivable: 1_320_000_000,
    payable: 870_000_000,
  };
}

// ─── Sales Orders ──────────────────────────────────
export async function fetchRecentSalesOrders(): Promise<SalesOrder[]> {
  return [
    {
      id: 'so-001', orderNumber: 'SO-2408-0134',
      customerName: 'Công ty TNHH Minh Phát',
      customerCode: 'KH-0041',
      date: '2026-08-12', dueDate: '2026-08-26',
      total: 284_500_000, paid: 284_500_000,
      status: 'completed', paymentStatus: 'paid', items: 8,
    },
    {
      id: 'so-002', orderNumber: 'SO-2408-0133',
      customerName: 'Tập đoàn Thành Công Group',
      customerCode: 'KH-0017',
      date: '2026-08-11', dueDate: '2026-08-25',
      total: 612_000_000, paid: 300_000_000,
      status: 'confirmed', paymentStatus: 'partial', items: 15,
    },
    {
      id: 'so-003', orderNumber: 'SO-2408-0132',
      customerName: 'Cty CP Hòa Bình Tech',
      customerCode: 'KH-0083',
      date: '2026-08-11', dueDate: '2026-08-25',
      total: 97_200_000, paid: 0,
      status: 'processing', paymentStatus: 'unpaid', items: 4,
    },
    {
      id: 'so-004', orderNumber: 'SO-2408-0131',
      customerName: 'DNTN Ngọc Việt',
      customerCode: 'KH-0029',
      date: '2026-08-10', dueDate: '2026-08-24',
      total: 148_900_000, paid: 148_900_000,
      status: 'shipping', paymentStatus: 'paid', items: 6,
    },
    {
      id: 'so-005', orderNumber: 'SO-2408-0130',
      customerName: 'Công ty TNHH TM DV Phú Quý',
      customerCode: 'KH-0056',
      date: '2026-08-09',
      total: 52_600_000, paid: 0,
      status: 'pending', paymentStatus: 'unpaid', items: 3,
    },
    {
      id: 'so-006', orderNumber: 'SO-2408-0129',
      customerName: 'Cty CP Xây dựng Đông Nam',
      customerCode: 'KH-0072',
      date: '2026-08-08',
      total: 335_000_000, paid: 0,
      status: 'cancelled', paymentStatus: 'unpaid', items: 11,
    },
  ];
}

// ─── Purchase Orders ───────────────────────────────
export async function fetchRecentPurchaseOrders(): Promise<PurchaseOrder[]> {
  return [
    {
      id: 'po-001', orderNumber: 'PO-2408-0047',
      supplierName: 'Zhejiang Longway Industrial Co.',
      supplierCode: 'NCC-0012', country: 'Trung Quốc',
      date: '2026-08-10', expectedDate: '2026-09-05',
      total: 1_240_000_000, paid: 620_000_000,
      status: 'confirmed', paymentStatus: 'partial', items: 12,
    },
    {
      id: 'po-002', orderNumber: 'PO-2408-0046',
      supplierName: 'Korea Precision Parts Ltd.',
      supplierCode: 'NCC-0028', country: 'Hàn Quốc',
      date: '2026-08-09', expectedDate: '2026-08-28',
      total: 654_000_000, paid: 654_000_000,
      status: 'shipping', paymentStatus: 'paid', items: 7,
    },
    {
      id: 'po-003', orderNumber: 'PO-2408-0045',
      supplierName: 'Taiwan Excellence Electronics',
      supplierCode: 'NCC-0035', country: 'Đài Loan',
      date: '2026-08-07',
      total: 2_180_000_000, paid: 0,
      status: 'pending', paymentStatus: 'unpaid', items: 24,
    },
    {
      id: 'po-004', orderNumber: 'PO-2408-0044',
      supplierName: 'Guangzhou Trading Intl.',
      supplierCode: 'NCC-0009', country: 'Trung Quốc',
      date: '2026-08-06', expectedDate: '2026-08-22',
      total: 418_500_000, paid: 418_500_000,
      status: 'completed', paymentStatus: 'paid', items: 8,
    },
    {
      id: 'po-005', orderNumber: 'PO-2408-0043',
      supplierName: 'Thai Manufacturing Group',
      supplierCode: 'NCC-0041', country: 'Thái Lan',
      date: '2026-08-05',
      total: 327_000_000, paid: 0,
      status: 'processing', paymentStatus: 'unpaid', items: 5,
    },
  ];
}

// ─── Shipments ─────────────────────────────────────
export async function fetchActiveShipments(): Promise<Shipment[]> {
  return [
    {
      id: 'sh-001', shipmentNumber: 'SHP-2408-0018',
      description: 'Linh kiện điện tử – Lô 08/2026',
      supplier: 'Zhejiang Longway Industrial',
      origin: 'Trung Quốc', destination: 'Việt Nam',
      portOrigin: 'Cảng Thượng Hải', portDestination: 'Cảng Hải Phòng',
      etd: '2026-08-14', eta: '2026-08-28',
      status: 'in_transit', containers: 2, weight: 18_400, value: 54_200,
    },
    {
      id: 'sh-002', shipmentNumber: 'SHP-2408-0017',
      description: 'Phụ tùng máy – Lô Hàn Quốc',
      supplier: 'Korea Precision Parts',
      origin: 'Hàn Quốc', destination: 'Việt Nam',
      portOrigin: 'Cảng Busan', portDestination: 'Cảng Cát Lái',
      etd: '2026-08-09', eta: '2026-08-24',
      status: 'arrived', containers: 1, weight: 6_200, value: 28_400,
    },
    {
      id: 'sh-003', shipmentNumber: 'SHP-2408-0016',
      description: 'Máy móc thiết bị – Đài Loan',
      supplier: 'Taiwan Excellence Electronics',
      origin: 'Đài Loan', destination: 'Việt Nam',
      portOrigin: 'Cảng Keelung', portDestination: 'Cảng Đà Nẵng',
      etd: '2026-08-20', eta: '2026-09-04',
      status: 'booking', containers: 3, weight: 32_000, value: 94_600,
    },
    {
      id: 'sh-004', shipmentNumber: 'SHP-2408-0015',
      description: 'Vải nguyên liệu – Thái Lan',
      supplier: 'Thai Manufacturing Group',
      origin: 'Thái Lan', destination: 'Việt Nam',
      portOrigin: 'Cảng Laem Chabang', portDestination: 'Cảng Cát Lái',
      etd: '2026-08-05', eta: '2026-08-15',
      status: 'customs', containers: 1, weight: 8_800, value: 14_200,
    },
  ];
}

// ─── Stock Alerts ──────────────────────────────────
export async function fetchStockAlerts(): Promise<StockItem[]> {
  return [
    {
      id: 'sk-001', code: 'HH-2041', name: 'Bo mạch điều khiển PLC S7-300',
      category: 'Điện tử', unit: 'Cái',
      currentStock: 3, minStock: 20, maxStock: 80,
      alertLevel: 'critical', value: 4_800_000,
    },
    {
      id: 'sk-002', code: 'HH-1872', name: 'Động cơ servo 750W Mitsubishi',
      category: 'Điện cơ', unit: 'Cái',
      currentStock: 0, minStock: 10, maxStock: 40,
      alertLevel: 'out', value: 12_400_000,
    },
    {
      id: 'sk-003', code: 'HH-3305', name: 'Cảm biến nhiệt độ Pt100',
      category: 'Cảm biến', unit: 'Cái',
      currentStock: 8, minStock: 15, maxStock: 60,
      alertLevel: 'low', value: 680_000,
    },
    {
      id: 'sk-004', code: 'HH-0924', name: 'Biến tần 7.5kW Fuji Electric',
      category: 'Điện tử', unit: 'Cái',
      currentStock: 2, minStock: 8, maxStock: 30,
      alertLevel: 'critical', value: 9_200_000,
    },
    {
      id: 'sk-005', code: 'HH-4412', name: 'Vòng bi SKF 6308',
      category: 'Cơ khí', unit: 'Chiếc',
      currentStock: 14, minStock: 30, maxStock: 120,
      alertLevel: 'low', value: 185_000,
    },
  ];
}

// ─── Revenue Chart Data ────────────────────────────
export async function fetchRevenueChart(): Promise<RevenueDataPoint[]> {
  return [
    { month: 'Th.3', revenue: 2_840_000_000, cost: 2_100_000_000, profit: 740_000_000 },
    { month: 'Th.4', revenue: 3_120_000_000, cost: 2_340_000_000, profit: 780_000_000 },
    { month: 'Th.5', revenue: 2_960_000_000, cost: 2_180_000_000, profit: 780_000_000 },
    { month: 'Th.6', revenue: 3_580_000_000, cost: 2_600_000_000, profit: 980_000_000 },
    { month: 'Th.7', revenue: 3_812_000_000, cost: 2_780_000_000, profit: 1_032_000_000 },
    { month: 'Th.8', revenue: 4_280_000_000, cost: 3_100_000_000, profit: 1_180_000_000 },
  ];
}

// ─── Formatters (UI helpers, not API-specific) ─────
export function formatVND(amount: number, compact = false): string {
  if (compact) {
    if (amount >= 1_000_000_000) {
      return `${(amount / 1_000_000_000).toFixed(1).replace(/\.0$/, '')} tỷ`;
    }
    if (amount >= 1_000_000) {
      return `${(amount / 1_000_000).toFixed(0)} tr`;
    }
    return `${amount.toLocaleString('vi-VN')}đ`;
  }
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    minimumFractionDigits: 0,
  }).format(amount);
}

export function formatUSD(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

export function formatWeight(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)} tấn`;
  return `${kg.toLocaleString('vi-VN')} kg`;
}
