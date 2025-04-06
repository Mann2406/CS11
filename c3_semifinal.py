import streamlit as st
from gtts import gTTS
import speech_recognition as sr
import os
import time
import pygame
from groq import Groq
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langdetect import detect
import requests
import json
from fpdf import FPDF
from datetime import datetime, timedelta
import tempfile
import unicodedata
from PIL import Image
import io
import re
import base64
from streamlit_lottie import st_lottie
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import random
import pyaudio


# API Keys (Replace with your actual keys)
AMADEUS_API_KEY = "KcJe1Ef160GbCmAurWO2ieApdYJnUgKG"
AMADEUS_API_SECRET = "8Axu4TAQGgvWpm0D"
GOOGLE_API_KEY = "AIzaSyBF_X-pCPrgGDDT_0XK1ObF7lR1MkEsTl0"
GROQ_API_KEY = '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'
WEATHERAPI_KEY = "AIzaSyBF_X-pCPrgGDDT_0XK1ObF7lR1MkEsTl0"  # Replace with actual WeatherAPI key
UNSPLASH_ACCESS_KEY = "FlKz5N26NpYD6MloqmzV-taJRCAf_zYX5O-EAt-XGn4"

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize Geocoder
geolocator = Nominatim(user_agent="travel_planner")

# Helper Functions
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Lottie animations
lottie_travel = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_sk5h1kfn.json")

