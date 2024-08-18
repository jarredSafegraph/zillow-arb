import json
from time import sleep

import backoff as backoff
import requests

from data.Rental import Rental
from data.RentalCollection import RentalCollection
import streamlit as st
from requests.exceptions import HTTPError
class ZillowApiCaller():
    api_key = st.secrets["zillow_api_key"]

    def make_query_dict(self, page, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms):
        if exact_bathrooms:
            baths_max = baths_min
        else:
            baths_max = 99
        if exact_bedrooms:
            beds_max = beds_min
        else:
            beds_max = 99
        querydict = {
            "location": f"{city}, {state}",
            "status_type": "ForRent",
            "rentMinPrice": f"{min_price}",
            "rentMaxPrice": f"{max_price}",
            "bathsMin": f"{baths_min}",
            "bedsMin": f"{beds_min}",
            "bathsMax": f"{baths_max}",
            "bedsMax": f"{beds_max}",
            "page": page,
        }
        #print(f"running for {querydict}")
        return querydict

    # Define the rate limit exception handler
    @backoff.on_exception(backoff.expo, HTTPError,
                          max_tries=5,
                          giveup=lambda e: e.response is not None and e.response.status_code != 429)
    def _get_props_by_page(self, page, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms,
                           exact_bedrooms):
        url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
        querydict = self.make_query_dict(page, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms)
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querydict)
        response.raise_for_status()  # Raise an exception for HTTP error codes
        return json.loads(response.text)


    def _fetch_pages_for_city(self, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms):
        try:
            initial_result = self._get_props_by_page(1, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms)
            num_pages = initial_result.get("totalPages")
            json_responses = [self._get_props_by_page(page, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms) for page in
                              range(1, num_pages + 1)]
            return json_responses
        except Exception as e:
            print(e)
            return []

    def fetch_pages_for_city(self, city, state, min_price, max_price, baths_min, beds_min, exact_bathrooms, exact_bedrooms):
        json_responses = self._fetch_pages_for_city(city, state, min_price, max_price,  baths_min, beds_min, exact_bathrooms, exact_bedrooms)
        all_props = [json_response.get("props") for json_response in json_responses]
        all_props = [props for props in all_props if props is not None]
        all_props = [prop for props in all_props for prop in props]
        collection = RentalCollection(rentals=[Rental.json_contructor(json_data) for json_data in all_props])
        if exact_bedrooms:
            collection.filter_by_bedrooms(beds_min)
        if exact_bathrooms:
            collection.filter_by_bathrooms(baths_min)
        return collection
