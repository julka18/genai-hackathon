#!/usr/bin/env python3
"""
Simple प्रchar Pipeline Test
Tests basic functionality without external API dependencies
"""

import os
import json
from pathlib import Path
from datetime import datetime

print("🚀 Testing प्रchar Pipeline - Basic Version")

def test_environment():
    """Test environment configuration"""
    print("\n1. Testing Environment...")
    
    env_file = Path(".env.local")
    if not env_file.exists():
        print("❌ .env.local not found")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv(".env.local")
        
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_channel = os.getenv("TELEGRAM_CHANNEL")
        
        if telegram_token and telegram_channel:
            print("✅ Basic Telegram configuration found")
        else:
            print("⚠️ Telegram configuration incomplete")
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            print("✅ Google API key found")
        else:
            print("⚠️ Google API key not set")
            
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_campaign_loading():
    """Test loading campaign data"""
    print("\n2. Testing Campaign Loading...")
    
    campaign_dir = Path("campaigns/kalamkari-scarf")
    if not campaign_dir.exists():
        print("❌ Sample campaign not found")
        return False
    
    metadata_file = campaign_dir / "metadata.json"
    if not metadata_file.exists():
        print("❌ Campaign metadata not found")
        return False
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"✅ Loaded campaign: {metadata.get('id')}")
        print(f"   Title (EN): {metadata.get('titles', {}).get('en')}")
        print(f"   Title (HI): {metadata.get('titles', {}).get('hi')}")
        
        # Check for assets
        assets_dir = campaign_dir / "assets"
        if assets_dir.exists():
            assets = list(assets_dir.glob("*.jpg")) + list(assets_dir.glob("*.png"))
            print(f"   Assets found: {len(assets)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Campaign loading failed: {e}")
        return False

def test_basic_imports():
    """Test basic module imports"""
    print("\n3. Testing Basic Imports...")
    
    modules_to_test = [
        ("os", "Built-in OS module"),
        ("json", "Built-in JSON module"),
        ("pathlib", "Built-in Path module"),
        ("requests", "HTTP requests"),
        ("dotenv", "Environment variables"),
        ("utilities.logger", "Custom logger"),
    ]
    
    success_count = 0
    
    for module, description in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module} - {e}")
    
    print(f"Import success rate: {success_count}/{len(modules_to_test)}")
    return success_count == len(modules_to_test)

def create_simple_caption(metadata):
    """Create a simple Instagram caption"""
    title_en = metadata.get('titles', {}).get('en', '')
    title_hi = metadata.get('titles', {}).get('hi', '')
    hashtags = metadata.get('hashtags', [])
    
    parts = []
    if title_hi and title_en:
        parts.append(f"✨ {title_hi} • {title_en}")
    elif title_en:
        parts.append(f"✨ {title_en}")
    
    parts.append("🎨 Handcrafted by Indian artisans")
    
    if hashtags:
        parts.append(" ".join(hashtags[:5]))
    
    return "\n\n".join(parts)

def test_caption_generation():
    """Test caption generation"""
    print("\n4. Testing Caption Generation...")
    
    try:
        test_metadata = {
            'titles': {'en': 'Test Product', 'hi': 'टेस्ट उत्पाद'},
            'hashtags': ['#handmade', '#artisan', '#india']
        }
        
        caption = create_simple_caption(test_metadata)
        print("✅ Caption generated:")
        print(caption)
        
        return True
        
    except Exception as e:
        print(f"❌ Caption generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*50)
    print("प्रchar BASIC PIPELINE TEST")
    print("="*50)
    
    tests = [
        test_environment,
        test_campaign_loading,
        test_basic_imports,
        test_caption_generation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All basic tests passed! Pipeline foundation is working.")
    elif passed > 0:
        print("⚠️ Some tests passed. Check failed tests above.")
    else:
        print("🚨 All tests failed. Check your setup.")
    
    print("="*50)

if __name__ == "__main__":
    main()