
# Import necessary modules
import os
import requests
from datetime import datetime
import sys
import streamlit as st
from streamlit_chat import message as st_message
import ast
import re
import getpass
from transformers import AutoTokenizer, AutoModelForCausalLM
import folium
from streamlit_folium import st_folium
import googlemaps
import streamlit as st
from streamlit_chat import message as st_message
import ast
import re
from neo4j import GraphDatabase


NEO4J_URI="neo4j+s://66f7f174.databases.neo4j.io"
NEO4J_USER="neo4j"
NEO4J_PASSWORD=""
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")




# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    trust_remote_code=True
)

# Load the model with device map for efficient loading
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True
)


# Define a simple login check function
def check_credentials(username, password):
    # Replace these with your actual authentication logic or stored credentials
    valid_username = "Hasnain"
    valid_password = "has12345"
    return username == valid_username and password == valid_password

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Display the login screen if the user is not logged in
if not st.session_state.logged_in:
    st.title("Login to One-Day Tour Planning Assistant")

    # Input fields for login ID and password
    username = st.text_input("Login ID")
    password = st.text_input("Password", type="password")

    # Submit button for login
    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            # st.experimental_rerun()  # Refresh the app to show the main content
        else:
            # st.error("Invalid login ID or password. Please try again.")
            pass

# !export GOOGLE_PLACES_API_KEY='AIzaSyC4tLTbZ1sjGRjJm6QKCAUO78J4geG0r_w'
class MemoryAgent:
    def __init__(self):
        self.user_preferences = {}
        self.questions = {
            'city': "Which city would you like to visit?",
            'date_and_time': "Great! Let’s get started. What day are you planning for, and what time do you want to start and end your day?",
            'interests': "Could you tell me your interests? For example, do you like historical sites, nature, shopping, or food experiences?",
            'budget': "What's your budget for the day?",
            'starting_point': "Where would you like to start your day? You can provide your hotel or any specific location, or we can start from the first attraction itself."
        }
        self.required_keys = ['city', 'date', 'start_time', 'end_time', 'interests', 'budget', 'starting_point']
        self.current_preference_key = None

    def update_preferences(self, user_message):
        message = user_message.strip().lower()
        prefs = self.user_preferences

        if self.current_preference_key:
            # Assign the user's message to the expected preference
            if self.current_preference_key == 'date_and_time':
                # Extract date, start_time, and end_time
                self.extract_date_and_time(user_message)
            elif self.current_preference_key == 'starting_point':
                if message in ["i'm not sure", "i am not sure", "not sure", "i don't know", "don't know", "i am not really sure"]:
                    # User is unsure about the starting point
                    prefs['starting_point'] = None
                    prefs['starting_point_confirmed'] = True  # No need to confirm
                else:
                    prefs['starting_point'] = user_message.strip()
                    prefs['starting_point_confirmed'] = False  # May need confirmation
            else:
                prefs[self.current_preference_key] = user_message.strip()
            self.current_preference_key = None
        else:
            # Handle option selections
            if "option" in message:
                option_number = int(''.join(filter(str.isdigit, message)))
                if 'pending_options' in prefs:
                    selected_option = prefs['pending_options'][option_number - 1]
                    prefs['starting_point'] = selected_option
                    prefs['starting_point_confirmed'] = True
                    del prefs['pending_options']
            else:
                # Try to extract preferences from message
                self.extract_preferences_from_message(message)

        # Handle adjustments after itinerary is generated
        if prefs.get('itinerary_generated', False):
            if any(word in message.lower() for word in ["add", "include", "change", "adjust", "i'd like to have lunch", "lunch"]):
                # Store the adjustment request
                prefs.setdefault('adjustments', []).append(user_message)
                prefs['needs_replanning'] = True  # Flag to indicate that itinerary needs updating

            # Handle budget adjustment
            if "budget" in message.lower() and any(word in message.lower() for word in ["low", "less", "reduce"]):
                new_budget = self.extract_budget_from_message(message)
                if new_budget:
                    prefs['budget'] = new_budget
                else:
                    current_budget = float(''.join(filter(str.isdigit, prefs.get('budget', '0'))))
                    if current_budget > 0:
                        prefs['budget'] = str(current_budget * 0.8)  # Reduce by 20%
                    else:
                        prefs['budget'] = '100'  # Set a default lower budget
                prefs['needs_reoptimization'] = True  # Flag for reoptimization

    def extract_date_and_time(self, message):
        prefs = self.user_preferences
        # Simple extraction logic (you can improve this with regex or NLP)
        date_part = ''
        start_time_part = ''
        end_time_part = ''

        # Extract date
        date_keywords = ["on", "date", "visiting"]
        for keyword in date_keywords:
            if keyword in message.lower():
                date_part = message.lower().split(keyword)[-1].strip()
                break
        if not date_part:
            date_part = message

        # Extract start time
        time_keywords = ["start at", "start", "begin", "from"]
        for keyword in time_keywords:
            if keyword in message.lower():
                start_time_part = message.lower().split(keyword)[-1].strip()
                break

        # Extract end time
        end_time_keywords = ["end at", "end", "finish by", "to", "till"]
        for keyword in end_time_keywords:
            if keyword in message.lower():
                end_time_part = message.lower().split(keyword)[-1].strip()
                break

        # Assign extracted values
        prefs['date'] = date_part.split('.')[0].strip()
        if 'am' in start_time_part or 'pm' in start_time_part:
            prefs['start_time'] = start_time_part.split('and')[0].strip()
        if 'am' in end_time_part or 'pm' in end_time_part:
            prefs['end_time'] = end_time_part.split('and')[0].strip()

    def extract_preferences_from_message(self, message):
        # Implement extraction logic if needed
        pass

    def extract_budget_from_message(self, message):
        # Extract budget from the message if specified
        budget = ''.join(filter(str.isdigit, message))
        if budget:
            return budget
        return None

    def get_missing_preferences(self):
        missing_prefs = []
        for key in self.required_keys:
            if key not in self.user_preferences:
                if key == 'date' and 'date_and_time' not in self.user_preferences:
                    missing_prefs.append('date_and_time')
                elif key == 'start_time' and 'date_and_time' not in self.user_preferences:
                    missing_prefs.append('date_and_time')
                elif key == 'end_time' and 'date_and_time' not in self.user_preferences:
                    missing_prefs.append('date_and_time')
                elif key != 'date' and key != 'start_time' and key != 'end_time':
                    missing_prefs.append(key)
        return list(set(missing_prefs))

    def get_next_question(self):
        missing_preferences = self.get_missing_preferences()
        if missing_preferences:
            key = missing_preferences[0]
            self.current_preference_key = key
            question = self.questions[key]
            return question
        else:
            return None

    def store_preference(self, key, value):
        # Method to store preferences in self.user_preferences
        self.user_preferences[key] = value

    def get_hotel_options(self, hotel_name):
        # Get the city from user preferences
        prefs = self.user_preferences
        city = prefs.get('city', '')
        if not city:
            city = 'your city'  # Default city if not provided

        api_key = os.getenv('GOOGLE_PLACES_API_KEY')  # Store your API key securely
        if not api_key:
            raise Exception("Google Places API key not found. Please set the 'GOOGLE_PLACES_API_KEY' environment variable.")

        # Build the request URL
        endpoint_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f"{hotel_name} in {city}",
            'type': 'lodging',
            'key': api_key
        }

        # Make the request to the Google Places API
        response = requests.get(endpoint_url, params=params)
        results = response.json().get('results', [])


