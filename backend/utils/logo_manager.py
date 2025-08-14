#!/usr/bin/env python3
"""
Logo management utility for storing and analyzing logos.
Handles logo storage, color extraction, and analysis for reports.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PIL import Image
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)


class LogoManager:
    def __init__(self, base_dir: str = None):
        """Initialize LogoManager with base directory for logo storage."""
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), "temp_logos")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
    def store_logo(self, session_id: str, logo_data: str, logo_filename: str) -> Dict[str, Any]:
        """
        Store a logo for a session and analyze it.
        
        Args:
            session_id: The session identifier
            logo_data: Base64 encoded logo image data
            logo_filename: Original filename of the logo
            
        Returns:
            Dict containing storage path and analysis results
        """
        try:
            # Create session directory
            session_dir = os.path.join(self.base_dir, session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            # Decode base64 data and save logo
            import base64
            if logo_data.startswith('data:image'):
                # Remove data URL prefix
                logo_data = logo_data.split(',')[1]
            
            logo_bytes = base64.b64decode(logo_data)
            logo_path = os.path.join(session_dir, logo_filename)
            
            with open(logo_path, 'wb') as f:
                f.write(logo_bytes)
            
            # Analyze the logo
            analysis = self._analyze_logo(logo_path)
            
            # Store analysis metadata
            metadata = {
                'session_id': session_id,
                'logo_filename': logo_filename,
                'logo_path': logo_path,
                'stored_at': datetime.now().isoformat(),
                'analysis': analysis
            }
            
            metadata_path = os.path.join(session_dir, 'logo_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Logo stored and analyzed for session {session_id}: {logo_filename}")
            return {
                'success': True,
                'logo_path': logo_path,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error storing logo for session {session_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_logo_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve logo analysis for a session."""
        try:
            metadata_path = os.path.join(self.base_dir, session_id, 'logo_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error retrieving logo analysis for session {session_id}: {e}")
            return None
    
    def _analyze_logo(self, logo_path: str) -> Dict[str, Any]:
        """
        Analyze a logo image to extract colors and other properties.
        
        Args:
            logo_path: Path to the logo image file
            
        Returns:
            Dict containing analysis results
        """
        try:
            with Image.open(logo_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get image dimensions
                width, height = img.size
                
                # Convert to numpy array for analysis
                img_array = np.array(img)
                
                # Extract dominant colors
                dominant_colors = self._extract_dominant_colors(img_array)
                
                # Analyze color distribution
                color_analysis = self._analyze_color_distribution(img_array)
                
                # Detect if logo is primarily dark or light
                brightness = self._analyze_brightness(img_array)
                
                return {
                    'dimensions': {'width': width, 'height': height},
                    'dominant_colors': dominant_colors,
                    'color_distribution': color_analysis,
                    'brightness': brightness,
                    'aspect_ratio': round(width / height, 2) if height > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error analyzing logo {logo_path}: {e}")
            return {
                'error': str(e),
                'dimensions': {'width': 0, 'height': 0},
                'dominant_colors': [],
                'color_distribution': {},
                'brightness': 'unknown',
                'aspect_ratio': 0
            }
    
    def _extract_dominant_colors(self, img_array: np.ndarray, num_colors: int = 5) -> List[Dict[str, Any]]:
        """Extract dominant colors from the image."""
        try:
            # Reshape image to 2D array of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            # Sample pixels for faster processing (take every 10th pixel)
            sample_pixels = pixels[::10]
            
            if len(sample_pixels) < num_colors:
                sample_pixels = pixels
            
            kmeans = KMeans(n_clusters=min(num_colors, len(sample_pixels)), random_state=42)
            kmeans.fit(sample_pixels)
            
            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            
            # Count pixels in each cluster
            labels = kmeans.labels_
            color_counts = Counter(labels)
            
            # Create color information
            dominant_colors = []
            for i, color in enumerate(colors):
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                dominant_colors.append({
                    'rgb': color.tolist(),
                    'hex': hex_color,
                    'percentage': round((color_counts[i] / len(labels)) * 100, 1)
                })
            
            # Sort by percentage (most dominant first)
            dominant_colors.sort(key=lambda x: x['percentage'], reverse=True)
            
            return dominant_colors
            
        except ImportError:
            # Fallback if sklearn is not available
            logger.warning("sklearn not available, using simple color extraction")
            return self._simple_color_extraction(img_array, num_colors)
        except Exception as e:
            logger.error(f"Error in dominant color extraction: {e}")
            return []
    
    def _simple_color_extraction(self, img_array: np.ndarray, num_colors: int = 5) -> List[Dict[str, Any]]:
        """Simple color extraction fallback method."""
        try:
            # Sample pixels from corners and center
            height, width = img_array.shape[:2]
            
            sample_points = [
                img_array[0, 0],  # Top-left
                img_array[0, width-1],  # Top-right
                img_array[height-1, 0],  # Bottom-left
                img_array[height-1, width-1],  # Bottom-right
                img_array[height//2, width//2]  # Center
            ]
            
            colors = []
            for i, color in enumerate(sample_points):
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                colors.append({
                    'rgb': color.tolist(),
                    'hex': hex_color,
                    'percentage': 20.0  # Equal distribution for simple method
                })
            
            return colors[:num_colors]
            
        except Exception as e:
            logger.error(f"Error in simple color extraction: {e}")
            return []
    
    def _analyze_color_distribution(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze the distribution of colors in the image."""
        try:
            # Calculate average RGB values
            avg_r = np.mean(img_array[:, :, 0])
            avg_g = np.mean(img_array[:, :, 1])
            avg_b = np.mean(img_array[:, :, 2])
            
            # Calculate color temperature (warm vs cool)
            if avg_r > avg_b:
                temperature = 'warm'
            elif avg_b > avg_r:
                temperature = 'cool'
            else:
                temperature = 'neutral'
            
            # Calculate saturation (how colorful vs grayscale)
            max_rgb = np.max(img_array, axis=2)
            min_rgb = np.min(img_array, axis=2)
            saturation = np.mean(max_rgb - min_rgb) / 255.0
            
            if saturation > 0.3:
                saturation_level = 'high'
            elif saturation > 0.1:
                saturation_level = 'medium'
            else:
                saturation_level = 'low'
            
            return {
                'average_rgb': [round(avg_r), round(avg_g), round(avg_b)],
                'temperature': temperature,
                'saturation': {
                    'value': round(saturation, 3),
                    'level': saturation_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error in color distribution analysis: {e}")
            return {
                'average_rgb': [0, 0, 0],
                'temperature': 'unknown',
                'saturation': {'value': 0, 'level': 'unknown'}
            }
    
    def _analyze_brightness(self, img_array: np.ndarray) -> str:
        """Analyze if the image is primarily dark or light."""
        try:
            # Convert to grayscale and calculate average brightness
            gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
            avg_brightness = np.mean(gray)
            
            if avg_brightness > 170:
                return 'light'
            elif avg_brightness < 85:
                return 'dark'
            else:
                return 'medium'
                
        except Exception as e:
            logger.error(f"Error in brightness analysis: {e}")
            return 'unknown'
    
    def cleanup_session_logos(self, session_id: str) -> bool:
        """Clean up logo files for a session."""
        try:
            session_dir = os.path.join(self.base_dir, session_id)
            if os.path.exists(session_dir):
                import shutil
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up logo files for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up logo files for session {session_id}: {e}")
            return False


