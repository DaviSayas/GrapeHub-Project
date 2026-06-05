// Wine API service — CRUD, photo upload, stats, suggestions.
import { api, API_BASE_URL } from './http.js';
import { auth } from './auth.js';

export const wineService = {
  list(params)       { return api.get('/wines', params); },
  get(id)            { return api.get(`/wines/${id}`); },
  create(data)       { return api.post('/wines', data); },
  update(id, data)   { return api.put(`/wines/${id}`, data); },
  remove(id)         { return api.del(`/wines/${id}`); },
  stats()            { return api.get('/wines/stats/summary'); },
  charts()           { return api.get('/wines/stats/charts'); },
  alerts()           { return api.get('/wines/alerts'); },
  window(id)         { return api.get(`/wines/${id}/window`); },
  pairing(id)        { return api.get(`/wines/${id}/pairing`); },
  history(id)        { return api.get(`/wines/${id}/history`); },

  // Multipart photo uploads (bottle / label)
  async uploadPhoto(id, file, kind = 'photo') {
    const fd = new FormData();
    fd.append('file', file);
    const endpoint = kind === 'label' ? 'label' : 'photo';
    const res = await fetch(`${API_BASE_URL}/wines/${id}/${endpoint}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.getToken()}` },
      body: fd,
    });
    if (!res.ok) {
      let msg = 'Erro no upload';
      try { msg = (await res.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  // CSV import/export
  async importCsv(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE_URL}/wines/import/csv`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.getToken()}` },
      body: fd,
    });
    if (!res.ok) {
      let msg = 'Erro na importação';
      try { msg = (await res.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  },

  async exportCsv() {
    const res = await fetch(`${API_BASE_URL}/wines/export/csv`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${auth.getToken()}` },
    });
    if (!res.ok) throw new Error('Erro na exportação');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'garrafeira_backup.csv';
    a.click();
    URL.revokeObjectURL(url);
  },

  async ocrLabel(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE_URL}/wines/ocr/label`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.getToken()}` },
      body: fd,
    });
    if (!res.ok) {
      let msg = 'Erro no OCR';
      try { msg = (await res.json()).message || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  },
};

export const producerService = {
  list(q) { return api.get('/producers', q ? { q } : undefined); },
  create(data) { return api.post('/producers', data); },
};

export const grapeService = {
  list(q) { return api.get('/grapes', q ? { q } : undefined); },
};

// ── Constants & helpers ──────────────────────────────────────────────────────

export const WINE_TYPE_LABELS = {
  red: 'Tinto', white: 'Branco', 'rosé': 'Rosé',
  sparkling: 'Espumante', fortified: 'Licoroso',
};
export const WINE_TYPE_ICONS = {
  red: '🍷', white: '🥂', 'rosé': '🌸', sparkling: '✨', fortified: '🪙',
};
export const WINE_TYPE_BADGE = {
  red: 'badge-red', white: 'badge-white', 'rosé': 'badge-rosé',
  sparkling: 'badge-sparkling', fortified: 'badge-fortified',
};
export const DW_STATUS_LABELS = {
  too_young: 'Muito jovem', almost_ready: 'Quase pronto', ready: 'Pronto para beber',
  peak: 'No pico! ✦', declining: 'A declinar', past_peak: 'Passou o pico',
};
export const DW_STATUS_CLASS = {
  too_young: 'dw-too_young', almost_ready: 'dw-almost_ready', ready: 'dw-ready',
  peak: 'dw-peak', declining: 'dw-declining', past_peak: 'dw-past_peak',
};
export const REGIONS = [
  'Douro','Alentejo','Dão','Bairrada','Vinho Verde','Lisboa','Setúbal','Algarve',
  'Bordeaux','Burgundy','Champagne','Rhône','Loire','Alsace',
  'Tuscany','Piedmont','Veneto','Sicily','Rioja','Ribera del Duero','Priorat',
  'Napa Valley','Mendoza','Barossa Valley','Other',
];

// Rating is on a 0-100 scale; map to 5 stars.
export function starsFromScore(score) {
  if (!score) return '☆☆☆☆☆';
  const full = Math.round(score / 20);
  return '★'.repeat(full) + '☆'.repeat(5 - full);
}

export function formatPrice(price) {
  if (price === null || price === undefined) return '—';
  return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(price);
}

export function photoUrl(path) {
  if (!path) return null;
  return `${API_BASE_URL}${path}`;
}
