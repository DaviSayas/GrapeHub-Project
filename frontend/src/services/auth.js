// GrapeHub auth state — JWT + user persisted in localStorage.
const { reactive } = Vue;

const K_TOKEN = 'grapehub_token';
const K_USER  = 'grapehub_user';

const state = reactive({
  token: localStorage.getItem(K_TOKEN) || null,
  user:  JSON.parse(localStorage.getItem(K_USER) || 'null'),
});

export const auth = {
  state,
  getToken()        { return state.token; },
  isAuthenticated() { return !!state.token; },
  isAdmin()         { return state.user?.role === 'admin'; },
  hasRole(...roles) { return state.user && roles.includes(state.user.role); },

  setSession(token, user) {
    state.token = token;
    state.user  = user;
    localStorage.setItem(K_TOKEN, token);
    localStorage.setItem(K_USER, JSON.stringify(user));
  },

  clear() {
    state.token = null;
    state.user  = null;
    localStorage.removeItem(K_TOKEN);
    localStorage.removeItem(K_USER);
  },
};
