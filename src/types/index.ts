// ===================================================
// TRADECORE — TYPE DEFINITIONS
// Shared TypeScript types across the application
// ===================================================

// ─── Order statuses ───
export type OrderStatus =
  | 'draft'
  | 'pending'
  | 'confirmed'
  | 'processing'
  | 'shipping'
  | 'completed'
  | 'cancelled'
  | 'returned';

export type PaymentStatus =
  | 'unpaid'
  | 'partial'
  | 'paid'
  | 'overdue'
  | 'refunded';

export type ShipmentStatus =
  | 'booking'
  | 'loading'
  | 'in_transit'
  | 'arrived'
  | 'customs'
  | 'warehoused'
  | 'completed';

export type StockAlertLevel = 'low' | 'critical' | 'out';

// ─── Domain entities ───
export interface SalesOrder {
  id: string;
  orderNumber: string;
  customerName: string;
  customerCode: string;
  date: string;
  dueDate?: string;
  total: number;
  paid: number;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  items: number;
  notes?: string;
}

export interface PurchaseOrder {
  id: string;
  orderNumber: string;
  supplierName: string;
  supplierCode: string;
  country: string;
  date: string;
  expectedDate?: string;
  total: number;
  paid: number;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  items: number;
}

export interface Shipment {
  id: string;
  shipmentNumber: string;
  description: string;
  supplier: string;
  origin: string;
  destination: string;
  portOrigin: string;
  portDestination: string;
  etd: string;
  eta: string;
  status: ShipmentStatus;
  containers: number;
  weight: number; // kg
  value: number;  // USD
}

export interface StockItem {
  id: string;
  code: string;
  name: string;
  category: string;
  unit: string;
  currentStock: number;
  minStock: number;
  maxStock: number;
  alertLevel: StockAlertLevel;
  value: number; // per unit, VND
}

export interface RevenueDataPoint {
  month: string;
  revenue: number;
  cost: number;
  profit: number;
}

export interface KPISummary {
  revenueThisMonth: number;
  revenueLastMonth: number;
  ordersThisMonth: number;
  ordersLastMonth: number;
  inventoryValue: number;
  receivable: number;
  payable: number;
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  taxCode?: string;
  phone: string;
  email?: string;
  address: string;
  totalDebt: number;
  totalOrders: number;
}

export interface Supplier {
  id: string;
  code: string;
  name: string;
  country: string;
  contactName: string;
  phone: string;
  email?: string;
  totalDebt: number;
}
