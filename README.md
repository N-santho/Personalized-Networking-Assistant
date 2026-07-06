# Personalized Networking Assistant

Personalized Networking Assistant is a complete production-quality AI-powered web application designed to help professionals prepare for networking events. It extracts key themes from event descriptions, generates tailored conversation starters (icebreakers) based on personal interests, verifies concepts/topics via Wikipedia, and logs previous recommendations with interactive thumbs up/down feedback and comments.

---

## Project Overview

Preparing for professional networking events can be challenging when encountering unfamiliar industries or technical jargon. This application addresses this challenge by providing an end-to-end local helper:
1. **Semantic Extraction**: Analyzes complex event descriptions to find the core subject areas.
2. **Contextual Suggestion**: Uses a local causal LLM (GPT-2) to craft tailored, relevant introductory icebreaker questions based on the intersection of event themes and user interests.
3. **External Grounding**: Provides a direct fact-checking interface integrated with Wikipedia to look up definitions of unknown terms instantly.
4. **Interactive Persistence**: Logs all requests and generated recommendations, allowing users to rate and comment on recommendations to refine future suggestions.

---

## Technologies Used

- **Web Services Backend**: [FastAPI](https://fastapi.tiangolo.com/) (high performance, automatic Swagger/Redoc metadata generation).
- **Frontend Dashboard**: [Streamlit](https://streamlit.io/) (interactive UI dashboard for fast ML deployment).
- **Machine Learning Inference**: [PyTorch](https://pytorch.org/) & [HuggingFace Transformers](https://huggingface.co/docs/transformers/index) (running local neural networks).
- **Database Engine**: [SQLite](https://sqlite.org/index.html) (serverless relational database).
- **ORM mapping**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (robust database schema declaration).
- **Topic Reference Lookup**: [MediaWiki API / Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) (authoritative public database).
- **Testing Infrastructure**: [Pytest](https://docs.pytest.org/) (functional integration and service unit test runner).

---

## Model & API Selection

For theme extraction, icebreaker generation, and factual verification, the Personalized Networking Assistant selectively uses specialized models and APIs tailored for local execution, speed, and accuracy:

### Why DistilBERT was selected (Theme Extraction)
- **Lightweight Architecture**: DistilBERT is a distilled version of BERT, retaining 97% of its language understanding capabilities while being 40% smaller and 60% faster.
- **Low Latency & CPU Friendly**: It executes extremely quickly on consumer-grade CPUs, making it ideal for real-time theme extraction without requiring expensive GPU setups.
- **Accurate Feature/Representation Mining**: It generates rich sentence embeddings and classification markers, enabling robust topic modeling on event descriptions.

### Why GPT-2 Small was selected (Causal Generation)
- **Local Autonomy & Zero API Fees**: Running GPT-2 Small (124M parameters) locally allows fully autonomous generation without needing subscription keys or hitting third-party API rate limits.
- **Predictable Local Footprint**: Having a compact memory size (~500MB), it easily fits on local machines while providing standard, flexible causal language capabilities.
- **Steerability & Determinism**: Using few-shot prompt injection, GPT-2 can be cleanly steered to produce structured bullet-point questions tailored to user-provided contexts. Generation is configured with `set_seed(42)` to run deterministically.

### Why Wikipedia API was selected (Fact Verification)
- **Unrestricted Public Knowledge**: The MediaWiki/Wikipedia API provides authoritative, community-vetted information covering millions of topics without requiring authentication or developer keys.
- **No Token Overhead**: Unlike LLM-based RAG or search integrations, the direct API has zero token costs and returns exact encyclopedic definitions.
- **Immediate Grounding**: Instantly contextualizes unfamiliar terms or technical jargon extracted from networking events, ensuring users are fully prepared.

---

## Architecture Diagram

```
                       +-----------------------------------+
                       |        Streamlit Frontend         |
                       |       (Multi-page Web App)        |
                       +-----------------+-----------------+
                                         |
                                         | HTTP Requests
                                         v
                       +-----------------+-----------------+
                       |         FastAPI Backend           |
                       |  (Uvicorn /docs & /redoc enabled) |
                       +---+-----------+-------------+-----+
                           |           |             |
       +-------------------+           |             +-------------------+
       |                               |                                 |
       v                               v                                 v
+------+-------------+      +----------+----------+             +--------+--------+
|   ThemeExtractor   |      |ConversationGenerator|             |  WikiService    |
| (DistilBERT Model) |      | (GPT-2 + set_seed)  |             | (MediaWiki API) |
+--------------------+      +---------------------+             +-----------------+
                                       |
                                       v
                            +----------+----------+
                            |   HistoryService    |
                            |  (SQLAlchemy ORM)   |
                            +----------+----------+
                                       |
                                       v
                            +----------+----------+
                            |  SQLite Database    |
                            |   (networking.db)   |
                            +---------------------+
```

---

## Folder Structure

```
skillwallet/
├── backend/
│   ├── app.py                     # FastAPI entry point
│   ├── database.py                # Database engine and session configuration
│   ├── models.py                  # SQLAlchemy Database Models
│   ├── schemas.py                 # Pydantic Schemas with detailed docstrings for OpenAPI
│   ├── config.py                  # Settings configuration management
│   ├── services/                  # Business Logic Services
│   │   ├── __init__.py
│   │   ├── theme_extractor.py     # DistilBERT themes extraction service
│   │   ├── conversation_generator.py # GPT-2 conversation starters generator
│   │   ├── wiki_service.py        # Wikipedia fetcher service
│   │   └── history_service.py     # Database CRUD service
│   ├── routes/                    # API Request Router Handlers
│   │   ├── __init__.py
│   │   ├── generate.py            # POST /generate route
│   │   ├── factcheck.py           # POST /factcheck route
│   │   ├── history.py             # GET /history route
│   │   └── feedback.py            # POST /feedback route
│   └── tests/                     # Unit Tests Suite
│       ├── __init__.py
│       ├── conftest.py            # Pytest configuration and shared fixtures
│       ├── test_theme_extractor.py
│       ├── test_conversation_generator.py
│       ├── test_wiki_service.py
│       ├── test_history_service.py
│       └── test_routes.py
├── frontend/                      # Streamlit UI Layer
│   ├── streamlit_app.py           # Main landing dashboard
│   └── pages/                     # Navigation pages
│       ├── Generate.py            # Event starters form
│       ├── Fact_Check.py          # Wikipedia topic checker
│       └── History.py             # Logs and feedback buttons
├── requirements.txt               # App dependencies
├── README.md                      # Documentation
└── .env.example                   # Environment configuration template
```

---

## Installation Guide

### Prerequisites
- Python 3.11+
- Pip package manager

### 1. Set Up Virtual Environment
Create and activate a python virtual environment to isolate libraries:

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
Install all required libraries for the backend (FastAPI, Pytest, Torch, Transformers) and frontend (Streamlit):
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Copy the `.env.example` file to `.env`:
```bash
copy .env.example .env   # On Windows
cp .env.example .env     # On macOS/Linux
```
You can customize the API port, host, logging level, or SQLite URL if desired.

---

## Running the Application

### 1. Run the Backend API Server
Start the FastAPI server via Uvicorn. This will automatically set up the SQLite database file (`networking.db`) and tables on launch, applying any database alterations (such as adding the `comment` column):
```bash
uvicorn backend.app:app --reload
```
- The backend API will be running at `http://127.0.0.1:8000`.
- Access the interactive documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.
- Access Redoc documentation at `http://127.0.0.1:8000/redoc`.

### 2. Run the Streamlit Frontend App
In a new terminal window (with the virtual environment activated), start the Streamlit web application:
```bash
streamlit run frontend/streamlit_app.py
```
- The frontend dashboard will open in your browser at `http://localhost:8501`.

---

## Testing Instructions

Run the test suite using `pytest` to verify backend correctness:
```bash
$env:PYTHONPATH="." # On Windows PowerShell
pytest backend/tests
```
The test suite utilizes mock objects to prevent heavy transformer downloads and network requests, testing the database, validators, service fallbacks, and endpoints in seconds.

---

## API Endpoints

### 1. Generate Starters
- **Endpoint**: `POST /generate`
- **Request Body**:
  ```json
  {
    "event_description": "AI for Sustainable Cities",
    "interests": "Climate Change, Urban Planning"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "themes": ["AI", "Sustainability", "Urban Planning"],
    "conversation_starters": [
      "How do you think AI can improve sustainable urban planning?",
      "What innovations in smart cities interest you most?",
      "Have you seen any AI applications making cities greener?"
    ]
  }
  ```

### 2. Fact Checker
- **Endpoint**: `POST /factcheck`
- **Request Body**:
  ```json
  {
    "topic": "Blockchain in Healthcare"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "title": "Blockchain in healthcare",
    "summary": "Blockchain in healthcare describes the application of cryptographic ledgers to medical records.",
    "wikipedia_link": "https://en.wikipedia.org/wiki/Blockchain_in_healthcare"
  }
  ```

### 3. Retrieve History Logs
- **Endpoint**: `GET /history`
- **Query Parameter**: `limit` (default: 50)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "event_description": "AI for Sustainable Cities",
      "themes": ["AI", "Sustainability", "Urban Planning"],
      "conversation_starters": [
        "How do you think AI can improve sustainable urban planning?",
        "What innovations in smart cities interest you most?",
        "Have you seen any AI applications making cities greener?"
      ],
      "liked": true,
      "comment": "Highly relevant to my research area.",
      "created_at": "2026-07-05T20:30:15.123456"
    }
  ]
  ```

### 4. Submit Feedback
- **Endpoint**: `POST /feedback`
- **Request Body**:
  ```json
  {
    "id": 1,
    "liked": true,
    "comment": "Highly relevant to my research area."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Feedback saved successfully.",
    "id": 1,
    "liked": true,
    "comment": "Highly relevant to my research area."
  }
  ```

---

## Screenshots

### Main Landing Page Dashboard
*Placeholder: Home Dashboard UI with sidebar options and status monitoring*

### Generator Interface
*Placeholder: Event inputs form and extracted theme pills alongside generated starters*

### Wikipedia verification
*Placeholder: Real-time search card fetching Wikipedia introduction summary and source link*

### History Logs
*Placeholder: Cards representing previous inputs, timestamps, and interactive like/dislike buttons*

---

## Future Scope

1. **Vector Database & Semantic Cache**: Store generated prompts in a vector database (e.g. ChromaDB) to perform semantic caches, avoiding repeating generations for similar events.
2. **Context-Aware LLMs**: Integrate larger open LLMs (like Llama-3 or Mistral-7B) via HuggingFace or API integrations (OpenAI, Gemini) for higher conversation quality.
3. **Calendar Integration**: Allow parsing calendar event descriptions directly from Google Calendar or Outlook invite links.
4. **LinkedIn Scraper integration**: Extract target contact profile descriptions to tailor icebreakers specifically for individual speakers.
