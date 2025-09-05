# IRON AI - Workout Planner

**AI-powered workout planner** - a modern web application for creating and tracking workout programs using artificial intelligence.

## 🎯 Main Goal

Create personalized workout programs using AI, tailored to individual user needs (experience, equipment, priorities), and provide convenient progress tracking.

## 🏗️ How It Works

1. **User registers** and logs into the system
2. **Selects parameters** for AI generation (experience, days per week, equipment, priorities)
3. **AI creates a program** based on scientific bodybuilding principles
4. **Program is saved** in the user's personal account
5. **User trains** according to the program and tracks progress

## ⚡ Key Features

### 🤖 AI Program Generation
- **What it does**: Creates personalized workout programs based on user parameters
- **Purpose**: Saves time on planning, ensures scientifically-based approach

### 📊 Program Management
- **What it does**: Saves, activates, and removes workout programs
- **Purpose**: Allows multiple programs and switching between them

### 🏋️ Workout Tracking
- **What it does**: Records completed sets, weights, reps, and RPE
- **Purpose**: Monitors progress and adjusts workload

### 📈 Load Progression
- **What it does**: Automatically increases weights and reps over weeks
- **Purpose**: Ensures constant progress and avoids plateaus

### 👤 Personal Dashboard
- **What it does**: Stores all user programs and workouts
- **Purpose**: Centralized place for managing training process

## 🛠️ Technical Features

- **Backend**: FastAPI (Python) - fast and modern web framework
- **Frontend**: HTML/CSS/JavaScript - clean and responsive interface
- **Database**: SQLite - lightweight and reliable file-based DB
- **AI**: OpenAI GPT - program generation based on scientific principles
- **Architecture**: Clean architecture with layer separation

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Open in browser**: http://localhost:8000

## 📁 Project Structure

```
ai-workout-planner/
├── app/                    # Backend application
│   ├── main.py            # API endpoints
│   ├── services.py        # Business logic
│   ├── repo.py            # Database operations
│   └── ai_client.py       # AI integration
├── frontend/              # Frontend files
│   ├── index.html         # Main page
│   ├── ai-plan.html       # AI plan generation
│   ├── my-plans.html      # My programs
│   └── workout-session.html # Workout session
└── database/              # Database
    └── workout.db         # SQLite database
```

## 🎨 Design

- **Minimalist** - focus on functionality
- **Modern** - clean lines and pleasant colors
- **Responsive** - works on all devices
- **Intuitive** - ease of use

## 📝 License

MIT License - free use and modification.

---

**IRON AI** - Train like a pro with AI-powered planning.