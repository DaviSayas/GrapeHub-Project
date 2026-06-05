// Wishlist service.
import { api } from './http.js';

export const wishlistService = {
  list()           { return api.get('/wishlist'); },
  create(data)     { return api.post('/wishlist', data); },
  update(id, data) { return api.put(`/wishlist/${id}`, data); },
  remove(id)       { return api.del(`/wishlist/${id}`); },
  deals()          { return api.get('/wishlist/deals/summary'); },
  recommendations() { return api.get('/wishlist/recommendations/summary'); },
};

export const PRIORITY_LABELS = { low: 'Baixa', medium: 'Média', high: 'Alta' };
export const PRIORITY_BADGE = { low: 'badge-muted', medium: 'badge-info', high: 'badge-warning' };
