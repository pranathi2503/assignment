import streamlit as st
import ollama
from googlesearch import search  
import json
import requests
from bs4 import BeautifulSoup

# Custom Styling
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #FF5733;
        color: white;
        font-size: 18px;
        border-radius: 10px;
    }
    .stTitle {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Function to fetch web search results
def get_search_results(query, num_results=5):
    try:
        return list(search(query, num_results=num_results))
    except Exception:
        return []  # Return empty list if search fails

# Function to fetch webpage summaries
def fetch_page_summary(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}  
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        for para in paragraphs:
            text = para.get_text(strip=True)
            if len(text) > 50:  
                return text
    except Exception:
        return None  

# Function to get activity suggestions
def get_activity_suggestions(destination, interests):
    query = f"Top things to do in {destination} for {', '.join(interests)}"
    links = get_search_results(query)
    return [{"url": link, "summary": fetch_page_summary(link)} for link in links]

# Function to get hidden gems
def get_hidden_gems(destination, interests):
    query = f"Hidden gems in {destination} for {', '.join(interests)}"
    links = get_search_results(query)
    return [{"url": link, "summary": fetch_page_summary(link)} for link in links]

# Function to get travel suggestions
def get_travel_suggestions(destination):
    query = f"Travel tips and safety information for {destination}"
    links = get_search_results(query)
    return [{"url": link, "summary": fetch_page_summary(link)} for link in links]

# Function to refine user inputs using Ollama
def refine_user_input(user_input):
    system_prompt = """You are an AI travel assistant. Extract key details from the user's input 
    and return them as a structured JSON object. 

    Example:
    {
        "destination": "Paris",
        "start_location": "New York",
        "budget": "Moderate",
        "trip_duration": 5,
        "purpose": "Leisure",
        "interests": ["Museums", "Food"]
    }"""

    response = ollama.chat(model="mistral", messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User input: {user_input}"}
    ])
    
    try:
        refined_json = json.loads(response['message']['content'])
        return refined_json
    except json.JSONDecodeError:
        return None  

# Streamlit UI
col1, col2 = st.columns([1, 2])

with col1:
    st.image("travel_banner.jpg", use_container_width=True)

with col2:
    st.title("✈️ AI-Powered Travel Planner")
    st.subheader("Plan your dream trip effortlessly!")

st.write("### 🌍 Enter your travel details below:")

# Collect user inputs
with st.form("user_input_form"):
    destination = st.text_input("📍 Destination")
    start_location = st.text_input("🚏 Starting Location")
    budget = st.selectbox("💰 Budget", ["Low", "Moderate", "Luxury"])
    trip_duration = st.number_input("📅 Trip Duration (days)", min_value=1, step=1)
    purpose = st.text_area("🎯 Purpose of Travel (e.g., vacation, work, adventure)")
    interests = st.multiselect("🎭 Interests", ["Beaches", "Hiking", "Museums", "Food", "Shopping", "Nightlife", "Culture"])

    submitted = st.form_submit_button("🚀 Submit")

if submitted:
    user_inputs = {
        "destination": destination,
        "start_location": start_location,
        "budget": budget,
        "trip_duration": trip_duration,
        "purpose": purpose,
        "interests": interests
    }

    with st.spinner("⏳ Processing your input..."):
        refined_inputs = refine_user_input(str(user_inputs))

    if refined_inputs:
        st.session_state["user_inputs"] = refined_inputs
        st.success("✅ Input processed successfully!")
    else:
        st.error("❌ Error in refining input. Try again.")

# Generate activity suggestions
if "user_inputs" in st.session_state and st.button("🌟 Generate Activity Suggestions"):
    user_data = st.session_state["user_inputs"]

    with st.spinner("🔍 Fetching recommendations..."):
        general_suggestions = get_activity_suggestions(user_data["destination"], user_data["interests"])
        hidden_gems = get_hidden_gems(user_data["destination"], user_data["interests"])
        travel_info = get_travel_suggestions(user_data["destination"])

    st.session_state["suggestions"] = {
        "activities": general_suggestions,
        "hidden_gems": hidden_gems,
        "info": travel_info
    }

if "suggestions" in st.session_state and st.session_state["suggestions"]:
    with st.expander("🎯 Recommended Activities"):
        for item in st.session_state["suggestions"]["activities"]:
            st.markdown(f"- [{item['url']}]({item['url']})")
            if item["summary"]:
                st.write(f"**Summary:** {item['summary']}")

    with st.expander("💎 Hidden Gems & Unique Experiences"):
        for item in st.session_state["suggestions"]["hidden_gems"]:
            st.markdown(f"- [{item['url']}]({item['url']})")
            if item["summary"]:
                st.write(f"**Summary:** {item['summary']}")

    with st.expander("🛡️ Additional Travel Info"):
        for item in st.session_state["suggestions"]["info"]:
            st.markdown(f"- [{item['url']}]({item['url']})")
            if item["summary"]:
                st.write(f"**Summary:** {item['summary']}")

# Generate Final Itinerary
if "suggestions" in st.session_state and st.button("📖 Generate Itinerary"):
    user_data = st.session_state["user_inputs"]
    itinerary_prompt = f"Generate a structured {user_data['trip_duration']}-day itinerary for {user_data['destination']}, including timings and travel tips."
    
    with st.spinner("📝 Creating your itinerary..."):
        itinerary_response = ollama.chat(model="llama3.2", messages=[
            {"role": "system", "content": "You are a professional travel planner. Create a structured itinerary."},
            {"role": "user", "content": itinerary_prompt}
        ])
    
    st.markdown("### 🗺️ Your Personalized Itinerary")
    st.markdown(f"""
    ```yaml
    {itinerary_response['message']['content']}
    ```
    """)

