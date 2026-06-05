// GrapeHub AppShell — premium sidebar navigation + toast system.
const { computed, ref, provide } = Vue;
const { useRouter, useRoute } = VueRouter;
import { auth } from '../services/auth.js';

export default {
  name: 'AppShell',
  setup() {
    const router = useRouter();
    const route  = useRoute();
    const user   = computed(() => auth.state.user);

    // ── Toast system ──────────────────────────────────────────────────────────
    const toasts = ref([]);
    function toast(msg, type = 'info', duration = 3500) {
      const id = Date.now();
      toasts.value.push({ id, msg, type });
      setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, duration);
    }
    provide('toast', toast); // child views can inject this

    // ── Navigation ────────────────────────────────────────────────────────────
    function logout() { auth.clear(); router.push('/login'); }
    function isActive(path) { return route.path === path || route.path.startsWith(path + '/'); }

    const toastIcon = (type) => ({ success: '✓', error: '✕', info: '🍷' })[type] || '•';

    return { user, logout, isActive, route, toasts, toastIcon };
  },

  template: `
    <div class="shell">
      <!-- SIDEBAR -->
      <aside class="sidebar">
        <div class="brand">Grape<span>Hub</span></div>
        <div class="brand-sub">Garrafeira Pessoal</div>

        <nav class="nav">
          <div class="nav-section">Início</div>
          <router-link to="/dashboard" class="nav-item" :class="{active: isActive('/dashboard')}">
            <span class="nav-icon">⬡</span>
            <span>Dashboard</span>
          </router-link>

          <div class="nav-section">Coleção</div>
          <router-link to="/cellar" class="nav-item" :class="{active: isActive('/cellar') || isActive('/wines')}">
            <span class="nav-icon">🍷</span>
            <span>Garrafeira</span>
          </router-link>
          <router-link to="/wines/new" class="nav-item" :class="{active: route.path === '/wines/new'}">
            <span class="nav-icon">＋</span>
            <span>Adicionar Garrafa</span>
          </router-link>

          <div class="nav-section">Histórico</div>
          <router-link to="/tastings" class="nav-item" :class="{active: isActive('/tastings')}">
            <span class="nav-icon">📓</span>
            <span>Degustações</span>
          </router-link>
          <router-link to="/wishlist" class="nav-item" :class="{active: isActive('/wishlist')}">
            <span class="nav-icon">♡</span>
            <span>Lista de Desejos</span>
          </router-link>
        </nav>

        <div class="sidebar-footer">
          <div class="sidebar-user">{{ user?.name }}</div>
          <div class="sidebar-role">{{ user?.role === 'admin' ? 'Administrador' : 'Sommelier' }}</div>
          <a href="#" class="sidebar-logout" @click.prevent="logout">Sair →</a>
        </div>
      </aside>

      <!-- MAIN -->
      <main class="main">
        <router-view></router-view>
      </main>

      <!-- TOASTS -->
      <div class="toast-container">
        <div v-for="t in toasts" :key="t.id" :class="['toast', 'toast-'+t.type]">
          <span>{{ toastIcon(t.type) }}</span>
          <span class="toast-msg">{{ t.msg }}</span>
        </div>
      </div>
    </div>
  `,
};
