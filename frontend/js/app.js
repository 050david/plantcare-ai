const fileInput = document.getElementById('fileInput');
const cameraInput = document.getElementById('cameraInput');
const cameraBtn = document.getElementById('cameraBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const dropZone = document.getElementById('dropZone');
const dropZoneContent = document.getElementById('dropZoneContent');
const previewImg = document.getElementById('previewImg');
const tryAgainBtn = document.getElementById('tryAgainBtn');

let selectedFile = null;

const diseaseInfo = {
  'Bacterial spot': 'Caused by Xanthomonas bacteria. Remove infected leaves, avoid overhead watering, and apply copper-based bactericide.',
  'Early blight': 'Caused by Alternaria fungus. Remove affected leaves, improve air circulation, and apply fungicide.',
  'Late blight': 'Caused by Phytophthora infestans. Destroy infected plants, avoid wet foliage, apply fungicide immediately.',
  'Leaf Mold': 'Caused by Passalora fulva fungus. Improve ventilation, reduce humidity, apply fungicide.',
  'Septoria leaf spot': 'Caused by Septoria lycopersici. Remove infected leaves, avoid wetting foliage, apply fungicide.',
  'Spider mites Two spotted spider mite': 'Caused by mite infestation. Apply miticide or neem oil, increase humidity around plants.',
  'Target Spot': 'Caused by Corynespora cassiicola fungus. Remove infected tissue and apply appropriate fungicide.',
  'Tomato YellowLeaf Curl Virus': 'Viral disease spread by whiteflies. Remove infected plants, control whitefly population.',
  'Tomato mosaic virus': 'Viral disease. Remove infected plants, disinfect tools, control aphids.',
};

// --- File Selection ---
fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
cameraInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
cameraBtn.addEventListener('click', () => cameraInput.click());
dropZone.addEventListener('click', () => {
  if (!previewImg.classList.contains('d-none')) return;
  fileInput.click();
});

// --- Drag and Drop ---
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) handleFile(file);
});

function handleFile(file) {
  if (!file) return;
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.classList.remove('d-none');
    dropZoneContent.classList.add('d-none');
  };
  reader.readAsDataURL(file);
  analyzeBtn.disabled = false;
  showEmpty();
}

// --- Analyze ---
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  showLoading();
  analyzeBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      },
      body: formData
    });

    if (response.status === 401) {
      logout();
      return;
    }

    if (!response.ok) throw new Error('Prediction failed');
    const data = await response.json();
    showResults(data);
  } catch (err) {
    alert('Error analyzing image. Make sure the backend is running.');
    showEmpty();
    analyzeBtn.disabled = false;
  }
});

// --- Try Again ---
tryAgainBtn.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  previewImg.classList.add('d-none');
  dropZoneContent.classList.remove('d-none');
  analyzeBtn.disabled = true;
  showEmpty();
});

// --- UI States ---
function showEmpty() {
  document.getElementById('emptyState').classList.remove('d-none');
  document.getElementById('loadingState').classList.add('d-none');
  document.getElementById('resultsState').classList.add('d-none');
}

function showLoading() {
  document.getElementById('emptyState').classList.add('d-none');
  document.getElementById('loadingState').classList.remove('d-none');
  document.getElementById('resultsState').classList.add('d-none');
}

function showResults(data) {
  document.getElementById('emptyState').classList.add('d-none');
  document.getElementById('loadingState').classList.add('d-none');
  document.getElementById('resultsState').classList.remove('d-none');

  const badge = document.getElementById('healthBadge');
  if (data.is_healthy) {
    badge.textContent = '✅ Healthy Plant';
    badge.className = 'badge bg-success fs-6 px-3 py-2';
  } else {
    badge.textContent = '⚠️ Disease Detected';
    badge.className = 'badge bg-warning text-dark fs-6 px-3 py-2';
  }

  document.getElementById('plantName').textContent = data.plant;
  document.getElementById('diseaseName').textContent = data.disease;

  const confidence = data.confidence;
  document.getElementById('confidenceText').textContent = `${confidence}%`;
  document.getElementById('confidenceBar').style.width = `${confidence}%`;

  const diseaseInfoEl = document.getElementById('diseaseInfo');
  const healthyInfoEl = document.getElementById('healthyInfo');
  const diseaseInfoText = document.getElementById('diseaseInfoText');

  if (data.is_healthy) {
    diseaseInfoEl.classList.add('d-none');
    healthyInfoEl.classList.remove('d-none');
  } else {
    healthyInfoEl.classList.add('d-none');
    diseaseInfoEl.classList.remove('d-none');
    const info = diseaseInfo[data.disease] || 'Consult an agricultural expert for treatment recommendations.';
    diseaseInfoText.textContent = info;
  }

  analyzeBtn.disabled = false;
}