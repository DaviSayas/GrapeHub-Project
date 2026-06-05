// GrapeHub — Register page.
const { ref } = Vue;
const { useRouter } = VueRouter;
import { api } from '../services/http.js';
import { auth } from '../services/auth.js';

export default {
  name: 'RegisterView',
  setup() {
    const router    = useRouter();
    const name      = ref('');
    const email     = ref('');
    const password  = ref('');
    const confirm   = ref('');
    const error     = ref('');
    const loading   = ref(false);

    async function submit() {
      error.value = '';
      if (password.value !== confirm.value) { error.value = 'As passwords não coincidem'; return; }
      if (password.value.length < 6) { error.value = 'A password deve ter pelo menos 6 caracteres'; return; }
      loading.value = true;
      try {
        const res = await api.post('/auth/register', {
          name: name.value.trim(),
          email: email.value.trim().toLowerCase(),
          password: password.value,
        });
        auth.setSession(res.access_token, res.user);
        router.push('/dashboard');
      } catch (e) {
        error.value = e.message || 'Erro ao criar conta';
      } finally { loading.value = false; }
    }

    return { name, email, password, confirm, error, loading, submit };
  },

  template: `
    <div class="login-screen">
      <aside class="login-aside">
        <div>
          <div class="login-brand">Grape<em>Hub</em></div>
          <p class="login-tagline">
            Crie a sua conta e comece a catalogar a sua coleção de vinhos hoje mesmo.
          </p>
          <div class="login-features">
            <div class="login-feat"><span class="login-feat-icon">🆓</span> Conta gratuita para sempre</div>
            <div class="login-feat"><span class="login-feat-icon">🔒</span> Dados privados e seguros</div>
            <div class="login-feat"><span class="login-feat-icon">📱</span> Funciona em todos os dispositivos</div>
            <div class="login-feat"><span class="login-feat-icon">☁️</span> Backup automático</div>
          </div>
        </div>
        <div class="login-foot">GrapeHub v1.0 · Gestão Premium de Garrafeira</div>
      </aside>

      <div class="login-form-wrap">
        <div class="login-card">
          <h2>Criar Conta</h2>
          <p class="muted">Comece a gerir a sua garrafeira gratuitamente.</p>

          <div v-if="error" class="alert alert-error">{{ error }}</div>

          <form @submit.prevent="submit">
            <div class="field">
              <label class="field-label">Nome</label>
              <input v-model="name" type="text" class="input" required autocomplete="name" placeholder="João Silva">
            </div>
            <div class="field">
              <label class="field-label">Email</label>
              <input v-model="email" type="email" class="input" required autocomplete="email" placeholder="sommelier@exemplo.pt">
            </div>
            <div class="field">
              <label class="field-label">Password</label>
              <input v-model="password" type="password" class="input" required placeholder="Mínimo 6 caracteres">
            </div>
            <div class="field">
              <label class="field-label">Confirmar Password</label>
              <input v-model="confirm" type="password" class="input" required placeholder="Repetir password">
            </div>

            <div class="mt-5">
              <button class="btn btn-gold btn-block btn-lg" :disabled="loading">
                <span v-if="loading" class="spinner"></span>
                <span v-else>Criar a Minha Garrafeira →</span>
              </button>
            </div>
          </form>

          <p class="text-center text-sm text-muted mt-4">
            Já tem conta?
            <router-link to="/login" class="text-gold"> Entrar →</router-link>
          </p>
        </div>
      </div>
    </div>
  `,
};
