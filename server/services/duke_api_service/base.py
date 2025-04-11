# services/duke_api_service/base.py
import requests
import json
import os
import logging
import dotenv
from typing import Dict, Any, Optional

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

class DukeApiServiceBase:
    def __init__(self, api_base_url: str, api_key: Optional[str] = None):
        self.api_base_url = api_base_url
        self.api_key = api_key
        
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None):
        """Make a request to the Duke API"""
        url = f"{self.api_base_url}/{endpoint}"
        headers = {}
        # headers["Authorization"] = f"Bearer {self.api_key}"
        headers['cache-control'] = 'max-age=0, private, must-revalidate'
        headers['content-type'] = 'application/json; charset=utf-8'
        
        # Initialize params dictionary if None
        if params is None:
            params = {}

        if self.api_key:
            params["access_token"] = self.api_key
            
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=params, headers=headers)
            # Add other methods as needed
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log error
            print(f"Error accessing Duke API: {e}")
            return None
    
    def load_metadata(self, metadata_name: str) -> Dict:
        """Load metadata from JSON file"""
        file_path = os.path.join('/home/ec2-user/websocket-handler/data/metadata', f"{metadata_name}.json")
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Log error
            print(f"Error loading metadata {metadata_name}: {e}")
            return {}