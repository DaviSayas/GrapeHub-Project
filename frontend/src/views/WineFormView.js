// GrapeHub — Add / Edit wine: photo upload+preview, producer autocomplete, grapes%.
const { ref, onMounted, computed, inject } = Vue;
const { useRouter, useRoute } = VueRouter;
import { wineService, producerService, grapeService, REGIONS, photoUrl } from '../services/wines.js';

export default {
  name: 'WineFormView',
  setup() {
    const router = useRouter();
    const route  = useRoute();
    const toast  = inject('toast', () => {});

    const isEdit = computed(() => !!route.params.id && route.path.endsWith('/edit'));
    const wineId = computed(() => route.params.id);

    const loading = ref(false);
    const saving  = ref(false);
    const error   = ref('');

    const form = ref({
      name: '', producer_name: '', region: 'Douro',
      vintage_year: new Date().getFullYear() - 3, wine_type: 'red',
      volume_ml: 750, alcoholic_degree: '', purchase_price: '',
      description: '', consume_from_year: '', consume_until_year: '',
      min_stock: 0, initial_stock: 0,
    });

    // Grapes (array of {name, percentage})
    const grapes = ref([]);
    function addGrape() { grapes.value.push({ name: '', percentage: '' }); }
    function removeGrape(i) { grapes.value.splice(i, 1); }

    // Producer autocomplete
    const producerSuggestions = ref([]);
    const showProducerList = ref(false);
    let producerTimer = null;
    function onProducerInput() {
      clearTimeout(producerTimer);
      producerTimer = setTimeout(async () => {
        if (form.value.producer_name.length < 2) { producerSuggestions.value = []; return; }
        try {
          producerSuggestions.value = await producerService.list(form.value.producer_name);
          showProducerList.value = true;
        } catch {}
      }, 250);
    }
    function pickProducer(p) {
      form.value.producer_name = p.name;
      if (p.region) form.value.region = p.region;
      showProducerList.value = false;
    }

    // Grape autocomplete (shared list)
    const allGrapes = ref([]);

    // Photo upload
    const photoPreview = ref(null);
    const labelPreview = ref(null);
    const photoFile = ref(null);
    const labelFile = ref(null);
    const ocrLoading = ref(false);
    const ocrResult = ref(null);

    function onPhotoChange(e, kind) {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        if (kind === 'label') { labelPreview.value = ev.target.result; labelFile.value = file; }
        else { photoPreview.value = ev.target.result; photoFile.value = file; }
      };
      reader.readAsDataURL(file);
    }

    async function runOcr() {
      if (!labelFile.value) { toast('Selecione uma foto da etiqueta primeiro', 'warning'); return; }
      ocrLoading.value = true;
      try {
        const result = await wineService.ocrLabel(labelFile.value);
        if (result.success) {
          ocrResult.value = result;
          const fields = result.extracted_fields;
          if (fields.name) form.value.name = fields.name;
          if (fields.region) form.value.region = fields.region;
          if (fields.wine_type) form.value.wine_type = fields.wine_type;
          if (fields.vintage_year) form.value.vintage_year = fields.vintage_year;
          if (fields.alcoholic_degree) form.value.alcoholic_degree = fields.alcoholic_degree;
          toast('Etiqueta analisada! Campos pré-preenchidos. 📖', 'success');
        } else {
          toast(result.message, 'warning');
        }
      } catch (e) { toast(e.message, 'error'); }
      finally { ocrLoading.value = false; }
    }

    async function load() {
      try { allGrapes.value = await grapeService.list(); } catch {}
      if (!isEdit.value) return;
      loading.value = true;
      try {
        const w = await wineService.get(wineId.value);
        Object.assign(form.value, {
          name: w.name, producer_name: w.producer?.name || '', region: w.region,
          vintage_year: w.vintage_year, wine_type: w.wine_type, volume_ml: w.volume_ml,
          alcoholic_degree: w.alcoholic_degree ?? '', purchase_price: w.purchase_price ?? '',
          description: w.description ?? '', consume_from_year: w.consume_from_year ?? '',
          consume_until_year: w.consume_until_year ?? '', min_stock: w.min_stock ?? 0,
          initial_stock: 0,
        });
        grapes.value = (w.grapes || []).map(g => ({ name: g.name, percentage: g.percentage ?? '' }));
        if (w.photo_path) photoPreview.value = photoUrl(w.photo_path);
        if (w.label_photo_path) labelPreview.value = photoUrl(w.label_photo_path);
      } catch (e) { error.value = e.message; }
      finally { loading.value = false; }
    }

    async function save() {
      error.value = '';
      if (!form.value.name.trim()) { error.value = 'O nome é obrigatório'; return; }
      if (!form.value.producer_name.trim()) { error.value = 'O produtor é obrigatório'; return; }
      saving.value = true;
      try {
        const payload = { ...form.value };
        ['alcoholic_degree','purchase_price','consume_from_year','consume_until_year'].forEach(k => {
          payload[k] = payload[k] === '' ? null : Number(payload[k]);
        });
        payload.vintage_year = parseInt(payload.vintage_year);
        payload.volume_ml = parseInt(payload.volume_ml) || 750;
        payload.min_stock = parseInt(payload.min_stock) || 0;
        payload.initial_stock = parseInt(payload.initial_stock) || 0;
        if (!payload.description) payload.description = null;
        payload.grapes = grapes.value
          .filter(g => g.name.trim())
          .map(g => ({ name: g.name.trim(), percentage: g.percentage === '' ? null : Number(g.percentage) }));

        let wine;
        if (isEdit.value) {
          wine = await wineService.update(wineId.value, payload);
        } else {
          wine = await wineService.create(payload);
        }

        // Upload photos if selected
        if (photoFile.value) {
          try { await wineService.uploadPhoto(wine.id, photoFile.value, 'photo'); }
          catch (e) { toast('Foto da garrafa: ' + e.message, 'error'); }
        }
        if (labelFile.value) {
          try { await wineService.uploadPhoto(wine.id, labelFile.value, 'label'); }
          catch (e) { toast('Foto da etiqueta: ' + e.message, 'error'); }
        }

        toast(isEdit.value ? 'Garrafa actualizada!' : 'Garrafa adicionada! 🍷', 'success');
        router.push('/wines/' + wine.id);
      } catch (e) {
        error.value = e.message || 'Erro ao guardar';
      } finally { saving.value = false; }
    }

    onMounted(load);

    const WINE_TYPES = [
      { v:'red', l:'🍷 Tinto' }, { v:'white', l:'🥂 Branco' }, { v:'rosé', l:'🌸 Rosé' },
      { v:'sparkling', l:'✨ Espumante' }, { v:'fortified', l:'🪙 Licoroso' },
    ];
    const VOLUMES = [375, 500, 750, 1000, 1500, 3000];
    const cy = new Date().getFullYear();
    const years = Array.from({ length: cy - 1949 }, (_, i) => cy - i);

    return {
      form, grapes, loading, saving, error, isEdit, save,
      addGrape, removeGrape, allGrapes,
      producerSuggestions, showProducerList, onProducerInput, pickProducer,
      photoPreview, labelPreview, onPhotoChange, ocrLoading, ocrResult, runOcr,
      WINE_TYPES, REGIONS, VOLUMES, years, router,
    };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">{{ isEdit ? '✏ Editar Garrafa' : '🍷 Adicionar Garrafa' }}
          <small>{{ isEdit ? 'Actualizar informações' : 'Registar novo vinho na garrafeira' }}</small>
        </h1>
        <button class="btn btn-ghost" @click="router.back()">← Cancelar</button>
      </div>

      <div v-if="loading" class="page-loading"><div class="page-loading-icon">🍷</div><span>A carregar…</span></div>

      <form v-else @submit.prevent="save" style="max-width:820px">
        <div v-if="error" class="alert alert-error mb-4">{{ error }}</div>

        <!-- PHOTOS -->
        <div class="card mb-5">
          <div class="section-title">Fotografias</div>
          <div class="grid-2">
            <div class="field">
              <label class="field-label">Foto da Garrafa</label>
              <label style="display:block;cursor:pointer;border:2px dashed var(--border-md);border-radius:12px;overflow:hidden;aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;background:var(--bg-card)">
                <img v-if="photoPreview" :src="photoPreview" style="width:100%;height:100%;object-fit:cover">
                <div v-else style="text-align:center;color:var(--ink-mute)">
                  <div style="font-size:2.5rem">📷</div>
                  <div class="text-xs">Clique para escolher</div>
                </div>
                <input type="file" accept="image/*" @change="onPhotoChange($event,'photo')" style="display:none">
              </label>
            </div>
            <div class="field">
              <label class="field-label">Foto da Etiqueta</label>
              <label style="display:block;cursor:pointer;border:2px dashed var(--border-md);border-radius:12px;overflow:hidden;aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;background:var(--bg-card)">
                <img v-if="labelPreview" :src="labelPreview" style="width:100%;height:100%;object-fit:cover">
                <div v-else style="text-align:center;color:var(--ink-mute)">
                  <div style="font-size:2.5rem">🏷️</div>
                  <div class="text-xs">Clique para escolher</div>
                </div>
                <input type="file" accept="image/*" @change="onPhotoChange($event,'label')" style="display:none">
              </label>
              <div v-if="labelPreview" style="margin-top:0.75rem">
                <button type="button" class="btn btn-ghost btn-sm" @click="runOcr" :disabled="ocrLoading">
                  <span v-if="ocrLoading" class="spinner"></span><span v-else>📖 Analisar Etiqueta (OCR)</span>
                </button>
                <div v-if="ocrResult" class="text-xs text-soft mt-2" style="background:rgba(201,168,76,.08);padding:0.5rem;border-radius:4px">
                  ✓ Etiqueta analisada - campos actualizados
                </div>
              </div>
            </div>
          </div>
          <p class="text-xs text-muted">Formatos: JPG, PNG, WEBP · máx 10 MB · armazenamento local</p>
        </div>

        <!-- IDENTITY -->
        <div class="card mb-5">
          <div class="section-title">Identificação</div>
          <div class="field-row">
            <div class="field">
              <label class="field-label">Nome do Vinho *</label>
              <input v-model="form.name" class="input" required placeholder="Ex: Reserva Vinhas Velhas">
            </div>
            <div class="field" style="position:relative">
              <label class="field-label">Produtor / Quinta *</label>
              <input v-model="form.producer_name" class="input" required autocomplete="off"
                     placeholder="Ex: Quinta do Crasto"
                     @input="onProducerInput" @focus="onProducerInput" @blur="setTimeout(()=>showProducerList=false,200)">
              <div v-if="showProducerList && producerSuggestions.length"
                   style="position:absolute;top:100%;left:0;right:0;z-index:20;background:var(--bg-elev);border:1px solid var(--border-md);border-radius:8px;margin-top:4px;max-height:180px;overflow-y:auto;box-shadow:var(--shadow)">
                <div v-for="p in producerSuggestions" :key="p.id" @mousedown="pickProducer(p)"
                     style="padding:8px 12px;cursor:pointer;font-size:.88rem" class="producer-option">
                  {{ p.name }} <span class="text-xs text-muted">· {{ p.region }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="field-row three">
            <div class="field">
              <label class="field-label">Tipo *</label>
              <select v-model="form.wine_type" class="select">
                <option v-for="t in WINE_TYPES" :key="t.v" :value="t.v">{{ t.l }}</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Ano *</label>
              <select v-model.number="form.vintage_year" class="select">
                <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Volume</label>
              <select v-model.number="form.volume_ml" class="select">
                <option v-for="v in VOLUMES" :key="v" :value="v">{{ v>=1000 ? (v/1000)+'L' : v+'ml' }}</option>
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label class="field-label">Região</label>
              <select v-model="form.region" class="select">
                <option v-for="r in REGIONS" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Álcool (%)</label>
              <input v-model="form.alcoholic_degree" type="number" step="0.1" min="0" max="25" class="input" placeholder="13.5">
            </div>
          </div>
        </div>

        <!-- GRAPES -->
        <div class="card mb-5">
          <div class="flex justify-between items-center mb-3">
            <div class="section-title" style="margin-bottom:0">Castas (composição)</div>
            <button type="button" class="btn btn-ghost btn-sm" @click="addGrape">＋ Adicionar casta</button>
          </div>
          <div v-if="!grapes.length" class="text-sm text-muted">Sem castas definidas. Adicione a composição do vinho.</div>
          <div v-for="(g,i) in grapes" :key="i" class="flex gap-3 items-center mb-2">
            <input v-model="g.name" class="input" list="grapeList" placeholder="Ex: Touriga Nacional" style="flex:2">
            <input v-model="g.percentage" type="number" min="0" max="100" class="input" placeholder="%" style="width:90px">
            <span class="text-muted">%</span>
            <button type="button" class="btn btn-danger btn-sm btn-icon" @click="removeGrape(i)">✕</button>
          </div>
          <datalist id="grapeList">
            <option v-for="g in allGrapes" :key="g.id" :value="g.name"></option>
          </datalist>
        </div>

        <!-- STOCK & PRICE -->
        <div class="card mb-5">
          <div class="section-title">Stock e Preço</div>
          <div class="field-row three">
            <div class="field">
              <label class="field-label">{{ isEdit ? 'Stock mínimo' : 'Stock inicial' }}</label>
              <input v-if="!isEdit" v-model.number="form.initial_stock" type="number" min="0" class="input">
              <input v-else v-model.number="form.min_stock" type="number" min="0" class="input">
            </div>
            <div class="field">
              <label class="field-label">{{ isEdit ? 'Preço (€)' : 'Stock mínimo (alerta)' }}</label>
              <input v-if="!isEdit" v-model.number="form.min_stock" type="number" min="0" class="input">
              <input v-else v-model="form.purchase_price" type="number" step="0.01" min="0" class="input" placeholder="0.00">
            </div>
            <div class="field">
              <label class="field-label">Preço de Compra (€)</label>
              <input v-if="!isEdit" v-model="form.purchase_price" type="number" step="0.01" min="0" class="input" placeholder="0.00">
              <input v-else disabled class="input" :value="'—'" style="opacity:.4">
            </div>
          </div>
          <p v-if="!isEdit" class="text-xs text-muted">O stock inicial cria automaticamente um movimento de entrada.</p>
        </div>

        <!-- WINDOW -->
        <div class="card mb-5">
          <div class="section-title">Janela de Consumo</div>
          <p class="text-sm text-muted mb-4">💡 Em branco = calculado automaticamente pelo tipo e região.</p>
          <div class="field-row">
            <div class="field">
              <label class="field-label">Beber a partir de</label>
              <input v-model.number="form.consume_from_year" type="number" min="1990" max="2100" class="input" placeholder="Auto">
            </div>
            <div class="field">
              <label class="field-label">Beber até</label>
              <input v-model.number="form.consume_until_year" type="number" min="1990" max="2100" class="input" placeholder="Auto">
            </div>
          </div>
          <div class="field">
            <label class="field-label">Notas do Produtor / Descrição</label>
            <textarea v-model="form.description" class="textarea" placeholder="Notas de produção, vinificação…"></textarea>
          </div>
        </div>

        <div class="flex gap-3" style="justify-content:flex-end">
          <button type="button" class="btn btn-ghost btn-lg" @click="router.back()">Cancelar</button>
          <button type="submit" class="btn btn-gold btn-lg" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            <span v-else>{{ isEdit ? '✓ Guardar' : '🍷 Adicionar à Garrafeira' }}</span>
          </button>
        </div>
      </form>
    </div>
  `,
};
