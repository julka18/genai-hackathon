"""
Instagram API Integration for प्रchar
Handles posting reels and images to Instagram using the Graph API
"""

import os
import time
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from utilities.logger import get_logger, step

log = get_logger("instagram_api")


@dataclass 
class InstagramMedia:
    """Instagram media item"""
    media_type: str  # "IMAGE" or "REELS"
    url: str
    caption: Optional[str] = None
    thumbnail_offset: Optional[int] = None  # For videos, in milliseconds


class InstagramGraphAPI:
    """
    Instagram Graph API client for posting reels and media
    
    Supports:
    - Reels posting (videos up to 90 seconds)
    - Image posting 
    - Carousel posts (multiple images/videos)
    - Caption generation with hashtags
    """
    
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.user_id = os.getenv("INSTAGRAM_USER_ID")
        self.app_id = os.getenv("INSTAGRAM_APP_ID")
        self.app_secret = os.getenv("INSTAGRAM_APP_SECRET")
        
        self.api_version = "v21.0"  # Latest as of September 2025
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Validate required Instagram API credentials"""
        required_vars = ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing Instagram API credentials: {missing_vars}")
    
    def post_reel(self, video_url: str, caption: str, **options) -> Dict[str, Any]:
        """
        Post a reel to Instagram
        
        Args:
            video_url: Public URL of the video file
            caption: Caption text with hashtags
            **options: Additional options like share_to_feed, location_id, etc.
            
        Returns:
            Dictionary with posting results
        """
        try:
            with step("Posting reel to Instagram", items=2):
                log.info(f"Posting reel: {video_url[:50]}...")
                
                # Step 1: Create container
                container_id = self._create_reel_container(video_url, caption, **options)
                log.info(f"Created container: {container_id}")
                
                # Step 2: Publish container
                media_id = self._publish_container(container_id)
                log.info(f"Published reel: {media_id}")
                
                return {
                    "success": True,
                    "platform": "instagram",
                    "media_id": media_id,
                    "container_id": container_id,
                    "media_type": "REELS"
                }
                
        except Exception as e:
            log.error(f"Failed to post reel: {e}")
            return {
                "success": False,
                "platform": "instagram", 
                "error": str(e),
                "media_type": "REELS"
            }
    
    def post_image(self, image_url: str, caption: str, **options) -> Dict[str, Any]:
        """
        Post a single image to Instagram
        
        Args:
            image_url: Public URL of the image file
            caption: Caption text with hashtags
            **options: Additional options
            
        Returns:
            Dictionary with posting results  
        """
        try:
            with step("Posting image to Instagram", items=2):
                log.info(f"Posting image: {image_url[:50]}...")
                
                # Step 1: Create container
                container_id = self._create_image_container(image_url, caption, **options)
                
                # Step 2: Publish container
                media_id = self._publish_container(container_id)
                
                return {
                    "success": True,
                    "platform": "instagram",
                    "media_id": media_id,
                    "container_id": container_id,
                    "media_type": "IMAGE"
                }
                
        except Exception as e:
            log.error(f"Failed to post image: {e}")
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e),
                "media_type": "IMAGE"
            }
    
    def post_carousel(self, media_items: List[InstagramMedia], caption: str) -> Dict[str, Any]:
        """
        Post a carousel (multiple images/videos) to Instagram
        
        Args:
            media_items: List of InstagramMedia objects
            caption: Caption for the carousel
            
        Returns:
            Dictionary with posting results
        """
        try:
            if len(media_items) > 10:
                raise ValueError("Instagram carousels support maximum 10 items")
            
            with step("Posting carousel to Instagram", items=len(media_items) + 1):
                # Create containers for each media item
                container_ids = []
                for i, media in enumerate(media_items):
                    log.info(f"Creating container {i+1}/{len(media_items)}")
                    
                    if media.media_type == "IMAGE":
                        container_id = self._create_image_container(
                            media.url, 
                            caption if i == 0 else None  # Only first item gets caption
                        )
                    elif media.media_type == "REELS":
                        container_id = self._create_reel_container(
                            media.url,
                            caption if i == 0 else None,
                            thumb_offset=media.thumbnail_offset
                        )
                    
                    container_ids.append(container_id)
                
                # Create carousel container
                carousel_id = self._create_carousel_container(container_ids, caption)
                
                # Publish carousel
                media_id = self._publish_container(carousel_id)
                
                return {
                    "success": True,
                    "platform": "instagram",
                    "media_id": media_id,
                    "carousel_id": carousel_id,
                    "container_ids": container_ids,
                    "media_type": "CAROUSEL"
                }
                
        except Exception as e:
            log.error(f"Failed to post carousel: {e}")
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e),
                "media_type": "CAROUSEL"
            }
    
    def _create_reel_container(self, video_url: str, caption: str, **options) -> str:
        """Create a reel container"""
        url = f"{self.base_url}/{self.user_id}/media"
        
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption or "",
            "access_token": self.access_token
        }
        
        # Add optional parameters
        if options.get("share_to_feed", True):
            params["share_to_feed"] = "true"
        
        if options.get("location_id"):
            params["location_id"] = options["location_id"]
            
        if options.get("thumb_offset"):
            params["thumb_offset"] = options["thumb_offset"]
        
        response = requests.post(url, params=params, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Container creation failed: {response.status_code} {response.text}")
        
        return response.json()["id"]
    
    def _create_image_container(self, image_url: str, caption: str, **options) -> str:
        """Create an image container"""
        url = f"{self.base_url}/{self.user_id}/media"
        
        params = {
            "image_url": image_url,
            "caption": caption or "",
            "access_token": self.access_token
        }
        
        if options.get("location_id"):
            params["location_id"] = options["location_id"]
        
        response = requests.post(url, params=params, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Image container creation failed: {response.status_code} {response.text}")
        
        return response.json()["id"]
    
    def _create_carousel_container(self, container_ids: List[str], caption: str) -> str:
        """Create a carousel container from individual containers"""
        url = f"{self.base_url}/{self.user_id}/media"
        
        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(container_ids),
            "caption": caption or "",
            "access_token": self.access_token
        }
        
        response = requests.post(url, params=params, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Carousel creation failed: {response.status_code} {response.text}")
        
        return response.json()["id"]
    
    def _publish_container(self, container_id: str, max_retries: int = 5) -> str:
        """
        Publish a container with retry logic
        
        Args:
            container_id: The container ID to publish
            max_retries: Maximum number of retries if video is still processing
            
        Returns:
            Published media ID
        """
        url = f"{self.base_url}/{self.user_id}/media_publish"
        
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        
        # Retry logic for video processing
        for attempt in range(max_retries):
            try:
                # Wait before publishing (videos need processing time)
                if attempt > 0:
                    wait_time = min(10 * (2 ** attempt), 60)  # Exponential backoff, max 60s
                    log.info(f"Waiting {wait_time}s for media processing (attempt {attempt + 1})")
                    time.sleep(wait_time)
                elif container_id:
                    time.sleep(5)  # Always wait a bit for initial processing
                
                response = requests.post(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return result["id"]
                elif response.status_code == 400 and "not finished processing" in response.text.lower():
                    if attempt < max_retries - 1:
                        log.warning(f"Media still processing, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    else:
                        raise Exception(f"Media processing timeout after {max_retries} attempts")
                else:
                    raise Exception(f"Publishing failed: {response.status_code} {response.text}")
                    
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    log.warning(f"Request failed, retrying... ({attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    raise Exception(f"Request failed after {max_retries} attempts: {e}")
        
        raise Exception(f"Failed to publish after {max_retries} attempts")
    
    def get_media_insights(self, media_id: str) -> Dict[str, Any]:
        """
        Get insights/metrics for posted media
        
        Args:
            media_id: The Instagram media ID
            
        Returns:
            Dictionary with engagement metrics
        """
        try:
            url = f"{self.base_url}/{media_id}/insights"
            
            # Metrics available for reels and images  
            metrics = [
                "likes", "comments", "shares", "saves", "reach", 
                "impressions", "plays", "profile_visits"
            ]
            
            params = {
                "metric": ",".join(metrics),
                "access_token": self.access_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                log.warning(f"Could not fetch insights: {response.status_code} {response.text}")
                return {"error": "Could not fetch insights"}
                
        except Exception as e:
            log.error(f"Error fetching insights: {e}")
            return {"error": str(e)}
    
    def validate_media_url(self, url: str, media_type: str = "REELS") -> bool:
        """
        Validate that a media URL meets Instagram requirements
        
        Args:
            url: Public URL of the media file
            media_type: "REELS" or "IMAGE"
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            response = requests.head(url, timeout=10)
            
            if response.status_code != 200:
                log.error(f"Media URL not accessible: {response.status_code}")
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            
            if media_type == "REELS":
                valid_types = ['video/mp4', 'video/quicktime', 'video/mov']
                if not any(vtype in content_type for vtype in valid_types):
                    log.error(f"Invalid video content type: {content_type}")
                    return False
            elif media_type == "IMAGE":
                valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
                if not any(vtype in content_type for vtype in valid_types):
                    log.error(f"Invalid image content type: {content_type}")
                    return False
            
            # Check file size (Instagram limits)
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                max_size = 1000 if media_type == "REELS" else 30  # MB
                
                if size_mb > max_size:
                    log.error(f"File too large: {size_mb:.1f}MB (max {max_size}MB)")
                    return False
            
            return True
            
        except Exception as e:
            log.error(f"Error validating media URL: {e}")
            return False


