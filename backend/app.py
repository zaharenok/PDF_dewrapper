"""
Page Dewarp SaaS - Backend API
FastAPI application for dewarping scanned document images
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dewarp_service import DewarpService
from preprocessing import ImagePreprocessor
from pdf_converter import PDFConverter
from pdf_processor import PDFProcessor

# Initialize FastAPI app
app = FastAPI(
    title="Page Dewarp SaaS",
    description="API for dewarping curved or distorted document pages",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure paths
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

# Serve CSS files from frontend directory
@app.get("/{filename}.css")
async def serve_css(filename: str):
    """Serve CSS files from frontend directory"""
    css_file = FRONTEND_DIR / f"{filename}.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

# Serve JS files from frontend directory
@app.get("/{filename}.js")
async def serve_js(filename: str):
    """Serve JavaScript files from frontend directory"""
    js_file = FRONTEND_DIR / f"{filename}.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS file not found")

# Initialize dewarp service
dewarp_service = DewarpService(
    upload_dir=str(UPLOAD_DIR),
    results_dir=str(RESULTS_DIR)
)

# Models
class DewarpResponse(BaseModel):
    task_id: str
    status: str
    message: str
    original_image: Optional[str] = None
    dewarped_image: Optional[str] = None
    processing_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str

# Cleanup old files in background
def cleanup_old_files():
    """Remove files older than 1 hour"""
    import time
    current_time = time.time()

    for directory in [UPLOAD_DIR, RESULTS_DIR]:
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:  # 1 hour
                    file_path.unlink()

# Routes
@app.get("/", response_class=FileResponse)
async def read_root():
    """Serve the landing page"""
    landing_file = FRONTEND_DIR / "landing.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    return JSONResponse(
        status_code=200,
        content={
            "message": "DocFix - Document Processing API",
            "docs": "/docs",
            "health": "/health",
            "app": "/app"
        }
    )

@app.get("/app", response_class=FileResponse)
async def read_app():
    """Serve the main application"""
    app_file = FRONTEND_DIR / "index.html"
    if app_file.exists():
        return FileResponse(app_file)
    return JSONResponse(
        status_code=404,
        content={"message": "App not found"}
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="page-dewarp-api"
    )

@app.post("/api/dewarp", response_model=DewarpResponse)
async def dewarp_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_dpi: int = 300,
    debug_level: int = 0,
    preserve_color: bool = True,
    process_all_pages: bool = True
):
    """
    Upload and dewarp a document image or PDF

    Parameters:
    - file: Image file (JPG, PNG, PDF)
    - output_dpi: Output DPI for the dewarped image (default: 300)
    - debug_level: Debug level (0-3, default: 0)

    Returns:
    - task_id: Unique task identifier
    - dewarped_image: URL to the processed image
    """

    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB max)
    MAX_FILE_SIZE = 20 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 20MB, got: {file_size / (1024*1024):.2f}MB"
        )

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{task_id}{file_ext}"

    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Convert PDF to image if needed
    processing_path = upload_path
    if file_ext == ".pdf":
        try:
            # Convert first page of PDF to image
            image_path = UPLOAD_DIR / f"{task_id}_converted.png"
            PDFConverter.convert_pdf_to_image(
                pdf_path=str(upload_path),
                output_path=str(image_path),
                dpi=output_dpi,
                page_number=1
            )
            processing_path = image_path
        except Exception as e:
            if upload_path.exists():
                upload_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"PDF conversion failed: {str(e)}"
            )

    # Process the image
    try:
        result = dewarp_service.process_image(
            input_path=str(processing_path),
            task_id=task_id,
            output_dpi=output_dpi,
            debug_level=debug_level
        )

        # Schedule cleanup
        background_tasks.add_task(cleanup_old_files)

        return DewarpResponse(
            task_id=task_id,
            status="success",
            message="Image dewarped successfully",
            original_image=f"/uploads/{task_id}{file_ext}",
            dewarped_image=result["output_path"],
            processing_time=result["processing_time"]
        )

    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Dewarping failed: {str(e)}"
        )

@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    """Get the dewarped image by task ID"""

    # Find result file
    result_files = list(RESULTS_DIR.glob(f"{task_id}_dewarped.*"))

    if not result_files:
        raise HTTPException(
            status_code=404,
            detail="Result not found"
        )

    result_file = result_files[0]
    return FileResponse(
        path=result_file,
        media_type="image/png",
        filename=f"dewarped_{task_id}.png"
    )

@app.delete("/api/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Delete files associated with a task"""

    deleted_files = []

    # Clean up uploads
    for file in UPLOAD_DIR.glob(f"{task_id}*"):
        file.unlink()
        deleted_files.append(str(file.name))

    # Clean up results
    for file in RESULTS_DIR.glob(f"{task_id}*"):
        file.unlink()
        deleted_files.append(str(file.name))

    return {
        "task_id": task_id,
        "deleted_files": deleted_files,
        "message": "Cleanup completed"
    }

