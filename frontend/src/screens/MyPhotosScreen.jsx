/**
 * MyPhotosScreen — /my-photos
 * Fluxo 4 / Etapa 12
 *
 * Exibe todas as fotos que o usuário já encontrou (state.myPhotos, persiste no localStorage).
 *
 * Filtro por evento:
 *   Quando navegado a partir da EventsScreen, recebe via useLocation().state:
 *     filterEvent — UUID do evento a filtrar
 *     eventName   — nome legível para exibir no título
 *   Quando filtrado: título = eventName, back button → /events.
 *   Quando direto (sem state): título = "Minhas Fotos", sem back button.
 *
 * Abas: Todas | Favoritas
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function MyPhotosScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const { state } = useApp();
  const [tab, setTab] = useState('all');

  const photos = state.myPhotos;
  const favorites = state.favorites;

  // filterEvent e eventName chegam via navigate('/my-photos', { state: {...} }) da EventsScreen
  const eventFilter = loc?.filterEvent || null;
  const eventName = loc?.eventName || null;

  // Aplica filtro de evento antes das abas
  const base = eventFilter ? photos.filter((p) => p.event_id === eventFilter) : photos;
  const filtered = tab === 'favs' ? base.filter((p) => favorites.has(p.photo_id)) : base;

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header — back button visível apenas quando filtrado por evento */}
      <div style={{ padding: '24px 20px 12px', display: 'flex', alignItems: 'center', gap: 12 }}>
        {eventFilter && (
          <button
            className="back-btn"
            onClick={() => navigate('/events')}
            aria-label="Voltar para eventos"
          >
            ‹
          </button>
        )}
        <div>
          <h2 style={{ marginBottom: 2 }}>
            {eventName ? eventName : 'Minhas Fotos'}
          </h2>
          <p style={{ fontSize: 13 }}>
            {base.length} foto{base.length !== 1 ? 's' : ''} salva{base.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Abas */}
      <div className="tabs">
        <button className={`tab ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>Todas</button>
        <button className={`tab ${tab === 'favs' ? 'active' : ''}`} onClick={() => setTab('favs')}>Favoritas</button>
      </div>

      {/* Empty states contextualizados */}
      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">{tab === 'favs' ? '❤️' : '📷'}</div>
          <h2 style={{ marginBottom: 8 }}>
            {tab === 'favs' ? 'Sem favoritos' : eventFilter ? 'Nenhuma foto deste evento' : 'Sem fotos salvas'}
          </h2>
          <p style={{ marginBottom: 24 }}>
            {tab === 'favs'
              ? 'Marque fotos como favoritas para encontrá-las aqui.'
              : eventFilter
              ? 'Faça uma busca para encontrar suas fotos neste evento.'
              : 'Faça uma busca para encontrar suas fotos nos eventos.'}
          </p>
          {tab !== 'favs' && (
            <button className="btn btn-primary" onClick={() => navigate('/choose')}>
              Buscar fotos
            </button>
          )}
        </div>
      ) : (
        <div className="photo-grid" style={{ overflowY: 'auto', flex: 1, paddingBottom: 20 }}>
          {filtered.map((photo, i) => (
            <div
              key={photo.photo_id}
              className="photo-card"
              style={{ animationDelay: `${i * 0.05}s` }}
              onClick={() => navigate(`/photo/${photo.photo_id}`, { state: { photo } })}
            >
              <img
                src={photo.preview_url}
                alt={photo.filename}
                loading="lazy"
                onError={(e) => { e.currentTarget.style.opacity = '0.3'; }}
              />
              {favorites.has(photo.photo_id) && (
                <div style={{ position: 'absolute', top: 6, left: 6, fontSize: 16 }}>❤️</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
