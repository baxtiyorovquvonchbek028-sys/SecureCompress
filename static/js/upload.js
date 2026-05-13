/* upload.js — Upload page logic */

const dropzone = document.getElementById('dropzone');
const dropzoneContent = document.getElementById('dropzoneContent');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const fileNameEl = document.getElementById('fileName');
const fileSizeEl = document.getElementById('fileSize');
const fileIconEl = document.getElementById('fileIcon');
const passwordInput = document.getElementById('passwordInput');
const togglePw = document.getElementById('togglePw');
const processBtn = document.getElementById('processBtn');
const strengthFill = document.getElementById('strengthFill');
const strengthLabel = document.getElementById('strengthLabel');

// Cards
const uploadCard = document.getElementById('uploadCard');
const progressCard = document.getElementById('progressCard');
const resultCard = document.getElementById('resultCard');
const errorCard = document.getElementById('errorCard');

let selectedFile = null;
let currentFileId = null;

// ─── File type icons ──────────────────────────────────────────────────────────
const fileIcons = {
    pdf: '📑', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊',
    csv: '📊', json: '📋', xml: '📋', txt: '📄', md: '📄',
    py: '🐍', js: '⚡', html: '🌐', css: '🎨',
    jpg: '🖼', jpeg: '🖼', png: '🖼', gif: '🖼',
    zip: '📦', tar: '📦', log: '📜'
};

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    return fileIcons[ext] || '📄';
}

// ─── File selection ───────────────────────────────────────────────────────────
function setFile(file) {
    selectedFile = file;
    dropzoneContent.style.display = 'none';
    filePreview.style.display = 'flex';
    fileIconEl.textContent = getFileIcon(file.name);
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatBytes(file.size);
    updateProcessBtn();
}

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) setFile(e.target.files[0]);
});

document.getElementById('removeFile').addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    filePreview.style.display = 'none';
    dropzoneContent.style.display = 'flex';
    updateProcessBtn();
});

// ─── Drag & drop ──────────────────────────────────────────────────────────────
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
});
dropzone.addEventListener('click', (e) => {
    if (e.target === dropzone || e.target.closest('.dropzone-content')) {
        fileInput.click();
    }
});

// ─── Password strength ────────────────────────────────────────────────────────
function checkPasswordStrength(pw) {
    if (!pw) return { score: 0, label: '' };
    let score = 0;
    if (pw.length >= 6) score++;
    if (pw.length >= 10) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    const labels = ['', 'Juda zaif', 'Zaif', 'O\'rtacha', 'Kuchli', 'Juda kuchli'];
    const colors = ['', '#ef4444', '#f97316', '#eab308', '#22c55e', '#16a34a'];
    return { score, label: labels[score] || '', color: colors[score] || '' };
}

passwordInput.addEventListener('input', () => {
    const pw = passwordInput.value;
    const result = checkPasswordStrength(pw);
    strengthFill.style.width = `${result.score * 20}%`;
    strengthFill.style.background = result.color;
    strengthLabel.textContent = result.label;
    strengthLabel.style.color = result.color;
    updateProcessBtn();
});

togglePw.addEventListener('click', () => {
    const isText = passwordInput.type === 'text';
    passwordInput.type = isText ? 'password' : 'text';
    togglePw.textContent = isText ? '👁' : '🙈';
});

// ─── Process button state ─────────────────────────────────────────────────────
function updateProcessBtn() {
    processBtn.disabled = !selectedFile || passwordInput.value.length < 6;
}

// ─── Progress simulation ──────────────────────────────────────────────────────
function showProgress(pct, message, stepIndex) {
    document.getElementById('progressStatus').textContent = message;
    document.getElementById('loadingBar').style.width = `${pct}%`;
    const steps = ['step1', 'step2', 'step3', 'step4'];
    steps.forEach((id, i) => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
        if (i < stepIndex) el.classList.add('done');
        if (i === stepIndex) el.classList.add('active');
        const fill = el.querySelector('.step-fill');
        if (i < stepIndex) fill.style.width = '100%';
        else if (i === stepIndex) fill.style.width = '50%';
        else fill.style.width = '0';
    });
}

function showCard(name) {
    uploadCard.style.display = name === 'upload' ? 'block' : 'none';
    progressCard.style.display = name === 'progress' ? 'block' : 'none';
    resultCard.style.display = name === 'result' ? 'block' : 'none';
    errorCard.style.display = name === 'error' ? 'block' : 'none';
}

