import { useNavigate } from 'react-router-dom';

export default function NotFoundScreen() {
  const navigate = useNavigate();

  return (
    <div className="screen" style={{ justifyContent: 'center', gap: 32, textAlign: 'center' }}>
      <div className="anim-fade-in-up">
        <div style={{
          fontSize: 80,
          fontWeight: 700,
          color: 'var(--accent)',
          lineHeight: 1,
          marginBottom: 8,
        }}>
          404
        </div>
        <h2 className="anim-fade-in-up delay-1" style={{ marginBottom: 12 }}>Página não encontrada</h2>
        <p className="anim-fade-in-up delay-2" style={{ fontSize: 15, lineHeight: 1.7, maxWidth: 280, margin: '0 auto', color: 'var(--text-muted)' }}>
          A página que você tentou acessar não existe ou foi movida.
        </p>
      </div>

      <div className="anim-fade-in-up delay-3">
        <button className="btn btn-primary" onClick={() => navigate('/splash')}>
          Voltar ao início
        </button>
      </div>
    </div>
  );
}
