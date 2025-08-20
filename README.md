# IRON AI - Workout Planner

A modern, AI-powered workout planning application with a bold, aggressive design aesthetic.

## 🏗️ Architecture

The project follows a clean, layered architecture:

```
app/
├── main.py          # FastAPI app + routes
├── db.py            # SQLite connection & setup
├── repo.py          # SQL functions (no SQL in handlers)
├── services.py      # Business logic
└── schemas.py       # Pydantic response schemas
```

### Key Features

- **Bold Design**: Aggressive red/orange color scheme with minimalist aesthetics
- **FastAPI Backend**: Modern Python web framework with automatic API documentation
- **SQLite Database**: Lightweight, file-based database with comprehensive workout tracking
- **Responsive Frontend**: Clean, modern UI that works on all devices
- **Program Management**: Full workout program lifecycle (programs → cycles → weeks → days → exercises → sets)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-workout-planner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python init_and_run.py
   ```

4. **Open in browser**
   - Main app: http://localhost:8000
   - API docs: http://localhost:8000/docs

## 📁 Project Structure

```
ai-workout-planner/
├── app/                    # FastAPI application
│   ├── main.py            # Routes and app configuration
│   ├── db.py              # Database connection and setup
│   ├── repo.py            # Data access layer (SQL queries)
│   ├── services.py        # Business logic
│   └── schemas.py         # Pydantic models
├── frontend/              # Static frontend files
│   ├── index.html         # Landing page
│   ├── workouts.html      # Program selection
│   ├── program-foundational.html  # Program detail
│   ├── styles.css         # Global styles
│   ├── app.js             # Landing page logic
│   ├── workouts.js        # Program selection logic
│   └── program-foundational.js    # Program detail logic
├── database/              # Database files
│   ├── workout.db         # SQLite database
│   ├── init_db.py         # Database initialization
│   ├── seed_db.py         # Data seeding
│   └── export_program.py  # JSON export (legacy)
├── requirements.txt       # Python dependencies
├── run_app.py            # Simple app runner
├── init_and_run.py       # Full initialization + runner
└── README.md             # This file
```

## 🎨 Design Philosophy

- **Bold & Aggressive**: Red/orange color scheme (#ff3e3e, #ff6b35)
- **Minimalist**: Clean typography, no clutter
- **Modern**: Smooth animations and hover effects
- **Responsive**: Works seamlessly on all devices

## 🗄️ Database Schema

The application uses a comprehensive workout tracking schema:

- **Programs**: Top-level workout programs
- **Cycles**: Program iterations with start dates
- **Weeks**: Weekly blocks within cycles
- **Training Days**: Individual workout days
- **Exercises**: Exercise catalog with equipment and target muscles
- **Day Exercises**: Exercises assigned to specific days
- **Sets**: Individual sets with weights, reps, RPE, and notes

## 🔌 API Endpoints

- `GET /` - Serve landing page
- `GET /api/programs` - List all programs
- `GET /api/programs/{name}` - Get program details
- `GET /api/programs/{name}/export` - Export program for frontend

## 🛠️ Development

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database and run
python init_and_run.py
```

### Database Operations

```bash
# Initialize database schema
python -c "from app.db import init_database; init_database()"

# Seed with foundational program
python -c "from app.services import seed_foundational_program; seed_foundational_program()"
```

### API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## 🎯 Current Features

- ✅ Landing page with bold design
- ✅ Program selection interface
- ✅ Foundational Bodybuilding program
- ✅ 3-day full body workout structure
- ✅ Exercise tracking with sets and reps
- ✅ FastAPI backend with automatic docs
- ✅ SQLite database with comprehensive schema
- ✅ Responsive design for all devices

## 🚧 Future Enhancements

- [ ] User authentication and profiles
- [ ] Progress tracking and analytics
- [ ] AI-powered workout generation
- [ ] Mobile app
- [ ] Social features and sharing
- [ ] Integration with fitness trackers

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**IRON AI** - Train like the elite with AI-powered planning.
