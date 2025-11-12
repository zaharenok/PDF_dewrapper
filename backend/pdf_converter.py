"""
PDF Converter Module
Converts PDF files to images for processing
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple
import logging
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFConverter:
    """Convert PDF files to images"""

    @staticmethod
    def pdf_to_images(
        pdf_path: str,
        dpi: int = 300,
        output_format: str = "PNG"
    ) -> List[Tuple[Image.Image, int]]:
        """
        Convert PDF pages to PIL Images

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default: 300)
            output_format: Output format (PNG, JPEG)

        Returns:
            List of tuples (PIL Image, page_number)
        """
        images = []
        
        try:
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            
            # Calculate zoom factor for DPI
            zoom = dpi / 72  # 72 is default DPI
            matrix = fitz.Matrix(zoom, zoom)
            
            logger.info(f"Converting PDF with {pdf_document.page_count} pages at {dpi} DPI")
            
            # Convert each page
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=matrix)
                
                # Convert to PIL Image
                img_data = pix.tobytes(output_format.lower())
                img = Image.open(io.BytesIO(img_data))
                
                images.append((img, page_num + 1))
                logger.info(f"Converted page {page_num + 1}/{pdf_document.page_count}")
            
            pdf_document.close()
            
            return images
            
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            raise

    @staticmethod
    def save_images(
        images: List[Tuple[Image.Image, int]],
        output_dir: Path,
        base_filename: str,
        format: str = "PNG"
    ) -> List[str]:
        """
        Save converted images to disk

        Args:
            images: List of (PIL Image, page_number) tuples
            output_dir: Output directory
            base_filename: Base filename without extension
            format: Image format (PNG, JPEG)

        Returns:
            List of saved file paths
        """
        saved_files = []
        
        output_dir.mkdir(exist_ok=True)
        
        for img, page_num in images:
            if len(images) > 1:
                # Multiple pages: add page number
                output_file = output_dir / f"{base_filename}_page{page_num}.{format.lower()}"
            else:
                # Single page: no page number needed
                output_file = output_dir / f"{base_filename}.{format.lower()}"
            
            img.save(output_file, format=format)
            saved_files.append(str(output_file))
            logger.info(f"Saved: {output_file}")
        
        return saved_files

    @staticmethod
    def convert_pdf_to_image(
        pdf_path: str,
        output_path: str,
        dpi: int = 300,
        page_number: int = 1
    ) -> str:
        """
        Convert a single PDF page to image

        Args:
            pdf_path: Path to PDF file
            output_path: Output image path
            dpi: Resolution (default: 300)
            page_number: Page to convert (1-indexed, default: 1)

        Returns:
            Path to saved image
        """
        try:
            pdf_document = fitz.open(pdf_path)
            
            if page_number < 1 or page_number > pdf_document.page_count:
                raise ValueError(f"Page {page_number} out of range (1-{pdf_document.page_count})")
            
            # Get the page (0-indexed)
            page = pdf_document[page_number - 1]
            
            # Calculate zoom for DPI
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            
            # Render to pixmap
            pix = page.get_pixmap(matrix=matrix)
            
            # Save directly to file
            pix.save(output_path)
            
            pdf_document.close()
            
            logger.info(f"Converted PDF page {page_number} to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting PDF page: {str(e)}")
            raise

    @staticmethod
    def get_pdf_info(pdf_path: str) -> dict:
        """
        Get PDF metadata

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF info
        """
        try:
            pdf_document = fitz.open(pdf_path)
            
            info = {
                "page_count": pdf_document.page_count,
                "metadata": pdf_document.metadata,
                "is_encrypted": pdf_document.is_encrypted,
                "needs_pass": pdf_document.needs_pass,
            }
            
            # Get first page dimensions
            if pdf_document.page_count > 0:
                page = pdf_document[0]
                rect = page.rect
                info["page_width"] = rect.width
                info["page_height"] = rect.height
            
            pdf_document.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            raise

    @staticmethod
    def is_valid_pdf(pdf_path: str) -> bool:
        """
        Check if file is a valid PDF

        Args:
            pdf_path: Path to file

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            pdf_document = fitz.open(pdf_path)
            is_valid = pdf_document.page_count > 0
            pdf_document.close()
            return is_valid
        except:
            return False
