/**
 * ResultsScreen — /
 * Fluxo 3 / Etapa 10
 *
 * Tela principal. Exibe os resultados da última busca com 3 abas:
 *   Todos    — todos os resultados ordenados por similaridade
 *   Eventos  — filtros por evento (nome real via event_name no resultado)
 *   Favoritos — filtrados por state.favorites (Set de photo_ids)
 *
 * 3 estados de exibição:
 *   1. Sem resultados e sem busca anterior  → empty state "Encontre suas fotos"
 *   2. Busca feita mas sem fotos (loc.empty) → empty state com dicas de selfie
 *   3. Com resultados                        → grid + abas
 *
 * Os resultados persistem em state.searchResults (memória) até a próxima busca.
 * As fotos são acessadas via navigate('/photo/:id', { state: { photo } }) — sem fetch extra.
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';

function EmptyHint({ navigate }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">🔍</div>
      <h2 style={{ marginBottom: 8 }}>Nenhuma foto encontrada</h2>
      <p style={{ marginBottom: 24 }}>
        Tente tirar uma selfie com boa iluminação, rosto centralizado e sem óculos de sol.
      </p>
      <button className="btn btn-primary" onClick={() => navigate('/choose')}>
        Tentar outra foto
      </button>
    </div>
  );
}

export default function ResultsScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const { state } = useApp();
  const [tab, setTab] = useState('all');
  const [selectedEvent, setSelectedEvent] = useState(null);

  const results = state.searchResults;
  const favorites = state.favorites;

  // ─── Estado 1: sem resultados e sem busca ────────────────────────────────

  if (results.length === 0 && loc?.empty) {
    return (
      <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 20px 0' }}>
          <h2>Suas Fotos</h2>
        </div>
        <EmptyHint navigate={navigate} />
      </div>
    );
  }

  // ─── Estado 2: vazio sem busca anterior ──────────────────────────────────

  if (results.length === 0) {
    return (
      <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 20px 0' }}>
          <h2 style={{ marginBottom: 4 }}>Suas Fotos</h2>
        </div>
        <div className="empty-state">
          <div className="empty-icon">📸</div>
          <h2 style={{ marginBottom: 8 }}>Encontre suas fotos</h2>
          <p style={{ marginBottom: 24 }}>Tire uma selfie para descobrir em quais eventos você aparece.</p>
          <button className="btn btn-primary" onClick={() => navigate('/choose')}>
            Buscar fotos
          </button>
        </div>
      </div>
    );
  }

  // ─── Estado 3: com resultados ─────────────────────────────────────────────

  // IDs únicos dos eventos presentes nos resultados
  const eventIds = [...new Set(results.map((r) => r.event_id).filter(Boolean))];

  // Mapa id → nome construído a partir do campo event_name de cada resultado
  // (event_name vem do backend desde a adição do joinedload em routes_search.py)
  const eventNameMap = Object.fromEntries(
    results.filter((r) => r.event_id).map((r) => [r.event_id, r.event_name || r.event_id])
  );

  const filtered = (() => {
    if (tab === 'favs') return results.filter((r) => favorites.has(r.photo_id));
    if (tab === 'events' && selectedEvent) return results.filter((r) => r.event_id === selectedEvent);
    return results;
  })();

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '24px 20px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ marginBottom: 2 }}>Suas Fotos</h2>
          <p style={{ fontSize: 13 }}>{results.length} foto{results.length !== 1 ? 's' : ''} encontrada{results.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          className="btn btn-ghost"
          onClick={() => navigate('/choose')}
          style={{ width: 'auto', color: 'var(--accent)', fontSize: 14 }}
        >
          Nova busca
        </button>
      </div>

      {/* Abas */}
      <div className="tabs">
        <button className={`tab ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>Todos</button>
        <button className={`tab ${tab === 'events' ? 'active' : ''}`} onClick={() => setTab('events')}>Eventos</button>
        <button className={`tab ${tab === 'favs' ? 'active' : ''}`} onClick={() => setTab('favs')}>Favoritos</button>
      </div>

      {/* Filtros de evento — visíveis só na aba Eventos */}
      {tab === 'events' && eventIds.length > 0 && (
        <div style={{ padding: '0 20px 12px', display: 'flex', gap: 8, overflowX: 'auto', scrollbarWidth: 'none' }}>
          {[null, ...eventIds].map((eid) => (
            <button
              key={eid ?? '__all__'}
              onClick={() => setSelectedEvent(eid)}
              style={{
                padding: '6px 14px', borderRadius: 20,
                border: '1px solid var(--border)',
                background: selectedEvent === eid ? 'var(--accent-dim)' : 'transparent',
                color: selectedEvent === eid ? 'var(--accent)' : 'var(--text-muted)',
                fontSize: 13, fontWeight: 600, cursor: 'pointer',
                whiteSpace: 'nowrap', fontFamily: 'inherit',
              }}
            >
              {eid ? (eventNameMap[eid] || `Evento ${eid.slice(0, 6)}…`) : 'Todos'}
            </button>
          ))}
        </div>
      )}

      {/* Grid de fotos */}
      <div className="photo-grid" style={{ overflowY: 'auto', flex: 1, paddingBottom: 20 }}>
        {filtered.map((photo, i) => (
          <div
            key={photo.photo_id}
            className="photo-card"
            style={{ animationDelay: `${i * 0.06}s` }}
            onClick={() => navigate(`/photo/${photo.photo_id}`, { state: { photo } })}
          >
            <img
              src={photo.preview_url}
              alt={photo.filename}
              loading="lazy"
              onError={(e) => { e.currentTarget.style.opacity = '0.3'; }}
            />
            <div className="photo-card-badge">{Math.round(photo.similarity * 100)}%</div>
          </div>
        ))}
        {filtered.length === 0 && tab === 'favs' && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Nenhum favorito ainda. Toque no ❤️ em uma foto para salvar.
          </div>
        )}
      </div>
    </div>
  );
}
