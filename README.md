# 🎯 MAESTRO - Multi-Agent Intelligence System

AI-powered pharmaceutical intelligence platform using specialized agents for market analysis, clinical trials, patents, and trade data.

---

## 🚀 Running the System

### Option 1: Without Docker (Simple)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Mac/Linux
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm start
```

**Access:** Open browser to `http://localhost:3000`

---

### Option 2: With Docker (Recommended)

```bash
docker-compose up -d
```

**Access:** Open browser to `http://localhost:3000`

**Stop services:**
```bash
docker-compose down
```

---

## 📋 Prerequisites

### Without Docker:
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional)
- Redis (optional)

### With Docker:
- Docker Desktop
- Docker Compose

---

## ⚙️ Setup

### Backend Setup

1. **Create virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure Tailwind (if needed):**
```bash
npx tailwindcss init -p
```

---

## 🔑 Environment Variables

Create `.env` file in `backend/` directory:

```env
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
DATABASE_URL=postgresql://maestro:password@localhost:5432/maestro_db
REDIS_URL=redis://localhost:6379/0
```

---

## 📦 Project Structure

```
Project/
├── backend/
│   ├── agents/          # AI agents
│   ├── api/             # REST API
│   ├── data_sources/    # External APIs
│   ├── processing/      # Data processing
│   ├── utils/           # Utilities
│   └── main.py          # Entry point
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx      # Main component
│   │   └── index.tsx
│   └── package.json
├── data/
├── logs/
└── docker-compose.yml
```

---

## 🧪 Testing

**Backend tests:**
```bash
cd backend
pytest tests/
```

**Frontend tests:**
```bash
cd frontend
npm test
```

---

## 📊 Features

- 🔍 **Market Intelligence Agent** - Market size, trends, forecasts
- 🧬 **Clinical Trials Agent** - Trial landscape analysis
- 📄 **Patent & IP Agent** - Freedom to operate analysis
- 🌍 **Trade Data Agent** - Supply chain insights
- 🤖 **Master Agent** - Orchestrates all agents

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- LangChain
- OpenAI/Anthropic
- PostgreSQL + pgvector
- Redis

**Frontend:**
- React + TypeScript
- Tailwind CSS
- Recharts
- Lucide Icons

---

## 📝 License

MIT License

---

## 👥 Contributors

- Arushi Vaidya

---

## 🆘 Troubleshooting

**Port already in use:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Docker issues:**
```bash
# Clean rebuild
docker-compose down -v
docker-compose up -d --build
```

**npm issues:**
```bash
# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

**Built with ❤️ for pharmaceutical intelligence**