# ItineraryGenerationAgent
class ItineraryGenerationAgent:
    def generate_itinerary(self, preferences):
        # Build the prompt dynamically
        prompt = f"Plan a one-day itinerary in {preferences.get('city', 'the city')} for a traveler."

        # Include date
        if 'date' in preferences:
            prompt += f" The traveler will be visiting on {preferences['date']}."

        # Include start and end times if available
        if 'start_time' in preferences and 'end_time' in preferences:
            prompt += f" They want to start at {preferences['start_time']} and finish by {preferences['end_time']}."
        elif 'start_time' in preferences:
            prompt += f" They want to start at {preferences['start_time']} with no specific end time."
        elif 'end_time' in preferences:
            prompt += f" They need to finish by {preferences['end_time']} but have no specific start time."
        else:
            prompt += " They have no specific time constraints."

        # Include budget if available
        if 'budget' in preferences:
            prompt += f" Their budget for the day is ${preferences['budget']}."
        else:
            prompt += " They have no specific budget constraints."

        # Include interests if available
        if 'interests' in preferences:
            prompt += f" They are interested in {preferences['interests']}."
        else:
            prompt += " They are not sure about their interests, please suggest popular options."

        # Include starting point if available
        if 'starting_point' in preferences and preferences['starting_point']:
            prompt += f" Their starting point is {preferences['starting_point']}."

        # Include any adjustments
        if 'adjustments' in preferences:
            adjustments = ' '.join(preferences['adjustments'])
            prompt += f" Please also consider the following adjustments: {adjustments}"

        # Include lunch preferences
        if 'lunch_preference' in preferences:
            prompt += f" They have a specific lunch preference: {preferences['lunch_preference']}."

        # Instruction to the assistant
        prompt += " Provide the itinerary with recommended places, estimated costs, time allocations, and check if attractions are open."
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        response = model.generate(
                    inputs,
                    max_new_tokens=150,
                    temperature=0.7,
                    top_p=0.95,
                    do_sample=True,
                    eos_token_id=tokenizer.eos_token_id
                )

        itinerary = response.choices[0].message.content.strip()
        return itinerary

