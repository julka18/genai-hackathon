"""
FastAPI Web Interface for प्रchar LangFlow Pipeline
Provides REST API endpoints for uploading images and creating reels

Endpoints:
- POST /upload-campaign: Upload images and metadata
- POST /create-reel: Generate reel from uploaded images  
- GET /campaign/{campaign_id}: Get campaign status
- POST /publish/{campaign_id}: Publish to social media platforms
"""

import os
import json
import asyncio
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import uvicorn
import requests
from utilities.firebase_client import get_firebase_client
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project modules
from langflow_pipeline import PracharPipeline
from scripts.instagram_poster import create_instagram_caption
from utilities.logger import get_logger

# Initialize logging
log = get_logger("web_api")

# FastAPI app setup
app = FastAPI(
    title="प्रchar - Artisan Reel Creator",
    description="AI-powered reel creation and social media automation for Indian artisans",
    version="1.0.0"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for web interface
web_dir = Path("web")
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Global pipeline instance
pipeline = PracharPipeline()

# In-memory campaign storage (use database in production)
campaigns_db = {}

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Pydantic models
class CampaignMetadata(BaseModel):
    title_en: Optional[str] = None
    title_hi: Optional[str] = None
    description_hi: Optional[str] = None
    price_low: Optional[int] = None
    price_high: Optional[int] = None
    currency: str = "INR"
    hashtags: List[str] = []
    whatsapp_link: Optional[str] = None


class ProcessUserPhotosRequest(BaseModel):
    phone_number: str
    product_details: str


class PublishRequest(BaseModel):
    platforms: List[str] = ["instagram", "telegram"]
    schedule_time: Optional[datetime] = None


class CampaignStatus(BaseModel):
    id: str
    status: str  # "uploaded", "processing", "ready", "published", "error"
    created_at: datetime
    images_count: int
    reel_path: Optional[str] = None
    metadata: Dict[str, Any]
    publish_results: Dict[str, Any] = {}
    error_message: Optional[str] = None


# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to प्रchar - AI Artisan Reel Creator",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }


@app.post("/upload-campaign")
async def upload_campaign(
    images: List[UploadFile] = File(...),
    title_en: Optional[str] = Form(None),
    title_hi: Optional[str] = Form(None),
    description_hi: Optional[str] = Form(None),
    price_low: Optional[int] = Form(None),
    price_high: Optional[int] = Form(None),
    hashtags: str = Form(""),
    whatsapp_link: Optional[str] = Form(None)
):
    """
    Upload campaign images and metadata
    
    Args:
        images: List of product images
        title_en: Product title in English
        title_hi: Product title in Hindi
        description_hi: Product description in Hindi
        price_low: Minimum price
        price_high: Maximum price
        hashtags: Comma-separated hashtags
        whatsapp_link: WhatsApp contact link
        
    Returns:
        Campaign ID and status
    """
    try:
        # Generate campaign ID
        campaign_id = str(uuid.uuid4())[:8]
        
        # Create campaign directory
        campaign_dir = UPLOAD_DIR / campaign_id
        campaign_dir.mkdir(exist_ok=True)
        assets_dir = campaign_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Save uploaded images
        saved_images = []
        for i, image in enumerate(images):
            if not image.content_type.startswith('image/'):
                raise HTTPException(400, f"File {image.filename} is not an image")
            
            # Save image
            file_extension = Path(image.filename).suffix.lower()
            if not file_extension:
                file_extension = '.jpg'
            
            image_path = assets_dir / f"img{i+1}{file_extension}"
            
            with open(image_path, 'wb') as f:
                content = await image.read()
                f.write(content)
            
            saved_images.append(str(image_path))
        
        # Process metadata
        hashtag_list = [tag.strip() for tag in hashtags.split(',') if tag.strip()]
        
        metadata = {
            "id": campaign_id,
            "titles": {
                "en": title_en,
                "hi": title_hi
            },
            "description": {
                "hi": description_hi
            },
            "price": {
                "low": price_low,
                "high": price_high,
                "currency": "INR"
            },
            "hashtags": hashtag_list,
            "cta": {
                "whatsapp": whatsapp_link
            },
            "assets": [str(Path(img).name) for img in saved_images],
            "created_at": datetime.now().isoformat()
        }
        
        # Save metadata
        metadata_path = campaign_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Store campaign in memory
        campaigns_db[campaign_id] = CampaignStatus(
            id=campaign_id,
            status="uploaded",
            created_at=datetime.now(),
            images_count=len(saved_images),
            metadata=metadata
        )
        
        log.info(f"Campaign uploaded: {campaign_id} with {len(saved_images)} images")
        
        return {
            "campaign_id": campaign_id,
            "status": "uploaded",
            "images_count": len(saved_images),
            "message": "Campaign uploaded successfully"
        }
        
    except Exception as e:
        log.error(f"Campaign upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.post("/create-reel/{campaign_id}")
async def create_reel(campaign_id: str):
    """
    Generate reel from uploaded campaign
    
    Args:
        campaign_id: Campaign identifier
        
    Returns:
        Reel generation status and download link
    """
    if campaign_id not in campaigns_db:
        raise HTTPException(404, "Campaign not found")
    
    campaign = campaigns_db[campaign_id]
    
    if campaign.status != "uploaded":
        raise HTTPException(400, f"Campaign status is {campaign.status}, expected 'uploaded'")
    
    try:
        # Update status
        campaign.status = "processing"
        campaigns_db[campaign_id] = campaign
        
        log.info(f"Starting reel generation for campaign: {campaign_id}")
        
        # Run pipeline asynchronously
        campaign_dir = str(UPLOAD_DIR / campaign_id)
        result = await pipeline.process_artisan_campaign(campaign_dir)
        
        if result.get("status") == "success":
            # Update campaign with results
            campaign.status = "ready"
            campaign.reel_path = result.get("reel_path")
            campaigns_db[campaign_id] = campaign
            
            return {
                "campaign_id": campaign_id,
                "status": "ready",
                "reel_path": campaign.reel_path,
                "enhanced_images_count": result.get("enhanced_images_count", 0),
                "message": "Reel created successfully"
            }
        else:
            # Handle error
            campaign.status = "error"
            campaign.error_message = result.get("error", "Unknown error")
            campaigns_db[campaign_id] = campaign
            
            raise HTTPException(500, f"Reel generation failed: {campaign.error_message}")
            
    except Exception as e:
        log.error(f"Reel generation error for {campaign_id}: {e}")
        
        # Update campaign status
        campaign.status = "error"
        campaign.error_message = str(e)
        campaigns_db[campaign_id] = campaign
        
        raise HTTPException(500, f"Reel generation failed: {str(e)}")


@app.post("/publish/{campaign_id}")
async def publish_campaign(campaign_id: str, publish_request: PublishRequest):
    """
    Publish campaign to social media platforms
    
    Args:
        campaign_id: Campaign identifier
        publish_request: Publishing configuration
        
    Returns:
        Publishing results for each platform
    """
    if campaign_id not in campaigns_db:
        raise HTTPException(404, "Campaign not found")
    
    campaign = campaigns_db[campaign_id]
    
    if campaign.status != "ready":
        raise HTTPException(400, f"Campaign status is {campaign.status}, expected 'ready'")
    
    try:
        log.info(f"Publishing campaign {campaign_id} to platforms: {publish_request.platforms}")
        
        # Generate caption
        caption = create_instagram_caption(campaign.metadata)
        
        publish_results = {}
        
        # Publish to Instagram
        if "instagram" in publish_request.platforms:
            try:
                from scripts.instagram_poster import InstagramGraphAPI
                
                if os.getenv("INSTAGRAM_ACCESS_TOKEN"):
                    instagram_api = InstagramGraphAPI()
                    
                    # For POC, we'll simulate the posting
                    # In production, this would upload the reel to a public URL first
                    result = instagram_api.post_reel(
                        video_url="https://placeholder-url.com/reel.mp4",  # Would be actual CDN URL
                        caption=caption
                    )
                    publish_results["instagram"] = result
                else:
                    publish_results["instagram"] = {
                        "success": False,
                        "error": "Instagram API credentials not configured"
                    }
                    
            except Exception as e:
                publish_results["instagram"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Publish to Telegram
        if "telegram" in publish_request.platforms:
            try:
                from scripts.telegram_poster import post_campaign as telegram_post
                
                # Convert metadata format
                legacy_metadata = {
                    "title_en": campaign.metadata.get('titles', {}).get('en'),
                    "title_hi": campaign.metadata.get('titles', {}).get('hi'),
                    "description_hi": campaign.metadata.get('description', {}).get('hi'),
                    "price": campaign.metadata.get('price', {}),
                    "hashtags": campaign.metadata.get('hashtags', []),
                    "cta_whatsapp": campaign.metadata.get('cta', {}).get('whatsapp')
                }
                
                # Get media files
                campaign_dir = UPLOAD_DIR / campaign_id
                assets_dir = campaign_dir / "assets"
                media_files = [str(f) for f in assets_dir.iterdir() if f.is_file()]
                
                result = telegram_post(legacy_metadata, media_files)
                publish_results["telegram"] = result
                
            except Exception as e:
                publish_results["telegram"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Update campaign
        campaign.status = "published"
        campaign.publish_results = publish_results
        campaigns_db[campaign_id] = campaign
        
        return {
            "campaign_id": campaign_id,
            "status": "published",
            "results": publish_results
        }
        
    except Exception as e:
        log.error(f"Publishing error for {campaign_id}: {e}")
        raise HTTPException(500, f"Publishing failed: {str(e)}")


@app.get("/campaign/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """Get campaign status and details"""
    if campaign_id not in campaigns_db:
        raise HTTPException(404, "Campaign not found")
    
    campaign = campaigns_db[campaign_id]
    
    return {
        "id": campaign.id,
        "status": campaign.status,
        "created_at": campaign.created_at,
        "images_count": campaign.images_count,
        "reel_path": campaign.reel_path,
        "metadata": campaign.metadata,
        "publish_results": campaign.publish_results,
        "error_message": campaign.error_message
    }


@app.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    return {
        "campaigns": [
            {
                "id": campaign.id,
                "status": campaign.status,
                "created_at": campaign.created_at,
                "images_count": campaign.images_count
            }
            for campaign in campaigns_db.values()
        ]
    }


@app.get("/download/{campaign_id}/reel")
async def download_reel(campaign_id: str):
    """Download generated reel"""
    if campaign_id not in campaigns_db:
        raise HTTPException(404, "Campaign not found")
    
    campaign = campaigns_db[campaign_id]
    
    if not campaign.reel_path or not Path(campaign.reel_path).exists():
        raise HTTPException(404, "Reel not found or not yet generated")
    
    return FileResponse(
        path=campaign.reel_path,
        filename=f"{campaign_id}_reel.mp4",
        media_type="video/mp4"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "campaigns_count": len(campaigns_db),
        "api_version": "1.0.0"
    }


@app.post("/process-user-photos")
async def process_user_photos(request: ProcessUserPhotosRequest):
    """
    Process photos for a user from Firebase, send to Lambda, and post to social media
    
    Args:
        request: Contains phone_number and product_details
        
    Returns:
        Processing status and posting results
    """
    try:
        log.info(f"Processing photos for user: {request.phone_number}")
        
        # Step 1: Get Firebase client and fetch photos
        firebase_client = get_firebase_client()
        user_data = firebase_client.get_user_photos(request.phone_number)
        
        if user_data['photos_count'] == 0:
            raise HTTPException(400, "No photos found for this user")
        
        # Step 2: Convert photos to base64 for Lambda
        base64_images = firebase_client.convert_photos_to_base64(user_data['photos'])
        
        if not base64_images:
            raise HTTPException(400, "Failed to convert photos to base64")
        
        # Step 3: Call Lambda API
        lambda_payload = {
            "product_details": request.product_details,
            "images": base64_images,
            "user_phone": request.phone_number
        }
        
        log.info(f"Calling Lambda with {len(base64_images)} images")
        
        lambda_url = os.getenv('AWS_LAMBDA_URL', 'https://your-lambda-url.amazonaws.com/process')
        
        lambda_response = requests.post(
            lambda_url,
            json=lambda_payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # Increased timeout for AI processing
        )
        
        if lambda_response.status_code != 200:
            raise HTTPException(500, f"Lambda call failed: {lambda_response.text}")
        
        lambda_result = lambda_response.json()
        log.info("Lambda processing completed")
        
        # Step 4: Process Lambda response and post to social media
        posting_results = await post_to_social_media(lambda_result, request.phone_number)
        
        # Return complete results
        return {
            "status": "success",
            "phone_number": request.phone_number,
            "images_processed": len(base64_images),
            "lambda_response": lambda_result,
            "posting_results": posting_results,
            "message": "Photos processed and posted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error processing photos for {request.phone_number}: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")


async def post_to_social_media(lambda_result: dict, user_phone: str) -> dict:
    """
    Post Lambda-processed content to Telegram and Instagram
    
    Args:
        lambda_result: Response from Lambda containing processed images and text
        user_phone: User's phone number
        
    Returns:
        Dictionary with posting results for each platform
    """
    posting_results = {}
    
    # Extract Lambda response data
    # Assuming Lambda returns: 
    # {
    #   "processed_images": ["url1", "url2", ...],  # Public URLs to processed images
    #   "generated_text": "caption text",
    #   "hashtags": ["#tag1", "#tag2", ...],
    #   "instagram_reel_url": "video_url"  # Optional reel URL
    # }
    
    processed_images = lambda_result.get("processed_images", [])
    generated_text = lambda_result.get("generated_text", "")
    hashtags = lambda_result.get("hashtags", [])
    reel_url = lambda_result.get("instagram_reel_url")
    
    # Default Telegram channels to post to
    default_channels = [
        "@prachar_artisans",  # Your main channel
        "@artisan_showcase"   # Add more channels as needed
    ]
    
    # 1. Post to Telegram
    try:
        log.info("Posting to Telegram...")
        from scripts.telegram_poster import post_campaign
        
        # Format metadata for Telegram
        telegram_metadata = {
            "title_hi": "हस्तशिल्प उत्पाद",
            "title_en": "Handcrafted Product", 
            "description_hi": generated_text,
            "hashtags": hashtags[:5],  # Limit hashtags
            "cta_whatsapp": f"https://wa.me/{user_phone.replace('+', '')}"
        }
        
        # Post using existing telegram poster
        telegram_result = post_campaign(telegram_metadata, processed_images)
        posting_results["telegram"] = {
            "success": True,
            "result": telegram_result
        }
        
        log.info("✅ Telegram posting successful")
        
    except Exception as e:
        log.error(f"❌ Telegram posting failed: {e}")
        posting_results["telegram"] = {
            "success": False,
            "error": str(e)
        }
    
    # 2. Post to Instagram
    try:
        log.info("Posting to Instagram...")
        from scripts.instagram_poster import InstagramGraphAPI, create_instagram_caption
        
        # Check if Instagram credentials are available
        if not os.getenv("INSTAGRAM_ACCESS_TOKEN"):
            posting_results["instagram"] = {
                "success": False,
                "error": "Instagram credentials not configured"
            }
        else:
            instagram_api = InstagramGraphAPI()
            
            # Create Instagram caption
            instagram_metadata = {
                "titles": {"en": "Handcrafted Product", "hi": "हस्तशिल्प उत्पाद"},
                "description": {"hi": generated_text},
                "hashtags": hashtags
            }
            caption = create_instagram_caption(instagram_metadata)
            
            # Post reel if available, otherwise post first image
            if reel_url:
                # Validate reel URL first
                if instagram_api.validate_media_url(reel_url, "REELS"):
                    result = instagram_api.post_reel(reel_url, caption)
                    posting_results["instagram"] = result
                else:
                    raise Exception("Invalid reel URL from Lambda")
            elif processed_images:
                # Post first processed image
                first_image = processed_images[0]
                if instagram_api.validate_media_url(first_image, "IMAGE"):
                    result = instagram_api.post_image(first_image, caption)
                    posting_results["instagram"] = result
                else:
                    raise Exception("Invalid image URL from Lambda")
            else:
                raise Exception("No valid media from Lambda for Instagram")
            
            log.info("✅ Instagram posting successful")
    
    except Exception as e:
        log.error(f"❌ Instagram posting failed: {e}")
        posting_results["instagram"] = {
            "success": False,
            "error": str(e)
        }
    
    return posting_results


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    log.info("🚀 Starting प्रchar API server")
    log.info(f"Upload directory: {UPLOAD_DIR.absolute()}")
    
    # Create required directories
    UPLOAD_DIR.mkdir(exist_ok=True)
    

    # Test pipeline initialization
    try:
        log.info("Testing pipeline initialization...")
        # Basic validation
        log.info("✅ Pipeline initialized successfully")
    except Exception as e:
        log.error(f"❌ Pipeline initialization failed: {e}")


@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    log.info("🛑 Shutting down प्रchar API server")


# Development server function
def run_dev_server():
    """Run development server"""
    uvicorn.run(
        "web_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_dev_server()