// GrapeHub — Wishlist (lista de desejos).
const { ref, onMounted, inject, computed } = Vue;
import { wishlistService, PRIORITY_LABELS, PRIORITY_BADGE } from '../services/wishlist.js';
import { wineService, formatPrice } from '../services/wines.js';

export default {
  name: 'WishlistView',
  setup() {
    const toast = inject('toast', () => {});
    const items = ref([]);
    const deals = ref(null);
    const recommendations = ref(null);
    const loading = ref(true);
    const showModal = ref(false);
    const saving = ref(false);
    const priorityFilter = ref('');
    const form = ref({ description:'', target_price:'', priority:'medium', notes:'', price_tracking: false });

    const filteredItems = computed(() => {
      if (!priorityFilter.value) return items.value;
      return items.value.filter(i => i.priority === priorityFilter.value);
    });

    async function load() {
      loading.value = true;
      try {
        const [w, d, r] = await Promise.all([
          wishlistService.list(),
          wishlistService.deals(),
          wishlistService.recommendations(),
        ]);
        items.value = w;
        deals.value = d;
        recommendations.value = r;
      } catch (e) { toast(e.message, 'error'); }
      finally { loading.value = false; }
    }

    async function save() {
      if (!form.value.description.trim()) { toast('Indique o vinho desejado', 'error'); return; }
      saving.value = true;
      try {
        const payload = {
          description: form.value.description.trim(),
          target_price: form.value.target_price === '' ? null : Number(form.value.target_price),
          price_tracking: form.value.price_tracking,
          priority: form.value.priority,
          notes: form.value.notes || null,
        };
        await wishlistService.create(payload);
        toast('Adicionado à lista de desejos! ♡', 'success');
        showModal.value = false;
        form.value = { description:'', target_price:'', priority:'medium', notes:'', price_tracking: false };
        await load();
      } catch (e) { toast(e.message, 'error'); }
      finally { saving.value = false; }
    }

    async function remove(id) {
      if (!confirm('Remover da lista de desejos?')) return;
      try { await wishlistService.remove(id); items.value = items.value.filter(i=>i.id!==id); toast('Removido','success'); }
      catch (e) { toast(e.message, 'error'); }
    }

    onMounted(load);
    return { items, filteredItems, deals, recommendations, loading, showModal, saving, form, priorityFilter, save, remove, load, formatPrice, PRIORITY_LABELS, PRIORITY_BADGE };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">♡ Lista de Desejos<small>Vinhos para adquirir</small></h1>
        <button class="btn btn-gold" @click="showModal=true">＋ Adicionar Desejo</button>
      </div>

      <div v-if="loading" class="page-loading"><div class="page-loading-icon">♡</div><span>A carregar…</span></div>

      <template v-else>
        <!-- DEALS SECTION -->
        <div v-if="deals && deals.deals_found > 0" class="card" style="border-top:3px solid var(--s-success);margin-bottom:2rem">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
            <div class="section-title" style="margin-bottom:0">🎉 {{ deals.deals_found }} Deal(s) Encontrada(s)!</div>
            <span class="badge badge-success">Preço-alvo atingido</span>
          </div>
          <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem">
            <div v-for="deal in deals.deals" :key="deal.item_id" class="card" v-if="deal.price_is_good" style="background:rgba(76,175,80,.08);border-left:4px solid var(--s-success);position:relative">
              <div style="position:absolute;top:0;right:0;font-size:1.5rem">✓</div>
              <div class="wine-card-name" style="margin-bottom:0.5rem">{{ deal.description }}</div>
              <div class="text-sm text-muted mb-2">{{ PRIORITY_LABELS[deal.priority] }}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin:0.5rem 0">
                <div><div class="text-xs text-muted">Preço-alvo</div><div style="font-size:1.1rem;font-weight:600;color:var(--s-success)">{{ formatPrice(deal.target_price) }}</div></div>
                <div><div class="text-xs text-muted">Estimado</div><div style="font-size:1.1rem;font-weight:600">{{ formatPrice(deal.estimated_price || 0) }}</div></div>
              </div>
            </div>
          </div>
        </div>

        <!-- RECOMMENDATIONS SECTION -->
        <div v-if="recommendations && recommendations.found > 0" class="card" style="border-top:3px solid var(--gold);margin-bottom:2rem">
          <div class="section-title">💡 Recomendações para ti</div>
          <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem">
            <div v-for="rec in recommendations.recommendations" :key="rec.id" class="card" style="background:rgba(201,168,76,.05)">
              <div class="wine-card-name" style="margin-bottom:0.25rem">{{ rec.name }}</div>
              <div class="text-xs text-muted">{{ rec.region }} · {{ rec.vintage }}</div>
              <div class="flex justify-between items-center mt-2" style="border-top:1px solid var(--border-md);padding-top:0.75rem">
                <span class="text-xs text-soft">{{ rec.score ? rec.score + '/100' : '—' }}</span>
                <span class="wine-price">{{ formatPrice(rec.price) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- WISHLIST SECTION -->
        <div v-if="!items.length" class="empty-state">
          <div class="empty-icon">♡</div><div class="empty-title">Lista de desejos vazia</div>
          <div class="empty-desc">Adicione os vinhos que sonha adquirir.</div>
          <button class="btn btn-gold mt-4" @click="showModal=true">♡ Adicionar Primeiro Desejo</button>
        </div>

        <div v-else>
          <div style="margin-bottom:1rem;display:flex;gap:0.5rem;flex-wrap:wrap">
            <button :class="['filter-chip', !priorityFilter?'active':'']" @click="priorityFilter=''">Todos ({{ items.length }})</button>
            <button :class="['filter-chip', priorityFilter==='high'?'active':'']" @click="priorityFilter='high'">Alta ({{ items.filter(i=>i.priority==='high').length }})</button>
            <button :class="['filter-chip', priorityFilter==='medium'?'active':'']" @click="priorityFilter='medium'">Média ({{ items.filter(i=>i.priority==='medium').length }})</button>
            <button :class="['filter-chip', priorityFilter==='low'?'active':'']" @click="priorityFilter='low'">Baixa ({{ items.filter(i=>i.priority==='low').length }})</button>
          </div>

          <div class="wine-grid">
            <div v-for="item in filteredItems" :key="item.id" class="wine-card">
              <div class="wine-card-header">
                <div style="flex:1"><div class="wine-card-name">{{ item.description }}</div></div>
                <div style="display:flex;gap:0.5rem;align-items:center">
                  <span v-if="item.price_tracking" class="badge badge-success" style="font-size:0.7rem">📊</span>
                  <span :class="['badge', PRIORITY_BADGE[item.priority]]">{{ PRIORITY_LABELS[item.priority] }}</span>
                </div>
              </div>
              <div v-if="item.notes" class="text-sm text-soft" style="font-style:italic;margin:0.5rem 0">"{{ item.notes }}"</div>
              <div class="wine-card-footer">
                <span v-if="item.target_price" class="wine-price">🎯 {{ formatPrice(item.target_price) }}</span>
                <span v-else class="text-xs text-muted">Sem preço-alvo</span>
                <button class="btn btn-danger btn-sm btn-icon" @click="remove(item.id)">✕</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- MODAL -->
      <div v-if="showModal" class="modal-overlay" @click.self="showModal=false">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">♡ Novo Desejo</div>
            <button class="modal-close" @click="showModal=false">✕</button>
          </div>
          <form @submit.prevent="save">
            <div class="field">
              <label class="field-label">Vinho desejado *</label>
              <input v-model="form.description" class="input" required placeholder="Ex: Pétrus 2005">
            </div>
            <div class="field-row">
              <div class="field">
                <label class="field-label">Preço-alvo (€)</label>
                <input v-model="form.target_price" type="number" step="0.01" min="0" class="input" placeholder="0.00">
              </div>
              <div class="field">
                <label class="field-label">Prioridade</label>
                <select v-model="form.priority" class="select">
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                </select>
              </div>
            </div>
            <div class="field">
              <label class="checkbox">
                <input v-model="form.price_tracking" type="checkbox">
                Monitorizar preços
              </label>
              <small class="text-muted">Receber notificações quando o preço atingir o alvo</small>
            </div>
            <div class="field">
              <label class="field-label">Notas</label>
              <textarea v-model="form.notes" class="textarea" placeholder="Porque o deseja…"></textarea>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-ghost" @click="showModal=false">Cancelar</button>
              <button type="submit" class="btn btn-gold" :disabled="saving">
                <span v-if="saving" class="spinner"></span><span v-else>♡ Adicionar</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
};
