#!/usr/bin/env python3
"""
Debug script to test imports and identify issues
"""

import sys
import traceback
from pathlib import Path

print("🔍 Debugging प्रchar imports...")
print(f"Python version: {sys.version}")
print(f"Working directory: {Path.cwd()}")

# Test 1: Basic langflow_pipeline import
print("\n1. Testing langflow_pipeline import...")
try:
    import langflow_pipeline
    print("✅ langflow_pipeline module imported")
    print(f"Available items: {[item for item in dir(langflow_pipeline) if not item.startswith('_')]}")
    
    # Try to import PracharPipeline specifically
    try:
        from langflow_pipeline import PracharPipeline
        print("✅ PracharPipeline class imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import PracharPipeline: {e}")
        
except Exception as e:
    print(f"❌ Error importing langflow_pipeline: {e}")
    traceback.print_exc()

# Test 2: Instagram poster import
print("\n2. Testing instagram_poster import...")
try:
    from scripts import instagram_poster
    print("✅ instagram_poster module imported")
    print(f"Available items: {[item for item in dir(instagram_poster) if not item.startswith('_')]}")
    
    # Try specific function
    try:
        from scripts.instagram_poster import create_instagram_caption
        print("✅ create_instagram_caption function imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import create_instagram_caption: {e}")
        
except Exception as e:
    print(f"❌ Error importing instagram_poster: {e}")
    traceback.print_exc()

# Test 3: Video generator import (this one worked)
print("\n3. Testing video_generator import...")
try:
    from utilities.video_generator import SimpleReelGenerator
    print("✅ SimpleReelGenerator imported successfully")
except Exception as e:
    print(f"❌ Error importing SimpleReelGenerator: {e}")
    traceback.print_exc()

# Test 4: Check if required dependencies are available
print("\n4. Testing required dependencies...")
required_deps = [
    'google.generativeai',
    'requests', 
    'dotenv',
    'fastapi',
    'uvicorn',
    'pillow',
    'aiohttp'
]

for dep in required_deps:
    try:
        __import__(dep)
        print(f"✅ {dep}")
    except ImportError:
        print(f"❌ {dep} - missing")

print("\n🔍 Debug complete!")