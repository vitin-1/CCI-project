/**
 * EventsScreen — /events
 * Fluxo 4 / Etapa 13
 *
 * Lista todos os eventos cadastrados. Endpoint público (sem token).
 * Ao clicar em um evento, navega para /my-photos com filtro aplicado:
 *   navigate('/my-photos', { state: { filterEvent: event.id, eventName: event.name } })
 *
 * API: GET /events
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
  } catch {
    return iso;
  }
}

// Emojis variados para dar identidade visual a cada card sem depender de imagem
const EVENT_EMOJIS = ['⛪', '🎵', '🙏', '✨', '🕊️', '🌿', '🔥', '💫'];

export default function EventsScreen() {
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getEvents()
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setError('Não foi possível carregar os eventos.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '24px 20px 16px' }}>
        <h2>Eventos</h2>
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <span className="spinner spinner-lg" />
        </div>
      )}

      {error && (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && events.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h2 style={{ marginBottom: 8 }}>Nenhum evento ainda</h2>
          <p>Os eventos aparecerão aqui assim que forem cadastrados.</p>
        </div>
      )}

      {!loading && events.length > 0 && (
        <div style={{ padding: '0 20px', display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto', flex: 1, paddingBottom: 20 }}>
          {events.map((event, i) => (
            <div
              key={event.id}
              className="event-card"
              style={{ animationDelay: `${i * 0.07}s` }}
              onClick={() => navigate('/my-photos', { state: { filterEvent: event.id, eventName: event.name } })}
            >
              <div className="event-thumb">
                {EVENT_EMOJIS[i % EVENT_EMOJIS.length]}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="event-name">{event.name}</div>
                <div className="event-meta">{formatDate(event.created_at)}</div>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
