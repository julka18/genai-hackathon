"""
Firebase client for fetching user uploaded photos and data
"""

import os
import json
import base64
import requests
from typing import List, Dict, Any, Optional
from google.cloud import firestore
from google.oauth2 import service_account
from utilities.logger import get_logger

log = get_logger("firebase_client")

class FirebaseClient:
    def __init__(self):
        """Initialize Firebase client with credentials"""
        self.db = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Firestore client"""
        try:
            # Try to get Firebase config from environment
            firebase_config = os.getenv('FIREBASE_CONFIG')
            
            if firebase_config:
                # Parse JSON config from environment variable
                config_dict = json.loads(firebase_config)
                credentials = service_account.Credentials.from_service_account_info(config_dict)
                self.db = firestore.Client(credentials=credentials)
                log.info("✅ Firebase initialized from environment config")
            else:
                # Try default credentials (for development)
                self.db = firestore.Client()
                log.info("✅ Firebase initialized with default credentials")
                
        except Exception as e:
            log.error(f"❌ Firebase initialization failed: {e}")
            self.db = None
    
    def get_user_photos(self, phone_number: str) -> Dict[str, Any]:
        """
        Fetch user photos and metadata by phone number
        
        Args:
            phone_number: User's phone number (used as ID)
            
        Returns:
            Dictionary containing user data and photos
        """
        if not self.db:
            raise Exception("Firebase not initialized")
        
        try:
            log.info(f"Fetching photos for user: {phone_number}")
            
            # Query user document by phone number
            user_ref = self.db.collection('users').document(phone_number)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                raise Exception(f"User {phone_number} not found")
            
            user_data = user_doc.to_dict()
            log.info(f"Found user data: {list(user_data.keys())}")
            
            # Get photos from subcollection
            photos_ref = user_ref.collection('photos')
            photos_docs = photos_ref.stream()
            
            photos = []
            for photo_doc in photos_docs:
                photo_data = photo_doc.to_dict()
                photos.append({
                    'id': photo_doc.id,
                    'url': photo_data.get('url'),
                    'base64_data': photo_data.get('base64_data'),
                    'filename': photo_data.get('filename'),
                    'upload_time': photo_data.get('upload_time'),
                    'metadata': photo_data.get('metadata', {})
                })
            
            result = {
                'user_data': user_data,
                'photos': photos,
                'photos_count': len(photos)
            }
            
            log.info(f"Successfully fetched {len(photos)} photos for user {phone_number}")
            return result
            
        except Exception as e:
            log.error(f"Error fetching photos for {phone_number}: {e}")
            raise
    
    def convert_photos_to_base64(self, photos: List[Dict]) -> List[str]:
        """
        Convert photo URLs/data to base64 strings for Lambda API
        
        Args:
            photos: List of photo dictionaries
            
        Returns:
            List of base64 encoded image strings
        """
        base64_images = []
        
        for photo in photos:
            try:
                # If already base64, use it
                if photo.get('base64_data'):
                    base64_images.append(photo['base64_data'])
                    continue
                
                # If URL provided, fetch and convert
                if photo.get('url'):
                    response = requests.get(photo['url'])
                    response.raise_for_status()
                    
                    # Convert to base64
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    base64_images.append(image_base64)
                    continue
                
                log.warning(f"Photo {photo.get('id')} has no usable data")
                
            except Exception as e:
                log.error(f"Error converting photo {photo.get('id')} to base64: {e}")
                continue
        
        log.info(f"Converted {len(base64_images)} photos to base64")
        return base64_images


# Global Firebase client instance
firebase_client = FirebaseClient()

def get_firebase_client() -> FirebaseClient:
    """Get the global Firebase client instance"""
    return firebase_client