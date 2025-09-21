"""
Firebase client for fetching user uploaded photos and data
Using Firebase Admin SDK - matches expected interface
"""

import os
import base64
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from utilities.logger import get_logger

log = get_logger("firebase_client")

class FirebaseClient:
    def __init__(self):
        self.db = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            if firebase_admin._apps:
                self.db = firestore.client()
                log.info("✅ Firebase Admin already initialized")
                return
            
            service_key_path = os.getenv('FIREBASE_SERVICE_KEY_PATH', 'serviceAccountKey.json')
            
            if os.path.exists(service_key_path):
                cred = credentials.Certificate(service_key_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                log.info(f"✅ Firebase initialized from service key: {service_key_path}")
            else:
                firebase_admin.initialize_app()
                self.db = firestore.client()
                log.info("✅ Firebase initialized with default credentials")
                
        except Exception as e:
            log.error(f"❌ Firebase initialization failed: {e}")
            self.db = None
    
    def get_user_photos_by_owner(self, owner_uid: str) -> Dict[str, Any]:
        """
        Find document by ownerUid and return photos (expected interface)
        
        Args:
            owner_uid: User's Firebase Auth UID
            
        Returns:
            Dictionary containing user data and photos
        """
        if not self.db:
            raise Exception("Firebase not initialized")
        
        # Collections to try
        collections_to_try = [
            'products', 'items', 'listings', 'campaigns', 'posts', 'documents'
        ]
        
        for collection in collections_to_try:
            try:
                log.info(f"Searching for ownerUid {owner_uid} in collection '{collection}'")
                
                query_ref = self.db.collection(collection).where('ownerUid', '==', owner_uid).limit(1)
                docs = list(query_ref.stream())
                
                if docs:
                    doc = docs[0]
                    data = doc.to_dict()
                    log.info(f"✅ Found document {doc.id} in collection '{collection}'")
                    
                    # Get media subcollection
                    media_ref = doc.reference.collection('media')
                    media_docs = list(media_ref.stream())
                    
                    photos = []
                    for media_doc in media_docs:
                        media_data = media_doc.to_dict()
                        data_field = media_data.get('data', '')
                        
                        base64_data = None
                        if data_field and data_field.startswith('data:image/'):
                            parts = data_field.split(',', 1)
                            if len(parts) == 2:
                                base64_data = parts[1]
                        
                        photos.append({
                            'id': media_doc.id,
                            'base64_data': base64_data,
                            'has_base64': bool(base64_data)
                        })
                    
                    # Return in expected format
                    result = {
                        'product_data': data,  # Expected by test_whole.py
                        'product_id': doc.id,  # Expected by test_whole.py
                        'photos': photos,
                        'photos_count': len(photos)
                    }
                    
                    log.info(f"Successfully fetched {len(photos)} photos for ownerUid {owner_uid}")
                    return result
                    
            except Exception as e:
                log.warning(f"Error searching collection '{collection}': {e}")
                continue
        
        raise Exception(f"No document found with ownerUid: {owner_uid}")
    
    def convert_photos_to_base64_list(self, photos: List[Dict]) -> List[str]:
        """
        Extract base64 strings from photos (expected interface)
        
        Args:
            photos: List of photo dictionaries
            
        Returns:
            List of base64 encoded image strings
        """
        base64_images = []
        
        for photo in photos:
            if photo.get('base64_data'):
                base64_images.append(photo['base64_data'])
        
        log.info(f"Extracted {len(base64_images)} base64 images")
        return base64_images
    
    def save_base64_images_as_files(self, base64_images: List[str], temp_dir: str = "temp_firebase") -> List[str]:
        """
        Save base64 images as temporary files (expected interface)
        
        Args:
            base64_images: List of base64 image strings
            temp_dir: Directory to save temporary files
            
        Returns:
            List of file paths
        """
        temp_path = Path(temp_dir)
        temp_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for i, base64_data in enumerate(base64_images):
            try:
                # Decode base64
                image_bytes = base64.b64decode(base64_data)
                
                # Save as temp file
                file_path = temp_path / f"firebase_image_{i+1}.png"
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                saved_files.append(str(file_path))
                log.info(f"Saved Firebase image to: {file_path}")
                
            except Exception as e:
                log.error(f"Error saving base64 image {i+1}: {e}")
                continue
        
        return saved_files


# Global instance
firebase_client = FirebaseClient()

def get_firebase_client() -> FirebaseClient:
    return firebase_client