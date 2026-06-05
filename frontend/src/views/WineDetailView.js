// GrapeHub — Wine detail: photos, window, pairing, stock movements, tastings.
const { ref, onMounted, inject, computed } = Vue;
const { useRouter, useRoute } = VueRouter;
import {
  wineService, WINE_TYPE_LABELS, WINE_TYPE_ICONS, DW_STATUS_LABELS, DW_STATUS_CLASS,
  formatPrice, photoUrl, starsFromScore,
} from '../services/wines.js';
import { stockService, MOVEMENT_TYPE_LABELS, MOVEMENT_TYPE_BADGE, MOVEMENT_TYPE_ICON } from '../services/stock.js';
import { tastingService, formatDate } from '../services/tastings.js';

export default {
  name: 'WineDetailView',
  setup() {
    const router = useRouter();
    const route  = useRoute();
    const toast  = inject('toast', () => {});
    const wineId = route.params.id;

    const wine     = ref(null);
    const win      = ref(null);
    const pairing  = ref(null);
    const movements = ref([]);
    const tastings = ref([]);
    const locations = ref([]);
    const history  = ref(null);
    const loading  = ref(true);
    const showLabel = ref(false);

    // Stock modal
    const showStockModal = ref(false);
    const stockForm = ref({ type: 'out', quantity: 1, location_id: '', reason: '', price: '', notes: '' });
    const stockSaving = ref(false);

    // Tasting modal
    const showTastingModal = ref(false);
    const tForm = ref({
      date: new Date().toISOString().substring(0,10), occasion: '',
      appearance: '', nose: '', palate: '', finish: '',
      overall_score: '', notes: '', would_buy_again: null,
    });
    const tSaving = ref(false);

    async function load() {
      loading.value = true;
      try {
        const [w, wi, p, mv, ts, locs, h] = await Promise.all([
          wineService.get(wineId),
          wineService.window(wineId),
          wineService.pairing(wineId),
          stockService.movements(wineId),
          tastingService.forWine(wineId),
          stockService.locations(),
          wineService.history(wineId),
        ]);
        wine.value = w; win.value = wi; pairing.value = p;
        movements.value = mv; tastings.value = ts; locations.value = locs; history.value = h;
      } catch (e) { toast(e.message, 'error'); }
      finally { loading.value = false; }
    }

    async function saveStock() {
      stockSaving.value = true;
      try {
        const payload = {
          wine_id: parseInt(wineId), type: stockForm.value.type,
          quantity: parseInt(stockForm.value.quantity),
          location_id: stockForm.value.location_id || null,
          reason: stockForm.value.reason || null,
          price: stockForm.value.price === '' ? null : Number(stockForm.value.price),
          notes: stockForm.value.notes || null,
        };
        await stockService.addMovement(payload);
        toast('Movimento de stock registado', 'success');
        showStockModal.value = false;
        stockForm.value = { type:'out', quantity:1, location_id:'', reason:'', price:'', notes:'' };
        await load();
      } catch (e) { toast(e.message, 'error'); }
      finally { stockSaving.value = false; }
    }

    async function saveTasting() {
      tSaving.value = true;
      try {
        const payload = {
          wine_id: parseInt(wineId),
          date: tForm.value.date,
          occasion: tForm.value.occasion || null,
          appearance: tForm.value.appearance || null,
          nose: tForm.value.nose || null,
          palate: tForm.value.palate || null,
          finish: tForm.value.finish || null,
          overall_score: tForm.value.overall_score === '' ? null : parseInt(tForm.value.overall_score),
          notes: tForm.value.notes || null,
          would_buy_again: tForm.value.would_buy_again,
        };
        await tastingService.create(payload);
        toast('Degustação registada! 🍷', 'success');
        showTastingModal.value = false;
        tForm.value = { date:new Date().toISOString().substring(0,10), occasion:'', appearance:'', nose:'', palate:'', finish:'', overall_score:'', notes:'', would_buy_again:null };
        await load();
      } catch (e) { toast(e.message, 'error'); }
      finally { tSaving.value = false; }
    }

    async function deleteWine() {
      if (!confirm(`Remover "${wine.value.name}"?`)) return;
      try { await wineService.remove(wineId); toast('Garrafa removida', 'success'); router.push('/cellar'); }
      catch (e) { toast(e.message, 'error'); }
    }

    onMounted(load);

    const dwBarPercent = computed(() => {
      if (!win.value) return 0;
      const { drink_from, drink_until } = win.value;
      const cur = new Date().getFullYear();
      if (cur < drink_from) return 0;
      if (cur > drink_until) return 100;
      return Math.round((cur - drink_from) / Math.max(1, drink_until - drink_from) * 100);
    });
    const dwColor = computed(() => ({
      too_young:'var(--dw-young)', almost_ready:'var(--dw-almost)', ready:'var(--dw-ready)',
      peak:'var(--dw-peak)', declining:'var(--dw-declining)', past_peak:'var(--dw-past)',
    }[win.value?.status] || 'var(--gold)'));

    return {
      wine, win, pairing, movements, tastings, history, locations, loading, showLabel,
      showStockModal, stockForm, stockSaving, saveStock,
      showTastingModal, tForm, tSaving, saveTasting,
      deleteWine, dwBarPercent, dwColor,
      WINE_TYPE_LABELS, WINE_TYPE_ICONS, DW_STATUS_LABELS, DW_STATUS_CLASS,
      MOVEMENT_TYPE_LABELS, MOVEMENT_TYPE_BADGE, MOVEMENT_TYPE_ICON,
      formatPrice, photoUrl, starsFromScore, formatDate, router,
    };
  },

  template: `
    <div class="page">
      <div v-if="loading" class="page-loading"><div class="page-loading-icon">🍷</div><span>A carregar…</span></div>

      <template v-else-if="wine">
        <div class="page-header">
          <div>
            <button class="btn btn-ghost btn-sm mb-3" @click="router.back()">← Voltar</button>
            <h1 class="page-title">{{ wine.name }}
              <small>{{ wine.producer?.name }} · {{ wine.region }}</small>
            </h1>
          </div>
          <div class="page-actions">
            <button class="btn btn-ghost" @click="router.push('/wines/'+wine.id+'/edit')">✏ Editar</button>
            <button class="btn btn-wine" @click="showStockModal=true">📦 Mov. Stock</button>
            <button class="btn btn-gold" @click="showTastingModal=true">🍷 Degustar</button>
            <button class="btn btn-danger btn-sm btn-icon" @click="deleteWine" title="Remover">🗑</button>
          </div>
        </div>

        <div class="detail-grid">
          <!-- LEFT -->
          <div class="detail-aside">
            <!-- Photo -->
            <div>
              <div v-if="(showLabel ? wine.label_photo_path : wine.photo_path)"
                   style="border-radius:18px;overflow:hidden;border:1px solid var(--border-md)">
                <img :src="photoUrl(showLabel ? wine.label_photo_path : wine.photo_path)" style="width:100%;display:block">
              </div>
              <div v-else class="wine-photo-placeholder">
                <div class="ph-icon">{{ showLabel ? '🏷️' : (WINE_TYPE_ICONS[wine.wine_type]||'🍷') }}</div>
                <small>{{ showLabel ? 'Sem foto da etiqueta' : 'Sem foto da garrafa' }}</small>
              </div>
              <div v-if="wine.photo_path || wine.label_photo_path" class="flex gap-2 mt-3" style="justify-content:center">
                <button :class="['btn btn-ghost btn-sm', !showLabel?'active':'']" @click="showLabel=false">Garrafa</button>
                <button :class="['btn btn-ghost btn-sm', showLabel?'active':'']" @click="showLabel=true">Etiqueta</button>
              </div>
            </div>

            <!-- Info -->
            <div class="card">
              <div class="flex justify-between items-center mb-4">
                <span :class="['badge', 'badge-'+(wine.wine_type==='rosé'?'rosé':wine.wine_type)]" style="font-size:.85rem;padding:5px 14px">
                  {{ WINE_TYPE_ICONS[wine.wine_type] }} {{ WINE_TYPE_LABELS[wine.wine_type] }}
                </span>
                <span class="text-mono text-gold" style="font-size:1.3rem;font-weight:700">{{ wine.vintage_year }}</span>
              </div>
              <div style="display:flex;flex-direction:column;gap:10px">
                <div class="flex justify-between"><span class="text-muted text-sm">Produtor</span><span class="text-soft">{{ wine.producer?.name }}</span></div>
                <div class="flex justify-between"><span class="text-muted text-sm">Região</span><span class="text-soft">{{ wine.region }}</span></div>
                <div v-if="wine.grapes_display" class="flex justify-between"><span class="text-muted text-sm">Castas</span><span class="text-soft" style="text-align:right;max-width:60%">{{ wine.grapes_display }}</span></div>
                <div v-if="wine.alcoholic_degree" class="flex justify-between"><span class="text-muted text-sm">Álcool</span><span class="text-soft">{{ wine.alcoholic_degree }}%</span></div>
                <div class="flex justify-between"><span class="text-muted text-sm">Volume</span><span class="text-soft">{{ wine.volume_ml>=1000 ? (wine.volume_ml/1000)+'L' : wine.volume_ml+'ml' }}</span></div>
                <div class="divider"></div>
                <div class="flex justify-between">
                  <span class="text-muted text-sm">Em stock</span>
                  <span :style="wine.min_stock && wine.current_stock<=wine.min_stock ? 'color:var(--s-warning);font-weight:700;font-size:1.1rem' : 'color:var(--gold);font-weight:700;font-size:1.1rem'">
                    {{ wine.current_stock }} un.{{ wine.min_stock && wine.current_stock<=wine.min_stock ? ' ⚠' : '' }}
                  </span>
                </div>
                <div v-if="wine.purchase_price" class="flex justify-between"><span class="text-muted text-sm">Preço ref.</span><span class="text-soft">{{ formatPrice(wine.purchase_price) }}</span></div>
              </div>
              <div v-if="wine.avg_score" class="mt-4 text-center">
                <div class="text-gold" style="font-size:1.6rem;letter-spacing:2px">{{ starsFromScore(wine.avg_score) }}</div>
                <div class="text-muted text-sm">{{ wine.avg_score }}/100 — média de {{ tastings.length }} degustação(ões)</div>
              </div>
            </div>
          </div>

          <!-- RIGHT -->
          <div class="detail-main">
            <!-- Window -->
            <div class="card" v-if="win">
              <div class="section-title">⏳ Janela de Consumo</div>
              <div class="flex justify-between items-center mb-3">
                <span :class="['dw-badge', DW_STATUS_CLASS[win.status]]" style="font-size:.9rem;padding:6px 16px">{{ DW_STATUS_LABELS[win.status] }}</span>
                <span class="text-sm text-muted text-mono">{{ win.drink_from }} – {{ win.drink_until }}</span>
              </div>
              <div class="dw-viz">
                <div class="dw-viz-bar-bg"><div class="dw-viz-bar-fill" :style="{width:dwBarPercent+'%',background:dwColor}"></div></div>
                <div class="dw-viz-labels">
                  <span>{{ wine.vintage_year }}</span>
                  <span>Pico: {{ win.peak_from }}–{{ win.peak_until }}</span>
                  <span>{{ win.drink_until }}</span>
                </div>
              </div>
              <p v-if="win.label" class="text-sm text-soft mt-3 text-center" style="font-style:italic">{{ win.label }}</p>
            </div>

            <!-- History Stats -->
            <div class="card" v-if="history">
              <div class="section-title">📈 Histórico da Garrafeira</div>
              <div class="grid-2" style="gap:1rem;margin-bottom:1.5rem">
                <div>
                  <div class="text-xs text-muted">Total Comprado</div>
                  <div style="font-size:1.3rem;font-weight:600;color:var(--s-success)">{{ history.total_purchased }} garrafas</div>
                </div>
                <div>
                  <div class="text-xs text-muted">Total Consumido</div>
                  <div style="font-size:1.3rem;font-weight:600;color:var(--s-danger)">{{ history.total_consumed }} garrafas</div>
                </div>
                <div>
                  <div class="text-xs text-muted">Taxa de Consumo</div>
                  <div style="font-size:1.3rem;font-weight:600;color:var(--gold)">{{ history.consumption_rate }} / mês</div>
                </div>
                <div>
                  <div class="text-xs text-muted">Período</div>
                  <div class="text-xs text-soft">{{ history.first_purchase_date ? new Date(history.first_purchase_date).toLocaleDateString('pt-PT') : '—' }} até {{ history.last_purchase_date ? new Date(history.last_purchase_date).toLocaleDateString('pt-PT') : '—' }}</div>
                </div>
              </div>
            </div>

            <!-- Pairing -->
            <div class="card" v-if="pairing">
              <div class="section-title">🍽️ Harmonizações & Gastronomia</div>

              <!-- Cuisines -->
              <div v-if="pairing.cuisines && pairing.cuisines.length" style="margin-bottom:1.5rem">
                <div class="text-xs text-muted mb-2">TIPOS DE COZINHA</div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="c in pairing.cuisines" :key="c" class="badge badge-gold" style="background:rgba(201,168,76,.2);border-color:var(--gold)">{{ c }}</span>
                </div>
              </div>

              <!-- Main foods -->
              <div style="margin-bottom:1.5rem">
                <div class="text-xs text-muted mb-2">PRATOS RECOMENDADOS</div>
                <div class="pairing-grid">
                  <span v-for="f in pairing.foods" :key="f" class="pairing-chip">🍴 {{ f }}</span>
                </div>
              </div>

              <!-- Ingredients -->
              <div v-if="pairing.ingredients && pairing.ingredients.length" style="margin-bottom:1.5rem">
                <div class="text-xs text-muted mb-2">INGREDIENTES PRINCIPAIS</div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="ing in pairing.ingredients" :key="ing" class="badge" style="background:rgba(139,41,66,.2);border-color:var(--s-danger);color:var(--text-main)">{{ ing }}</span>
                </div>
              </div>

              <!-- Sommelier tip -->
              <div v-if="pairing.sommelier_tip" style="background:rgba(201,168,76,.08);border-left:3px solid var(--gold);padding:0.75rem;border-radius:4px;margin-bottom:1.5rem">
                <div class="text-xs text-gold font-semibold">💭 Dica Sommelier</div>
                <div class="text-sm text-soft mt-1">{{ pairing.sommelier_tip }}</div>
              </div>

              <!-- Service details -->
              <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1.5rem">
                <div>
                  <div class="text-xs text-muted mb-1">TEMPERATURA</div>
                  <div class="text-sm text-gold">🌡️ {{ pairing.serving_temp }}</div>
                </div>
                <div>
                  <div class="text-xs text-muted mb-1">TIPO DE COPO</div>
                  <div class="text-sm text-soft">🍷 {{ pairing.glass_type }}</div>
                </div>
                <div>
                  <div class="text-xs text-muted mb-1">AREJAÇÃO</div>
                  <div class="text-sm text-soft">💨 {{ pairing.aeration }}</div>
                </div>
              </div>

              <!-- Avoid -->
              <div v-if="pairing.avoid && pairing.avoid.length">
                <div class="text-xs text-muted mb-2">EVITAR</div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="a in pairing.avoid" :key="a" class="text-xs text-muted" style="background:rgba(255,0,0,.08);padding:4px 10px;border-radius:4px;border:1px solid rgba(255,0,0,.2)">⛔ {{ a }}</span>
                </div>
              </div>
            </div>

            <!-- Stock movements -->
            <div class="card">
              <div class="flex justify-between items-center mb-4">
                <div class="section-title" style="margin-bottom:0">📦 Movimentos de Stock</div>
                <button class="btn btn-ghost btn-sm" @click="showStockModal=true">＋ Registar</button>
              </div>
              <div v-if="!movements.length" class="text-sm text-muted">Sem movimentos registados.</div>
              <div v-else class="timeline">
                <div v-for="m in movements" :key="m.id" class="timeline-item">
                  <div class="timeline-dot" :style="{background: m.type==='in'?'var(--s-success)':m.type==='out'?'var(--s-danger)':'var(--s-info)'}"></div>
                  <div class="timeline-content">
                    <div class="flex justify-between items-center">
                      <span :class="['badge', MOVEMENT_TYPE_BADGE[m.type]]">{{ MOVEMENT_TYPE_ICON[m.type] }} {{ MOVEMENT_TYPE_LABELS[m.type] }} · {{ m.quantity }}</span>
                      <span class="timeline-date">{{ formatDate(m.date) }}</span>
                    </div>
                    <div v-if="m.reason" class="text-sm text-soft mt-1">{{ m.reason }}</div>
                    <div v-if="m.notes" class="timeline-notes">{{ m.notes }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tastings -->
            <div class="card">
              <div class="flex justify-between items-center mb-4">
                <div class="section-title" style="margin-bottom:0">📓 Degustações</div>
                <button class="btn btn-gold btn-sm" @click="showTastingModal=true">🍷 Nova prova</button>
              </div>
              <div v-if="!tastings.length" class="empty-state" style="padding:var(--s5)">
                <div class="empty-icon" style="font-size:2rem">📓</div>
                <div class="empty-title" style="font-size:1rem">Sem degustações</div>
              </div>
              <div v-else class="timeline">
                <div v-for="t in tastings" :key="t.id" class="timeline-item">
                  <div class="timeline-dot"></div>
                  <div class="timeline-content">
                    <div class="flex justify-between items-center">
                      <span class="timeline-title">{{ t.occasion || 'Prova' }}</span>
                      <div class="flex gap-3 items-center">
                        <span v-if="t.overall_score" class="badge badge-gold">{{ t.overall_score }}/100</span>
                        <span class="timeline-date">{{ formatDate(t.date) }}</span>
                      </div>
                    </div>
                    <div v-if="t.overall_score" class="text-gold mt-1" style="font-size:.95rem">{{ starsFromScore(t.overall_score) }}</div>
                    <div class="grid-2 mt-2" style="gap:8px">
                      <div v-if="t.appearance" class="text-xs"><span class="text-muted">Aspecto:</span> <span class="text-soft">{{ t.appearance }}</span></div>
                      <div v-if="t.nose" class="text-xs"><span class="text-muted">Aroma:</span> <span class="text-soft">{{ t.nose }}</span></div>
                      <div v-if="t.palate" class="text-xs"><span class="text-muted">Boca:</span> <span class="text-soft">{{ t.palate }}</span></div>
                      <div v-if="t.finish" class="text-xs"><span class="text-muted">Final:</span> <span class="text-soft">{{ t.finish }}</span></div>
                    </div>
                    <div v-if="t.notes" class="timeline-notes">"{{ t.notes }}"</div>
                    <div v-if="t.would_buy_again !== null" class="text-xs mt-1" :style="t.would_buy_again ? 'color:var(--s-success)' : 'color:var(--ink-mute)'">
                      {{ t.would_buy_again ? '✓ Compraria novamente' : '✗ Não compraria novamente' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- STOCK MODAL -->
        <div v-if="showStockModal" class="modal-overlay" @click.self="showStockModal=false">
          <div class="modal">
            <div class="modal-header">
              <div class="modal-title">📦 Movimento de Stock</div>
              <button class="modal-close" @click="showStockModal=false">✕</button>
            </div>
            <form @submit.prevent="saveStock">
              <div class="field-row">
                <div class="field">
                  <label class="field-label">Tipo</label>
                  <select v-model="stockForm.type" class="select">
                    <option value="in">⬆ Entrada (compra)</option>
                    <option value="out">⬇ Saída (consumo/oferta/venda)</option>
                    <option value="adjust">⚖ Ajuste de inventário</option>
                  </select>
                </div>
                <div class="field">
                  <label class="field-label">Quantidade</label>
                  <input v-model.number="stockForm.quantity" type="number" min="1" class="input" required>
                </div>
              </div>
              <div class="field-row">
                <div class="field">
                  <label class="field-label">Localização</label>
                  <select v-model="stockForm.location_id" class="select">
                    <option value="">— Nenhuma —</option>
                    <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
                  </select>
                </div>
                <div class="field">
                  <label class="field-label">Motivo</label>
                  <input v-model="stockForm.reason" class="input" placeholder="compra / consumo / oferta…">
                </div>
              </div>
              <div class="field">
                <label class="field-label">Notas</label>
                <textarea v-model="stockForm.notes" class="textarea" style="min-height:60px"></textarea>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-ghost" @click="showStockModal=false">Cancelar</button>
                <button type="submit" class="btn btn-gold" :disabled="stockSaving">
                  <span v-if="stockSaving" class="spinner"></span><span v-else>✓ Registar</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- TASTING MODAL -->
        <div v-if="showTastingModal" class="modal-overlay" @click.self="showTastingModal=false">
          <div class="modal modal-wide">
            <div class="modal-header">
              <div class="modal-title">🍷 Nova Degustação</div>
              <button class="modal-close" @click="showTastingModal=false">✕</button>
            </div>
            <form @submit.prevent="saveTasting">
              <div class="field-row">
                <div class="field"><label class="field-label">Data</label><input v-model="tForm.date" type="date" class="input" required></div>
                <div class="field"><label class="field-label">Ocasião</label><input v-model="tForm.occasion" class="input" placeholder="Jantar, prova…"></div>
              </div>
              <div class="grid-2">
                <div class="field"><label class="field-label">Aspecto (cor)</label><textarea v-model="tForm.appearance" class="textarea" style="min-height:54px" placeholder="Rubi intenso…"></textarea></div>
                <div class="field"><label class="field-label">Aroma (nariz)</label><textarea v-model="tForm.nose" class="textarea" style="min-height:54px" placeholder="Frutos negros…"></textarea></div>
                <div class="field"><label class="field-label">Boca (palato)</label><textarea v-model="tForm.palate" class="textarea" style="min-height:54px" placeholder="Encorpado, taninos…"></textarea></div>
                <div class="field"><label class="field-label">Final</label><textarea v-model="tForm.finish" class="textarea" style="min-height:54px" placeholder="Longo, persistente…"></textarea></div>
              </div>
              <div class="field-row">
                <div class="field">
                  <label class="field-label">Classificação (1-100)</label>
                  <input v-model="tForm.overall_score" type="number" min="1" max="100" class="input" placeholder="Ex: 92">
                </div>
                <div class="field">
                  <label class="field-label">Compraria novamente?</label>
                  <select v-model="tForm.would_buy_again" class="select">
                    <option :value="null">—</option>
                    <option :value="true">✓ Sim</option>
                    <option :value="false">✗ Não</option>
                  </select>
                </div>
              </div>
              <div class="field"><label class="field-label">Notas gerais</label><textarea v-model="tForm.notes" class="textarea"></textarea></div>
              <div class="modal-footer">
                <button type="button" class="btn btn-ghost" @click="showTastingModal=false">Cancelar</button>
                <button type="submit" class="btn btn-gold" :disabled="tSaving">
                  <span v-if="tSaving" class="spinner"></span><span v-else>✓ Registar Prova</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </template>
    </div>
  `,
};