# OptimizationAgent
class OptimizationAgent:
    def optimize_itinerary(self, itinerary_text, preferences):
        # For demonstration purposes, we'll simulate optimization
        optimized_itinerary = itinerary_text

        # Adjust for lower budget
        if 'needs_reoptimization' in preferences and preferences['needs_reoptimization']:
            optimized_itinerary += "\n\nNote: The itinerary has been adjusted to accommodate your lower budget."
            preferences['needs_reoptimization'] = False  # Reset the flag

        return optimized_itinerary

# WeatherAgent
class WeatherAgent:
    def __init__(self):
        self.api_key = os.getenv('OPEN_WEARTHER_API_KEY')

    def get_weather(self, city, date):
        # For simplicity, we'll fetch the current weather
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get('weather'):
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp']
            weather_info = f"The weather in {city} on {date} is expected to be {weather_description} with a temperature of around {temperature}°C."
            # Provide recommendations based on weather
            if 'rain' in weather_description.lower():
                weather_info += " It might rain, so consider bringing an umbrella."
            elif 'clear' in weather_description.lower() or 'sunny' in weather_description.lower():
                weather_info += " It looks like it will be sunny, so no need for an umbrella."
            return weather_info
        else:
            return "Unable to fetch weather data at the moment."

# UserInteractionAgent
class UserInteractionAgent:
    def __init__(self):
        self.memory_agent = MemoryAgent()
        self.itinerary_agent = ItineraryGenerationAgent()
        self.optimization_agent = OptimizationAgent()
        self.weather_agent = WeatherAgent()
        self.conversation_history = []

    def process_user_input(self, user_message):
        self.conversation_history.append({'role': 'user', 'content': user_message})

        # Update preferences
        self.memory_agent.update_preferences(user_message)

        # Build the assistant's response
        assistant_message = self.build_assistant_response(user_message)

        self.conversation_history.append({'role': 'assistant', 'content': assistant_message})

        return assistant_message

    def build_assistant_response(self, user_message):
        prefs = self.memory_agent.user_preferences

        # Handle adjustments after itinerary is generated
        if prefs.get('needs_replanning', False):
            # Process the adjustment request
            adjustment_request = prefs['adjustments'][-1]  # Get the latest adjustment request

            # Update preferences based on the adjustment request
            if "lunch" in adjustment_request.lower():
                prefs['lunch_preference'] = adjustment_request

            # Regenerate and optimize the itinerary with the new preferences
            itinerary = self.itinerary_agent.generate_itinerary(prefs)
            optimized_itinerary = self.optimization_agent.optimize_itinerary(itinerary, prefs)
            prefs['needs_replanning'] = False  # Reset the flag

            assistant_message = f"Understood! Let me find a suitable option.\n\nI've updated your itinerary based on your preferences:\n{optimized_itinerary}"

            # Include weather updates or recommendations if needed
            weather_info = self.weather_agent.get_weather(prefs['city'], prefs.get('date', 'today'))
            assistant_message += f"\n\n{weather_info}"

            return assistant_message

        # Handle budget reoptimization
        if prefs.get('needs_reoptimization', False):
            # Regenerate and optimize the itinerary with the new budget
            itinerary = self.itinerary_agent.generate_itinerary(prefs)
            optimized_itinerary = self.optimization_agent.optimize_itinerary(itinerary, prefs)
            prefs['needs_reoptimization'] = False  # Reset the flag

            assistant_message = f"I've adjusted your itinerary based on your budget:\n{optimized_itinerary}"
            return assistant_message

        # Check if starting point needs confirmation
        if 'starting_point' in prefs and not prefs.get('starting_point_confirmed', False):
            if 'pending_options' in prefs:
                # Provide options
                assistant_message = f"Since there are multiple hotels named '{prefs['starting_point']}', could you confirm which one you are referring to? Here are some options:\n"
                options = prefs['pending_options']
                for idx, option in enumerate(options, 1):
                    assistant_message += f"Option {idx}: {option}\n"
                assistant_message += "Please select one of the options by typing 'Option 1', 'Option 2', or 'Option 3', or provide more details."
                return assistant_message
            else:
                # Generate options based on the starting point
                if prefs['starting_point'] is not None:
                    options = self.memory_agent.get_hotel_options(prefs['starting_point'])
                    assistant_message = f"Since there are multiple hotels named '{prefs['starting_point']}', could you confirm which one you are referring to? Here are some options:\n"
                    for idx, option in enumerate(options, 1):
                        assistant_message += f"Option {idx}: {option}\n"
                    assistant_message += "Please select one of the options by typing 'Option 1', 'Option 2', or 'Option 3', or provide more details."
                    return assistant_message
                else:
                    # User is unsure; proceed without a specific starting point
                    prefs['starting_point_confirmed'] = True  # No need to confirm

        # Check if all preferences are collected
        missing_prefs = self.memory_agent.get_missing_preferences()
        if missing_prefs:
            next_question = self.memory_agent.get_next_question()
            return next_question
        else:
            # All preferences collected, generate itinerary
            if not prefs.get('itinerary_generated', False):
                # Generate the itinerary
                itinerary = self.itinerary_agent.generate_itinerary(prefs)
                optimized_itinerary = self.optimization_agent.optimize_itinerary(itinerary, prefs)
                prefs['itinerary_generated'] = True

                assistant_message = f"Got it! Here is an initial itinerary for your day in {prefs['city']}, starting from {prefs.get('starting_point', 'the first attraction')}:\n{optimized_itinerary}"

                # Include weather updates or recommendations if needed
                weather_info = self.weather_agent.get_weather(prefs['city'], prefs.get('date', 'today'))
                assistant_message += f"\n\n{weather_info}\n\nLet me know if you have any specific preferences for lunch or if you'd like to add/change anything."

                return assistant_message
            else:
                # Itinerary already generated; ask for further adjustments
                return "Is there anything else you'd like to add or adjust in your itinerary?"

