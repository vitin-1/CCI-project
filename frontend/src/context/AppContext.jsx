/**
 * AppContext.jsx — Estado global da aplicação
 *
 * Persistência:
 *   sessionStorage → memberId, memberName  (limpos ao fechar o browser/aba)
 *   localStorage   → myPhotos, favorites   (persistem entre sessões — dados do dispositivo)
 *   memória        → searchResults, toast  (perdidos ao recarregar)
 *
 * Para consumir: const { state, dispatch } = useApp();
 * Para adicionar estado: incluir em initialState + reducer + (se precisar) useEffect de persistência
 */

import { createContext, useContext, useReducer, useEffect } from 'react';

const AppContext = createContext(null);

// Lê JSON do localStorage com fallback seguro
function loadStorage(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
  catch { return fallback; }
}

// ─── Estado inicial ───────────────────────────────────────────────────────────

const initialState = {
  memberId:      sessionStorage.getItem('cciMemberId') || null,
  memberName:    sessionStorage.getItem('cciMemberName') || '',
  searchResults: [],                                        // resultado da última busca
  myPhotos:      loadStorage('cciMyPhotos', []),            // todas as fotos já encontradas
  favorites:     new Set(loadStorage('cciFavorites', [])),  // Set de photo_ids favoritados
  toast:         null,                                      // { msg: string, kind: 'success'|'error'|'default' }
};

// ─── Reducer ──────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {

    // Autenticação — persiste em sessionStorage (limpo ao fechar o tab)
    case 'SET_MEMBER':
      sessionStorage.setItem('cciMemberId', action.id);
      sessionStorage.setItem('cciMemberName', action.name);
      return { ...state, memberId: action.id, memberName: action.name };

    // Substituição total dos resultados de busca (cada busca zera os anteriores)
    case 'SET_RESULTS':
      return { ...state, searchResults: action.results };

    // Merge de fotos novas sem duplicar — compara photo_id
    case 'ADD_MY_PHOTOS': {
      const existing = new Set(state.myPhotos.map(p => p.photo_id));
      const fresh = action.photos.filter(p => !existing.has(p.photo_id));
      return { ...state, myPhotos: [...fresh, ...state.myPhotos] };
    }

    // Toggle favorito — adiciona se ausente, remove se presente
    case 'TOGGLE_FAVORITE': {
      const favs = new Set(state.favorites);
      if (favs.has(action.photoId)) favs.delete(action.photoId);
      else favs.add(action.photoId);
      return { ...state, favorites: favs };
    }

    // Toast temporário — auto-clear em 3s via useEffect abaixo
    case 'SHOW_TOAST':
      return { ...state, toast: { msg: action.msg, kind: action.kind || 'default' } };

    case 'CLEAR_TOAST':
      return { ...state, toast: null };

    // Logout: limpa sessão mas mantém fotos e favoritos (dados do dispositivo)
    case 'LOGOUT':
      sessionStorage.clear();
      return {
        ...initialState,
        memberId:   null,
        memberName: '',
        myPhotos:   state.myPhotos,
        favorites:  state.favorites,
      };

    default:
      return state;
  }
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Sincroniza myPhotos com localStorage sempre que mudar
  useEffect(() => {
    localStorage.setItem('cciMyPhotos', JSON.stringify(state.myPhotos));
  }, [state.myPhotos]);

  // Set não é serializável diretamente — converte para array antes de salvar
  useEffect(() => {
    localStorage.setItem('cciFavorites', JSON.stringify([...state.favorites]));
  }, [state.favorites]);

  // Auto-clear toast após 3s (reinicia o timer a cada novo toast)
  useEffect(() => {
    if (!state.toast) return;
    const t = setTimeout(() => dispatch({ type: 'CLEAR_TOAST' }), 3000);
    return () => clearTimeout(t);
  }, [state.toast]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