// ─── Main upload handler ──────────────────────────────────────────────────────
processBtn.addEventListener('click', async () => {
    if (!selectedFile || passwordInput.value.length < 6) return;

    showCard('progress');

    const steps = [
        [10, 'Fayl yuklanmoqda...', 0],
        [35, 'Ma\'lumotlar siqilmoqda...', 1],
        [65, 'AES-256 shifrlash...', 2],
        [85, 'Maxfiy ma\'lumotlar skanerlanmoqda...', 3],
        [100, 'Tugadi!', 3]
    ];

    // Animate progress steps with realistic delays
    let stepIdx = 0;
    const progressTimer = setInterval(() => {
        if (stepIdx < steps.length) {
            const [pct, msg, si] = steps[stepIdx];
            showProgress(pct, msg, si);
            stepIdx++;
        }
    }, 600);

    const fd = new FormData();
    fd.append('file', selectedFile);
    fd.append('password', passwordInput.value);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: fd });
        clearInterval(progressTimer);
        showProgress(100, 'Muvaffaqiyatli!', 3);

        const data = await res.json();

        if (!res.ok || data.error) {
            showCard('error');
            document.getElementById('errorMsg').textContent = data.error || 'Noma\'lum xato';
            return;
        }

        await new Promise(r => setTimeout(r, 600));

        // Populate result
        currentFileId = data.file_id;
        document.getElementById('resOrigSize').textContent = data.original_size;
        document.getElementById('resCompSize').textContent = data.compressed_size;
        document.getElementById('resRatio').textContent = data.compression_ratio;
        document.getElementById('resEncSize').textContent = data.encrypted_size;
        document.getElementById('resHash').textContent = data.hash;
        document.getElementById('resFileId').textContent = data.file_id;

        // Warnings
        if (data.warnings && data.warnings.length > 0) {
            const warningsBox = document.getElementById('warningsBox');
            warningsBox.style.display = 'block';
            const warnList = document.getElementById('warnList');
            warnList.innerHTML = data.warnings.map(w => `<li>${w}</li>`).join('');
        }

        // Copy hash
        document.getElementById('copyHash').onclick = () => {
            copyToClipboard(data.hash, document.getElementById('copyHash'));
        };
        document.getElementById('copyId').onclick = () => {
            copyToClipboard(data.file_id, document.getElementById('copyId'));
        };

        showCard('result');

    } catch (err) {
        clearInterval(progressTimer);
        console.error(err);
        showCard('error');
        document.getElementById('errorMsg').textContent = 'Server bilan bog\'lanishda xato';
    }
});

// ─── Download ─────────────────────────────────────────────────────────────────
document.getElementById('downloadBtn').addEventListener('click', async () => {
    const dlPw = document.getElementById('dlPassword').value;
    if (!dlPw) { showToast('Parol kiriting', 'warning'); return; }
    if (!currentFileId) return;

    const btn = document.getElementById('downloadBtn');
    btn.disabled = true; btn.textContent = 'Yuklanmoqda...';

    const fd = new FormData();
    fd.append('password', dlPw);

    try {
        const res = await fetch(`/api/download/${currentFileId}`, { method: 'POST', body: fd });
        if (!res.ok) {
            const data = await res.json();
            showToast(data.error || 'Xato', 'error');
            return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = selectedFile ? selectedFile.name : 'decrypted_file';
        a.click(); URL.revokeObjectURL(url);
        showToast('Fayl yuklab olindi!', 'success');
    } catch (err) {
        showToast('Yuklab olishda xato', 'error');
    } finally {
        btn.disabled = false; btn.textContent = '⬇ Yuklab olish';
    }
});

// ─── New upload ───────────────────────────────────────────────────────────────
document.getElementById('newUploadBtn').addEventListener('click', () => {
    selectedFile = null; currentFileId = null;
    fileInput.value = ''; passwordInput.value = '';
    filePreview.style.display = 'none';
    dropzoneContent.style.display = 'flex';
    strengthFill.style.width = '0'; strengthLabel.textContent = '';
    document.getElementById('warningsBox').style.display = 'none';
    document.getElementById('warnList').innerHTML = '';
    updateProcessBtn();
    showCard('upload');
});

document.getElementById('retryBtn').addEventListener('click', () => showCard('upload'));