import os
import streamlit as st
os.environ['OPEN_WEARTHER_API_KEY']=""
os.environ['GOOGLE_PLACES_API_KEY'] = ''

# Initialize the UserInteractionAgent
import re

def extract_locations_from_itinerary(itinerary_text):
    locations = []
    # Adjust the regex pattern based on your itinerary format
    pattern = r"\*\*\d{1,2}:\d{2}\s?[APM]{2}\s?-\s?\d{1,2}:\d{2}\s?[APM]{2}\*\*:\s(.*?)[\.\n]"
    matches = re.findall(pattern, itinerary_text)
    for match in matches:
        # Remove action verbs and extract location
        activity = match.strip()
        action_verbs = ['Visit', 'Explore', 'Admire', 'Relax at', 'Lunch at', 'Toss a coin at', 'Climb']
        for verb in action_verbs:
            if activity.startswith(verb):
                location = activity.replace(verb, '').strip()
                locations.append(location)
                break
        else:
            locations.append(activity)
    return locations
# [google]
api_key = ""


interaction_agent = UserInteractionAgent()



import streamlit as st
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#000000"
font = "sans serif"
import streamlit as st
from streamlit_chat import message as st_message


# Initialize the interaction agent
if 'interaction_agent' not in st.session_state:
    st.session_state.interaction_agent = UserInteractionAgent()

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Custom CSS (optional for styling)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)
if st.session_state.logged_in:
    st.title("🗺️ One-Day Tour Planning Assistant")
    st.write("**Maximize your time, minimize the hassle – with your personalized  AI tour planner**")

    # **Add reset button in the sidebar**
    if st.sidebar.button('🔄 Reset Chat'):
        # **Reset the conversation history and interaction agent**
        st.session_state.conversation_history = []
        st.session_state.interaction_agent = UserInteractionAgent()
        st.session_state.user_input = ''
        # Optionally, you can also reset other session state variables if needed

    # Initialize session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'interaction_agent' not in st.session_state:
        # Replace this with your actual interaction agent instance
        st.session_state.interaction_agent = UserInteractionAgent()
    if 'focus_names' not in st.session_state:
        st.session_state.focus_names = []

    # Function to handle user input
    def handle_user_input():
        user_input = st.session_state.user_input
        if user_input:
            if user_input.lower() in ['exit', 'quit']:
                # Append assistant's farewell message
                assistant_message = "Thank you for using the One-Day Tour Planning Assistant. Have a great day!"
                st.session_state.conversation_history.append({
                    'role': 'assistant',
                    'content': assistant_message
                })
                st.session_state.user_input = ''
                extract_focus_names()
            else:
                # Append user's message
                st.session_state.conversation_history.append({'role': 'user', 'content': user_input})
                # Generate assistant's response
                assistant_response = st.session_state.interaction_agent.process_user_input(user_input)
                st.session_state.conversation_history.append({'role': 'assistant', 'content': assistant_response})
                st.session_state.user_input = ''
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation_history])
    # print(conversation_text)
    prompt = f"""You are a helpful assistant.

            Extract all place names from the following conversation and return them as a Python list.{conversation_text}"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
   
    response =model.generate(
                    inputs,
                    max_new_tokens=150,
                    temperature=0.7,
                    top_p=0.95,
                    do_sample=True,
                    eos_token_id=tokenizer.eos_token_id
                )

    # Extract the content from the API response
    # extracted_list = response.choices[0].message['content'].strip()
    extracted_list = response.choices[0].message.content.strip()
    extracted_list = extracted_list[1:] 




    # Display conversation history using streamlit-chat
    for i, message in enumerate(st.session_state.conversation_history):
        if message['role'] == 'user':
            st_message(message['content'], is_user=True, key=str(i) + '_user')
        else:
            st_message(message['content'], is_user=False, key=str(i) + '_ai')

    # Input field
    st.text_input("Type your message here:", key='user_input', on_change=handle_user_input)

    # Set up your Google Maps API key
    GOOGLE_MAPS_API_KEY = ""  # Replace with your actual API key
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    def extract_focus_names():
        conversation_text = "\n".join([msg['content'] for msg in st.session_state.conversation_history])
        prompt = f"Extract all place names from the following conversation and return them as a Python list:\n\n{conversation_text}\n\nReturn only the list and nothing else."

        # Encode the prompt
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Generate output
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.95,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id
        )

        # Decode the output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the list from the output
        try:
            import ast
            import re

            # Use regex to find the list in the generated text
            list_match = re.search(r'\[.*\]', generated_text, re.DOTALL)
            if list_match:
                list_str = list_match.group(0)
                st.session_state.focus_names = ast.literal_eval(list_str)
            else:
                st.error("Could not find a list in the model's output.")
        except Exception as e:
            st.error(f"Error parsing the model's output: {e}")

    # Extract the content from the API response
    extracted_list = response.choices[0].message.content.strip()

    # Debugging line to print the raw response
    print("Raw API Response:", extracted_list)

    # Convert the response to a Python list
    try:
        if extracted_list.startswith("[") and extracted_list.endswith("]"):
            locations = eval(extracted_list)  # Use eval carefully, or prefer ast.literal_eval for safer parsing
            print("Extracted Locations:", locations)
        else:
            print("Error: Response is not formatted as a Python list.")
            locations = []
    except (SyntaxError, NameError) as e:
        print("Error parsing the response:", e)
        locations = []

    # Function to get latitude and longitude using Google Maps API
    def geocode_location(location):
        geocode_result = gmaps.geocode(location)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']
            return lat, lng
        return None

    # Function to generate an interactive map
    def generate_map(locations):
        if not locations:
            st.error("No locations available to display on the map.")
            return None

        first_location_coords = geocode_location(locations[0])
        if first_location_coords is None:
            return None

        m = folium.Map(location=first_location_coords, zoom_start=14)

        for i, location in enumerate(locations):
            coords = geocode_location(location)
            if coords:
                folium.Marker(
                    coords,
                    popup=f"{i + 1}. {location}",
                    tooltip=location
                ).add_to(m)
            else:
                # st.warning(f"Warning: '{location}' could not be found. It was skipped.")
                pass

        coordinates = [geocode_location(loc) for loc in locations if geocode_location(loc)]
        if coordinates:
            folium.PolyLine(coordinates, color="blue", weight=2.5, opacity=1).add_to(m)

        return m

    if locations:
        map_object = generate_map(locations)
        if map_object:
            st_folium(map_object, width=700, height=500)
    else:
        pass








