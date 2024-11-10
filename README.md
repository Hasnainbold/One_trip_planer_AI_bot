# **One-Day Tour Planning Assistant**
![App Screenshot](https://github.com/Hasnainbold/One_trip_planer_AI_bot/blob/main/image1.png?raw=true)

## **Overview**
The **One-Day Tour Planning Assistant** is a web-based application built using **Streamlit** to help users create personalized one-day itineraries. It integrates **Mistral 7B model** to analyze conversation input for popular places and **Google Maps API** for geolocation and mapping using **folium**.

## **Features**
- **User Authentication**: Secure login system with login ID and password to access the app.
- **Interactive Conversation Analysis**: Extracts place names from user conversation using **Mistral 7B**.
- **Map Visualization**: Generates interactive maps with location markers and optimal travel paths.
- **Dynamic User Interaction**: Users can input custom conversation texts and generate maps based on extracted locations.

## Technologies Used

- **Streamlit**: Framework for building the interactive web interface.
- **Google Maps API**: Provides geolocation services to convert place names into latitude and longitude.
- **Folium**: Library for creating interactive maps.
- **streamlit-folium**: Integrates `folium` maps with the Streamlit application.
- **Neo4j**: Used as a vector database for efficient storage and retrieval of structured and unstructured data to enhance data relationships and querying capabilities.
- **Agents**:
  - **Interaction Agent**: Handles user interactions and processes user input to generate appropriate responses.
  - **Optimization Agent**: Optimizes the itinerary based on user preferences, such as budget and time constraints.
  - **Memory Agent**: Maintains session data to track user inputs and preserve context for continuous interaction.
  - **Weather Agent**: Fetches and provides real-time weather information for the chosen locations, helping users plan their day more effectively.
  - **News Agent**: Retrieves relevant news and updates related to the user's chosen destinations or general topics of interest to provide informative context.
  - **Task-specific Agents**: Custom agents designed to handle specific tasks, such as data retrieval, API integration, and analysis.


## **Installation**
Follow these steps to set up the project locally:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/one-day-tour-planning-assistant.git
   cd one-day-tour-planning-assistant

2. pip install streamlit openai folium streamlit-folium googlemaps
## Technologies Used

- **Streamlit**: Framework for building the interactive web interface.
- **OpenAI API**: Used for natural language processing to extract place names from user input.
- **Google Maps API**: Provides geolocation services to convert place names into latitude and longitude.
- **Folium**: Library for creating interactive maps.
- **streamlit-folium**: Integrates `folium` maps with the Streamlit application.