# Example usage functions
def create_instagram_caption(metadata: Dict[str, Any]) -> str:
    """Generate Instagram-optimized caption from metadata"""
    title_en = metadata.get('titles', {}).get('en', '')
    title_hi = metadata.get('titles', {}).get('hi', '')
    desc_hi = metadata.get('description', {}).get('hi', '')
    hashtags = metadata.get('hashtags', [])
    
    # Build caption components
    parts = []
    
    # Title line
    if title_hi and title_en:
        parts.append(f"✨ {title_hi} • {title_en}")
    elif title_en:
        parts.append(f"✨ {title_en}")
    elif title_hi:
        parts.append(f"✨ {title_hi}")
    
    # Description
    if desc_hi:
        parts.append(f"\n{desc_hi}")
    
    # Artisan branding
    parts.extend([
        "\n🎨 Handcrafted with love by Indian artisans",
        "🛍️ Support local craftspeople & traditional art",
        "🌱 Sustainable • Authentic • Unique"
    ])
    
    # Hashtags (Instagram recommends 3-5 relevant hashtags)
    if hashtags:
        hashtag_line = " ".join(hashtags[:5])  # Limit to 5 most relevant
        parts.append(f"\n\n{hashtag_line}")
    
    # Call to action
    parts.append("\n\n📱 DM for orders & custom designs!")
    
    return "".join(parts)


# Testing function
def test_instagram_api():
    """Test Instagram API integration"""
    try:
        api = InstagramGraphAPI()
        log.info("Instagram API credentials validated successfully!")
        
        # Test with placeholder URLs (won't actually post)
        test_video = "https://example.com/test-reel.mp4"
        test_caption = create_instagram_caption({
            'titles': {'en': 'Test Reel', 'hi': 'टेस्ट रील'},
            'description': {'hi': 'यह एक परीक्षण है'},
            'hashtags': ['#test', '#prachar', '#artisan']
        })
        
        log.info(f"Generated caption: {test_caption}")
        log.info("Instagram API integration ready!")
        
        return True
        
    except Exception as e:
        log.error(f"Instagram API test failed: {e}")
        return False


if __name__ == "__main__":
    test_instagram_api()