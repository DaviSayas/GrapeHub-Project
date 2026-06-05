// GrapeHub — Login page with premium split-screen layout.
const { ref } = Vue;
const { useRouter } = VueRouter;
import { api } from '../services/http.js';
import { auth } from '../services/auth.js';

export default {
  name: 'LoginView',
  setup() {
    const router   = useRouter();
    const email    = ref('');
    const password = ref('');
    const error    = ref('');
    const loading  = ref(false);

    async function submit() {
      error.value = ''; loading.value = true;
      try {
        const res = await api.post('/auth/login', {
          email: email.value.trim().toLowerCase(),
          password: password.value,
        });
        auth.setSession(res.access_token, res.user);
        router.push('/dashboard');
      } catch (e) {
        error.value = e.message || 'Credenciais inválidas';
      } finally { loading.value = false; }
    }

    return { email, password, error, loading, submit };
  },

  template: `
    <div class="login-screen">
      <!-- ASIDE — branding -->
      <aside class="login-aside">
        <div>
          <div class="login-brand">Grape<em>Hub</em></div>
          <p class="login-tagline">
            A sua garrafeira pessoal, organizada com elegância.<br>
            Catalogue, controle o stock e descubra o momento perfeito para cada garrafa.
          </p>
          <div class="login-features">
            <div class="login-feat"><span class="login-feat-icon">🍷</span> Catálogo digital premium</div>
            <div class="login-feat"><span class="login-feat-icon">💡</span> Sugestões de consumo inteligentes</div>
            <div class="login-feat"><span class="login-feat-icon">📊</span> Estatísticas e insights</div>
            <div class="login-feat"><span class="login-feat-icon">🍽️</span> Harmonizações gastronómicas</div>
            <div class="login-feat"><span class="login-feat-icon">📦</span> Controlo de stock em tempo real</div>
          </div>
        </div>
        <div class="login-foot">GrapeHub v1.0 · Gestão Premium de Garrafeira</div>
      </aside>

      <!-- FORM -->
      <div class="login-form-wrap">
        <div class="login-card">
          <h2>Bem-vindo</h2>
          <p class="muted">Entre na sua garrafeira pessoal.</p>

          <div v-if="error" class="alert alert-error">{{ error }}</div>

          <form @submit.prevent="submit">
            <div class="field">
              <label class="field-label">Email</label>
              <input v-model="email" type="email" class="input" required autocomplete="email" placeholder="sommelier@exemplo.pt">
            </div>
            <div class="field">
              <label class="field-label">Palavra-passe</label>
              <input v-model="password" type="password" class="input" required autocomplete="current-password" placeholder="••••••••">
            </div>

            <div class="mt-5">
              <button class="btn btn-gold btn-block btn-lg" :disabled="loading">
                <span v-if="loading" class="spinner"></span>
                <span v-else>Entrar na Garrafeira →</span>
              </button>
            </div>
          </form>

          <div class="divider-text mt-5"><span>ou</span></div>

          <p class="text-center text-sm text-muted mt-4">
            Não tem conta?
            <router-link to="/register" class="text-gold"> Criar conta gratuita →</router-link>
          </p>

        </div>
      </div>
    </div>
  `,
};