# Custom CSS
page_bg_img = """
<style>
[data-testid="stHeader"] {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255,255,255,0.1);
}
.custom-card {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    transition: all 0.3s ease;
}
.custom-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.25);
}
.stButton>button {
    border: none;
    padding: 12px 24px;
    border-radius: 12px;
    background: linear-gradient(135deg, #ff6a6a 0%, #c94b4b 100%)
;
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 14px rgba(0, 0, 0, 0.15);
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
}
.stTextInput>div>div>input,
.stDateInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    padding: 10px 15px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 18px 18px 0 18px;
    padding: 12px 16px;
    margin-left: auto;
    max-width: 80%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.assistant-message {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 18px 18px 18px 0;
    padding: 12px 16px;
    margin-right: auto;
    max-width: 80%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.gradient-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Geocode with Geopy
def geocode_location(location):
    try:
        location_data = geolocator.geocode(location, timeout=5)
        if location_data:
            return location_data.latitude, location_data.longitude
        return None, None
    except:
        return None, None

# Fetch Unsplash Images
def get_unsplash_images(city, count=7):
    queries = [
        f"{city} landmarks",
        f"{city} culture",
        f"{city} scenery",
        f"{city} architecture",
        f"{city} hidden gems",
    ]
    image_urls = []
    for query in queries[:count]:
        url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={UNSPLASH_ACCESS_KEY}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    image_urls.append(results[0]['urls']['regular'])
        except:
            pass
    return image_urls[:count]

# Amadeus Token
def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {"grant_type": "client_credentials", "client_id": AMADEUS_API_KEY, "client_secret": AMADEUS_API_SECRET}
    try:
        response = requests.post(url, data=data, timeout=5)
        response.raise_for_status()
        return response.json().get("access_token")
    except:
        return None

# Fetch Hotels
def get_hotels(city_code, budget=500):
    token = get_amadeus_token()
    if not token:
        return []
    url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city?cityCode={city_code}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        hotels = response.json().get("data", [])
        hotel_list = []
        for hotel in hotels[:5]:
            name = hotel['name']
            rating = hotel.get('rating', 'N/A')
            lat, lon = geocode_location(f"{name}, {city_code}")
            google_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
            hotel_list.append({"name": name, "rating": rating, "google_url": google_url})
        return hotel_list
    except:
        return []

# Fetch Flights
def get_flights(origin, destination, departure_date, return_date=None, budget=500):
    token = get_amadeus_token()
    if not token:
        return []
    url = f"https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode={origin}&destinationLocationCode={destination}&departureDate={departure_date}&adults=1"
    if return_date:
        url += f"&returnDate={return_date}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        flights = response.json().get("data", [])
        flight_details = []
        for f in flights[:3]:
            try:
                departure = f['itineraries'][0]['segments'][0]['departure']['at']
                carrier = f['itineraries'][0]['segments'][0]['carrierCode']
                price = float(f['price']['total'])
                if price <= budget:
                    flight_details.append({
                        "carrier": carrier,
                        "departure": departure,
                        "price": price,
                        "currency": f['price']['currency']
                    })
            except (KeyError, IndexError):
                continue
        return flight_details
    except:
        return []

# Fetch Attractions
def get_attractions(city):
    search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=top+attractions+in+{city}&key={GOOGLE_API_KEY}"
    try:
        search_response = requests.get(search_url, timeout=5)
        search_response.raise_for_status()
        results = search_response.json().get("results", [])
        attractions = []
        for place in results[:8]:
            try:
                place_id = place['place_id']
                details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,formatted_address,photos,website,url,types&key={GOOGLE_API_KEY}"
                details_response = requests.get(details_url, timeout=5)
                details_response.raise_for_status()
                details = details_response.json().get('result', {})
                photo_url = None
                if 'photos' in details and details['photos']:
                    photo_ref = details['photos'][0]['photo_reference']
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
                attractions.append({
                    "name": details.get("name", place.get("name", "N/A")),
                    "rating": details.get("rating", "N/A"),
                    "address": details.get("formatted_address", "N/A"),
                    "type": details.get("types", ["attraction"])[0].replace("_", " ").title(),
                    "website": details.get("website", ""),
                    "google_url": details.get("url", ""),
                    "photo_url": photo_url
                })
            except:
                continue
        return attractions
    except:
        return []

# Fetch Weather
def get_weather_forecast(city, start_date, end_date):
    lat, lon = geocode_location(city)
    if not lat or not lon:
        return None
    try:
        weather_url = f"https://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_KEY}&q={lat},{lon}&days=10"
        weather_response = requests.get(weather_url, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json().get('forecast', {}).get('forecastday', [])
        if not weather_data:
            return None
        trip_forecasts = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            daily_forecast = next((f for f in weather_data if f['date'] == date_str), None)
            if daily_forecast:
                trip_forecasts.append({
                    "date": date_str,
                    "temp": daily_forecast['day']['avgtemp_c'],
                    "description": daily_forecast['day']['condition']['text'],
                    "icon": daily_forecast['day']['condition']['icon'].split('/')[-1],
                    "humidity": daily_forecast['day']['avghumidity'],
                    "wind_speed": daily_forecast['day']['maxwind_kph'] / 3.6
                })
            current_date += timedelta(days=1)
        return trip_forecasts
    except:
        return None

# Fetch YouTube Links
def get_youtube_links(query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=1&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        items = response.json().get('items', [])
        if not items:
            return ""
        video_id = items[0]['id']['videoId']
        return f"https://www.youtube.com/watch?v={video_id}"
    except:
        return ""

# Generate PDF
def generate_pdf(itinerary, destination, trip_details, attractions, itinerary_number=1):
    class UnicodePDF(FPDF):
        def header(self):
            self.set_font("helvetica", "B", 20)
            self.set_text_color(0, 0, 0)
            self.set_xy(10, 10)
            self.cell(0, 10, f"Travel Itinerary {itinerary_number}: {destination}", new_x="LMARGIN", new_y="NEXT", align="C")

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f"Page {self.page_no()} | Generated on {datetime.now().strftime('%Y-%m-%d')}", new_x="RIGHT", new_y="TOP", align="C")

    pdf = UnicodePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Clean the itinerary text before processing
    def clean_text(text):
        # Remove any problematic characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()
        return text

    try:
        city_images = get_unsplash_images(destination, count=5)
        
        # Cover Page
        if city_images:
            pdf.add_page()
            try:
                response = requests.get(city_images[0], timeout=10)
                img = Image.open(io.BytesIO(response.content))
                img_path = os.path.join(tempfile.gettempdir(), f"cover_{destination}_{itinerary_number}.jpg")
                img.save(img_path)
                pdf.image(img_path, x=(210-190)/2, y=30, w=190)
                pdf.set_font("helvetica", "I", 12)
                pdf.set_xy(10, 100)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 10, "A Journey Awaits", new_x="LMARGIN", new_y="NEXT", align="C")
                os.remove(img_path)
            except Exception as e:
                st.warning(f"Couldn't add cover image: {str(e)}")

        # Trip Details
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Trip Overview", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 8, f"Duration: {trip_details['duration']} days", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Dates: {trip_details['departure_date']} to {trip_details['return_date']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Budget: ${trip_details['budget']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Interests: {clean_text(trip_details['interests'])}", new_x="LMARGIN", new_y="NEXT")
        
        # Attractions
        if attractions:
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "Recommended Attractions", new_x="LMARGIN", new_y="NEXT")
            for attraction in attractions[:5]:
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 8, clean_text(attraction['name']), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 10)
                pdf.cell(0, 6, clean_text(f"Type: {attraction['type']} | Rating: {attraction['rating']}"), new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, clean_text(f"Address: {attraction['address']}"), new_x="LMARGIN", new_y="NEXT")
                if attraction.get('google_url'):
                    pdf.set_text_color(0, 0, 255)
                    pdf.cell(0, 6, "Google Maps", new_x="LMARGIN", new_y="NEXT", link=attraction['google_url'])
                    pdf.set_text_color(0, 0, 0)
                pdf.ln(8)

        # Itinerary
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, f"Your Personalized Itinerary {itinerary_number}", new_x="LMARGIN", new_y="NEXT")
        
        # Clean and process the itinerary text
        clean_itinerary = unicodedata.normalize('NFKD', itinerary).encode('ascii', 'ignore').decode('ascii')
        paragraphs = [p for p in clean_itinerary.split('\n\n') if p.strip()]
        
        image_index = 1
        for para in paragraphs:
            if not para.strip():
                continue
                
            lines = [clean_text(line) for line in para.strip().split('\n') if line.strip()]
            if not lines:
                continue
                
            if "Day" in lines[0]:
                day_title = re.sub(r'\*\*(.*?)\*\*', r'\1', lines[0]).strip()
                pdf.set_font("helvetica", "B", 13)
                pdf.cell(0, 10, clean_text(day_title), new_x="LMARGIN", new_y="NEXT")
                
                if image_index < len(city_images) and pdf.get_y() + 60 < pdf.h - 15:
                    try:
                        response = requests.get(city_images[image_index], timeout=10)
                        img = Image.open(io.BytesIO(response.content))
                        img_path = os.path.join(tempfile.gettempdir(), f"day_{image_index}_{itinerary_number}.jpg")
                        img.save(img_path)
                        pdf.image(img_path, x=(210-60)/2, w=60, h=60)
                        pdf.set_font("helvetica", "I", 8)
                        pdf.cell(0, 5, clean_text(f"Scene {image_index}: {destination}"), new_x="LMARGIN", new_y="NEXT", align="C")
                        os.remove(img_path)
                        image_index += 1
                    except Exception as e:
                        st.warning(f"Couldn't add image {image_index}: {str(e)}")
                
                lines = lines[1:]
            
            pdf.set_font("helvetica", "", 11)
            for line in lines:
                line = clean_text(re.sub(r'\*\*(.*?)\*\*', r'\1', line))
                try:
                    if '<a href="' in line:
                        parts = line.split('<a href="')
                        for i, part in enumerate(parts):
                            if i == 0:
                                pdf.multi_cell(0, 8, clean_text(part))
                            else:
                                url_part, rest = part.split('">', 1)
                                text_part, remainder = rest.split('</a>', 1)
                                pdf.set_text_color(0, 0, 255)
                                pdf.multi_cell(0, 8, clean_text(text_part), link=url_part)
                                pdf.set_text_color(0, 0, 0)
                                pdf.multi_cell(0, 8, clean_text(remainder))
                    elif line.startswith("- "):
                        pdf.multi_cell(0, 8, clean_text(f"- {line.lstrip('- ').strip()}"))
                    else:
                        pdf.multi_cell(0, 8, clean_text(line.strip()))
                except Exception:
                    continue
                    
            pdf.ln(5)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_itinerary_{itinerary_number}.pdf") as temp_file:
            pdf_path = temp_file.name
            pdf.output(pdf_path)
        return pdf_path
        
    except Exception as e:
        st.error(f"Failed to generate PDF: {str(e)}")
        return None

# Chat Chain
def initialize_chat_chain():
    return {
        "client": groq_client,
        "memory": ConversationBufferMemory()
    }

def generate_groq_response(prompt, memory):
    history = memory.load_memory_variables({})["history"]
    messages = []
    for message in history:
        if isinstance(message, SystemMessage):
            messages.append({"role": "system", "content": message.content})
        elif isinstance(message, HumanMessage):
            messages.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            messages.append({"role": "assistant", "content": message.content})
    messages.append({"role": "user", "content": prompt})
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=4000,
            stream=False
        )
        memory.save_context({"input": prompt}, {"output": chat_completion.choices[0].message.content})
        return chat_completion.choices[0].message.content
    except:
        return "Sorry, I couldn't generate a response at this time."

# Text-to-Speech
def speak(text):
    try:
        lang = detect(text) if detect(text) != "un" else "en"
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
            tts = gTTS(text=text[:500], lang=lang)
            tts.save(temp_audio.name)
            pygame.mixer.init()
            pygame.mixer.music.load(temp_audio.name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
        os.unlink(temp_audio.name)
    except:
        pass

def get_voice_input():
    try:
        # First check if we're in an environment where microphone access is possible
        if os.environ.get('IS_STREAMLIT_CLOUD', 'false').lower() == 'true':
            st.warning("Voice input is not available in Streamlit Cloud. Please use text input.")
            return None
            
        try:
            import pyaudio  # Try importing PyAudio first
        except ImportError:
            st.warning("PyAudio is not installed. Please install it with: pip install pyaudio")
            return None
        except OSError:
            st.warning("PyAudio requires system dependencies. On Linux, try: sudo apt-get install portaudio19-dev")
            return None
            
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... Speak now.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5)
        try:
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.warning("Could not understand audio.")
            return None
        except sr.RequestError as e:
            st.warning(f"Speech recognition error: {str(e)}")
            return None
    except Exception as e:
        st.warning(f"Error during voice input: {str(e)}")
        return None
# Parse Itinerary for Map with Random Flow
def parse_itinerary_for_map(itinerary, destination, memory):
    itinerary_key = f"{destination}_{hash(itinerary)}"
    if itinerary_key in st.session_state.get("mapped_places_cache", {}):
        return st.session_state["mapped_places_cache"][itinerary_key]

    # Get base coordinates for the destination city
    base_lat, base_lon = geocode_location(destination)
    if not base_lat or not base_lon:
        return []

    # Fetch attractions as a pool of possible places
    attractions = get_attractions(destination)
    if not attractions:
        attractions = []

    # Select 7-12 random places within the city
    num_places = random.randint(7, 12)
    selected_places = []
    
    # Use attractions if available, otherwise generate random nearby points
    if len(attractions) >= num_places:
        selected_places = random.sample(attractions, num_places)
    else:
        selected_places = attractions.copy()
        remaining = num_places - len(attractions)
        for i in range(remaining):
            # Generate random offset within a small radius (approx 5-10 km)
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)
            lat = base_lat + lat_offset
            lon = base_lon + lon_offset
            name = f"Point of Interest {i+1}"
            selected_places.append({"name": name, "lat": lat, "lon": lon})

    # Assign days and order for flow
    mapped_places = []
    for i, place in enumerate(selected_places):
        day = f"Day {(i % st.session_state['trip_details']['duration']) + 1}"  # Cycle through trip days
        name = place.get("name", f"Point of Interest {i+1}")
        lat = place.get("lat", base_lat + random.uniform(-0.05, 0.05))
        lon = place.get("lon", base_lon + random.uniform(-0.05, 0.05))
        if not lat or not lon:
            lat, lon = geocode_location(f"{name}, {destination}")
            if not lat or not lon:
                lat, lon = base_lat + random.uniform(-0.05, 0.05), base_lon + random.uniform(-0.05, 0.05)
        mapped_places.append({"day": day, "name": name, "lat": lat, "lon": lon, "order": i + 1})

    # Cache the result
    if "mapped_places_cache" not in st.session_state:
        st.session_state["mapped_places_cache"] = {}
    st.session_state["mapped_places_cache"][itinerary_key] = mapped_places
    return mapped_places

if "chat_chain" not in st.session_state:
    st.session_state["chat_chain"] = initialize_chat_chain()
    st.session_state["conversation_history"] = [SystemMessage(content="""
        You are a professional travel planner assistant with expertise in creating personalized itineraries.
        When given a city, dates, budget, and interests, generate a highly detailed travel plan that includes:
        - Day-by-day structure with time slots
        - Hotel recommendations with Google Maps hyperlinks
        - Attraction visits with Google Maps hyperlinks
        - Dining suggestions
        - Transportation tips
        - Estimated costs
        - Local events with Google Maps hyperlinks
        - Weather, AQI, and time zone considerations
        - YouTube links for destination highlights
        
        Guidelines:
        1. Use hyperlinks (<a href='url' target='_blank'>Google Maps</a> or <a href='url' target='_blank'>YouTube</a>) for all place references and YouTube videos.
        2. Always provide links when relevant and available.
        3. Adjust recommendations based on weather if data is available.
        4. Include YouTube links for destination highlights.
    """)]
    st.session_state["itineraries"] = []
    st.session_state["trip_details"] = {}
    st.session_state["travel_chat"] = []
    st.session_state["pdf_paths"] = []
    st.session_state["attractions"] = []

# Main App
def main():
    # Hero Section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<h1 class='gradient-text'>AI Travel Itinerary Planner</h1>", unsafe_allow_html=True)
        st.markdown("""
        <p style="font-size: 1.2rem; color: #4a5568;">
            Create personalized travel plans with AI assistance. Get hotel recommendations, 
            flight options, attractions, weather forecasts, and more for your perfect trip.
        </p>
        """, unsafe_allow_html=True)
    with col2:
        if lottie_travel:
            st_lottie(lottie_travel, height=200, key="travel")

    # Main Container
    with st.container():
        with stylable_container(
            key="main_container",
            css_styles="""
            {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
                backdrop-filter: blur(4px);
            }
            """
        ):
            # Trip Planning Form
            st.markdown("### Trip Details")
            with st.form("travel_form"):
                col1, col2 = st.columns(2)
                with col1:
                    origin = st.text_input("From (Origin IATA code)", placeholder="e.g., LAX, JFK, LHR").upper()
                    destination = st.text_input("To (Destination city)", placeholder="e.g., Paris, Tokyo, New York")
                    departure_date = st.date_input("Departure date", min_value=datetime.now())
                with col2:
                    trip_length = st.number_input("Length of stay (days)", min_value=1, max_value=30, value=3)
                    budget = st.slider("Budget ($)", min_value=100, max_value=5000, value=500, step=100)
                
                st.markdown("### Traveler Preferences")
                col3, col4 = st.columns(2)
                with col3:
                    travelers = st.number_input("Number of travelers", min_value=1, max_value=20, value=1)
                    interests = st.text_area("Interests", placeholder="e.g., museums, hiking, local cuisine")
                with col4:
                    special_requests = st.text_area("Special requests", placeholder="Dietary needs, accessibility, etc.")
                
                submitted = st.form_submit_button("Generate Itineraries", use_container_width=True)

            if submitted and destination and origin:
                with st.spinner("Generating three unique itineraries for your trip..."):
                    progress_bar = st.progress(0)
                    return_date = departure_date + timedelta(days=trip_length)
                    city_code = destination[:3].upper()
                    
                    progress_bar.progress(10)
                    hotels = get_hotels(city_code, budget)
                    
                    progress_bar.progress(20)
                    flights = get_flights(origin, city_code, departure_date.strftime("%Y-%m-%d"), return_date.strftime("%Y-%m-%d"), budget)
                    
                    progress_bar.progress(30)
                    attractions = get_attractions(destination)
                    
                    progress_bar.progress(40)
                    weather = get_weather_forecast(destination, departure_date, return_date)
                    
                    progress_bar.progress(50)
                    youtube_link = get_youtube_links(f"{destination} travel highlights")
                    
                    st.session_state["attractions"] = attractions
                    
                    hotels_text = "\n".join([f"- {h['name']} (Rating: {h['rating']}) <a href='{h['google_url']}' target='_blank'>Google Maps</a>" if h['google_url'] else f"- {h['name']} (Rating: {h['rating']})" for h in hotels]) if hotels else "No hotels found"
                    flights_text = "\n".join([f"- {f['carrier']} at {f['departure']} ({f['price']} {f['currency']})" for f in flights]) if flights else "No flights found"
                    attractions_text = "\n".join([f"- {a['name']} ({a['type']}, Rating: {a['rating']}) <a href='{a['google_url']}' target='_blank'>Google Maps</a>" if a['google_url'] else f"- {a['name']} ({a['type']}, Rating: {a['rating']})" for a in attractions]) if attractions else "No attractions found"
                    weather_text = "\n".join([f"- {w['date']}: {w['description']}, {w['temp']}°C" for w in weather]) if weather else "Weather data not available"
                    youtube_text = f"<a href='{youtube_link}' target='_blank'>YouTube</a>" if youtube_link else "No YouTube link available"
                    
                    st.session_state["trip_details"] = {
                        "destination": destination,
                        "origin": origin,
                        "departure_date": departure_date.strftime("%Y-%m-%d"),
                        "return_date": return_date.strftime("%Y-%m-%d"),
                        "duration": trip_length,
                        "budget": budget,
                        "travelers": travelers,
                        "interests": interests,
                        "special_requests": special_requests,
                        "weather": weather,
                        "youtube_link": youtube_text
                    }
                    
                    prompt_base = f"""
                    Create a detailed {trip_length}-day itinerary for {destination} with:
                    - Budget: ${budget}
                    - Travelers: {travelers}
                    - Interests: {interests}
                    - Special requests: {special_requests if special_requests else 'None'}
                    
                    Available Hotels:
                    {hotels_text}
                    
                    Flight Options:
                    {flights_text}
                    
                    Top Attractions:
                    {attractions_text}
                    
                    Weather Forecast:
                    {weather_text}
                    
                    YouTube Highlight: {youtube_text}
                    
                    Instructions:
                    1. Structure the itinerary day-by-day with time slots
                    2. Include weather-appropriate activities if weather data is available
                    3. Recommend restaurants based on budget and interests
                    4. Include transportation tips with <a href='url' target='_blank'>Google Maps</a> hyperlinks
                    5. Provide estimated costs where possible
                    6. Include the YouTube link provided above
                    7. Use hyperlinks for all place references and YouTube videos
                    """
                    
                    itineraries = []
                    pdf_paths = []
                    
                    for i in range(3):
                        progress_bar.progress(60 + (i * 10))
                        variation_prompt = prompt_base + f"\n\nGenerate a unique itinerary (Option {i+1}) with a different focus or style (e.g., relaxed pace, adventure-focused, or budget-optimized)."
                        response = generate_groq_response(variation_prompt, st.session_state["chat_chain"]["memory"])
                        itineraries.append(response)
                        pdf_path = generate_pdf(response, destination, st.session_state["trip_details"], attractions, itinerary_number=i+1)
                        pdf_paths.append(pdf_path)
                    
                    st.session_state["itineraries"] = itineraries
                    st.session_state["pdf_paths"] = pdf_paths
                    st.session_state["travel_chat"].append({
                        "role": "assistant",
                        "content": f"I've created three unique {trip_length}-day itineraries for {destination}. Check them out below!"
                    })
                    
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    progress_bar.empty()

            # Display Itineraries
            if st.session_state.get("itineraries"):
                st.markdown("### Itineraries")
                cols = st.columns(3)
                for i, (itinerary, pdf_path) in enumerate(zip(st.session_state["itineraries"], st.session_state["pdf_paths"])):
                    with cols[i]:
                        st.markdown(f"#### Option {i+1}")
                        with st.expander(f"View Itinerary {i+1}", expanded=(i == 0)):
                            st.markdown(f"""
                            <div style="max-height: 400px; overflow-y: auto; padding: 10px;">
                                {itinerary}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "Download PDF",
                                    f,
                                    file_name=f"{destination.replace(' ', '_')}_itinerary_option_{i+1}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                        with col_btn2:
                            if st.button("Listen", key=f"listen_{i}", use_container_width=True):
                                summary = itinerary[:500] + "... [full itinerary above]"
                                speak(summary)

                # Map Section
                st.markdown("### Itinerary Flow Map")
                selected_itinerary = st.selectbox("Select Itinerary to Map", [f"Option {i+1}" for i in range(3)])
                itinerary_index = int(selected_itinerary.split()[1]) - 1
                with st.spinner("Generating flow map..."):
                    places = parse_itinerary_for_map(st.session_state["itineraries"][itinerary_index], destination, st.session_state["chat_chain"]["memory"])
                    if places:
                        lat, lon = geocode_location(destination)
                        m = folium.Map(location=[lat, lon] if lat and lon else [0, 0], zoom_start=13)
                        
                        # Sort places by order for sequential flow
                        places.sort(key=lambda x: x["order"])
                        
                        # Add markers and connect with polyline
                        coords = []
                        for i, place in enumerate(places):
                            coords.append([place["lat"], place["lon"]])
                            folium.Marker(
                                [place["lat"], place["lon"]],
                                popup=f"{place['day']}: {place['name']}",
                                tooltip=place["name"],
                                icon=folium.Icon(color="blue", icon="info-sign", prefix="fa")
                            ).add_to(m)
                            # Add numbered circle for order
                            folium.CircleMarker(
                                location=[place["lat"], place["lon"]],
                                radius=10,
                                popup=place["name"],
                                fill=True,
                                color="blue",
                                fill_color="blue",
                                fill_opacity=0
                            ).add_child(folium.Popup(f"{i+1}", show=True)).add_to(m)
                        
                        # Connect points with a polyline to show flow
                        if len(coords) > 1:
                            folium.PolyLine(coords, color="blue", weight=2.5, opacity=1).add_to(m)
                        
                        st_folium(m, width=700, height=500)
                    else:
                        st.warning("No places could be mapped for the flow.")

            # Destination Insights
            if st.session_state["trip_details"].get("weather"):
                st.markdown("### Weather Forecast")
                weather_data = st.session_state["trip_details"]["weather"]
                weather_df = pd.DataFrame({
                    'Date': [day['date'] for day in weather_data],
                    'Temperature (°C)': [day['temp'] for day in weather_data],
                    'Condition': [day['description'].title() for day in weather_data]
                })
                fig = px.line(weather_df, x='Date', y='Temperature (°C)', 
                              title=f"Weather Forecast for {st.session_state['trip_details']['destination']}",
                              markers=True, text='Condition')
                fig.update_traces(textposition="top center")
                st.plotly_chart(fig, use_container_width=True)

            if st.session_state.get("attractions"):
                st.markdown("### Top Attractions")
                for attraction in st.session_state["attractions"][:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"#### {attraction['name']}")
                        st.markdown(f"Rating: {attraction['rating']} | Type: {attraction['type']}")
                        st.markdown(f"Address: {attraction['address']}")
                        if attraction.get('google_url'):
                            st.markdown(f"<a href='{attraction['google_url']}' target='_blank'>Google Maps</a>", unsafe_allow_html=True)
                    with col2:
                        if attraction.get('photo_url'):
                            st.image(attraction['photo_url'], width=150)

            # Travel Assistant
            st.markdown("### Travel Assistant")
            st.markdown("Ask questions or request changes to your itinerary")
            
            with stylable_container(
                key="chat_container",
                css_styles="""
                {
                    max-height: 400px;
                    overflow-y: auto;
                    padding: 1rem;
                }
                """
            ):
                for message in st.session_state.get("travel_chat", []):
                    if message["role"] == "user":
                        st.markdown(f"<div class='user-message'><p>{message['content']}</p></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='assistant-message'><p>{message['content']}</p></div>", unsafe_allow_html=True)
            
            col_chat1, col_chat2, col_chat3 = st.columns([3, 1, 1])
            with col_chat1:
                user_input = st.text_input("Type your question or request:", key="chat_input", 
                                         placeholder="E.g., Suggest vegetarian restaurants", 
                                         label_visibility="collapsed")
            with col_chat2:
                if st.button("Send", use_container_width=True) and user_input:
                    st.session_state["travel_chat"].append({"role": "user", "content": user_input})
                    with st.spinner("Thinking..."):
                        weather_str = ", ".join([f"{w['date']}: {w['description']}, {w['temp']}°C" for w in st.session_state["trip_details"].get("weather", [])]) if st.session_state["trip_details"].get("weather") else "Weather data not available"
                        context = f"""
                        Current itinerary details:
                        Destination: {st.session_state["trip_details"]["destination"]}
                        Dates: {st.session_state["trip_details"]["departure_date"]} to {st.session_state["trip_details"]["return_date"]}
                        Budget: ${st.session_state["trip_details"]["budget"]}
                        Interests: {st.session_state["trip_details"]["interests"]}
                        Special Requests: {st.session_state["trip_details"].get("special_requests", "None")}
                        Weather: {weather_str}
                        
                        User question/request: {user_input}
                        """
                        response = generate_groq_response(context, st.session_state["chat_chain"]["memory"])
                        st.session_state["travel_chat"].append({"role": "assistant", "content": response})
                        st.rerun()
            with col_chat3:
                if st.button("Voice Input", use_container_width=True):
                    voice_input = get_voice_input()
                    if voice_input:
                        st.session_state["travel_chat"].append({"role": "user", "content": voice_input})
                        with st.spinner("Thinking..."):
                            weather_str = ", ".join([f"{w['date']}: {w['description']}, {w['temp']}°C" for w in st.session_state["trip_details"].get("weather", [])]) if st.session_state["trip_details"].get("weather") else "Weather data not available"
                            context = f"""
                            Current itinerary details:
                            Destination: {st.session_state["trip_details"]["destination"]}
                            Dates: {st.session_state["trip_details"]["departure_date"]} to {st.session_state["trip_details"]["return_date"]}
                            Budget: ${st.session_state["trip_details"]["budget"]}
                            Interests: {st.session_state["trip_details"]["interests"]}
                            Special Requests: {st.session_state["trip_details"].get("special_requests", "None")}
                            Weather: {weather_str}
                            
                            User question/request: {voice_input}
                            """
                            response = generate_groq_response(context, st.session_state["chat_chain"]["memory"])
                            st.session_state["travel_chat"].append({"role": "assistant", "content": response})
                            st.rerun()

if __name__ == "__main__":
    main()