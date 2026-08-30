import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';

const STATUS_ICON = { pending: '⏳', uploading: '⬆️', done: '✅', error: '❌' };
const STATUS_COLOR = { pending: 'var(--text-muted)', uploading: 'var(--accent)', done: 'var(--accent)', error: 'var(--danger)' };

export default function AdminUploadScreen() {
  const navigate = useNavigate();
  const token = sessionStorage.getItem('cciAdminToken');
  const fileRef = useRef(null);

  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [newName, setNewName] = useState('');
  const [creatingEvent, setCreatingEvent] = useState(false);
  const [eventError, setEventError] = useState('');

  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!token) { navigate('/admin', { replace: true }); return; }
    api.getEvents()
      .then((data) => {
        setEvents(data || []);
        if (data?.length) setSelectedId(data[0].id);
      })
      .catch(() => {});
  }, []);

  async function handleCreateEvent(e) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreatingEvent(true);
    setEventError('');
    try {
      const data = await api.admin.createEvent(newName.trim(), token);
      setEvents((prev) => [data, ...prev]);
      setSelectedId(data.id);
      setNewName('');
    } catch (err) {
      setEventError(err.message || 'Erro ao criar evento.');
    } finally {
      setCreatingEvent(false);
    }
  }

  async function handleDeleteEvent(eventId) {
    if (!window.confirm('Remover este evento e todas as suas fotos?')) return;
    try {
      await api.admin.deleteEvent(eventId, token);
      const remaining = events.filter((e) => e.id !== eventId);
      setEvents(remaining);
      if (selectedId === eventId) setSelectedId(remaining[0]?.id || '');
    } catch (err) {
      alert(err.message || 'Erro ao remover evento.');
    }
  }

  function handleFileSelect(e) {
    const selected = Array.from(e.target.files || []);
    setFiles(selected.map((f) => ({ file: f, status: 'pending', result: null, error: null })));
    e.target.value = '';
  }

  async function handleUpload() {
    if (!selectedId || !files.length || uploading) return;
    setUploading(true);
    const updated = files.map((f) => ({ ...f }));

    for (let i = 0; i < updated.length; i++) {
      if (updated[i].status === 'done') continue;
      updated[i].status = 'uploading';
      setFiles([...updated]);
      try {
        const result = await api.admin.uploadPhoto(selectedId, updated[i].file, token);
        updated[i].status = 'done';
        updated[i].result = result;
      } catch (err) {
        updated[i].status = 'error';
        updated[i].error = err.message || 'Erro ao enviar.';
      }
      setFiles([...updated]);
    }
    setUploading(false);
  }

  const done = files.filter((f) => f.status === 'done').length;
  const errors = files.filter((f) => f.status === 'error').length;
  const totalFaces = files.reduce((sum, f) => sum + (f.result?.face_count || 0), 0);

  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ padding: '20px 20px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="back-btn" onClick={() => navigate('/admin/queue')} aria-label="Voltar">‹</button>
          <h2>Upload de Fotos</h2>
        </div>
        <img src="/logo.jpg" alt="CCI" style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover' }} />
      </div>

      <div className="screen" style={{ gap: 24, paddingTop: 20, paddingBottom: 32 }}>

        {/* ─── Seção: Evento ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label className="input-label">Evento de destino</label>

          {events.length > 0 && (
            <select
              className="input"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              style={{ cursor: 'pointer' }}
            >
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>{ev.name}</option>
              ))}
            </select>
          )}

          {/* Criar novo evento */}
          <form onSubmit={handleCreateEvent} style={{ display: 'flex', gap: 8 }}>
            <input
              className="input"
              placeholder="Nome do novo evento…"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              className="btn btn-outline"
              disabled={!newName.trim() || creatingEvent}
              style={{ width: 'auto', padding: '0 18px', flexShrink: 0 }}
            >
              {creatingEvent ? <span className="spinner" /> : 'Criar'}
            </button>
          </form>
          {eventError && <div className="error-msg">{eventError}</div>}

          {/* Gerenciar eventos existentes */}
          {events.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {events.map((ev) => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--surface)', borderRadius: 'var(--r-xs)', border: `1px solid ${selectedId === ev.id ? 'var(--accent)' : 'var(--border)'}` }}>
                  <span style={{ fontSize: 14, color: selectedId === ev.id ? 'var(--accent)' : 'var(--text)' }}>{ev.name}</span>
                  <button
                    onClick={() => handleDeleteEvent(ev.id)}
                    style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: '0 4px' }}
                    aria-label="Remover evento"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="divider" />

        {/* ─── Seção: Fotos ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label className="input-label">Fotos do evento</label>

          <button
            className="btn btn-outline"
            onClick={() => fileRef.current?.click()}
            disabled={!selectedId}
          >
            Selecionar fotos
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />

          {files.length > 0 && (
            <>
              {/* Lista de arquivos com status */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 280, overflowY: 'auto' }}>
                {files.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--surface)', borderRadius: 'var(--r-xs)', border: '1px solid var(--border)' }}>
                    <span style={{ fontSize: 16 }}>{STATUS_ICON[f.status]}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.file.name}</p>
                      {f.status === 'done' && f.result && (
                        <p style={{ fontSize: 11, color: 'var(--accent)' }}>{f.result.face_count} rosto{f.result.face_count !== 1 ? 's' : ''} detectado{f.result.face_count !== 1 ? 's' : ''}</p>
                      )}
                      {f.status === 'error' && (
                        <p style={{ fontSize: 11, color: 'var(--danger)' }}>{f.error}</p>
                      )}
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: STATUS_COLOR[f.status], flexShrink: 0 }}>
                      {f.status === 'uploading' ? 'enviando…' : f.status}
                    </span>
                  </div>
                ))}
              </div>

              {/* Resumo pós-upload */}
              {!uploading && done > 0 && (
                <div className="card" style={{ textAlign: 'center', borderColor: 'var(--accent)' }}>
                  <p style={{ color: 'var(--accent)', fontWeight: 700, fontSize: 15 }}>
                    {done} foto{done !== 1 ? 's' : ''} enviada{done !== 1 ? 's' : ''} · {totalFaces} rosto{totalFaces !== 1 ? 's' : ''}
                  </p>
                  {errors > 0 && <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: 4 }}>{errors} falharam</p>}
                </div>
              )}

              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={!selectedId || uploading || files.every((f) => f.status === 'done')}
              >
                {uploading ? <><span className="spinner" /> Enviando {done}/{files.length}…</> : files.every((f) => f.status === 'done') ? 'Tudo enviado ✓' : `Enviar ${files.length} foto${files.length !== 1 ? 's' : ''}`}
              </button>

              {!uploading && (
                <button className="btn btn-ghost" onClick={() => setFiles([])} style={{ color: 'var(--text-muted)' }}>
                  Limpar lista
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
