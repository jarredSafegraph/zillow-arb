from dataclasses import dataclass

import pandas as pd
import streamlit as st

from data.Rental import Rental


@dataclass
class RentalCollection:
    rentals: list[Rental]

    def to_pandas_df(self):
        try:
            df = pd.DataFrame([rental.to_dict() for rental in self.rentals if
                               rental is not None and rental.price is not None and rental.zestimate is not None and rental.latitude is not None and rental.longitude is not None])
            if (df.empty):
                return None
            df['color'] = df['Relative Value'].apply(lambda x: int(
                255 * ((x - df['Relative Value'].min()) / (df['Relative Value'].max() - df['Relative Value'].min()))
            ))
            df['color'] = df['color'].apply(lambda x: [x, 255 - x, 0, 160])
            return df
        except Exception as e:
            return None

    def filter_by_bedrooms(self, bedrooms: int):
        self.rentals = [rental for rental in self.rentals if rental.bedrooms == bedrooms]

    def filter_by_bathrooms(self, bathrooms: int):
        self.rentals = [rental for rental in self.rentals if rental.bathrooms == bathrooms]

    def get_center_of_lat_lng(self):
        try:
            mid_lat = len(self.rentals) // 2
            mid_lng = len(self.rentals) // 2
            return self.rentals[mid_lat].latitude, self.rentals[mid_lng].longitude
        except IndexError:
            return 0, 0
