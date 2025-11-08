"""
Dewarp Service
Wrapper around page-dewarp library for document image correction
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DewarpService:
    """Service for dewarping document images"""

    def __init__(self, upload_dir: str, results_dir: str):
        self.upload_dir = Path(upload_dir)
        self.results_dir = Path(results_dir)

        # Ensure directories exist
        self.upload_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def process_image(
        self,
        input_path: str,
        task_id: str,
        output_dpi: int = 300,
        debug_level: int = 0,
        focal_length: Optional[float] = None,
        output_zoom: Optional[float] = None
    ) -> Dict:
        """
        Process an image using page-dewarp library

        Args:
            input_path: Path to input image
            task_id: Unique task identifier
            output_dpi: Output DPI (default: 300)
            debug_level: Debug level 0-3 (default: 0)
            focal_length: Camera focal length (optional)
            output_zoom: Output zoom factor (optional)

        Returns:
            Dictionary with processing results
        """

        start_time = time.time()

        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Prepare output path
        output_file = self.results_dir / f"{task_id}_dewarped.png"

        try:
            # Build command
            cmd = [
                "page-dewarp",
                str(input_file),
                "-d", str(debug_level),
                "-o", "file"
            ]

            # Add optional parameters
            if output_dpi:
                cmd.extend(["--output-dpi", str(output_dpi)])

            if focal_length:
                cmd.extend(["--focal-length", str(focal_length)])

            if output_zoom:
                cmd.extend(["--output-zoom", str(output_zoom)])

            logger.info(f"Running command: {' '.join(cmd)}")

            # Run page-dewarp command
            result = subprocess.run(
                cmd,
                cwd=str(self.results_dir),
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                logger.error(f"page-dewarp error: {result.stderr}")
                raise RuntimeError(f"Dewarping failed: {result.stderr}")

            # Find the output file
            # page-dewarp creates files like: input_name_thresh.png
            base_name = input_file.stem
            possible_outputs = [
                self.results_dir / f"{base_name}_thresh.png",
                self.results_dir / f"{base_name}_output.png",
                self.results_dir / f"{base_name}.png",
            ]

            actual_output = None
            for possible_file in possible_outputs:
                if possible_file.exists():
                    actual_output = possible_file
                    break

            if not actual_output:
                # Try to find any recently created PNG file
                recent_files = sorted(
                    self.results_dir.glob("*.png"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                if recent_files:
                    actual_output = recent_files[0]

            if actual_output and actual_output.exists():
                # Rename to our standard format
                actual_output.rename(output_file)
            else:
                raise RuntimeError("Output file not found after processing")

            processing_time = time.time() - start_time

            logger.info(f"Successfully dewarped image in {processing_time:.2f}s")

            return {
                "task_id": task_id,
                "output_path": f"/results/{output_file.name}",
                "processing_time": round(processing_time, 2),
                "output_file": str(output_file),
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("Processing timeout (60 seconds)")
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    def get_version(self) -> str:
        """Get page-dewarp version"""
        try:
            result = subprocess.run(
                ["page-dewarp", "--version"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
