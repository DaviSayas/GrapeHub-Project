// Collections service — sharing wine collections.
import { api } from './http.js';

export const collectionService = {
  list()                    { return api.get('/collections'); },
  create(data)              { return api.post('/collections', data); },
  update(id, data)          { return api.put(`/collections/${id}`, data); },
  remove(id)                { return api.del(`/collections/${id}`); },
  addWine(id, wineId)       { return api.post(`/collections/${id}/wines/${wineId}`, {}); },
  removeWine(id, wineId)    { return api.del(`/collections/${id}/wines/${wineId}`); },
  share(id)                 { return api.post(`/collections/${id}/share`, {}); },
  getPublic(token)          { return api.get(`/collections/public/${token}`); },
  compare(id, otherId)      { return api.get(`/collections/${id}/compare/${otherId}`); },
};
