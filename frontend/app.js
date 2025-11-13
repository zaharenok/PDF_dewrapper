// Page Dewarp - Frontend Application
// API endpoint
const API_BASE = window.location.origin;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const statusMessage = document.getElementById('statusMessage');
const errorMessage = document.getElementById('errorMessage');
const originalImage = document.getElementById('originalImage');
const dewarpedImage = document.getElementById('dewarpedImage');
const processingTime = document.getElementById('processingTime');
const taskId = document.getElementById('taskId');
const downloadBtn = document.getElementById('downloadBtn');
const newImageBtn = document.getElementById('newImageBtn');
const dpiInput = document.getElementById('dpiInput');
const debugLevel = document.getElementById('debugLevel');
const processingMode = document.getElementById('processingMode');
const applyPerspective = document.getElementById('applyPerspective');
const applyEnhancement = document.getElementById('applyEnhancement');
const preserveColor = document.getElementById('preserveColor');

// State
let currentTaskId = null;
let currentDewarpedImageUrl = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkAPIHealth();
});

function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Buttons
    downloadBtn.addEventListener('click', downloadResult);
    newImageBtn.addEventListener('click', resetApp);
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File handling
function handleFile(file) {
    console.log('📄 File selected:', file.name);
    console.log('📋 File type:', file.type);
    console.log('📏 File size:', (file.size / 1024 / 1024).toFixed(2), 'MB');
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp', 'image/tiff', 'application/pdf'];
    const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'];
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    console.log('🔍 File extension:', fileExtension);
    
    const typeValid = validTypes.includes(file.type);
    const extensionValid = validExtensions.includes(fileExtension);
    console.log('✅ Type valid:', typeValid);
    console.log('✅ Extension valid:', extensionValid);
    
    if (!typeValid && !extensionValid) {
        console.error('❌ File validation failed');
        showError('Invalid file type. Please upload a JPG, PNG, BMP, TIFF, or PDF file.');
        return;
    }

    // Validate file size (max 20MB)
    const maxSize = 20 * 1024 * 1024; // 20MB
    if (file.size > maxSize) {
        console.error('❌ File too large:', file.size);
        showError('File size too large. Maximum size is 20MB.');
        return;
    }

    console.log('✅ File validation passed, uploading...');
    // Process the file
    uploadAndProcess(file);
}

// Upload and process image
async function uploadAndProcess(file) {
    showStatus('Uploading file...');

    const formData = new FormData();
    formData.append('file', file);

    const mode = processingMode.value;
    const isPDF = file.name.toLowerCase().endsWith('.pdf');
    let endpoint = '/api/dewarp';

    console.log('📤 Upload mode:', mode);
    console.log('📄 Is PDF:', isPDF);
    
    // For PDF files, use dedicated PDF endpoint
    if (isPDF) {
        endpoint = '/api/process-pdf';
        formData.append('output_dpi', dpiInput.value);
        formData.append('preserve_color', preserveColor.checked ? 'true' : 'false');
        formData.append('apply_deskew', 'true');
    }
    // For images, use existing endpoints
    else if (mode === 'deskew') {
        endpoint = '/api/deskew';
        formData.append('method', 'hough');
    } else if (mode === 'full') {
        endpoint = '/api/process-full';
        formData.append('apply_deskew', 'true');
        formData.append('apply_dewarp', 'true');
        formData.append('apply_perspective', applyPerspective.checked ? 'true' : 'false');
        formData.append('enhance', applyEnhancement.checked ? 'true' : 'false');
        formData.append('output_dpi', dpiInput.value);
    } else {
        // dewarp mode
        formData.append('output_dpi', dpiInput.value);
        formData.append('debug_level', debugLevel.value);
    }

    console.log('🌐 Endpoint:', endpoint);
    console.log('📦 FormData entries:');
    for (let pair of formData.entries()) {
        if (pair[0] === 'file') {
            console.log('  file:', pair[1].name, pair[1].type, pair[1].size);
        } else {
            console.log(' ', pair[0] + ':', pair[1]);
        }
    }

    try {
        console.log('🚀 Sending request to:', `${API_BASE}${endpoint}`);
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        console.log('📨 Response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Server error:', error);
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        console.log('✅ Server response:', result);

        if (result.status === 'success') {
            // Check if it's a PDF result (has zip_download)
            if (result.zip_download) {
                displayPDFResults(result, file);
            } else {
                displayResults(result, file);
            }
        } else {
            throw new Error(result.message || 'Processing failed');
        }

    } catch (error) {
        console.error('❌ Error:', error);
        showError(error.message || 'An error occurred while processing the file');
    }
}

// Display results
function displayResults(result, originalFile) {
    currentTaskId = result.task_id;
    currentDewarpedImageUrl = `${API_BASE}${result.dewarped_image}`;

    // Show original image
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
    };
    reader.readAsDataURL(originalFile);

    // Show dewarped image
    dewarpedImage.src = currentDewarpedImageUrl;

    // Update info
    processingTime.textContent = `${result.processing_time}s`;
    taskId.textContent = result.task_id;

    // Show results section
    hideAllSections();
    resultsSection.style.display = 'block';
}

// Download result
function downloadResult() {
    if (currentDewarpedImageUrl) {
        const link = document.createElement('a');
        link.href = currentDewarpedImageUrl;
        link.download = `dewarped_${currentTaskId}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// UI State Management
function showStatus(message) {
    statusMessage.textContent = message;
    hideAllSections();
    statusSection.style.display = 'block';
}

function showError(message) {
    errorMessage.textContent = message;
    hideAllSections();
    errorSection.style.display = 'block';
}

function hideAllSections() {
    statusSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function resetApp() {
    hideAllSections();
    fileInput.value = '';
    currentTaskId = null;
    currentDewarpedImageUrl = null;
}

// API Health Check
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.warn('API health check failed:', error);
    }
}

// Utility: Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Display PDF results
function displayPDFResults(result, originalFile) {
    console.log('📄 Displaying PDF results:', result);
    
    currentTaskId = result.task_id;
    
    // Hide status, show results
    hideAllSections();
    resultsSection.style.display = 'block';
    
    // Update result info
    processingTime.textContent = `${result.processing_time}s`;
    taskId.textContent = result.task_id;
    
    // Replace comparison section with PDF info
    const comparison = resultsSection.querySelector('.comparison');
    comparison.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <h2>✅ PDF Processed Successfully!</h2>
            <p style="font-size: 18px; margin: 20px 0;">
                <strong>${result.page_count}</strong> pages processed
            </p>
            <p style="color: ${result.preserve_color ? 'green' : 'gray'};">
                ${result.preserve_color ? '🎨 Colors preserved' : '⚫ Black & white'}
            </p>
            <div style="margin: 30px 0;">
                <button id="downloadZipBtn" class="btn btn-success">
                    📦 Download All Pages (${result.page_count} pages)
                </button>
            </div>
            <p style="margin-top: 20px; color: #666;">
                All processed pages are included in the ZIP archive
            </p>
        </div>
    `;
    
    // Attach event listener to download button AFTER it's in the DOM
    const downloadZipBtn = document.getElementById('downloadZipBtn');
    downloadZipBtn.onclick = () => {
        // Use dedicated download endpoint
        const downloadUrl = `${API_BASE}/api/download-zip/${result.task_id}`;
        console.log('📥 Downloading ZIP from:', downloadUrl);
        
        // Simple direct download - most reliable method
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `processed_pages_${result.task_id}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        console.log('✅ Download link clicked!');
    };
}
