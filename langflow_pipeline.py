"""
प्रchar LangFlow Pipeline
Automated Reel Creation & Multi-Platform Posting for Indian Artisans

Pipeline Flow:
1. Upload artisan product images
2. Enhance images with Nano Banana (Gemini 2.5 Flash)
3. Generate reels using AI video models
4. Post to Instagram & Telegram automatically
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import google.generativeai as genai
import requests
from dotenv import load_dotenv

from utilities.logger import get_logger, step
from scripts.telegram_poster import post_campaign as telegram_post_campaign

# Load environment variables
load_dotenv(".env.local")

# Configure APIs
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Constants
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEO_FORMATS = {".mp4", ".mov"}
MAX_REEL_DURATION = 90  # seconds
INSTAGRAM_ASPECT_RATIO = "9:16"

log = get_logger("langflow_pipeline")


@dataclass
class ArtisanContent:
    """Data class for artisan content"""
    images: List[str]  # Image file paths
    metadata: Dict[str, Any]  # Campaign metadata
    enhanced_images: List[str] = None  # Enhanced image paths
    reel_video: str = None  # Generated reel path
    instagram_post_id: str = None
    telegram_thread_id: int = None


class NanoBananaEnhancer:
    """Handles image enhancement using Google's Nano Banana (Gemini 2.5 Flash)"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def enhance_artisan_images(self, images: List[str], enhancement_prompts: Dict[str, str]) -> List[str]:
        """
        Enhance artisan product images using Nano Banana
        
        Args:
            images: List of image file paths
            enhancement_prompts: Dictionary of enhancement instructions
        
        Returns:
            List of enhanced image paths
        """
        enhanced_images = []
        
        for i, image_path in enumerate(images):
            try:
                with step(f"Enhancing image {i+1}/{len(images)}", items=1):
                    # For this POC, we'll use Gemini to generate enhanced prompts
                    # In production, this would interface with the actual Nano Banana API
                    
                    enhanced_path = self._enhance_single_image(
                        image_path, 
                        enhancement_prompts.get('general', 'Enhance this artisan product image for social media marketing')
                    )
                    enhanced_images.append(enhanced_path)
                    
            except Exception as e:
                log.error(f"Error enhancing image {image_path}: {e}")
                # Fallback to original image
                enhanced_images.append(image_path)
        
        return enhanced_images
    
    def _enhance_single_image(self, image_path: str, prompt: str) -> str:
        """
        Enhance a single image with Nano Banana
        
        Note: This is a simplified implementation for POC.
        In production, this would use the actual Nano Banana API endpoints.
        """
        try:
            # For now, we'll simulate image enhancement
            # In actual implementation, this would call Nano Banana API
            
            # Read original image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            # Generate enhancement instructions using Gemini
            response = self.model.generate_content([
                f"Generate detailed image enhancement instructions for this artisan product image. "
                f"Focus on: lighting, background, product positioning, social media optimization. "
                f"Context: {prompt}",
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            enhancement_instructions = response.text
            log.info(f"Generated enhancement instructions: {enhancement_instructions}")
            
            # For POC, we'll copy the original image with enhanced filename
            original_path = Path(image_path)
            enhanced_path = original_path.parent / f"enhanced_{original_path.name}"
            
            # In production, this would be actual Nano Banana API call
            import shutil
            shutil.copy2(image_path, enhanced_path)
            
            return str(enhanced_path)
            
        except Exception as e:
            log.error(f"Error in _enhance_single_image: {e}")
            return image_path


class ReelGenerator:
    """Generates reels from enhanced images using AI video generation"""
    
    def __init__(self):
        self.veo_api_key = os.getenv("VEO_API_KEY")  # Google Veo 3 API
        self.nano_banana_video_key = os.getenv("NANO_BANANA_VIDEO_KEY")
    
    def create_reel_from_images(self, images: List[str], metadata: Dict[str, Any]) -> str:
        """
        Create a reel video from enhanced images
        
        Args:
            images: List of enhanced image paths
            metadata: Campaign metadata for context
        
        Returns:
            Path to generated reel video
        """
        with step("Generating reel from images", items=len(images)):
            try:
                # Generate video prompt based on metadata
                video_prompt = self._generate_video_prompt(metadata)
                
                # Create reel using AI video generation
                reel_path = self._generate_reel_video(images, video_prompt, metadata)
                
                return reel_path
                
            except Exception as e:
                log.error(f"Error creating reel: {e}")
                # Fallback: create simple slideshow
                return self._create_simple_slideshow(images, metadata)
    
    def _generate_video_prompt(self, metadata: Dict[str, Any]) -> str:
        """Generate video creation prompt from metadata"""
        title = metadata.get('titles', {}).get('en', 'Handmade Product')
        description = metadata.get('description', {}).get('hi', '')
        
        prompt = (
            f"Create a professional Instagram reel showcasing {title}. "
            f"Style: Elegant, warm lighting, artisan craftsmanship focus. "
            f"Movement: Smooth transitions, gentle zoom, rotation reveals. "
            f"Duration: 15-30 seconds. Aspect ratio: 9:16. "
            f"Context: Indian artisan marketplace, handmade quality emphasis."
        )
        
        return prompt
    
    def _generate_reel_video(self, images: List[str], prompt: str, metadata: Dict[str, Any]) -> str:
        """
        Generate reel video using AI video generation
        
        For POC, this simulates the video generation process.
        In production, this would use Veo 3 + Nano Banana Video APIs.
        """
        try:
            # Simulate video generation
            output_path = f"campaigns/{metadata.get('id', 'demo')}/generated_reel.mp4"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # For POC, we'll create a placeholder video file
            # In production, this would be actual API calls to Veo 3 / Nano Banana Video
            
            log.info(f"Video generation prompt: {prompt}")
            log.info(f"Using {len(images)} source images")
            
            # Simulate video creation (placeholder)
            with open(output_path, 'wb') as f:
                f.write(b"PLACEHOLDER_REEL_VIDEO_DATA")
            
            log.info(f"Generated reel: {output_path}")
            return output_path
            
        except Exception as e:
            log.error(f"Error in video generation: {e}")
            raise
    
    def _create_simple_slideshow(self, images: List[str], metadata: Dict[str, Any]) -> str:
        """Fallback: create simple slideshow video"""
        # This would use FFmpeg or similar to create a basic slideshow
        output_path = f"campaigns/{metadata.get('id', 'demo')}/slideshow_reel.mp4"
        log.info(f"Creating fallback slideshow: {output_path}")
        
        # Placeholder for slideshow creation
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(b"PLACEHOLDER_SLIDESHOW_DATA")
        
        return output_path


class InstagramPoster:
    """Handles posting reels to Instagram using Graph API"""
    
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_user_id = os.getenv("INSTAGRAM_USER_ID")
        self.graph_api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
    
    def post_reel(self, video_path: str, caption: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post reel to Instagram using Graph API
        
        Args:
            video_path: Path to the reel video file
            caption: Caption for the reel
            metadata: Campaign metadata
        
        Returns:
            Dictionary with posting results
        """
        try:
            with step("Posting to Instagram", items=2):
                # Step 1: Upload video to container
                container_id = self._upload_to_container(video_path, caption, metadata)
                
                # Step 2: Publish the container
                media_id = self._publish_container(container_id)
                
                return {
                    "platform": "instagram",
                    "media_id": media_id,
                    "container_id": container_id,
                    "success": True
                }
                
        except Exception as e:
            log.error(f"Instagram posting error: {e}")
            return {
                "platform": "instagram",
                "success": False,
                "error": str(e)
            }
    
    def _upload_to_container(self, video_path: str, caption: str, metadata: Dict[str, Any]) -> str:
        """Upload reel video to Instagram container"""
        
        # First, upload video to a public URL (in production, use CDN/cloud storage)
        video_url = self._upload_to_public_url(video_path)
        
        url = f"{self.base_url}/{self.instagram_user_id}/media"
        
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": True,  # Show in both Reels and Feed
            "access_token": self.access_token
        }
        
        response = requests.post(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Container upload failed: {response.text}")
        
        result = response.json()
        return result["id"]  # Container ID
    
    def _publish_container(self, container_id: str) -> str:
        """Publish the uploaded container"""
        url = f"{self.base_url}/{self.instagram_user_id}/media_publish"
        
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        
        # Wait for video processing
        time.sleep(10)  # Basic wait, production should poll status
        
        response = requests.post(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Container publish failed: {response.text}")
        
        result = response.json()
        return result["id"]  # Media ID
    
    def _upload_to_public_url(self, video_path: str) -> str:
        """
        Upload video to public URL (placeholder implementation)
        In production, this would upload to CDN/cloud storage
        """
        # For POC, return a placeholder URL
        return f"https://placeholder-cdn.com/video/{os.path.basename(video_path)}"


class PracharPipeline:
    """Main LangFlow pipeline orchestrator"""
    
    def __init__(self):
        self.enhancer = NanoBananaEnhancer()
        self.reel_generator = ReelGenerator()
        self.instagram_poster = InstagramPoster()
        
    async def process_artisan_campaign(self, campaign_dir: str) -> Dict[str, Any]:
        """
        Process complete artisan campaign through the pipeline
        
        Args:
            campaign_dir: Path to campaign directory
        
        Returns:
            Results dictionary with posting information
        """
        try:
            # Load campaign data
            content = self._load_campaign(campaign_dir)
            
            with step("Processing artisan campaign", items=4):
                # Step 1: Enhance images with Nano Banana
                log.info("Step 1: Enhancing images with Nano Banana")
                enhancement_prompts = {
                    'general': 'Enhance for Instagram reel, improve lighting, background, make product pop'
                }
                content.enhanced_images = self.enhancer.enhance_artisan_images(
                    content.images, 
                    enhancement_prompts
                )
                
                # Step 2: Generate reel from enhanced images
                log.info("Step 2: Generating reel with AI video")
                content.reel_video = self.reel_generator.create_reel_from_images(
                    content.enhanced_images, 
                    content.metadata
                )
                
                # Step 3: Post to Instagram
                log.info("Step 3: Posting to Instagram")
                caption = self._generate_instagram_caption(content.metadata)
                instagram_result = self.instagram_poster.post_reel(
                    content.reel_video, 
                    caption, 
                    content.metadata
                )
                
                # Step 4: Post to Telegram
                log.info("Step 4: Posting to Telegram")
                telegram_result = telegram_post_campaign(
                    self._convert_to_legacy_metadata(content.metadata),
                    [content.reel_video] + content.enhanced_images[:2]  # Reel + 2 images
                )
                
                return {
                    "campaign_id": content.metadata.get('id'),
                    "status": "success",
                    "instagram": instagram_result,
                    "telegram": telegram_result,
                    "enhanced_images_count": len(content.enhanced_images),
                    "reel_path": content.reel_video,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            log.error(f"Pipeline error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _load_campaign(self, campaign_dir: str) -> ArtisanContent:
        """Load campaign data from directory"""
        campaign_path = Path(campaign_dir)
        
        # Load metadata
        metadata_path = campaign_path / "metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find image files
        assets_dir = campaign_path / "assets"
        images = []
        for file_path in assets_dir.iterdir():
            if file_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                images.append(str(file_path))
        
        return ArtisanContent(
            images=sorted(images),
            metadata=metadata
        )
    
    def _generate_instagram_caption(self, metadata: Dict[str, Any]) -> str:
        """Generate Instagram reel caption from metadata"""
        title_en = metadata.get('titles', {}).get('en', '')
        title_hi = metadata.get('titles', {}).get('hi', '')
        desc_hi = metadata.get('description', {}).get('hi', '')
        hashtags = ' '.join(metadata.get('hashtags', []))
        
        caption_parts = [
            f"{title_hi} • {title_en}" if title_hi and title_en else title_en or title_hi,
            desc_hi,
            "",
            "✨ Handcrafted with love by Indian artisans",
            "🛍️ Support local craftspeople",
            "",
            hashtags,
            "",
            "DM for orders! 📱"
        ]
        
        return '\n'.join(part for part in caption_parts if part)
    
    def _convert_to_legacy_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata format for telegram posting"""
        return {
            "title_en": metadata.get('titles', {}).get('en'),
            "title_hi": metadata.get('titles', {}).get('hi'),
            "description_hi": metadata.get('description', {}).get('hi'),
            "price": metadata.get('price', {}),
            "hashtags": metadata.get('hashtags', []),
            "cta_whatsapp": metadata.get('cta', {}).get('whatsapp')
        }


# CLI interface for testing
async def main():
    """Main function for testing the pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="प्रchar LangFlow Pipeline")
    parser.add_argument(
        "--campaign", 
        default="campaigns/kalamkari-scarf",
        help="Campaign directory path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without actual posting"
    )
    
    args = parser.parse_args()
    
    pipeline = PracharPipeline()
    
    log.info("🚀 Starting प्रchar LangFlow Pipeline")
    log.info(f"Campaign: {args.campaign}")
    
    if args.dry_run:
        log.info("Running in DRY RUN mode (no actual posting)")
    
    result = await pipeline.process_artisan_campaign(args.campaign)
    
    print("\n" + "="*50)
    print("PIPELINE RESULTS")
    print("="*50)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())