// GrapeHub — Cellar/catalogue with filters, search, grid/list, photo thumbs.
const { ref, onMounted, inject } = Vue;
const { useRouter } = VueRouter;
import {
  wineService, WINE_TYPE_LABELS, WINE_TYPE_ICONS, DW_STATUS_LABELS, DW_STATUS_CLASS,
  formatPrice, photoUrl, starsFromScore,
} from '../services/wines.js';

export default {
  name: 'CellarView',
  setup() {
    const router  = useRouter();
    const toast   = inject('toast', () => {});

    const wines       = ref([]);
    const loading     = ref(true);
    const search      = ref('');
    const filterType  = ref('');
    const filterRegion = ref('');
    const filterProducer = ref('');
    const priceMin    = ref('');
    const priceMax    = ref('');
    const sortBy      = ref('recent');
    const sortOrder   = ref('desc');
    const inStockOnly = ref(false);
    const viewMode    = ref('grid');
    const deleting    = ref(null);
    const windowCache = ref({});
    const showAdvancedFilters = ref(false);

    const showImportModal = ref(false);
    const importFile      = ref(null);
    const importLoading   = ref(false);
    const importResult    = ref(null);

    async function importCsv() {
      if (!importFile.value) {
        toast('Selecione um arquivo CSV', 'warning');
        return;
      }
      importLoading.value = true;
      try {
        const result = await wineService.importCsv(importFile.value);
        importResult.value = result;
        toast(`${result.imported} garrafa(s) importada(s)!`, 'success');
        setTimeout(() => { load(); showImportModal.value = false; importResult.value = null; importFile.value = null; }, 1500);
      } catch (e) { toast(e.message, 'error'); }
      finally { importLoading.value = false; }
    }

    async function load() {
      loading.value = true;
      try {
        const params = { sort: sortBy.value, sort_order: sortOrder.value };
        if (filterType.value)    params.wine_type = filterType.value;
        if (filterRegion.value)  params.region = filterRegion.value;
        if (filterProducer.value) params.producer_id = filterProducer.value;
        if (priceMin.value)      params.price_min = parseFloat(priceMin.value);
        if (priceMax.value)      params.price_max = parseFloat(priceMax.value);
        if (search.value.trim()) params.q = search.value.trim();
        if (inStockOnly.value)   params.in_stock = true;
        wines.value = await wineService.list(params);
        wines.value.forEach(async (w) => {
          if (windowCache.value[w.id] === undefined) {
            try { windowCache.value[w.id] = await wineService.window(w.id); }
            catch { windowCache.value[w.id] = null; }
          }
        });
      } catch (e) { toast(e.message, 'error'); }
      finally { loading.value = false; }
    }

    async function deleteWine(id) {
      if (!confirm('Remover esta garrafa da garrafeira?')) return;
      deleting.value = id;
      try {
        await wineService.remove(id);
        wines.value = wines.value.filter(w => w.id !== id);
        toast('Garrafa removida', 'success');
      } catch (e) { toast(e.message, 'error'); }
      finally { deleting.value = null; }
    }

    function setFilter(t) { filterType.value = t; load(); }

    onMounted(load);

    const typeLabel = (t) => WINE_TYPE_LABELS[t] || t;
    const typeIcon  = (t) => WINE_TYPE_ICONS[t] || '🍷';
    const typeBadge = (t) => `badge-${t === 'rosé' ? 'rosé' : t}`;
    const dwInfo    = (id) => windowCache.value[id];

    return {
      wines, loading, search, filterType, filterRegion, filterProducer, priceMin, priceMax,
      sortBy, sortOrder, inStockOnly, viewMode, showAdvancedFilters,
      deleting, load, deleteWine, setFilter,
      showImportModal, importFile, importLoading, importResult, importCsv,
      typeLabel, typeIcon, typeBadge, dwInfo, photoUrl, starsFromScore,
      formatPrice, DW_STATUS_LABELS, DW_STATUS_CLASS, router,
      TYPES: ['', 'red', 'white', 'rosé', 'sparkling', 'fortified'],
      TYPE_LABELS: { '':'Todos', red:'Tinto', white:'Branco', 'rosé':'Rosé', sparkling:'Espumante', fortified:'Licoroso' },
      SORT_OPTIONS: [
        { value: 'recent', label: 'Mais recentes' },
        { value: 'name', label: 'Nome (A-Z)' },
        { value: 'year', label: 'Ano' },
        { value: 'score', label: 'Classificação' },
        { value: 'price', label: 'Preço' },
      ],
    };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">🍷 Garrafeira
          <small>{{ wines.length }} referência(s)</small>
        </h1>
        <div class="page-actions">
          <button :class="['btn btn-ghost btn-sm', viewMode==='grid'?'active':'']" @click="viewMode='grid'" title="Grelha">⊞</button>
          <button :class="['btn btn-ghost btn-sm', viewMode==='list'?'active':'']" @click="viewMode='list'" title="Lista">☰</button>
          <button class="btn btn-ghost" @click="showImportModal=true">📥 Importar CSV</button>
          <router-link to="/wines/new" class="btn btn-gold">＋ Adicionar</router-link>
        </div>
      </div>

      <!-- FILTERS -->
      <div class="filters-bar">
        <div class="flex gap-2" style="flex-wrap:wrap">
          <button v-for="t in TYPES" :key="t" :class="['filter-chip', filterType===t?'active':'']" @click="setFilter(t)">
            {{ TYPE_LABELS[t] }}
          </button>
        </div>
        <div style="width:1px;height:20px;background:var(--border)"></div>
        <label class="filter-chip" :class="{active: inStockOnly}" @click="inStockOnly=!inStockOnly;load()">
          {{ inStockOnly ? '☑' : '☐' }} Em stock
        </label>
        <select v-model="sortBy" class="select" style="width:auto" @change="load">
          <option v-for="opt in SORT_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <select v-model="sortOrder" class="select" style="width:auto" @change="load" v-show="sortBy !== 'recent'">
          <option value="asc">↑ Crescente</option>
          <option value="desc">↓ Decrescente</option>
        </select>
        <button :class="['filter-chip', showAdvancedFilters?'active':'']" @click="showAdvancedFilters=!showAdvancedFilters">
          ⚙ Avançado
        </button>
        <div class="search-wrap">
          <span class="search-icon">⌕</span>
          <input v-model="search" class="input" placeholder="Pesquisar vinho, produtor, região…"
                 @keyup.enter="load" @keyup.escape="search='';load()">
        </div>
        <button class="btn btn-ghost btn-sm" @click="load">Filtrar</button>
      </div>

      <!-- ADVANCED FILTERS -->
      <div v-if="showAdvancedFilters" class="card" style="margin-bottom:1rem;padding:1rem">
        <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem">
          <div>
            <label class="label">Região</label>
            <input v-model="filterRegion" class="input" placeholder="Ex: Douro, Alentejo" @keyup.enter="load">
          </div>
          <div>
            <label class="label">Produtor</label>
            <input v-model="filterProducer" class="input" type="number" placeholder="ID do produtor" @keyup.enter="load">
          </div>
          <div>
            <label class="label">Preço Mínimo (€)</label>
            <input v-model="priceMin" class="input" type="number" placeholder="Ex: 10" @keyup.enter="load">
          </div>
          <div>
            <label class="label">Preço Máximo (€)</label>
            <input v-model="priceMax" class="input" type="number" placeholder="Ex: 100" @keyup.enter="load">
          </div>
        </div>
        <div style="margin-top:1rem">
          <button class="btn btn-gold btn-sm" @click="load">Aplicar Filtros</button>
          <button class="btn btn-ghost btn-sm" @click="filterRegion='';filterProducer='';priceMin='';priceMax='';load()">Limpar</button>
        </div>
      </div>

      <div v-if="loading" class="page-loading">
        <div class="page-loading-icon">🍾</div><span>A carregar…</span>
      </div>

      <div v-else-if="!wines.length" class="empty-state">
        <div class="empty-icon">🍷</div>
        <div class="empty-title">Nenhum vinho encontrado</div>
        <div class="empty-desc">{{ filterType || search || inStockOnly ? 'Experimente outros filtros.' : 'Adicione a primeira garrafa!' }}</div>
        <router-link v-if="!filterType && !search" to="/wines/new" class="btn btn-gold mt-4">🍷 Adicionar Garrafa</router-link>
      </div>

      <!-- GRID -->
      <div v-else-if="viewMode==='grid'" class="wine-grid">
        <div v-for="wine in wines" :key="wine.id" class="wine-card">
          <!-- Photo or placeholder -->
          <div @click="router.push('/wines/'+wine.id)" style="cursor:pointer;margin:-4px -4px 4px;border-radius:14px 14px 0 0;overflow:hidden;height:140px;background:linear-gradient(160deg,var(--wine-deep),var(--bg-card));display:flex;align-items:center;justify-content:center">
            <img v-if="wine.photo_path" :src="photoUrl(wine.photo_path)" style="width:100%;height:100%;object-fit:cover">
            <span v-else style="font-size:3rem;opacity:.35">{{ typeIcon(wine.wine_type) }}</span>
          </div>

          <div class="wine-card-header" @click="router.push('/wines/'+wine.id)" style="cursor:pointer">
            <div style="flex:1">
              <div class="wine-card-name">{{ wine.name }}</div>
              <div class="wine-card-producer">{{ wine.producer_name }}</div>
            </div>
            <div class="wine-card-year">{{ wine.vintage_year }}</div>
          </div>

          <div class="wine-card-meta" @click="router.push('/wines/'+wine.id)" style="cursor:pointer">
            <span :class="['badge', typeBadge(wine.wine_type)]">{{ typeIcon(wine.wine_type) }} {{ typeLabel(wine.wine_type) }}</span>
            <span class="text-xs text-muted">{{ wine.region }}</span>
          </div>

          <div v-if="wine.avg_score" class="wine-rating" @click="router.push('/wines/'+wine.id)" style="cursor:pointer">
            <span class="wine-rating-stars">{{ starsFromScore(wine.avg_score) }}</span>
            <span class="wine-rating-val">{{ wine.avg_score }}/100</span>
          </div>

          <div v-if="dwInfo(wine.id)" @click="router.push('/wines/'+wine.id)" style="cursor:pointer">
            <span :class="['dw-badge', DW_STATUS_CLASS[dwInfo(wine.id).status]]">{{ DW_STATUS_LABELS[dwInfo(wine.id).status] }}</span>
          </div>

          <div class="wine-card-footer">
            <span class="wine-qty" :style="wine.min_stock && wine.current_stock <= wine.min_stock ? 'color:var(--s-warning)' : ''">
              📦 {{ wine.current_stock }}{{ wine.min_stock && wine.current_stock <= wine.min_stock ? ' ⚠' : '' }}
            </span>
            <div class="flex gap-2 items-center">
              <span v-if="wine.purchase_price" class="wine-price">{{ formatPrice(wine.purchase_price) }}</span>
              <button class="btn btn-ghost btn-sm btn-icon" title="Editar" @click.stop="router.push('/wines/'+wine.id+'/edit')">✏</button>
              <button class="btn btn-danger btn-sm btn-icon" title="Remover" @click.stop="deleteWine(wine.id)" :disabled="deleting===wine.id">✕</button>
            </div>
          </div>
        </div>
      </div>

      <!-- LIST -->
      <div v-else class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Vinho</th><th>Tipo</th><th>Região</th><th>Ano</th>
              <th>Stock</th><th>Nota</th><th>Preço</th><th></th>
            </tr></thead>
            <tbody>
              <tr v-for="wine in wines" :key="wine.id" style="cursor:pointer" @click="router.push('/wines/'+wine.id)">
                <td>
                  <div class="td-name">{{ wine.name }}</div>
                  <div class="td-producer">{{ wine.producer_name }}</div>
                </td>
                <td><span :class="['badge', typeBadge(wine.wine_type)]">{{ typeIcon(wine.wine_type) }} {{ typeLabel(wine.wine_type) }}</span></td>
                <td class="text-soft">{{ wine.region }}</td>
                <td class="td-year">{{ wine.vintage_year }}</td>
                <td><span class="badge" :class="wine.current_stock > (wine.min_stock||0) ? 'badge-success' : wine.current_stock > 0 ? 'badge-warning' : 'badge-danger'">{{ wine.current_stock }}</span></td>
                <td class="text-mono text-gold">{{ wine.avg_score ? wine.avg_score+'/100' : '—' }}</td>
                <td class="td-price">{{ formatPrice(wine.purchase_price) }}</td>
                <td @click.stop>
                  <div class="flex gap-2">
                    <button class="btn btn-ghost btn-sm" @click="router.push('/wines/'+wine.id+'/edit')">✏</button>
                    <button class="btn btn-danger btn-sm" @click="deleteWine(wine.id)" :disabled="deleting===wine.id">✕</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- IMPORT MODAL -->
      <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal=false">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">📥 Importar Garrafas (CSV)</div>
            <button class="modal-close" @click="showImportModal=false">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="!importResult">
              <div class="field" style="margin-bottom:1rem">
                <label class="label">Selecione um arquivo CSV</label>
                <input type="file" accept=".csv" @change="e => importFile = e.target.files?.[0] || null" class="input" style="cursor:pointer">
                <div class="text-xs text-muted mt-2">Colunas esperadas: name, producer, region, year, type, volume, alcohol, price, grapes_str</div>
              </div>
              <div class="card" style="background:rgba(201,168,76,.08);padding:0.75rem;margin-bottom:1rem">
                <div class="text-xs text-gold font-semibold mb-2">💡 Template CSV</div>
                <div class="text-xs text-soft" style="font-family:monospace">name,producer,region,year,type,volume,alcohol,price,grapes_str</div>
                <div class="text-xs text-soft" style="font-family:monospace">Douro Tinto,Quinta do Côa,Douro,2018,red,750,14.5,25,Touriga Nacional (50%), Tinta Roriz (50%)</div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-ghost" @click="showImportModal=false">Cancelar</button>
                <button class="btn btn-gold" @click="importCsv" :disabled="!importFile || importLoading">
                  <span v-if="importLoading" class="spinner"></span><span v-else>Importar →</span>
                </button>
              </div>
            </div>
            <div v-else class="text-center">
              <div style="font-size:2.5rem;margin-bottom:1rem">{{ importResult.imported > 0 ? '✓' : '⚠' }}</div>
              <div class="text-lg font-semibold mb-2">{{ importResult.imported }} garrafas importadas</div>
              <div v-if="importResult.errors.length" class="text-sm text-danger mb-4">
                {{ importResult.errors.length }} erro(s) encontrados
                <div class="mt-2 text-xs text-soft" style="max-height:150px;overflow-y:auto">
                  <div v-for="(err, idx) in importResult.errors" :key="idx">{{ err }}</div>
                </div>
              </div>
              <button class="btn btn-gold" @click="showImportModal=false">Fechar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
