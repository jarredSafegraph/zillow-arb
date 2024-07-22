import json

import requests

from data.Rental import Rental
from data.RentalCollection import RentalCollection
import streamlit as st

class ZillowApiCaller():
    api_key = st.secrets["zillow_api_key"]

    def _get_props_by_page(self, page, city, state, min_price, max_price, baths_min, beds_min):
        url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
        querystring = {"location": f"{city}, {state}", "status_type": "ForRent", "rentMinPrice": f"{min_price}",
                       "rentMaxPrice": f"{max_price}", "page": page, "bathsMin": baths_min, "bathsMax": baths_min, "bedsMin": beds_min, "bedsMax": beds_min}
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        return json.loads(response.text)

    def _fetch_pages_for_city(self, city, state, min_price, max_price, baths_min, beds_min):
        try:

            num_pages = self._get_props_by_page(1, city, state, min_price, max_price, baths_min, beds_min)["totalPages"]
            json_responses = [self._get_props_by_page(page, city, state, min_price, max_price, baths_min, beds_min) for page in
                              range(1, num_pages + 1)]
            return json_responses
        except Exception as e:
            return []

    def fetch_pages_for_city(self, city, state, min_price, max_price, baths_min, beds_min):
        json_responses = self._fetch_pages_for_city(city, state, min_price, max_price,  baths_min, beds_min)
        all_props = [json_response.get("props") for json_response in json_responses]
        all_props = [props for props in all_props if props is not None]
        all_props = [prop for props in all_props for prop in props]
        return RentalCollection(rentals=[Rental.json_contructor(json_data) for json_data in all_props])
