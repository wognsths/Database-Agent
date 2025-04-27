# Database-Agent
Database Agent using A2A architecture

## Project Structure
```
.
├── app/                    # Backend code
│   ├── api/                # API endpoints
│   ├── agents/             # Agent implementations
│   ├── core/               # Core functionality
│   └── main.py             # Backend entry point
├── frontend/               # Frontend code
│   └── ui/                 # Mesop UI implementation
├── docker-compose.yml      # Docker Compose configuration
├── app/Dockerfile          # Backend Docker configuration
└── frontend/Dockerfile     # Frontend Docker configuration
```

## Running with Docker

### Prerequisites
- Docker and Docker Compose must be installed.
- Google API key is required (for Gemini API).

### Environment Variables Setup
1. Create a `.env` file by referencing the `.env.example` file.
2. Set the required environment variables (especially `GOOGLE_API_KEY`).

### Build and Run
```bash
# Build services
docker-compose build

# Run services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Access Information
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:12000

### Stop Services
```bash
docker-compose down
```

## Database Information
- PostgreSQL database is configured by default.
- Data is stored in the Docker volume (`postgres_data`).
- The backend agent connects to the configured database to execute queries.

## Technologies Used
- Backend: FastAPI, SQLAlchemy, LangGraph
- Frontend: Mesop (Python UI framework)
- AI: Google Gemini API
- Database: PostgreSQL
- Containerization: Docker, Docker Compose


## .env
```
# Database settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=my_password
POSTGRES_DB=postgres
DB_USER=postgres
DB_PASSWORD=my_password
DB_HOST=postgres
DB_PORT=5432
DB_NAME=postgres

# Backend settings
BASE_URL=http://db-agent-backend:8000

# Frontend settings
A2A_UI_HOST=0.0.0.0
A2A_UI_PORT=12000
DEBUG_MODE=true

# Google API settings
GOOGLE_API_KEY=api_key

DATABASE_AGENT_URL=http://db-agent-database-agent:10001
HOST_AGENT_URL=http://db-agent-host-agent:10000

```
