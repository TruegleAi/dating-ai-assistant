"""
Image Analysis Service for Munch AI Dating Assistant
Handles screenshot OCR and conversation extraction from images
"""
import os
import base64
import io
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import requests
from pydantic import BaseModel


# ===================== PYDANTIC MODELS =====================

class ExtractedMessage(BaseModel):
    """Extracted message from screenshot"""
    sender: str  # "user" or "other"
    content: str
    timestamp: Optional[str] = None


class ImageAnalysisResult(BaseModel):
    """Result of image analysis"""
    success: bool
    messages: List[ExtractedMessage] = []
    raw_text: str = ""
    platform_detected: Optional[str] = None
    error: Optional[str] = None


class ImageInfo(BaseModel):
    """Image metadata"""
    width: int
    height: int
    format: str
    size_bytes: int


# ===================== IMAGE SERVICE CLASS =====================

class ImageAnalysisService:
    """
    Service for extracting conversation text from screenshots.
    Supports multiple image formats and OCR backends.
    """

    # Supported image formats
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'WEBP', 'BMP'}

    # Maximum image dimensions
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096
    MAX_SIZE_MB = 10

    # Platform detection patterns
    PLATFORM_PATTERNS = {
        'imessage': [r'delivered', r'read \d+:\d+', r'iMessage'],
        'whatsapp': [r'whatsapp', r'\d+:\d+ [AP]M', r'online'],
        'instagram': [r'instagram', r'seen', r'active \d+ (m|h) ago'],
        'tinder': [r'tinder', r'matched', r'super like'],
        'bumble': [r'bumble', r'expires in', r'extend'],
        'hinge': [r'hinge', r'like', r'comment'],
        'messenger': [r'messenger', r'active now', r'facebook']
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        model: str = "llava",
        fallback_models: List[str] = None
    ):
        """
        Initialize ImageAnalysisService for local Ollama.

        Args:
            base_url: Base URL for local Ollama
            api_key: API key (not needed for local)
            model: Vision model to use (e.g., llava, bakllava)
            fallback_models: Fallback models if primary unavailable
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        self.api_key = api_key or ""
        self.model = model
        self.fallback_models = fallback_models or []

    def validate_image(self, image_data: bytes) -> tuple[bool, Optional[ImageInfo], Optional[str]]:
        """
        Validate image data.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (is_valid, image_info, error_message)
        """
        try:
            # Check size
            size_mb = len(image_data) / (1024 * 1024)
            if size_mb > self.MAX_SIZE_MB:
                return False, None, f"Image too large: {size_mb:.1f}MB (max {self.MAX_SIZE_MB}MB)"

            # Open and validate image
            image = Image.open(io.BytesIO(image_data))

            # Check format
            if image.format not in self.SUPPORTED_FORMATS:
                return False, None, f"Unsupported format: {image.format}"

            # Check dimensions
            if image.width > self.MAX_WIDTH or image.height > self.MAX_HEIGHT:
                return False, None, f"Image too large: {image.width}x{image.height}"

            info = ImageInfo(
                width=image.width,
                height=image.height,
                format=image.format,
                size_bytes=len(image_data)
            )

            return True, info, None

        except Exception as e:
            return False, None, f"Invalid image: {str(e)}"

    def image_to_base64(self, image_data: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_data).decode('utf-8')

    def base64_to_image(self, base64_str: str) -> bytes:
        """Convert base64 string to image bytes."""
        return base64.b64decode(base64_str)

    def resize_image(
        self,
        image_data: bytes,
        max_width: int = 1024,
        max_height: int = 1024
    ) -> bytes:
        """
        Resize image if needed to fit within max dimensions.

        Args:
            image_data: Raw image bytes
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Resized image bytes (or original if no resize needed)
        """
        image = Image.open(io.BytesIO(image_data))

        # Calculate aspect-preserving resize
        if image.width <= max_width and image.height <= max_height:
            return image_data

        ratio = min(max_width / image.width, max_height / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))

        resized = image.resize(new_size, Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        resized.save(output, format=image.format or 'PNG')
        return output.getvalue()

    def detect_platform(self, text: str) -> Optional[str]:
        """
        Detect messaging platform from extracted text.

        Args:
            text: Extracted text from screenshot

        Returns:
            Platform name or None if not detected
        """
        text_lower = text.lower()

        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return platform

        return None

    def extract_text_with_vision_api(self, image_data: bytes) -> Optional[str]:
        """
        Extract text from image using local Ollama vision API.

        Args:
            image_data: Raw image bytes

        Returns:
            Extracted text or None on failure
        """
        try:
            # Resize image for API
            resized = self.resize_image(image_data, 1024, 1024)
            base64_image = self.image_to_base64(resized)

            prompt = """Analyze this screenshot of a text/chat conversation.
