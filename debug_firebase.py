"""
Debug Firebase by querying ownerUid directly
"""

import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv(".env.local")

def find_document_by_owner_uid(owner_uid: str):
    """Find document by querying ownerUid across collections"""
    print(f"🔍 Searching for documents with ownerUid: {owner_uid}")
    print("=" * 60)
    
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            service_key_path = os.getenv('FIREBASE_SERVICE_KEY_PATH', 'serviceAccountKey.json')
            cred = credentials.Certificate(service_key_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("✅ Firebase connected")

        docs = list(db.collection("media").limit(1).stream())
        print("------------------------Reached----------------------")
        for doc in docs:
            print(doc.id, doc.to_dict().keys())
        
        # Try common collection names
        common_collections = ['products']
        
        for collection_name in common_collections:
            try:
                print(f"\n📂 Searching in collection: '{collection_name}'...")
                
                # Query by ownerUid
                query_ref = db.collection(collection_name).where('ownerUid', '==', owner_uid)
                docs = list(query_ref.stream())
                
                if docs:
                    print(f"   ✅ Found {len(docs)} document(s)!")
                    
                    for i, doc in enumerate(docs):
                        data = doc.to_dict()
                        print(f"\n   📄 Document {i+1}: {doc.id}")
                        print(f"      Fields: {list(data.keys())}")
                        
                        # Check for media subcollection
                        media_ref = doc.reference.collection('media')
                        media_docs = list(media_ref.stream())
                        
                        print(f"      📷 Media subcollection: {len(media_docs)} documents")
                        
                        if media_docs:
                            for j, media_doc in enumerate(media_docs):
                                media_data = media_doc.to_dict()
                                data_field = media_data.get('data', '')
                                has_base64 = data_field.startswith('data:image/')
                                size = len(data_field) if data_field else 0
                                print(f"         Media {j+1}: {media_doc.id}")
                                print(f"         Has base64: {has_base64}")
                                print(f"         Data size: {size} chars")
                                if data_field:
                                    print(f"         Preview: {data_field[:50]}...")
                    
                    return collection_name, docs[0]  # Return collection name and first doc
                else:
                    print(f"   ❌ No documents found")
                    
            except Exception as e:
                print(f"   ❌ Error searching {collection_name}: {e}")
        
        print(f"\n❌ No documents found with ownerUid: {owner_uid}")
        return None, None
        
    except Exception as e:
        print(f"❌ Firebase debug failed: {e}")
        return None, None

def test_media_extraction(collection_name: str, owner_uid: str):
    """Test extracting media from found document"""
    print(f"\n🧪 Testing media extraction from '{collection_name}'")
    print("=" * 60)
    
    try:
        db = firestore.client()
        
        # Get document by ownerUid
        query_ref = db.collection(collection_name).where('ownerUid', '==', owner_uid).limit(1)
        docs = list(query_ref.stream())
        
        if not docs:
            print("❌ Document not found")
            return False
        
        doc = docs[0]
        print(f"📄 Document: {doc.id}")
        
        # Get media
        media_ref = doc.reference.collection('media')
        media_docs = list(media_ref.stream())
        
        print(f"📷 Found {len(media_docs)} media documents")
        
        base64_images = []
        
        for media_doc in media_docs:
            media_data = media_doc.to_dict()
            data_field = media_data.get('data', '')
            
            if data_field and data_field.startswith('data:image/'):
                # Extract base64 part
                parts = data_field.split(',', 1)
                if len(parts) == 2:
                    base64_data = parts[1]
                    base64_images.append(base64_data)
                    print(f"   ✅ Extracted base64 from {media_doc.id}: {len(base64_data)} chars")
                else:
                    print(f"   ❌ Invalid data format in {media_doc.id}")
            else:
                print(f"   ❌ No valid base64 data in {media_doc.id}")
        
        print(f"\n🎯 Total base64 images extracted: {len(base64_images)}")
        
        # Test saving one image
        if base64_images:
            try:
                import base64
                from pathlib import Path
                
                # Save first image as test
                test_path = Path("test_firebase_image.png")
                image_bytes = base64.b64decode(base64_images[0])
                
                with open(test_path, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"✅ Test image saved to: {test_path} ({len(image_bytes)} bytes)")
                return True
                
            except Exception as e:
                print(f"❌ Error saving test image: {e}")
                return False
        
        return len(base64_images) > 0
        
    except Exception as e:
        print(f"❌ Media extraction test failed: {e}")
        return False

if __name__ == "__main__":
    test_owner_uid = "n6NCxbGg6bTHBoUyTJFlEjN8eqe2"
    
    # Find the document
    collection_name, found_doc = find_document_by_owner_uid(test_owner_uid)
    
    if collection_name and found_doc:
        print(f"\n🎉 SUCCESS! Found document in collection: '{collection_name}'")
        
        # Test media extraction
        success = test_media_extraction(collection_name, test_owner_uid)
        
        if success:
            print(f"\n✅ Everything working! Use collection: '{collection_name}'")
            print(f"💡 Update firebase_client.py to use db.collection('{collection_name}')")
        else:
            print(f"\n❌ Media extraction failed")
    else:
        print(f"\n❌ Could not find document with ownerUid: {test_owner_uid}")
        print(f"💡 Double-check the ownerUid value or Firebase permissions")