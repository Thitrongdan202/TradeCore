import axios from 'axios';

/**
 * API client for TradeCore backend.
 *
 * In development: Vite proxy forwards /api/* to http://127.0.0.1:8000
 * In production:  Set VITE_API_URL to the deployed backend URL.
 *
 * Using a relative base URL ('') means all requests go to the same origin,
 * so the Vite dev proxy handles them transparently.
 */
const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request interceptor: attach JWT token ──────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('tradecore_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 globally ─────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('tradecore_token');
      if (window.location.pathname !== '/dang-nhap') {
        window.location.href = '/dang-nhap';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Classify an axios error into a user-friendly Vietnamese message.
 * Used by the login page and any other component needing error display.
 */
export function classifyApiError(err: unknown): string {
  if (!err || typeof err !== 'object') {
    return 'Đã xảy ra lỗi không xác định.';
  }
  const axiosError = err as { response?: { status?: number; data?: { detail?: string } }; request?: unknown; message?: string };

  if (axiosError.response) {
    const status = axiosError.response.status;
    const detail = axiosError.response.data?.detail;

    // Return exact backend message if available
    if (detail) return detail;

    if (status === 401) return 'Tên đăng nhập hoặc mật khẩu không chính xác.';
    if (status === 403) return 'Bạn không có quyền thực hiện thao tác này.';
    if (status === 422) return 'Dữ liệu gửi lên không hợp lệ.';
    if (status && status >= 500) return `Lỗi máy chủ (${status}). Vui lòng thử lại sau.`;
    return `Lỗi ${status ?? 'không xác định'} từ máy chủ.`;
  }

  if (axiosError.request) {
    // Request was made but no response (network error, backend down)
    return 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra backend đang chạy tại cổng 8000.';
  }

  return axiosError.message ?? 'Đã xảy ra lỗi khi gửi yêu cầu.';
}
