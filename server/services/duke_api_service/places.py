# services/duke_api_service/curriculum.py
from typing import Dict, List, Optional
from .base import DukeApiServiceBase
import os
import dotenv

dotenv.load_dotenv()


class PlacesApiService(DukeApiServiceBase):
    def __init__(self, api_base_url, api_key: Optional[str] = None):
        super().__init__(api_base_url, api_key)
        # Load the api values that actually work (tested that these return data)
        self.places_values = ['dining', 'central_campus', 'dukecard', 'east_campus', 'west_campus']
        
    def get_places_by_value(self, place_value: str) -> List[Dict]:
        """
        Get places for a specific place_value (e.g gets relevant dining locations in west_campus)
        
        Args:
            place_value: The subject place value (e.g., 'east_campus')
            
        Returns:
            List of places
            
        """
        if place_value not in self.places_values:
            print('Place Value for the place Duke API invalid!')
            return []
        
        endpoint = f"places/items"

        # pass in custom params for this specific route
        params = {'tag': place_value}
        api_response = self._make_request(endpoint, params=params)

        if not api_response:
            return []

        return api_response
    
    def get_places_by_all_values(self) -> List[Dict]:
        """
        Loop through all valid places values and returns the final result across all locations and values
            
        Returns:
            List of places
            
        """
        result = []
        for place_value in self.places_values:
            try:
                places_by_value = self.get_places_by_value(place_value)
                result.extend(places_by_value)
            
            except Exception as e:
                print(f"Error when retrieving places by value {place_value}: {e}")

        return result
    
    def get_place_details_by_id(self, place_id: str) -> Dict:
        """
        Return a json object containing details about the specific place (place by id)
        """
    
        endpoint = f"places/items/index"

        # pass in custom params for this specific route
        params = {'place_id': place_id}

        api_response = self._make_request(endpoint, params=params)

        if not api_response:
            return []

        return api_response

        

def main():
    place_api_service = PlacesApiService(os.getenv('DUKE_API_BASE_URI'), os.getenv('DUKE_API_KEY'))
    place_by_value = place_api_service.get_places_by_value('east_campus')
    # places_by_values = place_api_service.get_places_by_all_values()
    place_by_id = place_api_service.get_place_details_by_id('21641')
    print(place_by_id)

if __name__=='__main__':
    main()