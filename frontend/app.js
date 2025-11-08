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
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp', 'image/tiff'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a JPG, PNG, BMP, or TIFF image.');
        return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('File size too large. Maximum size is 10MB.');
        return;
    }

    // Process the file
    uploadAndProcess(file);
}

// Upload and process image
async function uploadAndProcess(file) {
    showStatus('Uploading image...');

    const formData = new FormData();
    formData.append('file', file);

    const mode = processingMode.value;
    let endpoint = '/api/dewarp';

    // Determine endpoint based on mode
    if (mode === 'deskew') {
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

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();

        if (result.status === 'success') {
            displayResults(result, file);
        } else {
            throw new Error(result.message || 'Processing failed');
        }

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred while processing the image');
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
