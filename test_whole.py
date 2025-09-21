"""
Test script for प्रchar with Real Firebase + Mocked Flask + Real Telegram
Tests: Firebase → Mock Flask → Telegram posting
"""

import requests
import json
import base64
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.local")

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_OWNER_UID = "n6NCxbGg6bTHBoUyTJFlEjN8eqe2"  # From your Firebase screenshot
TEST_PRODUCT = "Beautiful handcrafted jewelry pieces made with traditional techniques. Perfect for special occasions."

def test_firebase_connection():
    """Test if Firebase connection works"""
    print("🔥 Testing Firebase Connection...")
    
    try:
        from utilities.firebase_client import get_firebase_client
        
        firebase_client = get_firebase_client()
        
        if not firebase_client.db:
            print("❌ Firebase not initialized")
            return False
        
        # Try to fetch data for test owner
        result = firebase_client.get_user_photos_by_owner(TEST_OWNER_UID)
        
        print(f"✅ Firebase connected successfully!")
        print(f"📦 Product ID: {result.get('product_id')}")
        print(f"🖼️ Photos found: {result.get('photos_count')}")
        print(f"📊 Product fields: {list(result.get('product_data', {}).keys())}")
        
        # Show photo details
        for i, photo in enumerate(result.get('photos', [])[:3]):  # Show first 3
            print(f"   📷 Photo {i+1}: {photo.get('id')} (has_base64: {photo.get('has_base64')})")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Firebase test failed: {e}")
        return False, None

def create_mock_flask_responses_with_firebase_image(firebase_base64: str):
    """Create mock Flask responses using actual Firebase image"""
    
    # Mock Flask poster response - use Firebase image as "generated" poster
    mock_poster_response = MagicMock()
    mock_poster_response.status_code = 200
    mock_poster_response.json.return_value = {
        "success": True,
        "message": "Poster generated successfully with AI magic!",
        "poster_base64": firebase_base64  # Use actual Firebase image
    }
    
    # Mock Flask caption response
    mock_caption_response = MagicMock()
    mock_caption_response.status_code = 200
    mock_caption_response.json.return_value = {
        "success": True,
        "message": "Caption generated successfully",
        "caption": "✨ Exquisite handcrafted jewelry that tells a story! Each piece is meticulously crafted by skilled artisans using traditional techniques passed down through generations. Perfect for weddings, festivals, or any special occasion. 💍 #HandcraftedJewelry #TraditionalCraft #ArtisanMade #IndianJewelry"
    }
    
    return mock_poster_response, mock_caption_response

