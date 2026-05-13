/* script.js — Global utilities for SecureCompress */

// ─── Toast Notifications ────────────────────────────────────────────────────
(function() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);

    window.showToast = function(message, type = 'info', duration = 4000) {
        const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠️' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'none';
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };
})();

// ─── Navbar hamburger ───────────────────────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const navLinks = document.querySelector('.nav-links');
if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
}

// ─── Copy to clipboard helper ───────────────────────────────────────────────
window.copyToClipboard = function(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = '✓';
        btn.style.color = 'var(--green)';
        setTimeout(() => { btn.textContent = orig; btn.style.color = ''; }, 1500);
        showToast('Nusxa olindi!', 'success', 2000);
    }).catch(() => showToast('Nusxa olishda xato', 'error'));
};

// ─── Format bytes ────────────────────────────────────────────────────────────
window.formatBytes = function(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
    return (bytes / 1073741824).toFixed(1) + ' GB';
};

// ─── Animate numbers ─────────────────────────────────────────────────────────
window.animateNumber = function(el, target, duration = 800) {
    const start = performance.now();
    const from = parseInt(el.textContent) || 0;
    function step(now) {
        const p = Math.min((now - start) / duration, 1);
        el.textContent = Math.round(from + (target - from) * easeOut(p));
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
};

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

// ─── Intersection observer for fade-in animations ────────────────────────────
const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            const delay = e.target.dataset.delay || 0;
            setTimeout(() => {
                e.target.style.opacity = '1';
                e.target.style.transform = 'translateY(0)';
            }, parseInt(delay));
            observer.unobserve(e.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('[data-aos]').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
});
