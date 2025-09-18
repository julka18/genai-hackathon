"""
Video Generation Utilities for प्रchar
Creates Instagram reels from enhanced images using FFmpeg

This is a temporary implementation for POC purposes.
In production, this will be replaced with Nano Banana + Veo 3 integration.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from utilities.logger import get_logger, step

log = get_logger("video_generator")


class SimpleReelGenerator:
    """
    Simple reel generator using FFmpeg for POC
    
    Creates engaging video content from product images with:
    - Smooth transitions
    - Text overlays
    - Background music (optional)
    - Instagram-optimized 9:16 aspect ratio
    """
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "prachar_videos"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check if FFmpeg is available
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is installed and available"""
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, check=True)
            log.info("FFmpeg available for video generation")
        except (subprocess.CalledProcessError, FileNotFoundError):
            log.warning("FFmpeg not found. Video generation will be limited.")
            self.ffmpeg_available = False
        else:
            self.ffmpeg_available = True
    
    def create_product_reel(self, 
                           images: List[str], 
                           metadata: Dict[str, Any],
                           duration: int = 15,
                           output_path: Optional[str] = None) -> str:
        """
        Create an Instagram reel from product images
        
        Args:
            images: List of image file paths
            metadata: Product metadata for text overlays
            duration: Total video duration in seconds
            output_path: Output video path (auto-generated if None)
            
        Returns:
            Path to generated reel video
        """
        if not self.ffmpeg_available:
            return self._create_placeholder_video(output_path)
        
        try:
            with step("Creating product reel", items=len(images) + 2):
                # Prepare output path
                if not output_path:
                    campaign_id = metadata.get('id', 'unknown')
                    output_path = str(self.temp_dir / f"{campaign_id}_reel.mp4")
                
                # Create video from images
                reel_path = self._generate_slideshow_reel(
                    images, metadata, duration, output_path
                )
                
                log.info(f"Created reel: {reel_path}")
                return reel_path
                
        except Exception as e:
            log.error(f"Error creating reel: {e}")
            return self._create_placeholder_video(output_path)
    
    def _generate_slideshow_reel(self, 
                                images: List[str], 
                                metadata: Dict[str, Any],
                                duration: int,
                                output_path: str) -> str:
        """Generate slideshow-style reel with transitions"""
        
        # Calculate timing
        image_duration = duration / len(images)
        transition_duration = 0.5
        
        # Prepare images (ensure they exist and are valid)
        valid_images = []
        for img_path in images:
            if Path(img_path).exists():
                valid_images.append(img_path)
            else:
                log.warning(f"Image not found: {img_path}")
        
        if not valid_images:
            raise ValueError("No valid images found for reel generation")
        
        # Create filter complex for smooth transitions
        filter_parts = []
        input_parts = []
        
        for i, img_path in enumerate(valid_images):
            input_parts.extend(["-loop", "1", "-t", str(image_duration + transition_duration), 
                              "-i", img_path])
            
            # Scale and crop to 9:16 aspect ratio (1080x1920 for Instagram)
            scale_filter = f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS"
            
            if i < len(valid_images) - 1:
                # Add fade transition
                scale_filter += f",fade=t=out:st={image_duration}:d={transition_duration}"
            
            filter_parts.append(f"{scale_filter}[v{i}]")
        
        # Concatenate videos
        concat_inputs = "".join(f"[v{i}]" for i in range(len(valid_images)))
        filter_parts.append(f"{concat_inputs}concat=n={len(valid_images)}:v=1:a=0[outv]")
        
        # Build FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg", "-y",  # Overwrite output
            *input_parts,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", "30",  # 30 FPS
            "-t", str(duration),
            output_path
        ]
        
        log.info("Generating video with FFmpeg...")
        log.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(ffmpeg_cmd, 
                              capture_output=True, 
                              text=True,
                              timeout=300)  # 5 minute timeout
        
        if result.returncode != 0:
            log.error(f"FFmpeg failed: {result.stderr}")
            raise Exception(f"Video generation failed: {result.stderr}")
        
        # Verify output exists and has reasonable size
        output_file = Path(output_path)
        if not output_file.exists():
            raise Exception("Output video file was not created")
        
        file_size = output_file.stat().st_size
        if file_size < 1000:  # Less than 1KB suggests failure
            raise Exception(f"Output video file is too small: {file_size} bytes")
        
        log.info(f"Successfully created {file_size / 1024 / 1024:.1f}MB reel")
        return output_path
    
    def add_text_overlay(self, 
                        video_path: str, 
                        metadata: Dict[str, Any],
                        output_path: Optional[str] = None) -> str:
        """
        Add text overlays to video (product name, price, etc.)
        
        Args:
            video_path: Input video path
            metadata: Product metadata for text
            output_path: Output path (auto-generated if None)
            
        Returns:
            Path to video with text overlays
        """
        if not self.ffmpeg_available:
            return video_path
        
        try:
            if not output_path:
                input_file = Path(video_path)
                output_path = str(input_file.parent / f"{input_file.stem}_with_text{input_file.suffix}")
            
            # Extract text from metadata
            title_en = metadata.get('titles', {}).get('en', '')
            title_hi = metadata.get('titles', {}).get('hi', '')
            price = metadata.get('price', {})
            
            # Build text overlay filters
            text_filters = []
            
            # Main title (top of screen)
            if title_en:
                text_filters.append(
                    f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"text='{title_en}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=100:"
                    f"borderw=2:bordercolor=black"
                )
            
            # Hindi title (below English)
            if title_hi:
                y_pos = 180 if title_en else 100
                text_filters.append(
                    f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                    f"text='{title_hi}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y={y_pos}:"
                    f"borderw=2:bordercolor=black"
                )
            
            # Price (bottom of screen)
            if price and price.get('low') and price.get('high'):
                price_text = f"₹{price['low']}-₹{price['high']}"
                text_filters.append(
                    f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"text='{price_text}':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=h-150:"
                    f"borderw=2:bordercolor=black"
                )
            
            if not text_filters:
                log.info("No text overlays to add")
                return video_path
            
            # Combine filters
            filter_complex = ",".join(text_filters)
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", filter_complex,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                output_path
            ]
            
            log.info("Adding text overlays...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                log.error(f"Text overlay failed: {result.stderr}")
                return video_path  # Return original on failure
            
            log.info(f"Added text overlays to {output_path}")
            return output_path
            
        except Exception as e:
            log.error(f"Error adding text overlay: {e}")
            return video_path  # Return original on failure
    
    def _create_placeholder_video(self, output_path: Optional[str] = None) -> str:
        """Create a placeholder video when FFmpeg is not available"""
        if not output_path:
            output_path = str(self.temp_dir / "placeholder_reel.mp4")
        
        # Create a minimal placeholder file
        with open(output_path, 'wb') as f:
            f.write(b"PLACEHOLDER_REEL_VIDEO_DATA")
        
        log.info(f"Created placeholder reel: {output_path}")
        return output_path
    
    def optimize_for_instagram(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Optimize video for Instagram requirements
        
        Instagram Reels specifications:
        - Aspect ratio: 9:16 (1080x1920)
        - Duration: 15-90 seconds  
        - Frame rate: 23-60 FPS
        - Format: MP4 (H.264)
        """
        if not self.ffmpeg_available:
            return video_path
        
        try:
            if not output_path:
                input_file = Path(video_path)
                output_path = str(input_file.parent / f"{input_file.stem}_instagram{input_file.suffix}")
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-c:v", "libx264",
                "-preset", "slow",  # Better quality for final output
                "-crf", "20",  # High quality
                "-pix_fmt", "yuv420p",  # Instagram compatibility
                "-r", "30",  # 30 FPS
                "-movflags", "+faststart",  # Optimize for streaming
                output_path
            ]
            
            log.info("Optimizing for Instagram...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                log.error(f"Instagram optimization failed: {result.stderr}")
                return video_path
            
            log.info(f"Optimized for Instagram: {output_path}")
            return output_path
            
        except Exception as e:
            log.error(f"Error optimizing for Instagram: {e}")
            return video_path


def create_demo_reel(images: List[str], metadata: Dict[str, Any], output_dir: str) -> str:
    """
    Create a demo reel for testing purposes
    
    Args:
        images: List of product image paths
        metadata: Product metadata
        output_dir: Directory to save output
        
    Returns:
        Path to created reel
    """
    generator = SimpleReelGenerator()
    
    try:
        # Create base reel
        base_reel = generator.create_product_reel(
            images=images,
            metadata=metadata,
            duration=20  # 20 second reel
        )
        
        # Add text overlays
        text_reel = generator.add_text_overlay(base_reel, metadata)
        
        # Optimize for Instagram
        final_path = os.path.join(output_dir, f"{metadata.get('id', 'demo')}_reel.mp4")
        optimized_reel = generator.optimize_for_instagram(text_reel, final_path)
        
        return optimized_reel
        
    except Exception as e:
        log.error(f"Demo reel creation failed: {e}")
        # Return placeholder
        placeholder_path = os.path.join(output_dir, f"{metadata.get('id', 'demo')}_placeholder.mp4")
        return generator._create_placeholder_video(placeholder_path)


if __name__ == "__main__":
    # Test video generation
    test_images = [
        "campaigns/kalamkari-scarf/assets/img1.jpg",
        "campaigns/kalamkari-scarf/assets/img2.jpg"
    ]
    
    test_metadata = {
        "id": "test-reel",
        "titles": {
            "en": "Test Product Reel",
            "hi": "टेस्ट उत्पाद रील"
        },
        "price": {
            "low": 799,
            "high": 1199,
            "currency": "INR"
        }
    }
    
    reel_path = create_demo_reel(test_images, test_metadata, ".")
    print(f"Created demo reel: {reel_path}")