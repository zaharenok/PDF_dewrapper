# API Usage Examples

Examples of using the DocFix API in various programming languages.

## Table of Contents

- [Python](#python)
- [JavaScript/Node.js](#javascript-nodejs)
- [cURL](#curl)
- [PHP](#php)
- [Ruby](#ruby)

---

## Python

### Basic Dewarp

```python
import requests

# Upload and dewarp an image
url = "http://localhost:8000/api/dewarp"

files = {
    'file': open('document.jpg', 'rb')
}

data = {
    'output_dpi': 300,
    'debug_level': 0
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Task ID: {result['task_id']}")
print(f"Processing time: {result['processing_time']}s")
print(f"Dewarped image: {result['dewarped_image']}")

# Download the result
dewarped_url = f"http://localhost:8000{result['dewarped_image']}"
dewarped_image = requests.get(dewarped_url)

with open('dewarped_document.png', 'wb') as f:
    f.write(dewarped_image.content)
```

### Deskew Only

```python
import requests

url = "http://localhost:8000/api/deskew"

files = {
    'file': open('tilted_document.jpg', 'rb')
}

data = {
    'method': 'hough'
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Message: {result['message']}")
print(f"Result: {result['dewarped_image']}")
```

### Full Processing Pipeline

```python
import requests

url = "http://localhost:8000/api/process-full"

files = {
    'file': open('document.jpg', 'rb')
}

data = {
    'apply_deskew': True,
    'apply_dewarp': True,
    'apply_perspective': True,
    'enhance': True,
    'output_dpi': 300
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Processing time: {result['processing_time']}s")
```

### Using with a Python Class

```python
import requests
from pathlib import Path
from typing import Dict, Optional

class DocFixClient:
    """Client for DocFix API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def dewarp(self, image_path: str, output_dpi: int = 300) -> Dict:
        """Dewarp a document image"""
        url = f"{self.base_url}/api/dewarp"

        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'output_dpi': output_dpi, 'debug_level': 0}
            response = requests.post(url, files=files, data=data)

        return response.json()

    def deskew(self, image_path: str, method: str = 'hough') -> Dict:
        """Deskew a document image"""
        url = f"{self.base_url}/api/deskew"

        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'method': method}
            response = requests.post(url, files=files, data=data)

        return response.json()

    def process_full(self, image_path: str, **kwargs) -> Dict:
        """Full processing pipeline"""
        url = f"{self.base_url}/api/process-full"

        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, data=kwargs)

        return response.json()

    def download_result(self, result_url: str, output_path: str):
        """Download processed image"""
        full_url = f"{self.base_url}{result_url}"
        response = requests.get(full_url)

        with open(output_path, 'wb') as f:
            f.write(response.content)

# Usage
client = DocFixClient()

# Dewarp
result = client.dewarp('document.jpg', output_dpi=300)
client.download_result(result['dewarped_image'], 'output.png')

# Full processing
result = client.process_full(
    'document.jpg',
    apply_deskew=True,
    apply_dewarp=True,
    apply_perspective=True,
    enhance=True,
    output_dpi=300
)
```

---

## JavaScript (Node.js)

### Using Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function dewarpImage(imagePath) {
    const url = 'http://localhost:8000/api/dewarp';

    const formData = new FormData();
    formData.append('file', fs.createReadStream(imagePath));
    formData.append('output_dpi', 300);
    formData.append('debug_level', 0);

    try {
        const response = await axios.post(url, formData, {
            headers: formData.getHeaders()
        });

        console.log('Task ID:', response.data.task_id);
        console.log('Processing time:', response.data.processing_time);

        // Download result
        const imageUrl = `http://localhost:8000${response.data.dewarped_image}`;
        const imageResponse = await axios.get(imageUrl, { responseType: 'stream' });

        imageResponse.data.pipe(fs.createWriteStream('dewarped_output.png'));

        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Usage
dewarpImage('document.jpg')
    .then(result => console.log('Success:', result))
    .catch(err => console.error('Failed:', err));
```

### Using Fetch (Browser/Modern Node.js)

```javascript
async function uploadAndDewarp(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_dpi', 300);
    formData.append('debug_level', 0);

    try {
        const response = await fetch('http://localhost:8000/api/dewarp', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            console.log('Success!');
            console.log('Task ID:', result.task_id);
            console.log('Dewarped image:', result.dewarped_image);

            // Download result
            const imageUrl = `http://localhost:8000${result.dewarped_image}`;
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = 'dewarped.png';
            link.click();
        }

        return result;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Usage in browser with file input
document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        uploadAndDewarp(file);
    }
});
```

---

## cURL

### Basic Dewarp

```bash
curl -X POST http://localhost:8000/api/dewarp \
  -F "file=@document.jpg" \
  -F "output_dpi=300" \
  -F "debug_level=0"
```

### Deskew

```bash
curl -X POST http://localhost:8000/api/deskew \
  -F "file=@tilted_document.jpg" \
  -F "method=hough"
```

### Full Processing

```bash
curl -X POST http://localhost:8000/api/process-full \
  -F "file=@document.jpg" \
  -F "apply_deskew=true" \
  -F "apply_dewarp=true" \
  -F "apply_perspective=true" \
  -F "enhance=true" \
  -F "output_dpi=300"
```

### Download Result

```bash
# Get the result URL from the response, then:
curl -O http://localhost:8000/results/abc123_dewarped.png
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## PHP

```php
<?php

function dewarpImage($imagePath, $outputDpi = 300) {
    $url = 'http://localhost:8000/api/dewarp';

    $ch = curl_init();

    $postData = [
        'file' => new CURLFile($imagePath),
        'output_dpi' => $outputDpi,
        'debug_level' => 0
    ];

    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

    curl_close($ch);

    if ($httpCode === 200) {
        $result = json_decode($response, true);
        echo "Task ID: " . $result['task_id'] . "\n";
        echo "Processing time: " . $result['processing_time'] . "s\n";
        echo "Dewarped image: " . $result['dewarped_image'] . "\n";

        // Download result
        $imageUrl = 'http://localhost:8000' . $result['dewarped_image'];
        $imageData = file_get_contents($imageUrl);
        file_put_contents('dewarped_output.png', $imageData);

        return $result;
    } else {
        throw new Exception("Error: HTTP $httpCode");
    }
}

// Usage
try {
    $result = dewarpImage('document.jpg', 300);
    echo "Success!\n";
} catch (Exception $e) {
    echo "Failed: " . $e->getMessage() . "\n";
}

?>
```

---

## Ruby

```ruby
require 'httparty'
require 'json'

class DocFixClient
  def initialize(base_url = 'http://localhost:8000')
    @base_url = base_url
  end

  def dewarp(image_path, output_dpi: 300)
    url = "#{@base_url}/api/dewarp"

    response = HTTParty.post(url,
      multipart: true,
      body: {
        file: File.new(image_path),
        output_dpi: output_dpi,
        debug_level: 0
      }
    )

    JSON.parse(response.body)
  end

  def deskew(image_path, method: 'hough')
    url = "#{@base_url}/api/deskew"

    response = HTTParty.post(url,
      multipart: true,
      body: {
        file: File.new(image_path),
        method: method
      }
    )

    JSON.parse(response.body)
  end

  def download_result(result_url, output_path)
    image_url = "#{@base_url}#{result_url}"
    image_data = HTTParty.get(image_url).body

    File.open(output_path, 'wb') do |file|
      file.write(image_data)
    end
  end
end

# Usage
client = DocFixClient.new

result = client.dewarp('document.jpg', output_dpi: 300)
puts "Task ID: #{result['task_id']}"
puts "Processing time: #{result['processing_time']}s"

client.download_result(result['dewarped_image'], 'output.png')
puts "Downloaded to output.png"
```

---

## Response Examples

### Successful Response

```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "success",
  "message": "Image dewarped successfully",
  "original_image": "/uploads/abc123-def456-ghi789.jpg",
  "dewarped_image": "/results/abc123-def456-ghi789_dewarped.png",
  "processing_time": 2.34
}
```

### Error Response

```json
{
  "detail": "Invalid file type. Allowed: .jpg, .jpeg, .png, .bmp, .tiff"
}
```

---

## Best Practices

1. **File Size**: Keep images under 10MB for optimal processing
2. **Image Format**: Use JPG or PNG for best results
3. **DPI Settings**: Use 300 DPI for documents, 150 DPI for previews
4. **Error Handling**: Always implement proper error handling
5. **Timeouts**: Set appropriate timeouts (60+ seconds for large images)
6. **Cleanup**: Use the cleanup endpoint to remove old files

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production use, consider implementing:
- Request rate limits per IP/API key
- Concurrent processing limits
- File size limits
- Queue system for batch processing

---

## Need Help?

- API Documentation: http://localhost:8000/docs
- Interactive API: http://localhost:8000/redoc
- GitHub Issues: [Report a bug](https://github.com/your-repo/issues)
