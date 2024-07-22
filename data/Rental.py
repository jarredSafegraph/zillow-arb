from dataclasses import dataclass

@dataclass
class Rental:
    address: str
    unit: str
    price: float
    bedrooms: int
    bathrooms: int
    zestimate: int
    days_on_zillow: int
    latitude: float
    longitude: float
    size: int = 35
    relative_value: float = 0


    def __post_init__(self):
        self.relative_value = self.compute_relative_value()

    @staticmethod
    def json_contructor(json_data):
        def safe_get_field(json_data, field):
            if field in json_data:
                return json_data[field]
            else:
                return None
        return Rental(
            address=json_data["address"],
            unit=safe_get_field(json_data, "unit"),
            price=safe_get_field(json_data, "price"),
            bedrooms=safe_get_field(json_data, "bedrooms"),
            bathrooms=safe_get_field(json_data, "bathrooms"),
            zestimate=safe_get_field(json_data, "rentZestimate"),
            days_on_zillow=safe_get_field(json_data, "daysOnZillow"),
            latitude=safe_get_field(json_data, "latitude"),
            longitude=safe_get_field(json_data, "longitude")
        )

    def compute_relative_value(self) -> float:
        def safe_int(to_convert):
            if to_convert is None:
                return 0
            try:
                return int(to_convert)
            except ValueError:
                return 0
        return safe_int(self.price) - safe_int(self.zestimate)

    def set_sze(self, size: int):
        self.size = size

    def to_dict(self):
        return {
            "Address": self.address,
            "Unit": self.unit,
            "Price": self.price,
            "Bedrooms": self.bedrooms,
            "Bathrooms": self.bathrooms,
            "Zestimate": self.zestimate,
            "Days on Zillow": self.days_on_zillow,
            "Relative Value": self.relative_value,
            "Latitude": self.latitude,
            "Longitude": self.longitude,
            "Size": self.size
        }