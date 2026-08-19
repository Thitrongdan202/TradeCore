"""
TradeCore — Available Permissions Definition
"""
from typing import List, Dict

# Standard actions
ACTION_VIEW = "view"
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_APPROVE = "approve"
ACTION_IMPORT = "import"
ACTION_EXPORT = "export"

STANDARD_ACTIONS = [
    ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE,
    ACTION_APPROVE, ACTION_IMPORT, ACTION_EXPORT
]

# Vietnamese translations for actions
ACTION_NAMES = {
    ACTION_VIEW: "Xem",
    ACTION_CREATE: "Thêm",
    ACTION_UPDATE: "Sửa",
    ACTION_DELETE: "Xóa",
    ACTION_APPROVE: "Phê duyệt",
    ACTION_IMPORT: "Nhập dữ liệu",
    ACTION_EXPORT: "Xuất dữ liệu"
}

# Define resources and their applicable actions
RESOURCES: Dict[str, Dict[str, List[str]]] = {
    "overview": {
        "name": "Tổng quan",
        "actions": [ACTION_VIEW]
    },
    "quotation": {
        "name": "Báo giá",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "sales_order": {
        "name": "Đơn bán hàng",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "invoice": {
        "name": "Hóa đơn",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "purchase_request": {
        "name": "Đề nghị mua",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE]
    },
    "purchase_order": {
        "name": "Đơn mua hàng",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "inventory": {
        "name": "Tồn kho",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_APPROVE, ACTION_IMPORT, ACTION_EXPORT]
    },
    "stock_in": {
        "name": "Nhập kho",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "stock_out": {
        "name": "Xuất kho",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE, ACTION_EXPORT]
    },
    "stock_transfer": {
        "name": "Chuyển kho",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE]
    },
    "import_shipment": {
        "name": "Nhập khẩu",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE]
    },
    "export_shipment": {
        "name": "Xuất khẩu",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_APPROVE]
    },
    "shipment_batch": {
        "name": "Lô hàng",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE]
    },
    "container": {
        "name": "Container",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE]
    },
    "customer": {
        "name": "Khách hàng",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_IMPORT, ACTION_EXPORT]
    },
    "supplier": {
        "name": "Nhà cung cấp",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_IMPORT, ACTION_EXPORT]
    },
    "product": {
        "name": "Sản phẩm",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_IMPORT, ACTION_EXPORT]
    },
    "price_list": {
        "name": "Bảng giá",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE, ACTION_IMPORT, ACTION_EXPORT]
    },
    "report": {
        "name": "Báo cáo",
        "actions": [ACTION_VIEW, ACTION_EXPORT]
    },
    "user": {
        "name": "Người dùng",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE]
    },
    "role": {
        "name": "Vai trò",
        "actions": [ACTION_VIEW, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE]
    },
    "permission": {
        "name": "Phân quyền",
        "actions": [ACTION_VIEW]
    },
    "company_setting": {
        "name": "Cài đặt công ty",
        "actions": [ACTION_VIEW, ACTION_UPDATE]
    },
    "audit_log": {
        "name": "Nhật ký hoạt động",
        "actions": [ACTION_VIEW, ACTION_EXPORT]
    },
    "tech_support": {
        "name": "Hỗ trợ kỹ thuật",
        "actions": [ACTION_VIEW, ACTION_UPDATE]
    }
}
