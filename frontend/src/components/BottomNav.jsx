/**
 * BottomNav — navegação inferior
 * Presente em todas as telas do MainLayout (/, /events, /my-photos, /profile, /photo/:id)
 *
 * 5 itens:
 *   Início      → /
 *   Eventos     → /events
 *   📷 (centro) → /choose  (inicia fluxo de busca)
 *   Minhas Fotos→ /my-photos
 *   Perfil      → /profile
 *
 * Estado ativo:
 *   A função is(path) verifica pathname === path OU pathname.startsWith(path + '/')
 *   O item Início usa lógica negativa adicional para não ativar quando em /events, /my-photos ou /profile
 */

import { useNavigate, useLocation } from 'react-router-dom';

const IconHome = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);
const IconEvents = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);
const IconCamera = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
    <circle cx="12" cy="13" r="4" />
  </svg>
);
const IconPhotos = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </svg>
);
const IconProfile = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

export default function BottomNav() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // Retorna true se pathname é exatamente path ou começa com path/
  const is = (path) => pathname === path || pathname.startsWith(path + '/');

  return (
    <nav className="bottom-nav" role="navigation" aria-label="Navegação principal">
      <button
        className={`nav-item ${is('/') && !is('/events') && !is('/my-photos') && !is('/profile') ? 'active' : ''}`}
        onClick={() => navigate('/')}
        aria-label="Início"
      >
        <IconHome />
        <span>Início</span>
      </button>

      <button
        className={`nav-item ${is('/events') ? 'active' : ''}`}
        onClick={() => navigate('/events')}
        aria-label="Eventos"
      >
        <IconEvents />
        <span>Eventos</span>
      </button>

      {/* Botão central de busca — sempre proeminente */}
      <div className="nav-item-center">
        <button
          className="nav-cam-btn"
          onClick={() => navigate('/choose')}
          aria-label="Encontrar fotos"
        >
          <IconCamera />
        </button>
      </div>

      <button
        className={`nav-item ${is('/my-photos') ? 'active' : ''}`}
        onClick={() => navigate('/my-photos')}
        aria-label="Minhas Fotos"
      >
        <IconPhotos />
        <span>Minhas Fotos</span>
      </button>

      <button
        className={`nav-item ${is('/profile') ? 'active' : ''}`}
        onClick={() => navigate('/profile')}
        aria-label="Perfil"
      >
        <IconProfile />
        <span>Perfil</span>
      </button>
    </nav>
  );
}
