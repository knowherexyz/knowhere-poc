import logging
import requests
import re
from typing import Optional, List, Tuple, Dict, Any

from my_proof.models.google import GoogleUserInfo
from my_proof.config import settings

def get_google_user() -> Optional[GoogleUserInfo]:
    """
    Get Google user information using the OAuth token.
    
    Returns:
        Optional[GoogleUserInfo]: User information if successful, None if failed
    """
    try:
        if not settings.GOOGLE_TOKEN:
            raise ValueError("GOOGLE_TOKEN is not set in environment")
            
        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            params={"alt": "json"},
            headers={"Authorization": f"Bearer {settings.GOOGLE_TOKEN}"}
        )
        
        response.raise_for_status()
        user_data = response.json()
        
        return GoogleUserInfo(**user_data)
        
    except Exception as e:
        logging.error(f"Failed to get Google user info: {str(e)}")
        return None

def extract_coordinates(timeline_data: Dict[str, Any], schema_type: str) -> List[Tuple[float, float]]:
    """
    Extract all coordinates from a Google Timeline JSON object.
    
    Args:
        timeline_data: The timeline JSON data
        schema_type: The schema type ('google-timeline-ios.json' or 'google-timeline-android.json')
        
    Returns:
        List[Tuple[float, float]]: List of (latitude, longitude) tuples
    """
    coordinates = set()  # Use set to avoid duplicates
    
    try:
        # iOS format
        if schema_type == 'google-timeline-ios.json':
            for entry in timeline_data:
                # Extract from timelinePath points
                if 'timelinePath' in entry:
                    for path in entry['timelinePath']:
                        if 'point' in path:
                            # Format: "geo:37.421955,-122.084058"
                            match = re.match(r'geo:(-?\d+\.\d+),(-?\d+\.\d+)', path['point'])
                            if match:
                                lat, lng = float(match.group(1)), float(match.group(2))
                                coordinates.add((lat, lng))
                
                # Extract from visit locations
                if 'visit' in entry and 'topCandidate' in entry['visit']:
                    place_loc = entry['visit']['topCandidate'].get('placeLocation')
                    if place_loc:
                        match = re.match(r'geo:(-?\d+\.\d+),(-?\d+\.\d+)', place_loc)
                        if match:
                            lat, lng = float(match.group(1)), float(match.group(2))
                            coordinates.add((lat, lng))
                            
        # Android format
        elif schema_type == 'google-timeline-android.json':
            for segment in timeline_data['semanticSegments']:
                # Extract from timelinePath
                if 'timelinePath' in segment:
                    for path in segment['timelinePath']:
                        if 'point' in path:
                            # Format: "lat,lng" or "lat°, lng°"
                            point = path['point'].replace('°', '').replace(' ', '')
                            lat, lng = map(float, point.split(','))
                            coordinates.add((lat, lng))
                
                # Extract from visit locations
                if 'visit' in segment and 'topCandidate' in segment['visit']:
                    place_loc = segment['visit']['topCandidate'].get('placeLocation', {}).get('latLng')
                    if place_loc:
                        lat, lng = map(float, place_loc.replace('°', '').replace(' ', '').split(','))
                        coordinates.add((lat, lng))
                
                # Extract from activity locations
                if 'activity' in segment:
                    activity = segment['activity']
                    for point in ['start', 'end']:
                        if point in activity and 'latLng' in activity[point]:
                            lat_lng = activity[point]['latLng']
                            lat, lng = map(float, lat_lng.replace('°', '').replace(' ', '').split(','))
                            coordinates.add((lat, lng))
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

        return list(coordinates)
        
    except Exception as e:
        logging.error(f"Failed to extract coordinates: {str(e)}")
        return []