Extract ALL the messages you can see, clearly indicating:
1. Who sent each message (the user or the other person)
2. The exact text of each message
3. Any timestamps if visible

Format your response as:
[USER]: message text here
[OTHER]: message text here
[USER]: another message

Be thorough and capture every visible message."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [base64_image]
                    }
                ],
                "stream": False,
                "options": {"temperature": 0.1}
            }

            # Try primary model, then fallbacks
            models_to_try = [self.model] + self.fallback_models

            for model in models_to_try:
                try:
                    payload["model"] = model
                    print(f"   Trying vision model: {model}")
                    response = requests.post(
                        self.api_url,
                        json=payload,
                        timeout=120  # Vision models need more time
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result.get('message', {}).get('content', '')
                        if content:
                            print(f"   Vision extraction successful with {model}")
                            return content
                    else:
                        print(f"   Vision API error: {response.status_code} - {response.text[:200]}")
                except Exception as e:
                    print(f"   Vision model {model} failed: {e}")
                    continue

            return None

        except Exception as e:
            print(f"Vision API error: {e}")
            return None

    def parse_extracted_text(self, raw_text: str) -> List[ExtractedMessage]:
        """
        Parse extracted text into structured messages.

        Args:
            raw_text: Raw text from OCR/vision API

        Returns:
            List of ExtractedMessage objects
        """
        messages = []

        # Pattern to match [USER]: or [OTHER]: format
        pattern = r'\[(\w+)\]:\s*(.+?)(?=\[\w+\]:|$)'
        matches = re.findall(pattern, raw_text, re.DOTALL | re.IGNORECASE)

        for sender, content in matches:
            sender_normalized = "user" if sender.upper() == "USER" else "other"
            content_clean = content.strip()

            if content_clean:
                messages.append(ExtractedMessage(
                    sender=sender_normalized,
                    content=content_clean
                ))

        # If no structured format found, try line-by-line analysis
        if not messages:
            lines = raw_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 2:
                    # Simple heuristic: alternating messages
                    sender = "user" if len(messages) % 2 == 0 else "other"
                    messages.append(ExtractedMessage(
                        sender=sender,
                        content=line
                    ))

        return messages

    def analyze_image(self, image_data: bytes) -> ImageAnalysisResult:
        """
        Full analysis pipeline for conversation screenshot.

        Args:
            image_data: Raw image bytes

        Returns:
            ImageAnalysisResult with extracted messages
        """
        # Validate image
        is_valid, info, error = self.validate_image(image_data)
        if not is_valid:
            return ImageAnalysisResult(
                success=False,
                error=error
            )

        # Extract text using vision API
        raw_text = self.extract_text_with_vision_api(image_data)

        if not raw_text:
            return ImageAnalysisResult(
                success=False,
                error="Could not extract text from image. Vision API unavailable."
            )

        # Parse messages
        messages = self.parse_extracted_text(raw_text)

        # Detect platform
        platform = self.detect_platform(raw_text)

        return ImageAnalysisResult(
            success=True,
            messages=messages,
            raw_text=raw_text,
            platform_detected=platform
        )

    def analyze_base64_image(self, base64_str: str) -> ImageAnalysisResult:
        """
        Analyze image from base64 string.

        Args:
            base64_str: Base64 encoded image

        Returns:
            ImageAnalysisResult
        """
        try:
            # Remove data URL prefix if present
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            image_data = self.base64_to_image(base64_str)
            return self.analyze_image(image_data)

        except Exception as e:
            return ImageAnalysisResult(
                success=False,
                error=f"Invalid base64 image: {str(e)}"
            )


# ===================== SINGLETON INSTANCE =====================

_image_service_instance: Optional[ImageAnalysisService] = None


def get_image_service(
    base_url: str = "http://localhost:11434",
    api_key: Optional[str] = None,
    model: str = "llava",
    fallback_models: List[str] = None
) -> ImageAnalysisService:
    """
    Get or create ImageAnalysisService singleton instance.

    Args:
        base_url: Local Ollama base URL
        api_key: API key (not needed for local)
        model: Vision model name
        fallback_models: Fallback vision models

    Returns:
        ImageAnalysisService instance
    """
    global _image_service_instance

    if _image_service_instance is None:
        _image_service_instance = ImageAnalysisService(
            base_url=base_url,
            api_key=api_key,
            model=model,
            fallback_models=fallback_models or []
        )

    return _image_service_instance
