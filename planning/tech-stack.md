# Tech Stack Recommendation for Superior Spotify

## Your Situation

You're primarily a **Python/ML coder**, so the frontend framework choice (React vs Vue) is less important than:
1. Getting something working quickly
2. Leveraging Python for as much as possible
3. Keeping the architecture clean for future scaling

## Recommended Stack: Python-Centric

### Backend-First Approach

**Core Decision**: Since you're comfortable with Python, build a **Python backend** that serves both:
1. API endpoints for data/ML
2. Serves the frontend (or mounts a frontend framework)

### Option 1: FastAPI + Simple Frontend (Recommended for You)

**Why**:
- You write 90% Python (backend + ML)
- Frontend can be minimal: HTML/CSS/JS or a simple template system
- FastAPI is async, fast, and has great documentation
- Easy to deploy on Railway, Render, or even a VPS

**Stack**:
```
Backend:     FastAPI (Python)
Database:    PostgreSQL (via SQLAlchemy ORM)
Cache:       Redis (for API responses)
Frontend:    HTMX + Jinja2 templates OR simple vanilla JS
Charts:      Plotly (Python → generates interactive charts)
Task Queue:  Celery + Redis (for background stats calculation)
```

**What Plotly gives you**:
```python
# You write pure Python, get interactive charts
import plotly.express as px

fig = px.line(df, x='date', y='danceability',
              title='Your Danceability Over Time')
fig.write_html('chart.html')  # or render inline
```

**Example FastAPI Structure**:
```python
# main.py
from fastapi import FastAPI
from routes import stats, recommendations, auth

app = FastAPI()
app.include_router(stats.router)
app.include_router(recommendations.router)
app.include_router(auth.router)

# Serve simple frontend
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/")
def homepage(request):
    return templates.TemplateResponse("index.html", {"request": request})
```

### Option 2: FastAPI + Vue/React (More Frontend Work)

**If you want a proper SPA (Single Page Application)**:

**Vue.js (Nuxt)** - Easier Learning Curve:
- More beginner-friendly than React
- Simpler syntax, less boilerplate
- Great documentation

**React (Next.js)** - More Ecosystem:
- Larger community, more components
- More concepts to learn initially

**But honestly**: For a statistics dashboard, you might not need a full SPA.

### Option 3: Streamlit (Fastest MVP, Limited Flexibility)

**What is Streamlit**:
- Pure Python web app framework
- Turn data scripts into web apps in minutes
- Built-in charts, sidebars, session state

**Example**:
```python
import streamlit as st
import plotly.express as px

st.title("Superior Spotify Stats")

# Your data
df = get_user_listening_data()

# Charts
st.line_chart(df.groupby('date')['danceability'].mean())

# Audio feature radar
fig = px.line_radar(df, categories=['danceability', 'energy', 'valence'])
st.plotly_chart(fig)
```

**Pros**:
- 100% Python, no JavaScript needed
- Interactive charts built-in
- Deployable to Streamlit Cloud instantly

**Cons**:
- Less flexible for custom UI/UX
- Harder to add advanced features (smart shuffle player)
- More of a "dashboard" than a full app

**Recommendation**: **Start with Streamlit for MVP**, then migrate to FastAPI when you need more control

---

## Database: PostgreSQL

**Why PostgreSQL**:
- Robust, reliable, handles JSONB (for flexible criteria)
- Great time-series capabilities for listening events
- Scales from local to production

**Setup for Local Development**:
```bash
# Option 1: Docker (easiest)
docker run --name spotify-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres

# Option 2: Homebrew (Mac)
brew install postgresql
brew services start postgresql
```

**ORM: SQLAlchemy + Alembic**
```python
# Models
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ListeningEvent(Base):
    __tablename__ = 'listening_events'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    track_id = Column(String)
    played_at = Column(DateTime)
    # ...
```

---

## ML Pipeline Structure

Since you're an ML coder, here's how to organize the ML components:

```
ml/
├── similarity.py       # Cosine similarity, track matching
├── clustering.py       # K-means, DBSCAN for mood detection
├── shuffle.py          # Smart shuffle scoring algorithm
├── patterns.py         # Listening pattern analysis
├── recommendations.py  # Hybrid recommendation engine
└── features.py         # Feature extraction from audio data
```

**Example: Audio Similarity Service**
```python
# ml/similarity.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class AudioSimilarity:
    def __init__(self, audio_features_db):
        self.db = audio_features_db
        self.feature_columns = [
            'danceability', 'energy', 'valence',
            'acousticness', 'instrumentalness', 'tempo'
        ]

    def get_track_vector(self, track_id):
        """Get normalized audio feature vector for a track"""
        features = self.db.get_features(track_id, self.feature_columns)
        return np.array(features).reshape(1, -1)

    def find_similar(self, track_id, candidate_pool, n=10):
        """Find n most similar tracks to target"""
        target_vec = self.get_track_vector(track_id)
        candidate_vectors = np.array([
            self.get_track_vector(t) for t in candidate_pool
        ])

        similarities = cosine_similarity(target_vec, candidate_vectors)[0]
        top_indices = np.argsort(similarities)[::-1][:n]

        return [(candidate_pool[i], similarities[i]) for i in top_indices]
```

---

## Development Workflow Recommendation

### Phase 1: Local MVP (Weeks 1-3)
1. Set up PostgreSQL locally
2. Build FastAPI backend with listening event endpoints
3. Use Streamlit for quick frontend visualization
4. Focus on core stats: top tracks, audio feature breakdown

### Phase 2: ML Features (Weeks 4-6)
1. Implement audio similarity clustering
2. Build smart shuffle algorithm
3. Add pattern-based playlist generation
4. Enhance visualizations

### Phase 3: Production Prep (Weeks 7-8)
1. Migrate from Streamlit to custom frontend if needed
2. Add authentication, user isolation
3. Set up Redis caching
4. Deploy to Railway/Render

---

## Quick Start Commands

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis celery
pip install pandas numpy scikit-learn plotly
pip install spotipy python-dotenv

# 3. Start database (Docker)
docker run --name spotify-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres

# 4. Run backend
uvicorn main:app --reload

# 5. Run Streamlit frontend (if using)
streamlit run app.py
```

---

## Final Recommendation

**For someone who's primarily an ML/Python coder**:

1. **Start with Streamlit** for instant gratification and rapid prototyping
2. **Build the ML logic in pure Python** (can be reused later)
3. **When you need more UI control**, migrate to FastAPI + simple templates
4. **Use Plotly for all charts** (works in both Streamlit and FastAPI)

This minimizes the JavaScript learning curve while maximizing your Python strengths.

---

**Does this approach make sense? Or would you like me to:**
1. Sketch out a Streamlit MVP structure?
2. Design the FastAPI backend schema first?
3. Build the ML similarity engine as a standalone module?
