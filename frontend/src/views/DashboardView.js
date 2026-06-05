// GrapeHub Dashboard — 4 metric cards, 4 charts, alerts, recent wines, PDF export.
const { ref, onMounted, inject, computed } = Vue;
const { useRouter } = VueRouter;
import {
  wineService, WINE_TYPE_LABELS, WINE_TYPE_ICONS, formatPrice, photoUrl,
} from '../services/wines.js';
import { API_BASE_URL } from '../services/http.js';
import { auth } from '../services/auth.js';

export default {
  name: 'DashboardView',
  setup() {
    const router = useRouter();
    const toast  = inject('toast', () => {});

    const stats   = ref(null);
    const charts  = ref(null);
    const investment = ref(null);
    const alerts  = ref([]);
    const recent  = ref([]);
    const loading = ref(true);
    const exporting = ref(false);

    const user = computed(() => auth.state.user);
    let chartInstances = [];

    function destroyCharts() { chartInstances.forEach(c => c && c.destroy()); chartInstances = []; }

    function buildCharts(s, c) {
      destroyCharts();
      const axis = {
        legend: { labels: { color: '#C9B8A3', font: { size: 11 } } },
      };

      // 1. Doughnut — distribution by type
      const elType = document.getElementById('chType');
      if (elType && s.by_type) {
        chartInstances.push(new Chart(elType, {
          type: 'doughnut',
          data: {
            labels: Object.keys(s.by_type).map(t => WINE_TYPE_LABELS[t] || t),
            datasets: [{
              data: Object.values(s.by_type), borderWidth: 2, borderColor: '#141414',
              backgroundColor: ['#D4364A','#E8C96A','#F4956A','#8AC8E8','#C87830'],
            }],
          },
          options: { cutout: '62%', plugins: axis },
        }));
      }

      // 2. Horizontal bar — top 5 regions
      const elReg = document.getElementById('chRegions');
      if (elReg && s.by_region) {
        const sorted = Object.entries(s.by_region).sort((a,b)=>b[1]-a[1]).slice(0,5);
        chartInstances.push(new Chart(elReg, {
          type: 'bar',
          data: {
            labels: sorted.map(([k])=>k),
            datasets: [{ data: sorted.map(([,v])=>v), backgroundColor:'rgba(201,168,76,.4)', borderColor:'#C9A84C', borderWidth:1, borderRadius:4 }],
          },
          options: {
            indexAxis: 'y',
            scales: { x: { ticks:{color:'#8A8078'}, grid:{color:'rgba(201,168,76,.08)'} }, y:{ ticks:{color:'#C9B8A3'}, grid:{display:false} } },
            plugins: { legend: { display:false } },
          },
        }));
      }

      // 3. Bar — monthly consumption (last 12 months)
      const elCons = document.getElementById('chConsumption');
      if (elCons && c) {
        chartInstances.push(new Chart(elCons, {
          type: 'bar',
          data: {
            labels: c.month_labels,
            datasets: [{ label:'Garrafas consumidas', data: c.monthly_consumption, backgroundColor:'rgba(139,41,66,.5)', borderColor:'#8B2942', borderWidth:1, borderRadius:4 }],
          },
          options: {
            scales: { x:{ ticks:{color:'#8A8078',font:{size:9}}, grid:{display:false} }, y:{ ticks:{color:'#8A8078',precision:0}, grid:{color:'rgba(201,168,76,.08)'} } },
            plugins: { legend: { display:false } },
          },
        }));
      }

      // 4. Line — collection value over time
      const elVal = document.getElementById('chValue');
      if (elVal && c) {
        chartInstances.push(new Chart(elVal, {
          type: 'line',
          data: {
            labels: c.month_labels,
            datasets: [{ label:'Valor (€)', data: c.value_timeline, borderColor:'#C9A84C', backgroundColor:'rgba(201,168,76,.12)', fill:true, tension:.3, pointRadius:2, pointBackgroundColor:'#C9A84C' }],
          },
          options: {
            scales: { x:{ ticks:{color:'#8A8078',font:{size:9}}, grid:{display:false} }, y:{ ticks:{color:'#8A8078',callback:v=>'€'+v}, grid:{color:'rgba(201,168,76,.08)'} } },
            plugins: { legend: { display:false } },
          },
        }));
      }
    }

    async function load() {
      loading.value = true;
      try {
        // Carregar stats e charts
        const s = await wineService.stats();
        const c = await wineService.charts();

        // Carregar investment (com fallback se falhar)
        let inv = null;
        try {
          const res = await fetch(`${API_BASE_URL}/wines/investment/summary`, {
            headers: { Authorization: `Bearer ${auth.getToken()}` },
          });
          if (res.ok) inv = await res.json();
        } catch {}

        // Carregar alerts e wines
        const a = await wineService.alerts();
        const w = await wineService.list({ sort:'recent' });

        stats.value = s;
        charts.value = c;
        investment.value = inv;
        alerts.value = a;
        recent.value = w.slice(0, 6);

        // Construir gráficos após um pequeno delay
        window.setTimeout(() => buildCharts(s, c), 100);
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        loading.value = false;
      }
    }

    async function exportPdf() {
      exporting.value = true;
      try {
        const res = await fetch(`${API_BASE_URL}/reports/collection.pdf`, {
          headers: { Authorization: `Bearer ${auth.getToken()}` },
        });
        if (!res.ok) throw new Error('Erro ao gerar PDF');
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'garrafeira.pdf'; a.click();
        URL.revokeObjectURL(url);
        toast('PDF exportado! 📄', 'success');
      } catch (e) { toast(e.message, 'error'); }
      finally { exporting.value = false; }
    }

    async function exportCsv() {
      exporting.value = true;
      try {
        await wineService.exportCsv();
        toast('CSV exportado! 📥', 'success');
      } catch (e) { toast(e.message, 'error'); }
      finally { exporting.value = false; }
    }

    onMounted(load);

    const alertIcon = (s) => ({ success:'🌟', warning:'⚠️', danger:'🔴', muted:'⌛' })[s] || '•';
    const typeIcon = (t) => WINE_TYPE_ICONS[t] || '🍷';

    return {
      stats, charts, investment, alerts, recent, loading, exporting, exportPdf, exportCsv,
      alertIcon, typeIcon, formatPrice, photoUrl, WINE_TYPE_LABELS, router, user,
    };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title" style="font-size:1.5rem">
          Olá, {{ user?.name?.split(' ')[0] }} 👋
          <small>A sua garrafeira · {{ new Date().toLocaleDateString('pt-PT',{weekday:'long',day:'numeric',month:'long'}) }}</small>
        </h1>
        <div class="page-actions">
          <button class="btn btn-ghost" @click="exportCsv" :disabled="exporting">
            <span v-if="exporting" class="spinner"></span><span v-else>📥 Backup CSV</span>
          </button>
          <button class="btn btn-ghost" @click="exportPdf" :disabled="exporting">
            <span v-if="exporting" class="spinner"></span><span v-else>📄 Exportar PDF</span>
          </button>
          <router-link to="/wines/new" class="btn btn-gold">＋ Adicionar Garrafa</router-link>
        </div>
      </div>

      <div v-if="loading" class="page-loading"><div class="page-loading-icon">🍷</div><span>A carregar…</span></div>

      <template v-else-if="stats">
        <!-- URGENT ACTIONS -->
        <div v-if="alerts.filter(a => a.type === 'urgent' || a.type === 'peak').length">
          <div class="section-title" style="color:var(--s-danger);margin-bottom:1rem">🔴 Ações Imediatas</div>
          <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem;margin-bottom:2rem">
            <div v-for="a in alerts.filter(a => a.type === 'urgent' || a.type === 'peak')" :key="a.wine_id+a.type" :class="['card','card-alert','alert-'+a.severity]" style="padding:1rem;border-left:4px solid;border-left-color:var(--s-danger)">
              <div style="display:flex;justify-content:space-between;align-items:start;gap:1rem">
                <div style="flex:1">
                  <div style="font-weight:600;font-size:1rem;margin-bottom:0.25rem">{{ a.wine_name }} {{ a.vintage }}</div>
                  <div style="font-size:0.9rem;color:var(--text-muted);margin-bottom:0.75rem">{{ a.message }}</div>
                  <button class="btn btn-sm btn-gold" @click="router.push('/wines/'+a.wine_id)">Ver vinho →</button>
                </div>
                <span style="font-size:2rem">{{ alertIcon(a.severity) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- METRIC CARDS -->
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-icon">🍾</div><div class="stat-label">Referências</div><div class="stat-value">{{ stats.total_wines }}</div><div class="stat-sub">vinhos / {{ stats.total_bottles }} garrafas</div></div>
          <div class="stat-card card-premium"><div class="stat-icon">💰</div><div class="stat-label">Valor Total</div><div class="stat-value" style="font-size:1.4rem">{{ formatPrice(stats.total_value) }}</div><div class="stat-sub">da colecção em stock</div></div>
          <div class="stat-card"><div class="stat-icon">🍷</div><div class="stat-label">Prontas a Beber</div><div class="stat-value">{{ stats.ready_now }}</div><div class="stat-sub">no período ideal</div></div>
          <div class="stat-card"><div class="stat-icon">⏳</div><div class="stat-label">Beber em Breve</div><div class="stat-value">{{ stats.ending_soon }}</div><div class="stat-sub">próximos 12 meses</div></div>
        </div>

        <!-- INVESTMENT CARD -->
        <div v-if="investment" class="card" style="margin-bottom:2rem;border-top:3px solid var(--s-warning)">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem">
            <div>
              <div class="section-title" style="margin-bottom:1rem">💼 Investimento da Coleção</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem">
                <div><div class="text-xs text-muted">Valor Total</div><div style="font-size:1.3rem;font-weight:600">{{ formatPrice(investment.total_value) }}</div></div>
                <div><div class="text-xs text-muted">Investido</div><div style="font-size:1.3rem;font-weight:600">{{ formatPrice(investment.total_invested) }}</div></div>
                <div><div class="text-xs text-muted">ROI Estimado</div><div :style="{fontSize:'1.3rem',fontWeight:'600',color:investment.roi_estimate.roi_percent >= 0 ? 'var(--s-success)' : 'var(--s-danger)'}">{{ investment.roi_estimate.roi_percent.toFixed(1) }}%</div></div>
                <div><div class="text-xs text-muted">Ganho Potencial</div><div :style="{fontSize:'1.3rem',fontWeight:'600',color:investment.roi_estimate.potential_gain >= 0 ? 'var(--s-success)' : 'var(--s-danger)'}">{{ formatPrice(investment.roi_estimate.potential_gain) }}</div></div>
              </div>
              <div style="font-size:0.85rem;color:var(--text-muted)">Preço: €{{ investment.min_price }} - €{{ investment.max_price }} (média €{{ investment.avg_price }})</div>
            </div>
            <div>
              <div style="display:grid;grid-template-columns:1fr;gap:1rem">
                <div v-if="investment.appreciation_wines.length">
                  <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.5rem">🟢 Top Apreciados</div>
                  <div v-for="w in investment.appreciation_wines" :key="w.id" style="font-size:0.85rem;margin-bottom:0.3rem">
                    <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ w.name }} {{ w.vintage }} <span style="color:var(--s-success)">+{{ formatPrice(w.appreciation) }}</span></div>
                  </div>
                </div>
                <div v-if="investment.depreciation_wines.length">
                  <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.5rem">🔴 Top Desapreciados</div>
                  <div v-for="w in investment.depreciation_wines" :key="w.id" style="font-size:0.85rem;margin-bottom:0.3rem">
                    <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ w.name }} {{ w.vintage }} <span style="color:var(--s-danger)">{{ formatPrice(w.appreciation) }}</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4 CHARTS -->
        <div class="grid-2 mb-5">
          <div class="chart-wrap"><div class="chart-title">Distribuição por Tipo</div><div class="chart-container"><canvas id="chType" style="max-height:220px"></canvas></div></div>
          <div class="chart-wrap"><div class="chart-title">Top 5 Regiões</div><div class="chart-container"><canvas id="chRegions" style="max-height:220px"></canvas></div></div>
          <div class="chart-wrap"><div class="chart-title">Consumo Mensal (12 meses)</div><div class="chart-container"><canvas id="chConsumption" style="max-height:220px"></canvas></div></div>
          <div class="chart-wrap"><div class="chart-title">Evolução do Valor</div><div class="chart-container"><canvas id="chValue" style="max-height:220px"></canvas></div></div>
        </div>

        <div class="dash-grid">
          <!-- Recent wines -->
          <div class="card">
            <div class="flex justify-between items-center mb-4">
              <div class="section-title" style="margin-bottom:0">🍷 Coleção Recente</div>
              <router-link to="/cellar" class="btn btn-ghost btn-sm">Ver tudo →</router-link>
            </div>
            <div v-if="!recent.length" class="empty-state" style="padding:var(--s5)">
              <div class="empty-icon">🍾</div><div class="empty-title">Garrafeira vazia</div>
              <router-link to="/wines/new" class="btn btn-gold mt-3">Adicionar Garrafa</router-link>
            </div>
            <div v-else class="wine-grid" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">
              <div v-for="w in recent" :key="w.id" class="wine-card" @click="router.push('/wines/'+w.id)">
                <div class="wine-card-header">
                  <div><div class="wine-card-name">{{ w.name }}</div><div class="wine-card-producer">{{ w.producer_name }}</div></div>
                  <div class="wine-card-year">{{ w.vintage_year }}</div>
                </div>
                <div class="wine-card-footer">
                  <span class="wine-qty">📦 {{ w.current_stock }}</span>
                  <span v-if="w.avg_score" class="wine-rating-val text-gold">{{ w.avg_score }}/100</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Alerts -->
          <div class="card">
            <div class="section-title">🔔 Alertas</div>
            <div v-if="!alerts.length" class="text-sm text-muted">Sem alertas. Tudo em ordem! 🍷</div>
            <div v-else class="alerts-list">
              <div v-for="a in alerts.slice(0,8)" :key="a.wine_id+a.type" :class="['alert-item','alert-'+a.severity]">
                <span class="alert-icon">{{ alertIcon(a.severity) }}</span>
                <span class="alert-msg"><span class="alert-wine-link" @click="router.push('/wines/'+a.wine_id)">{{ a.message }}</span></span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="empty-state">
        <div class="empty-icon">🍾</div><div class="empty-title">A garrafeira está vazia</div>
        <router-link to="/wines/new" class="btn btn-gold btn-lg mt-4">🍷 Adicionar Primeira Garrafa</router-link>
      </div>
    </div>
  `,
};
