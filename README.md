# WorldCup Forecast Engine 2026

Professional tournament forecasting platform for the FIFA World Cup 2026. Simulates match outcomes, group stages, and complete tournaments using Monte Carlo methods with 100,000+ iterations.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Next.js Frontend (React)             │
│         TypeScript · Tailwind · shadcn/ui         │
├─────────────────────────────────────────────────┤
│              FastAPI REST API Layer               │
│          Pydantic · OpenAPI · CORS · Cache        │
├─────────────────────────────────────────────────┤
│                  Service Layer                    │
│   IGF Engine │ Match Engine │ Monte Carlo Engine  │
├─────────────────────────────────────────────────┤
│            Data Collection Layer                  │
│  FIFA · Elo · FBref · Transfermarkt · FootballData│
├─────────────────────────────────────────────────┤
│         Repository Layer (SQLAlchemy)             │
│          PostgreSQL/Neon · Alembic · Redis        │
└─────────────────────────────────────────────────┘
```

### Modules

| Module | Description |
|--------|-------------|
| **IGF Engine** | Global Strength Index — composite rating from Elo, form, xG, xGA, opponent strength, WC experience, squad quality |
| **Match Engine** | Poisson, Dixon-Coles, Elo, and Bayesian match prediction models |
| **Monte Carlo** | 100k+ tournament simulations with Numba-accelerated group + knockout stages |
| **Collectors** | Adapter-pattern data collectors for 5 providers |
| **API** | REST + OpenAPI + pagination + filtering |

## Tech Stack

### Backend
- **Python 3.13**, FastAPI, SQLAlchemy, Alembic, Pydantic
- PostgreSQL (Neon-compatible), Redis
- Pandas, NumPy, SciPy, Polars, Numba
- Pytest, httpx, tenacity

### Frontend
- **Next.js 14**, TypeScript, Tailwind CSS, shadcn/ui
- Lucide icons, Radix UI primitives

### DevOps
- Docker, Docker Compose
- GitHub Actions CI/CD
- Vercel (frontend) / Railway or Render (backend) / Neon (database)

## Quick Start

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourorg/worldcup-forecast-2026.git
cd worldcup-forecast-2026

# 2. Backend setup
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit credentials

# 3. Database (Docker)
docker compose up -d db

# 4. Run migrations
alembic upgrade head

# 5. Start backend
uvicorn app.main:app --reload --port 8000

# 6. Frontend setup (new terminal)
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Docker Compose (full stack)

```bash
docker compose up --build
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/teams` | List all teams |
| GET | `/api/v1/teams/{id}` | Get team details |
| POST | `/api/v1/teams` | Create team |
| GET | `/api/v1/matches` | List matches (filter by `?stage=`) |
| GET | `/api/v1/matches/{id}` | Get match details |
| GET | `/api/v1/matches/{id}/prediction` | Get match prediction |
| GET | `/api/v1/groups` | List all groups |
| GET | `/api/v1/groups/{id}` | Group with standings |
| GET | `/api/v1/predictions` | All match predictions |
| GET | `/api/v1/predictions/rankings` | IGF rankings |
| GET | `/api/v1/rankings/elo` | Elo ratings |
| GET | `/api/v1/rankings/fifa` | FIFA rankings |
| GET | `/api/v1/rankings/igf` | IGF composite scores |
| GET | `/api/v1/simulations` | List simulations |
| POST | `/api/v1/simulations` | Create simulation |
| POST | `/api/v1/simulations/{id}/run` | Execute simulation |
| GET | `/api/v1/simulations/{id}` | Simulation results |

Interactive docs at `/docs` (Swagger) and `/redoc` (ReDoc).

## API Examples

```bash
# List teams
curl http://localhost:8000/api/v1/teams

# Get match prediction
curl http://localhost:8000/api/v1/matches/{id}/prediction

# Run simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{"competition_id": "...", "num_simulations": 100000}'

# Execute and get results
curl -X POST http://localhost:8000/api/v1/simulations/{id}/run
```

## Simulation Engine

The Monte Carlo engine supports:

- **100,000+ simulations** per run
- **Numba JIT** acceleration for group stage (x10-50 speedup)
- **Process-level parallelism** for multi-core execution
- **Poisson goal model** based on team IGF scores
- Full group → R16 → QF → SF → Final bracket progression
- Per-team probabilities for each elimination round

### IGF Score Factors

| Factor | Default Weight | Source |
|--------|---------------|--------|
| Elo Rating | 25% | eloratings.net |
| Recent Form | 15% | Last 10 matches |
| xG Performance | 15% | FBref |
| xG Against | 10% | FBref |
| Opponent Strength | 10% | Weighted opponents |
| WC Experience | 10% | Historical WC appearances |
| Squad Quality | 15% | Transfermarkt values |

## Project Structure

```
worldcup-forecast-2026/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers
│   │   ├── core/          # Config, dependencies, security
│   │   ├── domain/        # DDD entities
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic layer
│   │   ├── collectors/    # Data provider adapters
│   │   ├── engine/        # IGF, Match, Monte Carlo engines
│   │   ├── db/            # Session, Base, migrations
│   │   └── main.py        # FastAPI app entrypoint
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages (App Router)
│   │   ├── components/    # UI components (shadcn-style)
│   │   └── lib/           # API client & utilities
│   └── package.json
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## Testing

```bash
cd backend
pytest -v --tb=short
```

## Deployment

### Backend (Railway / Render)

```bash
# Set environment variables in dashboard:
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
```

### Frontend (Vercel)

```bash
cd frontend
npx vercel --prod
# Set NEXT_PUBLIC_API_URL to deployed backend URL
```

### Database (Neon)

1. Create a Neon PostgreSQL database
2. Run migrations: `alembic upgrade head`
3. Seed data: `python scripts/seed_data.py`

## License

MIT
