
# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction
import requests
import http.client
import json


class ActionTouristInfo(Action):

    def name(self) -> Text:
        return "action_tourist_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        tourist_attraction = tracker.get_slot('tourist_attraction')
        if tourist_attraction:
            response = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{tourist_attraction}")
            data = response.json()
            if response.status_code == 200:
                description = data.get('extract', 'Sorry, I could not find any information on that.')
                dispatcher.utter_message(text=description)
            else:
                dispatcher.utter_message(text="Sorry, I couldn't fetch information at the moment.")
        else:
            dispatcher.utter_message(text="Could you please specify the tourist attraction you want to know about?")
        
        return []

class ValidateTouristInfoForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_tourist_info_form"

    def validate_tourist_attraction(self,
                                    slot_value: Any,
                                    dispatcher: CollectingDispatcher,
                                    tracker: Tracker,
                                    domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if slot_value:
            return {"tourist_attraction": slot_value}
        else:
            dispatcher.utter_message(text="I didn't understand that. Can you please specify the tourist attraction again?")
            return {"tourist_attraction": None}

class ActionSearchPlace(Action):
    def name(self) -> str:
        return "action_search_place"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        place_type = tracker.get_slot("type")
        location = tracker.get_slot("location")
        api_key = "AIzaSyAGCdA9HLhndXlo6rLkOmpr3n9aMw8X4AQ"
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={place_type}+in+{location}&key={api_key}"
        
        response = requests.get(url)
        results = response.json().get("results", [])

        if results:
            names = [result["name"] for result in results[:5]]
            response_text = "Here are the top results: \n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(names)])
        else:
            response_text = "I couldn't find any results for your query."

        dispatcher.utter_message(text=response_text)
        return []

class ActionFetchTouristSpots(Action):

    def name(self) -> Text:
        return "action_fetch_tourist_spots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract location from the latest user message
        entities = tracker.latest_message['entities']
        location = None
        for entity in entities:
            if entity['entity'] == 'location':
                location = entity['value']
                break

        if not location:
            dispatcher.utter_message(text="Sorry, I couldn't understand the location.")
            return []

        # Use a geocoding API to convert location to coordinates (latitude and longitude)
        geocoding_api_key = "c45c2b93c8b84c5da58a9d9197da92ff"  # Replace with your OpenCage API key
        geocoding_response = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={geocoding_api_key}")

        if geocoding_response.status_code == 200:
            geocoding_data = geocoding_response.json()
            if geocoding_data['results']:
                coordinates = geocoding_data['results'][0]['geometry']
                latitude = coordinates['lat']
                longitude = coordinates['lng']

                radius = 10000  # 10 km radius
                limit = 10  # Limit to 10 results

                # Call Wikimedia API to fetch tourist spots
                response = requests.get(f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gscoord={latitude}|{longitude}&gsradius={radius}&gslimit={limit}&format=json")

                if response.status_code == 200:
                    data = response.json()
                    places = data.get("query", {}).get("geosearch", [])
                    if places:
                        spots = [place["title"] for place in places]
                        spots_list = "\n".join(spots)
                        dispatcher.utter_message(text=f"Here are some tourist spots in {location}:\n{spots_list}")
                    else:
                        dispatcher.utter_message(text=f"Sorry, I couldn't find any tourist spots in {location}.")
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't fetch tourist spots at the moment. Please try again later.")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find the coordinates for {location}.")
        else:
            dispatcher.utter_message(text="Sorry, I couldn't fetch the coordinates at the moment. Please try again later.")

        return []


class ActionGetAiResponse(Action):

    def name(self) -> Text:
        return "action_get_ai_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the user's question from the latest message
        user_question = tracker.latest_message['text']

        # Set up the connection and headers for the API call
        conn = http.client.HTTPSConnection("chatgpt-42.p.rapidapi.com")
        payload = json.dumps({
            "messages": [{"role": "user", "content": user_question}],
            "system_prompt": "",
            "temperature": 0.9,
            "top_k": 5,
            "top_p": 0.9,
            "image": "",
            "max_tokens": 256
        })
        headers = {
            'x-rapidapi-key': "6c163ad2camsh8b065d6c196f570p19c333jsn61739cf3fb36",
            'x-rapidapi-host': "chatgpt-42.p.rapidapi.com",
            'Content-Type': "application/json"
        }

        # Make the API request
        conn.request("POST", "/matag2", payload, headers)
        res = conn.getresponse()
        data = res.read()

        # Print the raw response for debugging
        print("Raw API response:", data.decode("utf-8"))

        # Parse the JSON response
        response_data = json.loads(data.decode("utf-8"))

        # Print the parsed response for debugging
        print("Parsed API response:", response_data)

        # Extract the AI response
        ai_response = response_data.get("result", "I'm sorry, I couldn't find an answer to your question.")

        # Send the AI response back to the user
        dispatcher.utter_message(text=ai_response)

        return []