@app.post("/api/deskew", response_model=DewarpResponse)
async def deskew_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: str = "hough"
):
    """
    Upload and deskew (straighten tilted) a document image or PDF

    Parameters:
    - file: Image file (JPG, PNG, PDF)
    - method: Deskew method ('hough' or 'projection', default: 'hough')

    Returns:
    - task_id: Unique task identifier
    - dewarped_image: URL to the deskewed image
    """
    import cv2

    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB max)
    MAX_FILE_SIZE = 20 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 20MB, got: {file_size / (1024*1024):.2f}MB"
        )

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{task_id}{file_ext}"

    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert PDF to image if needed
        processing_path = upload_path
        if file_ext == ".pdf":
            image_path = UPLOAD_DIR / f"{task_id}_converted.png"
            PDFConverter.convert_pdf_to_image(
                pdf_path=str(upload_path),
                output_path=str(image_path),
                dpi=300,
                page_number=1
            )
            processing_path = image_path

        # Process the image
        import time
        start_time = time.time()

        # Read image
        image = cv2.imread(str(processing_path))

        # Deskew
        deskewed, angle = ImagePreprocessor.deskew(image, method=method)

        # Save result
        output_path = RESULTS_DIR / f"{task_id}_deskewed.png"
        cv2.imwrite(str(output_path), deskewed)

        processing_time = time.time() - start_time

        # Schedule cleanup
        background_tasks.add_task(cleanup_old_files)

        return DewarpResponse(
            task_id=task_id,
            status="success",
            message=f"Image deskewed by {angle:.2f} degrees",
            original_image=f"/uploads/{task_id}{file_ext}",
            dewarped_image=f"/results/{output_path.name}",
            processing_time=round(processing_time, 2)
        )

    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Deskewing failed: {str(e)}"
        )

@app.post("/api/process-full", response_model=DewarpResponse)
async def process_full(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    apply_deskew: bool = True,
    apply_dewarp: bool = True,
    apply_perspective: bool = False,
    enhance: bool = False,
    output_dpi: int = 300
):
    """
    Full document processing pipeline

    Parameters:
    - file: Image file (JPG, PNG, PDF)
    - apply_deskew: Apply deskewing (default: True)
    - apply_dewarp: Apply dewarping (default: True)
    - apply_perspective: Apply perspective correction (default: False)
    - enhance: Apply image enhancement (default: False)
    - output_dpi: Output DPI (default: 300)

    Returns:
    - task_id: Unique task identifier
    - dewarped_image: URL to the processed image
    """
    import cv2

    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB max)
    MAX_FILE_SIZE = 20 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 20MB, got: {file_size / (1024*1024):.2f}MB"
        )

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{task_id}{file_ext}"

    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert PDF to image if needed
        processing_path = upload_path
        if file_ext == ".pdf":
            image_path = UPLOAD_DIR / f"{task_id}_converted.png"
            PDFConverter.convert_pdf_to_image(
                pdf_path=str(upload_path),
                output_path=str(image_path),
                dpi=output_dpi,
                page_number=1
            )
            processing_path = image_path

        # Process the image
        import time
        start_time = time.time()

        # Read image
        image = cv2.imread(str(processing_path))
        steps = []

        # Step 1: Deskew
        if apply_deskew:
            image, angle = ImagePreprocessor.deskew(image, method='hough')
            steps.append(f"Deskewed by {angle:.2f}°")

        # Step 2: Perspective correction
        if apply_perspective:
            image = ImagePreprocessor.perspective_correction(image, auto_detect=True)
            steps.append("Perspective corrected")

        # Step 3: Enhancement
        if enhance:
            image = ImagePreprocessor.enhance_image(image, ['denoise', 'contrast'])
            steps.append("Enhanced")

        # Save intermediate result
        intermediate_path = RESULTS_DIR / f"{task_id}_preprocessed.png"
        cv2.imwrite(str(intermediate_path), image)

        # Step 4: Dewarp (if requested)
        if apply_dewarp:
            result = dewarp_service.process_image(
                input_path=str(intermediate_path),
                task_id=f"{task_id}_final",
                output_dpi=output_dpi,
                debug_level=0
            )
            final_image_url = result["output_path"]
            steps.append("Dewarped")
        else:
            final_image_url = f"/results/{intermediate_path.name}"

        processing_time = time.time() - start_time

        # Schedule cleanup
        background_tasks.add_task(cleanup_old_files)

        return DewarpResponse(
            task_id=task_id,
            status="success",
            message=f"Processing complete: {', '.join(steps)}",
            original_image=f"/uploads/{task_id}{file_ext}",
            dewarped_image=final_image_url,
            processing_time=round(processing_time, 2)
        )

    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

@app.post("/api/process-pdf")
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_dpi: int = 300,
    preserve_color: bool = True,
    apply_deskew: bool = True
):
    """
    Process multi-page PDF with color preservation
    
    Parameters:
    - file: PDF file
    - output_dpi: Output DPI (default: 300)
    - preserve_color: Keep colors (default: True)  
    - apply_deskew: Apply deskewing (default: True)
    
    Returns:
    - ZIP archive with all processed pages
    """
    import cv2
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="This endpoint only accepts PDF files"
        )
    
    # Validate file size (20MB max)
    MAX_FILE_SIZE = 20 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 20MB, got: {file_size / (1024*1024):.2f}MB"
        )
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{task_id}.pdf"
    
    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process all pages
        result = PDFProcessor.process_pdf_multipage(
            pdf_path=str(upload_path),
            task_id=task_id,
            output_dir=RESULTS_DIR,
            dpi=output_dpi,
            preserve_color=preserve_color,
            apply_deskew=apply_deskew,
            apply_dewarp=False  # Dewarp makes B&W
        )
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_old_files)
        
        return {
            "task_id": task_id,
            "status": "success",
            "message": f"Processed {result['page_count']} pages successfully",
            "page_count": result['page_count'],
            "zip_download": result['zip_path'],
            "processing_time": result['processing_time'],
            "preserve_color": preserve_color
        }
        
    except Exception as e:
        # Clean up on failure
        if upload_path.exists():
            upload_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )
