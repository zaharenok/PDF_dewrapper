"""
PDF Multi-page Processor
Processes all pages of PDF with color preservation
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict
import logging
import zipfile
import time
from pdf_converter import PDFConverter
from preprocessing import ImagePreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process multi-page PDFs with color preservation"""

    @staticmethod
    def process_pdf_multipage(
        pdf_path: str,
        task_id: str,
        output_dir: Path,
        dpi: int = 300,
        preserve_color: bool = True,
        apply_deskew: bool = True,
        apply_dewarp: bool = False
    ) -> Dict:
        """
        Process all pages of a PDF

        Args:
            pdf_path: Path to PDF file
            task_id: Unique task ID
            output_dir: Output directory for results
            dpi: Resolution for conversion
            preserve_color: Keep original colors (True) or convert to B&W (False)
            apply_deskew: Apply deskewing
            apply_dewarp: Apply dewarping (note: makes B&W)

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        try:
            # Get PDF info
            pdf_info = PDFConverter.get_pdf_info(pdf_path)
            page_count = pdf_info['page_count']
            
            logger.info(f"Processing PDF with {page_count} pages")
            
            # Convert all pages to images
            images = PDFConverter.pdf_to_images(pdf_path, dpi=dpi)
            
            processed_files = []
            
            for img, page_num in images:
                logger.info(f"Processing page {page_num}/{page_count}")
                
                # Convert PIL to OpenCV
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Apply deskewing if requested
                if apply_deskew:
                    img_cv, angle = ImagePreprocessor.deskew(img_cv, method='hough')
                    logger.info(f"Page {page_num}: Deskewed by {angle:.2f}°")
                
                # Apply enhancement for better quality
                if preserve_color:
                    # For color: enhance contrast
                    lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    img_cv = cv2.merge([l, a, b])
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_LAB2BGR)
                
                # Save processed page
                output_file = output_dir / f"{task_id}_page{page_num:03d}.png"
                cv2.imwrite(str(output_file), img_cv)
                processed_files.append(str(output_file))
                
                logger.info(f"Page {page_num}: Saved to {output_file.name}")
            
            # Create ZIP archive with all pages
            zip_path = output_dir / f"{task_id}_all_pages.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in processed_files:
                    file_name = Path(file_path).name
                    zipf.write(file_path, file_name)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed {page_count} pages in {processing_time:.2f}s")
            
            return {
                "task_id": task_id,
                "page_count": page_count,
                "processed_files": [Path(f).name for f in processed_files],
                "zip_file": zip_path.name,
                "zip_path": f"/results/{zip_path.name}",
                "processing_time": round(processing_time, 2),
                "preserve_color": preserve_color
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    @staticmethod
    def create_preview_grid(
        image_paths: List[str],
        output_path: str,
        grid_cols: int = 2
    ) -> str:
        """
        Create a preview grid of all pages

        Args:
            image_paths: List of image file paths
            output_path: Output path for grid image
            grid_cols: Number of columns in grid

        Returns:
            Path to grid image
        """
        images = [cv2.imread(path) for path in image_paths]
        
        if not images:
            raise ValueError("No images to create grid")
        
        # Calculate grid dimensions
        n_images = len(images)
        grid_rows = (n_images + grid_cols - 1) // grid_cols
        
        # Resize all images to same height
        target_height = 400
        resized = []
        for img in images:
            h, w = img.shape[:2]
            aspect = w / h
            new_w = int(target_height * aspect)
            resized.append(cv2.resize(img, (new_w, target_height)))
        
        # Find max width
        max_width = max(img.shape[1] for img in resized)
        
        # Create grid
        grid_height = grid_rows * target_height
        grid_width = grid_cols * max_width
        grid = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 255
        
        for idx, img in enumerate(resized):
            row = idx // grid_cols
            col = idx % grid_cols
            
            y = row * target_height
            x = col * max_width
            
            h, w = img.shape[:2]
            grid[y:y+h, x:x+w] = img
        
        cv2.imwrite(output_path, grid)
        
        return output_path
