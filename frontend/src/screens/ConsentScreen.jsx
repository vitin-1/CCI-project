/**
 * ConsentScreen — /consent
 * Fluxo 1 / Etapa 5
 *
 * Aceite LGPD obrigatório antes da primeira busca.
 * Também acessível via ProfileScreen para re-consent (POST /consent é idempotente).
 *
 * Guard interno: se !memberId → /register (useEffect no mount).
 *   Evita acesso direto pela URL sem ter completado o cadastro.
 *
 * API: POST /consent { member_id }
 * Sucesso → /choose (início do fluxo de busca)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';

export default function ConsentScreen() {
  const navigate = useNavigate();
  const { state } = useApp();

  // Guard: redireciona se chegar aqui sem memberId (ex: URL digitada diretamente)
  useEffect(() => {
    if (!state.memberId) navigate('/register', { replace: true });
  }, [state.memberId]);

  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleConsent() {
    if (!agreed || !state.memberId) return;
    setLoading(true);
    setError('');
    try {
      await api.consent({ member_id: state.memberId });
      navigate('/choose', { replace: true });
    } catch (err) {
      setError(err.message || 'Erro ao registrar consentimento.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen" style={{ paddingTop: 32, gap: 20, paddingBottom: 32 }}>
      <div className="anim-fade-in-up" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <img src="/logo.jpg" alt="CCI Aliança" style={{ width: 44, height: 44, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
        <div>
          <h1 style={{ fontSize: 22, marginBottom: 4 }}>Privacidade e Consentimento</h1>
          <p style={{ fontSize: 14 }}>Leia com atenção antes de continuar.</p>
        </div>
      </div>

      {/* Texto LGPD — scrollável se o conteúdo for maior que a tela */}
      <div
        className="card anim-fade-in-up delay-1"
        style={{ flex: 1, overflowY: 'auto', fontSize: 14, lineHeight: 1.8, color: 'var(--text)', gap: 12, display: 'flex', flexDirection: 'column' }}
      >
        <p style={{ color: 'var(--accent)', fontWeight: 700, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Lei Geral de Proteção de Dados (LGPD)
        </p>
        <p>Ao continuar, você autoriza a CCI Aliança a processar seus dados biométricos faciais para identificá-lo em fotos tiradas nos eventos da nossa Igreja.</p>
        <div className="divider" />
        <p><strong style={{ color: 'var(--text)' }}>O que coletamos:</strong> embedding facial gerado a partir da selfie que você enviar. A selfie em si nunca é armazenada.</p>
        <p><strong style={{ color: 'var(--text)' }}>Para que serve:</strong> exclusivamente para encontrar as fotos em que você aparece nos eventos da Igreja.</p>
        <p><strong style={{ color: 'var(--text)' }}>Quem tem acesso:</strong> somente a equipe técnica da CCI Aliança, mediante autenticação.</p>
        <p><strong style={{ color: 'var(--text)' }}>Por quanto tempo:</strong> os dados biométricos são excluídos automaticamente após 90 dias.</p>
        <p><strong style={{ color: 'var(--text)' }}>Download das fotos:</strong> cada download exige verificação de identidade via código enviado ao seu WhatsApp.</p>
        <p><strong style={{ color: 'var(--text)' }}>Seus direitos:</strong> você pode solicitar exclusão dos seus dados a qualquer momento pelo Perfil do aplicativo.</p>
        <div className="divider" />
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Art. 7º e 11º da Lei nº 13.709/2018 (LGPD) — Base legal: consentimento explícito do titular.</p>
      </div>

      <div className="anim-fade-in-up delay-2" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <label style={{ display: 'flex', alignItems: 'flex-start', gap: 12, cursor: 'pointer' }}>
          <div
            onClick={() => setAgreed(!agreed)}
            style={{
              width: 22, height: 22,
              borderRadius: 6,
              border: `2px solid ${agreed ? 'var(--accent)' : 'var(--border)'}`,
              background: agreed ? 'var(--accent)' : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
              marginTop: 2,
              transition: 'all 0.15s',
            }}
          >
            {agreed && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <polyline points="2,6 5,9 10,3" stroke="var(--bg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
          <span style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.5 }}>
            Li e concordo com o uso dos meus dados biométricos conforme descrito acima.
          </span>
        </label>

        {error && <div className="error-msg">{error}</div>}

        <button
          className="btn btn-primary"
          onClick={handleConsent}
          disabled={!agreed || loading}
        >
          {loading ? <span className="spinner" /> : 'Continuar'}
        </button>
      </div>
    </div>
  );
}
