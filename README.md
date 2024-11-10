# **One-Day Tour Planning Assistant**

## **Overview**
The **One-Day Tour Planning Assistant** is a web-based application built using **Streamlit** to help users create personalized one-day itineraries. It integrates **Mistral 7B model** to analyze conversation input for popular places and **Google Maps API** for geolocation and mapping using **folium**.

## **Features**
- **User Authentication**: Secure login system with login ID and password to access the app.
- **Interactive Conversation Analysis**: Extracts place names from user conversation using **Mistral 7B**.
- **Map Visualization**: Generates interactive maps with location markers and optimal travel paths.
- **Dynamic User Interaction**: Users can input custom conversation texts and generate maps based on extracted locations.

## **Technologies Used**
- **Streamlit**: For building the web application interface.
- **Google Maps API**: For geocoding place names to obtain latitude and longitude.
- **Folium**: For creating interactive maps with location markers and routes.
- **streamlit-folium**: To integrate `folium` maps within the Streamlit application.

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
