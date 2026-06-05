// Tastings (structured diário de prova) service.
import { api } from './http.js';

export const tastingService = {
  list(params)      { return api.get('/tastings', params); },
  forWine(wineId)   { return api.get(`/tastings/wine/${wineId}`); },
  create(data)      { return api.post('/tastings', data); },
  update(id, data)  { return api.put(`/tastings/${id}`, data); },
  remove(id)        { return api.del(`/tastings/${id}`); },
  stats()           { return api.get('/tastings/stats/summary'); },
};

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit', month: 'short', year: 'numeric',
  }).format(new Date(dateStr));
}
