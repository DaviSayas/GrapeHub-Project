// GrapeHub — Collections view (manage and share wine collections).
const { ref, onMounted, inject } = Vue;
import { collectionService } from '../services/collections.js';
import { formatPrice } from '../services/wines.js';

export default {
  name: 'CollectionsView',
  setup() {
    const toast = inject('toast', () => {});
    const collections = ref([]);
    const loading = ref(true);
    const showModal = ref(false);
    const saving = ref(false);
    const form = ref({ name: '', description: '', is_public: false });
    const shareModal = ref(null);
    const copyingLink = ref(false);

    async function load() {
      loading.value = true;
      try {
        collections.value = await collectionService.list();
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        loading.value = false;
      }
    }

    async function save() {
      if (!form.value.name.trim()) {
        toast('Nome da collection é obrigatório', 'error');
        return;
      }
      saving.value = true;
      try {
        await collectionService.create(form.value);
        toast('Collection criada! 🎉', 'success');
        showModal.value = false;
        form.value = { name: '', description: '', is_public: false };
        await load();
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        saving.value = false;
      }
    }

    async function deleteCollection(id) {
      if (!confirm('Remover esta collection?')) return;
      try {
        await collectionService.remove(id);
        collections.value = collections.value.filter(c => c.id !== id);
        toast('Collection removida', 'success');
      } catch (e) {
        toast(e.message, 'error');
      }
    }

    async function shareCollection(id) {
      try {
        const result = await collectionService.share(id);
        shareModal.value = {
          id,
          name: collections.value.find(c => c.id === id)?.name,
          link: window.location.origin + '/collections/public/' + result.share_token,
          token: result.share_token,
        };
      } catch (e) {
        toast(e.message, 'error');
      }
    }

    async function copyShareLink() {
      if (!shareModal.value) return;
      copyingLink.value = true;
      try {
        await navigator.clipboard.writeText(shareModal.value.link);
        toast('Link copiado! 📋', 'success');
      } catch (e) {
        toast('Erro ao copiar link', 'error');
      } finally {
        copyingLink.value = false;
      }
    }

    onMounted(load);

    return {
      collections,
      loading,
      showModal,
      saving,
      form,
      shareModal,
      copyingLink,
      save,
      load,
      deleteCollection,
      shareCollection,
      copyShareLink,
      formatPrice,
    };
  },

  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">📚 Minhas Collections<small>Organize e partilhe a sua garrafeira</small></h1>
        <button class="btn btn-gold" @click="showModal=true">＋ Nova Collection</button>
      </div>

      <div v-if="loading" class="page-loading"><div class="page-loading-icon">📚</div><span>A carregar…</span></div>

      <div v-else-if="!collections.length" class="empty-state">
        <div class="empty-icon">📚</div>
        <div class="empty-title">Sem collections criadas</div>
        <div class="empty-desc">Crie a sua primeira collection para organizar os seus vinhos.</div>
        <button class="btn btn-gold mt-4" @click="showModal=true">📚 Criar Primeira Collection</button>
      </div>

      <div v-else class="grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;margin-bottom:2rem">
        <div v-for="col in collections" :key="col.id" class="card" style="display:flex;flex-direction:column">
          <div class="section-title" style="margin-bottom:0.5rem">{{ col.name }}</div>
          <div class="text-sm text-muted mb-3">{{ col.description || 'Sem descrição' }}</div>

          <div style="flex:1;background:rgba(201,168,76,.04);padding:0.75rem;border-radius:6px;margin-bottom:1rem">
            <div class="text-xs text-muted">Vinhos na collection</div>
            <div style="font-size:1.5rem;font-weight:600;color:var(--gold)">0</div>
          </div>

          <div class="flex gap-2">
            <button v-if="col.is_public" class="btn btn-ghost btn-sm flex-1" @click="shareCollection(col.id)">
              🔗 Partilhado
            </button>
            <button v-else class="btn btn-ghost btn-sm flex-1" @click="shareCollection(col.id)">
              👁️ Tornar Pública
            </button>
            <button class="btn btn-danger btn-sm btn-icon" @click="deleteCollection(col.id)">✕</button>
          </div>
        </div>
      </div>

      <!-- CREATE MODAL -->
      <div v-if="showModal" class="modal-overlay" @click.self="showModal=false">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">📚 Nova Collection</div>
            <button class="modal-close" @click="showModal=false">✕</button>
          </div>
          <form @submit.prevent="save">
            <div class="field">
              <label class="field-label">Nome *</label>
              <input v-model="form.name" class="input" required placeholder="Ex: Douro Premium">
            </div>
            <div class="field">
              <label class="field-label">Descrição</label>
              <textarea v-model="form.description" class="textarea" placeholder="Descreva a sua collection…"></textarea>
            </div>
            <div class="field">
              <label class="checkbox">
                <input v-model="form.is_public" type="checkbox">
                Tornar pública (outras pessoas podem visualizar)
              </label>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-ghost" @click="showModal=false">Cancelar</button>
              <button type="submit" class="btn btn-gold" :disabled="saving">
                <span v-if="saving" class="spinner"></span><span v-else>📚 Criar</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- SHARE MODAL -->
      <div v-if="shareModal" class="modal-overlay" @click.self="shareModal=null">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">🔗 Partilhar "{{ shareModal.name }}"</div>
            <button class="modal-close" @click="shareModal=null">✕</button>
          </div>
          <div class="modal-body">
            <div class="card" style="background:rgba(201,168,76,.08);padding:1rem;margin-bottom:1rem">
              <div class="text-xs text-gold font-semibold mb-2">Link de Partilha</div>
              <div style="display:flex;gap:0.5rem">
                <input type="text" :value="shareModal.link" readonly class="input" style="flex:1">
                <button class="btn btn-gold" @click="copyShareLink" :disabled="copyingLink">
                  {{ copyingLink ? '📋…' : '📋' }}
                </button>
              </div>
              <div class="text-xs text-muted mt-2">Partilhe este link para que outros vejam a sua collection</div>
            </div>

            <div style="display:flex;gap:0.5rem;flex-wrap:wrap;justify-content:center">
              <button class="btn btn-ghost btn-sm" @click="shareModal=null">Fechar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
};
