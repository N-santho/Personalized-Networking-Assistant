import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Personalized Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default page navigation list in the sidebar using custom CSS
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# API Endpoint Configuration
BACKEND_URL = "https://personalized-networking-assistant-nx1h.onrender.com"

# Timeout constants (in seconds)
# Render free tier cold starts can take 30-60s; ML model loading adds another 60-90s
TIMEOUT_GENERATE = 180   # /generate: DistilBERT + GPT-2 load on first call
TIMEOUT_FACTCHECK = 20   # /factcheck: lightweight Wikipedia API call
TIMEOUT_HISTORY   = 15   # /history:  simple DB read
TIMEOUT_FEEDBACK  = 10   # /feedback: simple DB write

# Inject premium design CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Apply fonts */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Gradient Style */
    .title-text {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    /* Topic pills/badges */
    .topic-pill {
        background: rgba(124, 58, 237, 0.12);
        color: #a78bfa;
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 20px;
        padding: 5px 15px;
        font-size: 0.9rem;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Cards and boxes */
    .starter-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(8px);
        transition: transform 0.2s;
    }
    .starter-card:hover {
        transform: translateY(-2px);
        border-color: rgba(124, 58, 237, 0.3);
    }
    
    /* History & Feedback items */
    .history-box {
        background: rgba(255, 255, 255, 0.01);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    .rating-badge {
        font-weight: bold;
        font-size: 0.85rem;
        padding: 3px 8px;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State variables for Story 7
if "generated_topics" not in st.session_state:
    st.session_state.generated_topics = []
if "generated_starters" not in st.session_state:
    st.session_state.generated_starters = []
if "event_description" not in st.session_state:
    st.session_state.event_description = ""
if "interests" not in st.session_state:
    st.session_state.interests = ""
if "fact_check_result" not in st.session_state:
    st.session_state.fact_check_result = None
if "last_generated_id" not in st.session_state:
    st.session_state.last_generated_id = None

# Helper functions
def submit_feedback_signal(record_id: int, liked_status: bool, index: int):
    """
    Submits user rating validation thumbs signal back to the API database service.
    """
    try:
        payload = {
            "id": record_id,
            "liked": liked_status,
            "comment": None
        }
        res = requests.post(f"{BACKEND_URL}/feedback", json=payload, timeout=TIMEOUT_FEEDBACK)
        if res.status_code == 200:
            st.toast(f"Feedback logged successfully for starter #{index + 1}!")
        else:
            st.error(f"Failed to submit feedback: {res.json().get('detail')}")
    except Exception as e:
        st.error(f"Error submitting feedback: {str(e)}")

# Story 1: Application Setup and Configuration
st.markdown("<h1 class='title-text'>🤝 Personalized Networking Assistant</h1>", unsafe_allow_html=True)
st.write("Generate AI-powered conversation starters for professional networking events.")
st.info(
    "⏳ **First request may take up to 2–3 minutes.** "
    "The backend runs on Render's free tier, which sleeps after inactivity. "
    "ML models (DistilBERT + GPT-2) are also loaded on the first call. "
    "Subsequent requests will be much faster."
)
st.markdown("---")

# Main Content Layout - Split into Generator & Fact Check Panel
col_left, col_right = st.columns([1.2, 0.8], gap="large")

with col_left:
    st.markdown("### Event Context Input")
    
    # Story 2: Input fields
    event_desc_input = st.text_area(
        label="Event Description",
        value=st.session_state.event_description,
        placeholder="Paste the event description here...",
        height=140,
        help="Paste key event schedules, tracks, workshops, or host descriptions."
    )
    # Track update to session state
    st.session_state.event_description = event_desc_input
    
    interests_input = st.text_input(
        label="User Interests",
        value=st.session_state.interests,
        placeholder="Example: AI, Machine Learning, Robotics",
        help="Specify topics or fields that you are interested in discussing."
    )
    # Track update to session state
    st.session_state.interests = interests_input

    # Generation Trigger Button
    generate_btn = st.button("Generate Conversation Starters 🚀", use_container_width=True)

    if generate_btn:
        if not event_desc_input.strip():
            st.warning("⚠️ Event Description is required.")
        elif not interests_input.strip():
            st.warning("⚠️ User Interests field is required.")
        else:
            with st.spinner("Analyzing themes and drafting conversation starters..."):
                try:
                    payload = {
                        "event_description": event_desc_input.strip(),
                        "interests": interests_input.strip()
                    }
                    response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=TIMEOUT_GENERATE)
                    
                    if response.status_code == 201:
                        result_data = response.json()
                        st.session_state.last_generated_id = result_data.get("id")
                        st.session_state.generated_topics = result_data.get("themes", [])
                        st.session_state.generated_starters = result_data.get("conversation_starters", [])
                        st.success("✅ Conversation starters generated successfully!")
                    else:
                        st.error(f"API Error ({response.status_code}): {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Failed to communicate with backend service: {str(e)}")

    # Story 3: Results Display and Feedback System
    if st.session_state.generated_topics or st.session_state.generated_starters:
        st.markdown("---")
        
        # Display extracted topics
        st.markdown("### Extracted Topics")
        pill_html = ""
        for topic in st.session_state.generated_topics:
            pill_html += f"<span class='topic-pill'>{topic}</span>"
        st.markdown(pill_html, unsafe_allow_html=True)
        st.write("")

        # Display conversation starters
        st.markdown("### Conversation Starters")
        
        for idx, starter in enumerate(st.session_state.generated_starters):
            with st.container():
                st.markdown(f"<div class='starter-card'>💡 {starter}</div>", unsafe_allow_html=True)
                btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 7.6])

                with btn_col1:
                    if st.button("👍 Like", key=f"like_{st.session_state.last_generated_id}_{idx}"):
                        submit_feedback_signal(st.session_state.last_generated_id, True, idx)
                with btn_col2:
                    if st.button("👎 Dislike", key=f"dislike_{st.session_state.last_generated_id}_{idx}"):
                        submit_feedback_signal(st.session_state.last_generated_id, False, idx)
                st.write("")

