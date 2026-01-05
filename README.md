# LLM Council

Quick guide for the project.

---

## English

### What is this?

- A three-stage "LLM council" that queries multiple providers in parallel, ranks their answers, and synthesizes a final reply (chairman model).
- FastAPI backend with MongoDB persistence, rate limiting, Prometheus metrics, and SSE streaming mode.
- React + Vite frontend with themed UI, routing (home/settings/analytics), and toast notifications.
- CI: GitHub Actions builds multi-arch Docker images and pushes to GHCR (frontend and backend).

### Architecture

- Backend: FastAPI entry in `backend/main.py`; orchestration in `backend/council.py`; MongoDB access in `backend/storage_mongo.py`; configuration in `backend/config.py` and runtime settings in `backend/settings.py`.
- Frontend: React app under `frontend/src` with pages `App.jsx`, `Settings.jsx`, `Analytics.jsx`; theme system in `frontend/src/theme` and `frontend/src/themes`.
- Deployment: `docker-compose.yml` for local; `Dockerfile.backend` and `Dockerfile.frontend` for images; `nginx.conf` for reverse proxy.

### Prerequisites

- Docker + Docker Compose (for the quickest start).
- Or locally: Python 3.11+ with uv/poetry/pip, Node 20+ for the frontend, and MongoDB reachable.
- API keys (optional but recommended) via environment variables: `GROQ_API_KEY`, `SAMBANOVA_API_KEY`, `GOOGLE_AI_API_KEY`, `MISTRAL_API_KEY`, `COHERE_API_KEY`, `HUGGINGFACE_API_KEY`, `OPENROUTER_API_KEY`.

### Quick start (Docker)

1. Copy `.env.example` if you have one (or create `.env`) and set the API keys and Mongo URL:

```
MONGODB_URL=mongodb://mongo:27017
MONGODB_DATABASE=llm_council
GROQ_API_KEY=...
SAMBANOVA_API_KEY=...
GOOGLE_AI_API_KEY=...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
HUGGINGFACE_API_KEY=...
OPENROUTER_API_KEY=...
```

2. Run:

```
docker-compose up --build
```

3. Frontend at http://localhost:5173 (or via nginx at http://localhost:8080 if using the provided config). Backend API at http://localhost:8000.

### Local development (split)

- Backend:
  - Create venv, install: `uv pip install -r requirements.txt` (or `pip install -e .` if using `pyproject.toml`).
  - Run: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`.
- Frontend:
  - `cd frontend && npm install`
  - `npm run dev` (defaults to port 5173).

### Notable endpoints

- `GET /health` basic health.
- `GET /api/conversations` list conversations.
- `POST /api/conversations` create conversation.
- `POST /api/conversations/{id}/message` run the 3-stage council.
- `POST /api/conversations/{id}/message/stream` SSE stream through the stages.
- `GET /api/analytics` aggregated request metrics; `GET /api/analytics/errors` recent errors.

### Storage & analytics

- Conversations, messages, and analytics are stored in MongoDB (see `backend/storage_mongo.py`).
- Rate limits via `slowapi`; metrics exposed with `prometheus_fastapi_instrumentator`.

### Deployment notes

- GHCR images: `ghcr.io/<owner>/llm-council-backend` and `ghcr.io/<owner>/llm-council-frontend` built via `.github/workflows/docker-build.yml`.
- The workflow now marks images public after push; ensure `packages: write` permission remains enabled.

### Customization

- Enable/disable council members and chairman in `backend/settings.py` (dynamic getters used at runtime).
- Theme tweaks under `frontend/src/themes/*.css` and `frontend/src/theme/themes.js`.

---

## Türkçe

### Bu proje ne yapar?

- Birden fazla LLM sağlayıcısını paralel sorgulayan, yanıtları oylayan ve başkan model ile nihai yanıtı sentezleyen üç aşamalı "LLM konseyi".
- FastAPI backend: MongoDB kalıcılık, hız limiti, Prometheus metrikleri, SSE ile aşama aşama yayın.
- React + Vite frontend: tema desteği, sayfalar (ana, ayarlar, analiz) ve bildirimler.
- CI: GitHub Actions çoklu mimari Docker imajlarını derleyip GHCR’a gönderir (frontend ve backend).

### Mimari

- Backend: Giriş `backend/main.py`; orkestrasyon `backend/council.py`; Mongo erişimi `backend/storage_mongo.py`; yapılandırma `backend/config.py`, çalışma zamanı ayarları `backend/settings.py`.
- Frontend: React kodu `frontend/src` altında; sayfalar `App.jsx`, `Settings.jsx`, `Analytics.jsx`; tema sistemi `frontend/src/theme` ve `frontend/src/themes`.
- Dağıtım: Yerel için `docker-compose.yml`; imajlar için `Dockerfile.backend` ve `Dockerfile.frontend`; ters proxy için `nginx.conf`.

### Önkoşullar

- En hızlı başlatma için Docker + Docker Compose.
- Yerelde çalışacaksanız: Python 3.11+, Node 20+, erişilebilir bir MongoDB.
- Opsiyonel ama önerilen API anahtarları: `GROQ_API_KEY`, `SAMBANOVA_API_KEY`, `GOOGLE_AI_API_KEY`, `MISTRAL_API_KEY`, `COHERE_API_KEY`, `HUGGINGFACE_API_KEY`, `OPENROUTER_API_KEY`.

### Hızlı başlat (Docker)

1. `.env` dosyasında Mongo ve anahtarları tanımlayın:

```
MONGODB_URL=mongodb://mongo:27017
MONGODB_DATABASE=llm_council
GROQ_API_KEY=...
SAMBANOVA_API_KEY=...
GOOGLE_AI_API_KEY=...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
HUGGINGFACE_API_KEY=...
OPENROUTER_API_KEY=...
```

2. Çalıştırın:

```
docker-compose up --build
```

3. Frontend: http://localhost:5173 (veya nginx ile http://localhost:8080); Backend API: http://localhost:8000.

### Yerel geliştirme (ayrık)

- Backend:
  - Sanal ortam kurun; bağımlılıkları yükleyin: `uv pip install -r requirements.txt` (ya da `pip install -e .`).
  - Çalıştırın: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`.
- Frontend:
  - `cd frontend && npm install`
  - `npm run dev` (varsayılan 5173).

### Önemli uç noktalar

- `GET /health` sağlık kontrolü.
- `GET /api/conversations` sohbet listesi.
- `POST /api/conversations` yeni sohbet.
- `POST /api/conversations/{id}/message` üç aşamalı konsey.
- `POST /api/conversations/{id}/message/stream` aşamalı SSE yayın.
- `GET /api/analytics` özet metrikler; `GET /api/analytics/errors` son hatalar.

### Depolama ve analiz

- Sohbetler ve analitik MongoDB’de tutulur (`backend/storage_mongo.py`).
- Hız limiti `slowapi` ile, metrikler `prometheus_fastapi_instrumentator` ile sunulur.

### Dağıtım notları

- GHCR imajları: `ghcr.io/<owner>/llm-council-backend` ve `ghcr.io/<owner>/llm-council-frontend`, `.github/workflows/docker-build.yml` ile üretilir.
- Workflow push sonrası imajları public yapar; `packages: write` izni açık kalmalıdır.

### Özelleştirme

- Aktif konsey üyeleri ve başkan `backend/settings.py` üzerinden yönetilir (çalışma anında okunur).
- Tema ve görünüm ayarları `frontend/src/themes/*.css` ve `frontend/src/theme/themes.js` içinde düzenlenebilir.
