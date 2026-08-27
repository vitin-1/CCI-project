/**
 * App.jsx — Roteamento principal e layouts
 *
 * Layouts disponíveis:
 *   MainLayout  — requer memberId; inclui BottomNav e Toast
 *   FlowLayout  — requer memberId; sem BottomNav (fluxo câmera/busca)
 *   Livre       — sem guard; usado em onboarding, admin e informativas
 *
 * Para adicionar uma nova tela:
 *   1. Importar o componente abaixo
 *   2. Adicionar <Route> dentro do layout correto
 *   3. Atualizar FLOWS.md
 */

import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import BottomNav from './components/BottomNav';
import Toast from './components/Toast';

// ─── Onboarding ──────────────────────────────────────────────────────────────
import SplashScreen from './screens/SplashScreen';
import WelcomeScreen from './screens/WelcomeScreen';
import HowItWorksScreen from './screens/HowItWorksScreen';
import RegisterScreen from './screens/RegisterScreen';
import ConsentScreen from './screens/ConsentScreen';

// ─── Fluxo de busca (sem bottom nav) ─────────────────────────────────────────
import ChooseOptionScreen from './screens/ChooseOptionScreen';
import CaptureScreen from './screens/CaptureScreen';
import ProcessingScreen from './screens/ProcessingScreen';
import SuccessScreen from './screens/SuccessScreen';

// ─── Área principal (com bottom nav) ─────────────────────────────────────────
import ResultsScreen from './screens/ResultsScreen';
import PhotoDetailScreen from './screens/PhotoDetailScreen';
import MyPhotosScreen from './screens/MyPhotosScreen';
import EventsScreen from './screens/EventsScreen';
import ProfileScreen from './screens/ProfileScreen';

// ─── Admin (rotas livres, token próprio) ─────────────────────────────────────
import AdminLoginScreen from './screens/admin/AdminLoginScreen';
import AdminQueueScreen from './screens/admin/AdminQueueScreen';
import AdminCaseScreen from './screens/admin/AdminCaseScreen';

// ─── Layouts ──────────────────────────────────────────────────────────────────

// Área autenticada com bottom nav (Início, Eventos, Minhas Fotos, Perfil, Detalhe)
function MainLayout() {
  const { state } = useApp();
  if (!state.memberId) return <Navigate to="/welcome" replace />;
  return (
    <div className="screen-full" style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </div>
      <BottomNav />
      <Toast />
    </div>
  );
}

// Fluxo de câmera/busca: autenticado mas sem bottom nav para tela cheia
function FlowLayout() {
  const { state } = useApp();
  if (!state.memberId) return <Navigate to="/welcome" replace />;
  return (
    <>
      <Outlet />
      <Toast />
    </>
  );
}

// ─── Rotas ───────────────────────────────────────────────────────────────────

function AppRoutes() {
  const { state } = useApp();
  const hasAuth = !!state.memberId;

  return (
    <div className="app-shell">
      <Routes>
        {/* Splash — sempre a primeira tela; rota * também cai aqui */}
        <Route path="/splash" element={<SplashScreen />} />

        {/* Onboarding — bloqueado se já autenticado */}
        <Route path="/welcome" element={hasAuth ? <Navigate to="/" replace /> : <WelcomeScreen />} />
        <Route path="/register" element={hasAuth ? <Navigate to="/" replace /> : <RegisterScreen />} />

        {/* Sem guard: consent é acessado também por usuários logados (re-consent via Perfil) */}
        <Route path="/consent" element={<ConsentScreen />} />

        {/* Informativa: acessível a qualquer momento, sem guard */}
        <Route path="/how-it-works" element={<HowItWorksScreen />} />

        {/* Área principal — requer memberId + BottomNav */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<ResultsScreen />} />
          <Route path="/events" element={<EventsScreen />} />
          <Route path="/my-photos" element={<MyPhotosScreen />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/photo/:id" element={<PhotoDetailScreen />} />
        </Route>

        {/* Fluxo de busca — requer memberId, sem BottomNav */}
        <Route element={<FlowLayout />}>
          <Route path="/choose" element={<ChooseOptionScreen />} />
          <Route path="/capture" element={<CaptureScreen />} />
          <Route path="/processing" element={<ProcessingScreen />} />
          <Route path="/success" element={<SuccessScreen />} />
        </Route>

        {/* Admin — token próprio (sessionStorage); sem guard de memberId */}
        <Route path="/admin" element={<AdminLoginScreen />} />
        <Route path="/admin/queue" element={<AdminQueueScreen />} />
        <Route path="/admin/case/:id" element={<AdminCaseScreen />} />

        {/* Fallback — qualquer URL desconhecida vai para splash */}
        <Route path="*" element={<Navigate to="/splash" replace />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppRoutes />
      </AppProvider>
    </BrowserRouter>
  );
}
