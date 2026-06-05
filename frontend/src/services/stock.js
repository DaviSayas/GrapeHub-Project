// Stock movements + cellar locations service.
import { api } from './http.js';

export const stockService = {
  addMovement(data)     { return api.post('/stock/movements', data); },
  movements(wineId)     { return api.get(`/stock/movements/${wineId}`); },
  balance(wineId)       { return api.get(`/stock/balance/${wineId}`); },
  locations()           { return api.get('/stock/locations'); },
  createLocation(data)  { return api.post('/stock/locations', data); },
  deleteLocation(id)    { return api.del(`/stock/locations/${id}`); },
};

export const MOVEMENT_TYPE_LABELS = {
  in: 'Entrada', out: 'Saída', adjust: 'Ajuste',
};
export const MOVEMENT_TYPE_BADGE = {
  in: 'badge-success', out: 'badge-danger', adjust: 'badge-info',
};
export const MOVEMENT_TYPE_ICON = {
  in: '⬆', out: '⬇', adjust: '⚖',
};