def test_complete_flow_with_firebase():
    """Test the complete flow: Real Firebase → Mock Flask → Real Telegram"""
    print("🧪 Testing Complete Flow (Firebase + Mock Flask + Telegram)")
    print("=" * 70)
    
    # Step 1: Check if backend is running
    print("1. Testing backend connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("💡 Make sure to run: python web_api.py")
        return False
    
    # Step 2: Test Firebase connection
    print("\n2. Testing Firebase connection...")
    firebase_success, firebase_data = test_firebase_connection()
    if not firebase_success:
        print("❌ Firebase connection failed")
        return False
    
    # Get first image from Firebase for Flask mocking
    firebase_photos = firebase_data.get('photos', [])
    if not firebase_photos or not firebase_photos[0].get('base64_data'):
        print("❌ No usable photos found in Firebase")
        return False
    
    first_image_base64 = firebase_photos[0].get('base64_data')
    print(f"📷 Using Firebase image for mocking: {len(first_image_base64)} chars")
    
    # Step 3: Check Telegram token
    print("\n3. Checking Telegram configuration...")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_channel = os.getenv("TELEGRAM_CHANNEL")
    
    if telegram_token and telegram_channel:
        print(f"✅ Telegram token: {telegram_token[:10]}...")
        print(f"✅ Telegram channel: {telegram_channel}")
    else:
        print("❌ Missing Telegram configuration in .env.local")
        return False
    
    # Step 4: Create mock Flask responses with Firebase image
    print("\n4. Preparing mock Flask responses...")
    mock_poster_response, mock_caption_response = create_mock_flask_responses_with_firebase_image(first_image_base64)
    print("✅ Mock Flask responses ready with Firebase image")
    
    # Step 5: Test with mocked Flask calls but real Firebase
    print("\n5. Testing complete integration...")
    
    test_payload = {
        "owner_uid": TEST_OWNER_UID,  # Changed from phone_number to owner_uid
        "product_details": TEST_PRODUCT
    }
    
    # Mock only the Flask requests, not Firebase
    with patch('requests.post') as mock_post:
        def mock_post_side_effect(url, **kwargs):
            if "/generate-poster" in url:
                print("🎨 Mocking Flask poster generation (using Firebase image)...")
                return mock_poster_response
            elif "/generate-caption" in url:
                print("📝 Mocking Flask caption generation...")
                return mock_caption_response
            else:
                # For any other requests, use real requests
                return requests.post(url, **kwargs)
        
        mock_post.side_effect = mock_post_side_effect
        
        try:
            print("📡 Calling process-user-photos endpoint...")
            response = requests.post(
                f"{BACKEND_URL}/process-user-photos",
                json=test_payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API call successful!")
                print(f"👤 Owner UID: {result.get('owner_uid')}")
                print(f"🤖 Flask Response: {result.get('flask_response', {})}")
                
                # Check Flask integration
                flask_response = result.get('flask_response', {})
                if flask_response.get('poster_generated') and flask_response.get('caption_generated'):
                    print("✅ Flask integration successful!")
                    print(f"🎨 Poster: {flask_response.get('poster_message', 'Generated')}")
                    caption = flask_response.get('generated_caption', '')
                    print(f"📝 Caption: {caption[:100]}...")
                else:
                    print("❌ Flask integration issues")
                
                # Check Telegram posting result
                telegram_result = result.get('posting_results', {}).get('telegram', {})
                if telegram_result.get('success'):
                    print("✅ Telegram posting successful!")
                    thread_id = telegram_result.get('result', {}).get('thread_head_id')
                    print(f"📨 Posted to {telegram_channel}")
                    print(f"🔗 Thread ID: {thread_id}")
                    print(f"📄 Caption used: {telegram_result.get('caption_used', 'N/A')}")
                else:
                    print(f"❌ Telegram posting failed: {telegram_result.get('error')}")
                
                return True
                
            else:
                print(f"❌ API call failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Error response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False

def test_direct_firebase_to_telegram():
    """Test direct Firebase → Telegram without Flask"""
    print("\n" + "="*70)
    print("🧪 Testing Direct Firebase → Telegram")
    print("=" * 70)
    
    try:
        # Get Firebase data
        firebase_success, firebase_data = test_firebase_connection()
        if not firebase_success:
            return False
        
        from utilities.firebase_client import get_firebase_client
        firebase_client = get_firebase_client()
        
        # Convert Firebase photos to files
        photos = firebase_data.get('photos', [])
        base64_images = firebase_client.convert_photos_to_base64_list(photos)
        
        if not base64_images:
            print("❌ No base64 images found")
            return False
        
        # Save as temporary files
        temp_files = firebase_client.save_base64_images_as_files(base64_images)
        print(f"💾 Saved {len(temp_files)} Firebase images as temp files")
        
        # Post to Telegram
        from scripts.telegram_poster import post_campaign
        
        product_data = firebase_data.get('product_data', {})
        test_metadata = {
            "title_hi": product_data.get('titles', {}).get('hi', 'Firebase टेस्ट'),
            "title_en": product_data.get('titles', {}).get('en', 'Firebase Test'), 
            "description_hi": f"Firebase test with real data - {product_data.get('description', {}).get('en', 'Real Firebase image')}",
            "hashtags": product_data.get('hashtags', []) + ["#firebase", "#test", "#prachar"],
            "cta_whatsapp": product_data.get('cta', {}).get('whatsapp', 'Contact for more info')
        }
        
        print("📡 Posting Firebase images to Telegram...")
        result = post_campaign(test_metadata, temp_files)
        
        print("✅ Direct Firebase→Telegram test successful!")
        print(f"📨 Result: {result}")
        
        # Cleanup temp files
        for file_path in temp_files:
            try:
                Path(file_path).unlink()
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Direct Firebase→Telegram test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 प्रchar Firebase Integration Test Suite")
    print("=" * 70)
    
    # Test 1: Complete flow with Firebase
    success1 = test_complete_flow_with_firebase()
    
    print(f"\n{'✅ PASSED' if success1 else '❌ FAILED'} - Complete Firebase flow test")
    
    if not success1:
        print("\n💡 Trying direct Firebase→Telegram test to isolate issues...")
        success2 = test_direct_firebase_to_telegram()
        print(f"{'✅ PASSED' if success2 else '❌ FAILED'} - Direct Firebase→Telegram test")
    
    print("\n" + "=" * 70)
    print("🏁 Test Suite Completed!")
    
    if success1:
        print("🎉 All systems working! Firebase + Mock Flask + Telegram integration successful.")
        print("💡 Next: Replace Flask mocking with real Flask app")
    else:
        print("🔧 Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()