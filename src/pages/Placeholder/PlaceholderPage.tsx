// ===================================================
// TRADECORE — PLACEHOLDER PAGE
// Used for routes not yet implemented
// ===================================================

import { Link, useLocation } from 'react-router-dom';

export function PlaceholderPage() {
  const { pathname } = useLocation();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
      gap: 'var(--space-4)',
    }}>
      <div style={{
        width: 48,
        height: 48,
        borderRadius: 'var(--radius-lg)',
        background: 'var(--color-primary-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-primary)',
        fontSize: '20px',
      }}>
        🚧
      </div>
      <div>
        <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Trang đang phát triển
        </h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-base)' }}>
          Tính năng <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--color-surface-overlay)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>{pathname}</code> sẽ sớm ra mắt.
        </p>
      </div>
      <Link
        to="/"
        style={{
          marginTop: 'var(--space-2)',
          color: 'var(--color-primary)',
          fontWeight: 500,
          fontSize: 'var(--font-size-base)',
        }}
      >
        ← Về tổng quan
      </Link>
    </div>
  );
}
