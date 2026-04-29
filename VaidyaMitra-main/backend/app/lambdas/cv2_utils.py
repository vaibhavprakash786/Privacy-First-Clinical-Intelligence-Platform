"""
OpenCV Image Preprocessing Utilities

Applies standard computer vision techniques (deskew, noise reduction, thresholding)
to maximize OCR accuracy for Amazon Textract.
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def preprocess_for_ocr(image_bytes: bytes) -> Optional[bytes]:
    """
    Run full preprocessing pipeline on image bytes.
    Returns cleaned image bytes (JPEG) ready for Textract, or None if failed.
    """
    try:
        # Decode bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Deskew (correct rotation)
        deskewed = _deskew(gray)

        # 3. Noise Reduction (Gaussian blur)
        # using a slight blur to remove speckles but keep text sharp
        blurred = cv2.GaussianBlur(deskewed, (3, 3), 0)

        # 4. Enhance Contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(blurred)

        # 5. Adaptive Thresholding (Binarization) to separate text from background
        # This works best for scanned documents with uneven lighting
        binarized = cv2.adaptiveThreshold(
            contrast_enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Re-encode to JPEG
        success, encoded = cv2.imencode('.jpg', binarized)
        if success:
            return encoded.tobytes()
        return None

    except Exception as e:
        logger.error(f"OpenCV processing failed: {e}")
        # In case of failure, return original bytes safely
        return image_bytes


def _deskew(image: np.ndarray) -> np.ndarray:
    """Detect text skew and rotate image to level it out."""
    # Grab the (x, y) coordinates of all pixel values that are greater than zero
    # First, invert the image because cv2.minAreaRect expects white text on black background
    coords = np.column_stack(np.where(cv2.bitwise_not(image) > 0))
    if len(coords) == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    # The `cv2.minAreaRect` function returns values in the range [-90, 0)
    # Convert angle so it rotates correctly
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # If the angle is practically 0, skip rotation
    if abs(angle) < 0.5:
        return image

    # Rotate the image to deskew it
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return rotated
