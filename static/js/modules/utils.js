// utils.js - 共通ユーティリティ関数

export function escapeHTML(str) {
    if (typeof str !== 'string') {
        str = String(str);
    }
    return str.replace(/[&<"'\/]/g, function(match) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '/': '&#x2F;'
        }[match];
    });
}

export function showAlert(alertId, message, type = 'info') {
    const alertEl = document.getElementById(alertId);
    if (!alertEl) return;
    
    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = message;
    alertEl.style.display = 'block';
}

export function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

export function setButtonLoading(button, isLoading) {
    const spinner = button.querySelector('.spinner-border');
    button.disabled = isLoading;
    if (spinner) {
        spinner.classList.toggle('d-none', !isLoading);
    }
}
