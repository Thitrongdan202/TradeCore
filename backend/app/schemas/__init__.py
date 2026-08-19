"""
TradeCore — Pydantic Schemas Package
Exports all schemas for API request validation and response serialization.
"""
from .common import MessageResponse, PaginatedResponse
from .user import (
    RoleBase, RoleCreate, RoleUpdate, RoleResponse,
    UserBase, UserCreate, UserUpdate, UserResponse, UserWithRolesResponse,
)
from .product import (
    ProductTypeEnum, UoMCategoryEnum, UoMTypeEnum,
    UnitOfMeasureBase, UnitOfMeasureCreate, UnitOfMeasureUpdate, UnitOfMeasureResponse,
    ProductCategoryBase, ProductCategoryCreate, ProductCategoryUpdate,
    ProductCategoryResponse, ProductCategoryTreeResponse,
    ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductDetailResponse,
)
from .partner import (
    PaymentTermBase, PaymentTermCreate, PaymentTermUpdate, PaymentTermResponse,
    CustomerBase, CustomerCreate, CustomerUpdate, CustomerResponse, CustomerDetailResponse,
    SupplierBase, SupplierCreate, SupplierUpdate, SupplierResponse, SupplierDetailResponse,
)
from .inventory import (
    LocationTypeEnum, MovementTypeEnum, ReferenceTypeEnum,
    WarehouseBase, WarehouseCreate, WarehouseUpdate, WarehouseResponse, WarehouseDetailResponse,
    WarehouseLocationBase, WarehouseLocationCreate, WarehouseLocationUpdate, WarehouseLocationResponse,
    StockBalanceResponse,
    StockMovementCreate, StockMovementResponse, StockAdjustmentCreate,
)
from .pricing import (
    PriceListItemBase, PriceListItemCreate, PriceListItemUpdate, PriceListItemResponse,
    PriceListBase, PriceListCreate, PriceListUpdate, PriceListResponse, PriceListDetailResponse,
    PriceLookupResponse,
)
from .sales import (
    OrderStatusEnum, PaymentStatusEnum,
    SalesOrderItemBase, SalesOrderItemCreate, SalesOrderItemUpdate, SalesOrderItemResponse,
    SalesOrderBase, SalesOrderCreate, SalesOrderUpdate,
    SalesOrderStatusUpdate, SalesOrderPaymentUpdate,
    SalesOrderResponse, SalesOrderDetailResponse,
)
from .purchase import (
    PurchaseOrderItemBase, PurchaseOrderItemCreate, PurchaseOrderItemUpdate, PurchaseOrderItemResponse,
    PurchaseOrderBase, PurchaseOrderCreate, PurchaseOrderUpdate,
    PurchaseOrderStatusUpdate, PurchaseOrderPaymentUpdate,
    PurchaseOrderReceiveLine, PurchaseOrderReceiveRequest,
    PurchaseOrderResponse, PurchaseOrderDetailResponse,
)
from .dashboard import (
    DashboardKPISummary, RevenueChartDataPoint,
    RecentSalesOrderSummary, RecentPurchaseOrderSummary,
    LowStockItem, DashboardResponse,
)

__all__ = [
    # Common
    "MessageResponse",
    "PaginatedResponse",
    # User / Role
    "RoleBase", "RoleCreate", "RoleUpdate", "RoleResponse",
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserWithRoleResponse",
    # Products & UoM
    "ProductTypeEnum", "UoMCategoryEnum", "UoMTypeEnum",
    "UnitOfMeasureBase", "UnitOfMeasureCreate", "UnitOfMeasureUpdate", "UnitOfMeasureResponse",
    "ProductCategoryBase", "ProductCategoryCreate", "ProductCategoryUpdate",
    "ProductCategoryResponse", "ProductCategoryTreeResponse",
    "ProductBase", "ProductCreate", "ProductUpdate", "ProductResponse", "ProductDetailResponse",
    # Partners
    "PaymentTermBase", "PaymentTermCreate", "PaymentTermUpdate", "PaymentTermResponse",
    "CustomerBase", "CustomerCreate", "CustomerUpdate", "CustomerResponse", "CustomerDetailResponse",
    "SupplierBase", "SupplierCreate", "SupplierUpdate", "SupplierResponse", "SupplierDetailResponse",
    # Inventory
    "LocationTypeEnum", "MovementTypeEnum", "ReferenceTypeEnum",
    "WarehouseBase", "WarehouseCreate", "WarehouseUpdate", "WarehouseResponse", "WarehouseDetailResponse",
    "WarehouseLocationBase", "WarehouseLocationCreate", "WarehouseLocationUpdate", "WarehouseLocationResponse",
    "StockBalanceResponse",
    "StockMovementCreate", "StockMovementResponse", "StockAdjustmentCreate",
    # Pricing
    "PriceListItemBase", "PriceListItemCreate", "PriceListItemUpdate", "PriceListItemResponse",
    "PriceListBase", "PriceListCreate", "PriceListUpdate", "PriceListResponse", "PriceListDetailResponse",
    "PriceLookupResponse",
    # Sales
    "OrderStatusEnum", "PaymentStatusEnum",
    "SalesOrderItemBase", "SalesOrderItemCreate", "SalesOrderItemUpdate", "SalesOrderItemResponse",
    "SalesOrderBase", "SalesOrderCreate", "SalesOrderUpdate",
    "SalesOrderStatusUpdate", "SalesOrderPaymentUpdate",
    "SalesOrderResponse", "SalesOrderDetailResponse",
    # Purchase
    "PurchaseOrderItemBase", "PurchaseOrderItemCreate", "PurchaseOrderItemUpdate", "PurchaseOrderItemResponse",
    "PurchaseOrderBase", "PurchaseOrderCreate", "PurchaseOrderUpdate",
    "PurchaseOrderStatusUpdate", "PurchaseOrderPaymentUpdate",
    "PurchaseOrderReceiveLine", "PurchaseOrderReceiveRequest",
    "PurchaseOrderResponse", "PurchaseOrderDetailResponse",
    # Dashboard
    "DashboardKPISummary", "RevenueChartDataPoint",
    "RecentSalesOrderSummary", "RecentPurchaseOrderSummary",
    "LowStockItem", "DashboardResponse",
]
