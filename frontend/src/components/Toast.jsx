/**
 * Toast — notificação temporária
 * Exibido no topo de MainLayout e FlowLayout.
 * Auto-dispensado após 3s via AppContext (SHOW_TOAST → CLEAR_TOAST).
 * Kinds: 'success' | 'error' | 'default'
 * Estilizado em index.css pelo seletor .toast.{kind}
 */

import { useApp } from '../context/AppContext';

export default function Toast() {
  const { state } = useApp();
  if (!state.toast) return null;
  return (
    <div className={`toast ${state.toast.kind}`} role="alert" aria-live="polite">
      {state.toast.msg}
    </div>
  );
}
