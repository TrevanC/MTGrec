# MTG EDH/Commander Upgrade Recommender

An application that analyzes Magic: The Gathering EDH/Commander decks and provides upgrade recommendations based on synergy scoring, deck statistics, and community data.

## Architecture

- **Frontend:** Next.js (React) - Single page application with session-only deck storage
- **Backend:** FastAPI (Python) - Stateless REST API
- **Database:** PostgreSQL - Stores Scryfall card data and co-occurrence statistics
- **Data Source:** Scryfall bulk data for MTG card information

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repo-url>
   cd MTGrec
   ```

2. **Start all services with Docker:**
   ```bash
   docker-compose up
   ```

   or, put it in background
   ```bash
   docker-compose up -d
   ```
   
   This will start:
   - PostgreSQL database on port 5432
   - FastAPI backend on port 8000
   - Next.js frontend on port 3000

   - to bring it down
   ```bash
   docker-compose down
   ```

   - to rebuild 
   ```bash
   docker-compose build --no-cache

   # or 
   docker-compose build
   ```

3. **Import Scryfall data (required for recommendations):**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r scripts/requirements.txt
   
   # Import card data
   cd scripts
   python import_scryfall.py
   ```

4. **Verify InferenceRecommender initialization:**
   The backend automatically initializes a pre-trained ML model (`InferenceRecommender`) on startup. Check the logs to ensure successful initialization:
   ```bash
   docker-compose logs backend
   ```
   Look for "InferenceRecommender initialized successfully" message.

### Alternative: Local Development

If you prefer to run services locally instead of Docker:

1. **Start database:**
   ```bash
   docker-compose up db
   ```

2. **Backend (FastAPI):**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Frontend (Next.js):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python service
├── scripts/           # Data import and utility scripts
├── docs/              # Product and technical documentation
└── docker-compose.yml # Development environment
```

## Key Features

- **Deck Analysis:** Comprehensive deck statistics, mana curve, color distribution
- **Synergy Evaluation:** Multi-layer scoring system for card relationships
- **Smart Recommendations:** Upgrade suggestions based on commander, synergy, and budget
- **Inference Engine:** Pre-trained ML models for sophisticated card recommendations
- **Session-Based:** No account required, decks stored in browser session only
- **Export Support:** Integration with Moxfield and Archidekt
- **Debug Mode:** JSON request/response logging for development

## Access Points

Once running, visit:
- **Frontend Application:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/api/v1/docs
- **API Documentation (ReDoc):** http://localhost:8000/api/v1/redoc
- **Health Check:** http://localhost:8000/health

## Database Access

- **PostgreSQL:** localhost:5432
- **Database:** mtg_recommender
- **Username:** postgres
- **Password:** password

### Using pgAdmin 4

1. Install pgAdmin 4
2. Create new server connection:
   - Host: localhost
   - Port: 5432
   - Database: mtg_recommender
   - Username: postgres
   - Password: password

### Using psql

```bash
# Connect via Docker
docker-compose exec db psql -U postgres -d mtg_recommender

# Or connect locally (if psql is installed)
psql -h localhost -p 5432 -U postgres -d mtg_recommender
```

## Debug Mode

The application runs in debug mode by default (controlled by `DEBUG=true` in docker-compose.yml). In debug mode:

- **Request/Response Logging**: All API requests and responses are automatically saved to JSON files in `backend/requests/` and `backend/responses/` directories
- **Verbose Logging**: Detailed initialization and operation logs are displayed
- **Development Features**: Enhanced error reporting and debugging information

To disable debug mode for production, change `DEBUG: "true"` to `DEBUG: "false"` in docker-compose.yml.

## Troubleshooting

### Common Issues

1. **Empty API docs at /docs**: Use `/api/v1/docs` instead
2. **Database connection errors**: Ensure PostgreSQL container is running with `docker-compose ps`
3. **Import script errors**: Make sure you're in a virtual environment with required packages
4. **Frontend build errors**: Check Node.js version compatibility (React 19 requires Node 18+)
5. **InferenceRecommender initialization fails**: Check that `data/processed/compact_dataset.json` and `data/processed/similarity_model.pkl` exist
6. **No recommendations returned**: Verify the InferenceRecommender initialized successfully and check debug logs

### Checking Service Status

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Restart services
docker-compose restart
```

## Contributing

See the documentation in `docs/` for detailed product and technical specifications.