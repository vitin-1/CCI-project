import { useNavigate } from 'react-router-dom';

const STEPS = [
  {
    icon: '📝',
    title: 'Cadastro rápido',
    desc: 'Informe seu nome completo e número de WhatsApp. É só isso — sem senha, sem complicação.',
  },
  {
    icon: '🔒',
    title: 'Seus dados protegidos',
    desc: 'Antes de qualquer busca, você lê e autoriza o uso dos seus dados biométricos. Tudo dentro da Lei Geral de Proteção de Dados (LGPD).',
  },
  {
    icon: '🤳',
    title: 'Uma selfie sua',
    desc: 'Tire uma selfie pela câmera do app ou envie uma foto da galeria. Ela é processada na hora e nunca fica salva.',
  },
  {
    icon: '🔍',
    title: 'IA encontra você',
    desc: 'Nossa inteligência artificial varre todas as fotos dos eventos e identifica os momentos em que você aparece.',
  },
  {
    icon: '📷',
    title: 'Veja seus momentos',
    desc: 'As fotos encontradas ficam no seu perfil, organizadas por evento. Favorite as que mais gostar.',
  },
  {
    icon: '⬇️',
    title: 'Download seguro',
    desc: 'Para baixar a foto original em alta resolução, confirmamos sua identidade com um código enviado ao seu WhatsApp.',
  },
];

export default function HowItWorksScreen() {
  const navigate = useNavigate();

  return (
    <div className="screen" style={{ paddingTop: 32, paddingBottom: 40, gap: 0 }}>
      {/* Header */}
      <div className="anim-fade-in-up" style={{ textAlign: 'center', marginBottom: 32 }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            position: 'absolute',
            left: 20,
            top: 32,
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: 28,
            cursor: 'pointer',
            lineHeight: 1,
          }}
          aria-label="Voltar"
        >
          ‹
        </button>
        <img
          src="/logo.jpg"
          alt="CCI Aliança"
          style={{ width: 72, height: 72, borderRadius: '50%', objectFit: 'cover', marginBottom: 16 }}
        />
        <h1 style={{ fontSize: 22, marginBottom: 8 }}>Como funciona?</h1>
        <p style={{ fontSize: 14, lineHeight: 1.6, maxWidth: 300, margin: '0 auto' }}>
          Em poucos passos você encontra todas as suas fotos nos eventos da Igreja.
        </p>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 32 }}>
        {STEPS.map((step, i) => (
          <div
            key={i}
            className="card anim-fade-in-up"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 16,
              animationDelay: `${0.08 * i}s`,
              opacity: 0,
              animation: `fadeInUp 0.4s ${0.08 * i}s ease forwards`,
            }}
          >
            {/* Step number + icon */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, flexShrink: 0 }}>
              <div style={{
                width: 44,
                height: 44,
                background: 'var(--accent-dim)',
                border: '1.5px solid var(--accent)',
                borderRadius: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 22,
              }}>
                {step.icon}
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ width: 1, height: 14, background: 'var(--border)' }} />
              )}
            </div>

            <div style={{ paddingTop: 4 }}>
              <div style={{
                fontSize: 11,
                fontWeight: 700,
                color: 'var(--accent)',
                letterSpacing: '0.6px',
                textTransform: 'uppercase',
                marginBottom: 4,
              }}>
                Passo {i + 1}
              </div>
              <h3 style={{ fontSize: 15, marginBottom: 4 }}>{step.title}</h3>
              <p style={{ fontSize: 13, lineHeight: 1.6 }}>{step.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className="anim-fade-in-up" style={{ animationDelay: '0.5s', display: 'flex', flexDirection: 'column', gap: 0 }}>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/register')}
          style={{ marginBottom: 32 }}
        >
          Começar agora
        </button>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          padding: '20px 0 0',
          borderTop: '1px solid var(--border)',
        }}>
          <div style={{
            width: 32,
            height: 2,
            background: 'var(--accent)',
            margin: '0 auto 16px',
            borderRadius: 2,
          }} />
          <p style={{
            fontSize: 14,
            fontStyle: 'italic',
            color: 'var(--text)',
            lineHeight: 1.7,
            fontWeight: 500,
          }}>
            "CCI uma igreja que ama<br />com o amor de Jesus"
          </p>
          <img
            src="/logo.jpg"
            alt="CCI Aliança"
            style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover', marginTop: 14, opacity: 0.7 }}
          />
        </div>
      </div>
    </div>
  );
}
