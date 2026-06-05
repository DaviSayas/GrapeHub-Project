// GrapeHub — Vue Router (hash mode, no build step required).
const { createRouter, createWebHashHistory } = VueRouter;

import { auth } from '../services/auth.js';
import LoginView    from '../views/LoginView.js';
import RegisterView from '../views/RegisterView.js';
import AppShell     from '../components/AppShell.js';
import DashboardView  from '../views/DashboardView.js';
import CellarView     from '../views/CellarView.js';
import WineDetailView from '../views/WineDetailView.js';
import WineFormView   from '../views/WineFormView.js';
import TastingsView   from '../views/TastingsView.js';
import WishlistView   from '../views/WishlistView.js';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login',    component: LoginView,    meta: { public: true } },
    { path: '/register', component: RegisterView, meta: { public: true } },
    {
      path: '/',
      component: AppShell,
      children: [
        { path: '',          redirect: '/dashboard' },
        { path: 'dashboard', component: DashboardView },
        { path: 'cellar',    component: CellarView },
        { path: 'wines/new', component: WineFormView },
        { path: 'wines/:id', component: WineDetailView },
        { path: 'wines/:id/edit', component: WineFormView },
        { path: 'tastings',  component: TastingsView },
        { path: 'wishlist',  component: WishlistView },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach((to, from, next) => {
  const loggedIn = auth.isAuthenticated();
  if (to.meta.public) {
    return loggedIn && (to.path === '/login' || to.path === '/register')
      ? next('/dashboard') : next();
  }
  if (!loggedIn) return next('/login');
  next();
});

export default router;
