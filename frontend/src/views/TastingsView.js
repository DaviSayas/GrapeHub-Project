// GrapeHub — Tastings journal (diário de prova).
const { ref, onMounted, inject } = Vue;
const { useRouter } = VueRouter;
import { tastingService, formatDate } from '../services/tastings.js';
import { wineService, starsFromScore } from '../services/wines.js';

export default {
  name: 'TastingsView',
  setup() {
    const router = useRouter();
    const toast  = inject('toast', () => {});

    const tastings = ref([]);
    const winesMap = ref({});
    const stats    = ref(null);
    const loading  = ref(true);

    async function load() {
      loading.value = true;
      try {
        const [list, s] = await Promise.all([
          tastingService.list({ limit: 100 }), tastingService.stats(),
        ]);
        tastings.value = list; stats.value = s;
        const ids = [...new Set(list.map(t => t.wine_id))];
        await Promise.all(ids.map(async id => {
          try { winesMap.value[id] = await wineService.get(id); } catch {}
        }));
      } catch (e) { toast(e.message, 'error'); }
      finally { loading.value = false; }
    }

    async function remove(id) {
      if (!confirm('Remover esta degustação?')) return;
      try { await tastingService.remove(id); tastings.value = tastings.value.filter(t=>t.id!==id); toast('Removida','success'); }
      catch (e) { toast(e.message, 'error'); }
    }

    onMounted(load);
    return { tastings, winesMap, stats, loading, remove, formatDate, starsFromScore, router };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">📓 Degustações<small>Diário de prova estruturado</small></h1>
      </div>

      <div class="stats-grid" v-if="stats" style="grid-template-columns:repeat(3,1fr)">
        <div class="stat-card"><div class="stat-icon">📓</div><div class="stat-label">Total de Provas</div><div class="stat-value">{{ stats.total }}</div></div>
        <div class="stat-card card-premium"><div class="stat-icon">⭐</div><div class="stat-label">Classificação Média</div><div class="stat-value">{{ stats.avg_score>0 ? stats.avg_score : '—' }}</div><div class="stat-sub">de 100 pontos</div></div>
        <div class="stat-card"><div class="stat-icon">🔁</div><div class="stat-label">Compraria de Novo</div><div class="stat-value">{{ stats.would_buy_again }}</div></div>
      </div>

      <div v-if="loading" class="page-loading"><div class="page-loading-icon">📓</div><span>A carregar…</span></div>

      <div v-else-if="!tastings.length" class="empty-state">
        <div class="empty-icon">📓</div><div class="empty-title">Sem degustações</div>
        <div class="empty-desc">Abra uma garrafa e registe a prova!</div>
        <router-link to="/cellar" class="btn btn-gold mt-4">→ Ver Garrafeira</router-link>
      </div>

      <div v-else class="card">
        <div class="timeline">
          <div v-for="t in tastings" :key="t.id" class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="flex justify-between items-start">
                <div style="flex:1">
                  <div class="timeline-title" style="cursor:pointer" @click="router.push('/wines/'+t.wine_id)">
                    {{ winesMap[t.wine_id]?.name || ('Garrafa #'+t.wine_id) }}
                    <span class="text-xs text-muted">{{ winesMap[t.wine_id]?.vintage_year }}</span>
                  </div>
                  <div class="text-xs text-muted">{{ winesMap[t.wine_id]?.producer?.name }} · {{ t.occasion || 'Prova' }}</div>
                </div>
                <div class="flex gap-3 items-center">
                  <span v-if="t.overall_score" class="badge badge-gold">{{ t.overall_score }}/100</span>
                  <span class="timeline-date">{{ formatDate(t.date) }}</span>
                  <button class="btn btn-danger btn-sm btn-icon" @click="remove(t.id)">✕</button>
                </div>
              </div>
              <div v-if="t.overall_score" class="text-gold mt-1">{{ starsFromScore(t.overall_score) }}</div>
              <div v-if="t.notes" class="timeline-notes">"{{ t.notes }}"</div>
              <div v-if="t.would_buy_again !== null" class="text-xs mt-1" :style="t.would_buy_again?'color:var(--s-success)':'color:var(--ink-mute)'">
                {{ t.would_buy_again ? '✓ Compraria novamente' : '✗ Não compraria' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