with col_right:
    # Story 4: Fact Checking Section
    st.markdown("### Fact Check")
    
    fact_query = st.text_input(
        label="Concept Search",
        placeholder="Enter a topic or statement to verify",
        help="Verify any unknown concepts, definitions, or organizations instantly."
    )
    
    verify_btn = st.button("Verify 🔍", use_container_width=True)
    
    if verify_btn:
        if not fact_query.strip():
            st.warning("⚠️ Enter a topic to perform lookup.")
        else:
            with st.spinner("Checking references..."):
                try:
                    payload = {"topic": fact_query.strip()}
                    res = requests.post(f"{BACKEND_URL}/factcheck", json=payload, timeout=TIMEOUT_FACTCHECK)
                    
                    if res.status_code == 200:
                        st.session_state.fact_check_result = res.json()
                    elif res.status_code == 404:
                        st.session_state.fact_check_result = {
                            "error": f"Topic '{fact_query}' could not be verified on Wikipedia."
                        }
                    else:
                        st.session_state.fact_check_result = {
                            "error": f"Server error: {res.json().get('detail')}"
                        }
                except Exception as e:
                    st.session_state.fact_check_result = {"error": str(e)}

    # Display fact check result from session state (Story 7 compliance)
    if st.session_state.fact_check_result:
        res = st.session_state.fact_check_result
        if "error" in res:
            st.error(res["error"])
        else:
            st.info(
                f"**📖 Verified Summary: {res.get('title')}**\n\n"
                f"{res.get('summary')}\n\n"
                f"[Read Wikipedia article ↗]({res.get('wikipedia_link')})"
            )

st.markdown("---")

# Layout for History logs
history_col, feedback_col = st.columns(2, gap="large")

# Fetch database logs for Story 5 & 6
db_history = []
try:
    response = requests.get(f"{BACKEND_URL}/history?limit=30", timeout=TIMEOUT_HISTORY)
    if response.status_code == 200:
        db_history = response.json()
except Exception:
    pass

with history_col:
    # Story 5: Conversation History
    st.markdown("### Conversation History")
    
    if not db_history:
        st.markdown("<p style='color: #6b7280;'>No previous conversation starters found.</p>", unsafe_allow_html=True)
    else:
        for item in db_history:
            # Format timestamp
            try:
                dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                formatted_time = item["created_at"]
                
            with st.container():
                st.markdown(
                    f"<div class='history-box'>"
                    f"<span style='color:#9ca3af; font-size:0.85rem;'>⏰ {formatted_time}</span><br>"
                    f"**Event Description:** {item['event_description']}<br>"
                    f"**Extracted Topics:** {', '.join(item['themes'])}<br>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                with st.expander("View Starters"):
                    for s in item["conversation_starters"]:
                        st.markdown(f"- {s}")
                st.write("")

with feedback_col:
    # Story 6: Feedback History
    st.markdown("### Feedback History")
    
    # Filter logs that have been rated
    rated_items = [item for item in db_history if item.get("liked") is not None]
    
    if not rated_items:
        st.markdown("<p style='color: #6b7280;'>No feedback updates logged yet.</p>", unsafe_allow_html=True)
    else:
        for item in rated_items:
            try:
                dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                formatted_time = item["created_at"]
                
            icon = "👍 Like" if item["liked"] else "👎 Dislike"
            
            with st.container():
                st.markdown(
                    f"<div class='history-box'>"
                    f"<span style='color:#9ca3af; font-size:0.85rem;'>⏰ {formatted_time}</span><br>"
                    f"**Feedback Signal:** {icon}<br>"
                    f"**Suggestion:**<br>",
                    unsafe_allow_html=True
                )
                for s in item["conversation_starters"]:
                    st.markdown(f"- {s}")
                st.markdown("</div>", unsafe_allow_html=True)
                st.write("")
