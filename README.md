# 🍷 GrapeHub — Gestão de Garrafeira Pessoal

Aplicação web **full-stack premium** para gerir a sua coleção pessoal de vinhos. Catálogo digital com upload de fotos, gestão de stock por localização na cave, diário de degustação estruturado, sugestões inteligentes de janela de consumo, dashboard com gráficos e exportação PDF.

> Implementa o plano de estágio "Gestão de Garrafeira Pessoal" (FastAPI + SQLite + Vue 3). Tema escuro premium em **Bordeaux & Ouro**, totalmente em português.

---

## ✨ Funcionalidades

### Catálogo & Stock
- 📋 **Catálogo digital** — nome, produtor, região, castas (com %), ano, tipo, volume, álcool, preço
- 📸 **Upload de fotos** — garrafa **e** etiqueta, com pré-visualização (armazenamento local)
- 📦 **Gestão de stock por movimentos** — entrada / saída / ajuste, com motivo, preço, data e notas
- 🗺️ **Localizações na cave** — prateleiras/zonas; stock calculado a partir do histórico de movimentos
- ⚠️ **Alerta de stock mínimo** configurável por garrafa
- ♡ **Lista de desejos** — vinhos a adquirir, com preço-alvo e prioridade

### Inteligência
- 💡 **Janela de consumo inteligente** — calculada automaticamente por tipo + região (Douro, Bordeaux, Champagne, Porto…)
- 🔔 **Alertas** — pico de maturidade, a declinar, beber urgente, stock baixo
- 🍽️ **Harmonizações** — pratos, temperatura de serviço e tipo de copo por vinho

### Degustação & Insights
- 📓 **Diário de prova estruturado** (WSET) — aspecto, aroma, boca, final, classificação **1–100**, "compraria de novo"
- 📊 **Dashboard com 4 gráficos** — distribuição por tipo, top regiões, consumo mensal, evolução do valor
- 📈 **Métricas** — valor total, garrafas prontas a beber, a beber em breve, classificação média
- 📄 **Exportação PDF** (ReportLab) — capa, catálogo completo, top degustadas, consumir em breve
- ⬇️ **Exportação CSV**

### Plataforma
- 🔐 Autenticação JWT (registo/login, bcrypt)
- 🔍 Pesquisa e filtros (nome, produtor, região, tipo, em stock, ordenação)
- 📱 PWA instalável
- 🎨 UI responsiva (desktop / tablet / mobile)

---

## 🗄️ Modelo de Dados (relacional)

```
users          producers      grapes
  │                │             │
  └── wines ───────┘             │
       ├── wine_grapes ──────────┘   (composição com %)
       ├── stock_movements  (in/out/adjust → stock calculado)
       ├── tastings         (aspecto, aroma, boca, final, score 1-100)
       └── (created_by → users)
  cellar_locations (user)        wishlist (user)
```

| Tabela | Campos-chave |
|--------|-------------|
| **producers** | name, country, region, website |
| **grapes** | name |
| **wines** | name, producer_id, region, vintage_year, type, photo_path, label_photo_path, consume_from/until_year, min_stock |
| **wine_grapes** | wine_id, grape_id, percentage |
| **cellar_locations** | user_id, name, description |
| **stock_movements** | wine_id, location_id, type(in/out/adjust), quantity, reason, price, date |
| **tastings** | wine_id, date, occasion, appearance, nose, palate, finish, overall_score(1-100), would_buy_again |
| **wishlist** | wine_id/description, target_price, priority |

---

## 🛠️ Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 · SQLite · python-jose (JWT) · bcrypt |
| Uploads / PDF | python-multipart · Pillow · ReportLab |
| Frontend | Vue 3 (Composition API, UMD — **sem build**) · Vue Router · Chart.js |
| Design | CSS custom properties (tema escuro) · Playfair Display + Inter |

---

## 🚀 Como Iniciar (Windows)

**Duplo-clique em `START_GRAPEHUB.bat`** — na primeira execução cria o ambiente virtual, instala dependências e inicializa a base de dados com dados demo. Depois abre:

➡️ **http://localhost:8000** · API docs: **http://localhost:8000/docs**

### Manual (PowerShell)
```powershell
cd C:\Users\Liionforce\Desktop\GrapeHub\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.seed     # cria DB + dados demo
python start.py           # arranca em http://localhost:8000
```

### Contas
| Email | Password | Role |
|-------|----------|------|
| `adm@liionforce.com` | `adm123` | Admin |
| `davi@liionforce.com` | `davi123` | User |
| `eliude@liionforce.com` | `eliude123` | User |
| `utilizador@liionforce.com` | `utilizador@liionforce` | User |

---

## 📚 Principais Endpoints

```
POST /auth/register · /auth/login · GET /auth/me

GET/POST/PUT/DELETE  /wines            CRUD de garrafas
POST /wines/{id}/photo · /label        upload de fotos (multipart)
GET  /wines/stats/summary · /charts    métricas + dados dos gráficos
GET  /wines/alerts                     alertas de consumo + stock
GET  /wines/{id}/window · /pairing     janela de consumo + harmonização

GET  /producers?q= · POST /producers   autocomplete de produtores
GET  /grapes?q=                        castas

POST /stock/movements                  entrada/saída/ajuste
GET  /stock/movements/{wine_id}        histórico · /balance/{id} saldo
GET/POST/DELETE /stock/locations       localizações na cave

GET/POST/PUT/DELETE /tastings          diário de prova
GET/POST/PUT/DELETE /wishlist          lista de desejos

GET  /reports/collection.pdf           PDF da coleção (ReportLab)
GET  /reports/collection.csv           CSV
```

Documentação interativa (Swagger): **http://localhost:8000/docs**

---

## 🧪 Testes

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests -v
```

**25 testes** cobrindo: autenticação, CRUD de vinhos, modelo relacional (produtores/castas), **movimentos de stock** (entrada/saída/ajuste + saldo), **upload de fotos** (válido/inválido), degustações estruturadas, **geração de PDF** (200 + content-type), CSV, estatísticas, gráficos e lógica de sugestões.

---

## 📂 Estrutura

```
GrapeHub/
├── START_GRAPEHUB.bat
├── backend/
│   ├── start.py · requirements.txt · wine_cellar.db
│   └── app/
│       ├── main.py
│       ├── api/      auth · users · producers · grapes · wines · stock · tastings · wishlist · reports
│       ├── models/   user · producer · grape(+wine_grape) · wine · location · stock · tasting · wishlist
│       ├── schemas/  (pydantic por domínio)
│       ├── services/ suggestions · pairing · photos · pdf_report · serializers
│       └── db/       session · seed
│   └── tests/        conftest · test_wines (25 testes)
├── frontend/
│   ├── index.html · manifest.json · service-worker.js
│   └── src/
│       ├── components/AppShell.js
│       ├── views/     Login · Register · Dashboard · Cellar · WineDetail · WineForm · Tastings · Wishlist
│       ├── services/  http · auth · wines · stock · tastings · wishlist
│       └── assets/    styles.css · Vue/Router/Chart (UMD)
└── uploads/wines/     (fotos guardadas localmente)
```

---

## 🧠 Janela de Consumo

Calculada por **tipo + região** (regras enológicas). Ex.: Tinto Bordeaux `+8 a +35 anos` (pico +12 a +25); Branco Vinho Verde `0 a +3`; Champagne `+1 a +15`; Porto `+5 a +50`. Estados: Muito jovem → Quase pronto → Pronto → **No pico ✦** → A declinar → Passou o pico.

---

**Desenvolvido com ❤️ e 🍷 — GrapeHub v1.0**
