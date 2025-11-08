# Page Dewarp SaaS

A web-based SaaS application for straightening curved and distorted document pages using the powerful page dewarping algorithm by Matt Zucker.

## Overview

This application provides a simple web interface to dewarp (straighten) scanned document images that are curved, warped, or photographed at angles. It uses the [page-dewarp](https://github.com/mzucker/page_dewarp) library which implements a "cubic sheet" model for document image correction.

### Use Cases

- Straighten photos of book pages
- Fix curved scanned documents
- Correct perspective distortion in photographed documents
- Prepare documents for OCR processing
- Archive and digitize physical documents

## Features

- **Modern Web Interface**: Clean, responsive UI with drag-and-drop support
- **RESTful API**: Full-featured FastAPI backend
- **Real-time Processing**: Upload and process images instantly
- **Configurable Output**: Adjust DPI and debug levels
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Auto-cleanup**: Automatic removal of old processed files
- **Side-by-side Comparison**: View original and dewarped images together

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **page-dewarp**: Document dewarping library
- **OpenCV**: Image processing
- **NumPy/SciPy**: Scientific computing
- **Uvicorn**: ASGI server

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **Modern CSS**: Responsive design with CSS Grid and Flexbox
- **HTML5 File API**: Drag-and-drop file uploads

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd PDF_dewrapper
```

2. Build and run with Docker Compose:
```bash
docker-compose up -d
```

3. Access the application at `http://localhost:8000`

### Manual Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PDF_dewrapper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Run the application:
```bash
cd backend
python app.py
```

5. Access the application at `http://localhost:8000`

## Usage

### Web Interface

1. Open `http://localhost:8000` in your browser
2. Drag and drop an image, or click to browse
3. (Optional) Adjust advanced settings:
   - **Output DPI**: Resolution of the output image (default: 300)
   - **Debug Level**: Amount of debugging information (0-3)
4. Wait for processing to complete
5. View the side-by-side comparison
6. Download the dewarped image

### API Endpoints

#### Upload and Dewarp Image

```bash
POST /api/dewarp
Content-Type: multipart/form-data

Parameters:
- file: Image file (required)
- output_dpi: Output DPI (optional, default: 300)
- debug_level: Debug level 0-3 (optional, default: 0)

Response:
{
  "task_id": "uuid",
  "status": "success",
  "message": "Image dewarped successfully",
  "original_image": "/uploads/uuid.jpg",
  "dewarped_image": "/results/uuid_dewarped.png",
  "processing_time": 2.34
}
```

Example using cURL:

```bash
curl -X POST http://localhost:8000/api/dewarp \
  -F "file=@document.jpg" \
  -F "output_dpi=300" \
  -F "debug_level=0"
```

#### Get Result

```bash
GET /api/result/{task_id}

Returns the dewarped image file
```

#### Health Check

```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-01-08T12:00:00",
  "service": "page-dewarp-api"
}
```

#### Cleanup Task Files

```bash
DELETE /api/cleanup/{task_id}

Response:
{
  "task_id": "uuid",
  "deleted_files": ["file1.jpg", "file2.png"],
  "message": "Cleanup completed"
}
```

## Project Structure

```
PDF_dewrapper/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── dewarp_service.py      # Dewarping service wrapper
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html            # Main HTML interface
│   ├── style.css             # Styling
│   └── app.js                # Frontend JavaScript
├── uploads/                  # Uploaded images (auto-created)
├── results/                  # Processed images (auto-created)
├── static/                   # Static assets
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Configuration

### Environment Variables

You can configure the application using environment variables:

- `LOG_LEVEL`: Logging level (default: INFO)
- `UPLOAD_DIR`: Directory for uploaded files
- `RESULTS_DIR`: Directory for processed files

### Advanced Options

The page-dewarp algorithm supports additional parameters:

- `--focal-length`: Camera focal length for perspective correction
- `--output-zoom`: Zoom factor for output image
- `--adaptive-winsz`: Window size for adaptive thresholding
- `--min-text-width`: Minimum text width for detection

See the [page-dewarp documentation](https://github.com/lmmx/page-dewarp) for more details.

## How It Works

The page dewarping algorithm uses a "cubic sheet" model to correct document distortions:

1. **Text Detection**: Identifies text regions in the image
2. **Contour Analysis**: Analyzes the curvature of text lines
3. **Model Fitting**: Fits a cubic spline model to the page surface
4. **Transformation**: Applies geometric transformation to flatten the page
5. **Thresholding**: Converts to binary image for optimal OCR

For a detailed technical explanation, read Matt Zucker's article: [Page Dewarping](https://mzucker.github.io/2016/08/15/page-dewarping.html)

## Performance

- **Processing Time**: Typically 2-5 seconds per image
- **Supported Formats**: JPG, PNG, BMP, TIFF
- **Maximum File Size**: 10MB (configurable)
- **Auto-cleanup**: Files older than 1 hour are automatically deleted

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Running in Development Mode

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Upload test image
curl -X POST http://localhost:8000/api/dewarp \
  -F "file=@test_image.jpg"
```

## Deployment

### Production Deployment

For production deployment, consider:

1. **Use a reverse proxy** (Nginx, Traefik)
2. **Enable HTTPS** with SSL certificates
3. **Set up monitoring** and logging
4. **Configure file retention policies**
5. **Scale with multiple workers**

Example with Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

**Issue**: OpenCV import error
```
Solution: Install system dependencies:
apt-get install libgl1-mesa-glx libglib2.0-0
```

**Issue**: Processing timeout
```
Solution: Increase timeout in dewarp_service.py or reduce image size
```

**Issue**: Memory errors with large images
```
Solution: Resize images before processing or increase available memory
```

## License

This project is open source. The page-dewarp library is licensed under the MIT License.

## Credits

- **Page Dewarping Algorithm**: [Matt Zucker](https://github.com/mzucker)
- **Original Article**: [Page Dewarping Technical Write-up](https://mzucker.github.io/2016/08/15/page-dewarping.html)
- **Modern Python Library**: [lmmx/page-dewarp](https://github.com/lmmx/page-dewarp)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Check the [page-dewarp documentation](https://github.com/lmmx/page-dewarp)
- Review the API documentation at `/docs`
- Open an issue in this repository

## Roadmap

- [ ] Batch processing support
- [ ] PDF input/output support
- [ ] Cloud storage integration (S3, Google Cloud Storage)
- [ ] User authentication and rate limiting
- [ ] Image preprocessing options (rotation, cropping)
- [ ] OCR integration
- [ ] REST API client libraries (Python, JavaScript)

---

Built with FastAPI, page-dewarp, and modern web technologies.
