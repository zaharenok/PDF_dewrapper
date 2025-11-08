"""
Image Preprocessing Module
Includes deskewing, perspective correction, and image enhancement
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Image preprocessing for document images"""

    @staticmethod
    def deskew(image: np.ndarray, method: str = 'hough') -> Tuple[np.ndarray, float]:
        """
        Deskew an image (correct rotation/tilt)

        Args:
            image: Input image (BGR or grayscale)
            method: 'hough' or 'projection' (default: 'hough')

        Returns:
            Tuple of (deskewed_image, angle)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if method == 'hough':
            angle = ImagePreprocessor._detect_skew_hough(gray)
        else:
            angle = ImagePreprocessor._detect_skew_projection(gray)

        logger.info(f"Detected skew angle: {angle:.2f} degrees")

        # Rotate image to deskew
        if abs(angle) > 0.1:  # Only rotate if angle is significant
            deskewed = ImagePreprocessor._rotate_image(image, angle)
            return deskewed, angle
        else:
            return image, 0.0

    @staticmethod
    def _detect_skew_hough(gray: np.ndarray) -> float:
        """Detect skew using Hough Line Transform"""

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return 0.0

        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            # Filter angles close to horizontal
            if -45 < angle < 45:
                angles.append(angle)

        if not angles:
            return 0.0

        # Return median angle
        return float(np.median(angles))

    @staticmethod
    def _detect_skew_projection(gray: np.ndarray) -> float:
        """Detect skew using projection profile analysis"""

        # Binarize image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Try different angles
        angles = np.arange(-5, 5, 0.5)
        best_angle = 0
        best_score = 0

        h, w = binary.shape

        for angle in angles:
            # Rotate image
            rotated = ImagePreprocessor._rotate_image(binary, angle)

            # Calculate horizontal projection
            projection = np.sum(rotated == 0, axis=1)

            # Score is variance of projection (higher = better alignment)
            score = np.var(projection)

            if score > best_score:
                best_score = score
                best_angle = angle

        return best_angle

    @staticmethod
    def _rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle"""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new image size
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Adjust rotation matrix for new size
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Rotate image
        rotated = cv2.warpAffine(image, M, (new_w, new_h),
                                  borderMode=cv2.BORDER_REPLICATE)

        return rotated

    @staticmethod
    def perspective_correction(image: np.ndarray, auto_detect: bool = True) -> np.ndarray:
        """
        Correct perspective distortion in document images

        Args:
            image: Input image
            auto_detect: Auto-detect document corners (default: True)

        Returns:
            Perspective-corrected image
        """
        if auto_detect:
            # Detect document corners
            corners = ImagePreprocessor._detect_document_corners(image)

            if corners is None:
                logger.warning("Could not detect document corners")
                return image

            # Apply perspective transform
            return ImagePreprocessor._apply_perspective_transform(image, corners)
        else:
            return image

    @staticmethod
    def _detect_document_corners(image: np.ndarray) -> Optional[np.ndarray]:
        """Detect document corners using contour detection"""

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 75, 200)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        # If we found a quadrilateral
        if len(approx) == 4:
            return approx.reshape(4, 2)

        return None

    @staticmethod
    def _apply_perspective_transform(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Apply perspective transformation to straighten document"""

        # Order corners: top-left, top-right, bottom-right, bottom-left
        rect = ImagePreprocessor._order_points(corners)

        (tl, tr, br, bl) = rect

        # Calculate width
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        # Calculate height
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        # Destination points
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype=np.float32)

        # Get perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)

        # Apply transformation
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        return warped

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left"""

        rect = np.zeros((4, 2), dtype=np.float32)

        # Sum: top-left has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Diff: top-right has smallest diff, bottom-left has largest diff
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    @staticmethod
    def enhance_image(image: np.ndarray, operations: list = None) -> np.ndarray:
        """
        Enhance image quality with various operations

        Args:
            image: Input image
            operations: List of operations to apply
                       ['denoise', 'sharpen', 'contrast', 'brightness']

        Returns:
            Enhanced image
        """
        if operations is None:
            operations = ['denoise', 'contrast']

        result = image.copy()

        for op in operations:
            if op == 'denoise':
                result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
            elif op == 'sharpen':
                kernel = np.array([[-1, -1, -1],
                                   [-1, 9, -1],
                                   [-1, -1, -1]])
                result = cv2.filter2D(result, -1, kernel)
            elif op == 'contrast':
                lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                result = cv2.merge([l, a, b])
                result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
            elif op == 'brightness':
                hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                v = cv2.add(v, 10)
                result = cv2.merge([h, s, v])
                result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)

        return result

    @staticmethod
    def binarize(image: np.ndarray, method: str = 'otsu') -> np.ndarray:
        """
        Binarize image (convert to black and white)

        Args:
            image: Input image
            method: 'otsu', 'adaptive', or 'simple'

        Returns:
            Binarized image
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if method == 'otsu':
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'adaptive':
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)
        else:  # simple
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        return binary
