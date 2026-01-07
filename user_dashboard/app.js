const API_URL = 'https://review-predictor-using-llm.onrender.com/api';
const ROOT_URL = 'https://review-predictor-using-llm.onrender.com';

// Backend Status Management
let backendStatus = 'connecting'; // 'online', 'offline', 'connecting'
let statusCheckInterval = null;

function updateStatusIndicator(status, text) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (!statusDot || !statusText) return;

    // Remove all status classes
    statusDot.classList.remove('online', 'offline', 'pulsing');

    // Update status
    backendStatus = status;

    switch (status) {
        case 'online':
            statusDot.classList.add('online');
            statusText.textContent = text || 'Backend Online';
            statusText.style.color = 'var(--success-color)';
            break;
        case 'offline':
            statusDot.classList.add('offline');
            statusText.textContent = text || 'Backend Offline';
            statusText.style.color = 'var(--error-color)';
            break;
        case 'connecting':
        default:
            statusDot.classList.add('pulsing');
            statusText.textContent = text || 'Connecting...';
            statusText.style.color = 'var(--text-secondary)';
            break;
    }
}

// Check backend health
async function checkBackendHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch(ROOT_URL + '/health', {
            signal: controller.signal,
            method: 'GET'
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            updateStatusIndicator('online');
            return true;
        } else {
            updateStatusIndicator('offline', 'Backend Error');
            return false;
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            updateStatusIndicator('connecting', 'Waking up...');
        } else {
            updateStatusIndicator('offline', 'Cannot Reach Backend');
        }
        return false;
    }
}

// Initial warmup with retry logic
async function warmupBackend() {
    updateStatusIndicator('connecting', 'Waking backend...');

    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
        const success = await checkBackendHealth();
        if (success) {
            console.log('Backend is ready!');
            break;
        }
        attempts++;
        if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3s between attempts
        }
    }

    // Start periodic health checks every 30 seconds
    if (statusCheckInterval) clearInterval(statusCheckInterval);
    statusCheckInterval = setInterval(checkBackendHealth, 30000);
}

window.addEventListener('DOMContentLoaded', warmupBackend);

document.getElementById('reviewForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const responseArea = document.getElementById('responseArea');
    const responseTitle = document.getElementById('responseTitle');
    const responseMessage = document.getElementById('responseMessage');

    const ratingEl = document.querySelector('input[name="rating"]:checked');
    const reviewText = document.getElementById('reviewText').value;

    if (!ratingEl) {
        alert('Please select a rating');
        return;
    }

    const rating = parseInt(ratingEl.value);

    // Check if backend is offline before submitting
    if (backendStatus === 'offline') {
        const retry = confirm('Backend appears to be offline. Try to wake it up and submit?');
        if (!retry) return;

        // Try to wake up backend
        await checkBackendHealth();
        if (backendStatus === 'offline') {
            alert('Unable to connect to backend. Please try again in a few moments.');
            return;
        }
    }

    // Set Loading State
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
    responseArea.style.display = 'none';

    // UX: Update text if it takes too long (Render Cold Start)
    let slowLoadingTimeout = setTimeout(() => {
        if (submitBtn.disabled) {
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Waking up... (almost there)';
        }
    }, 4000);

    try {
        console.log("Sending request to:", `${API_URL}/reviews`);
        const response = await fetch(`${API_URL}/reviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating, review: reviewText })
        });

        clearTimeout(slowLoadingTimeout);
        console.log("Response status:", response.status);

        let data;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            // Handle non-JSON response (e.g. 500 html page)
            const text = await response.text();
            console.error("Non-JSON response:", text);
            throw new Error(`Server Error (${response.status})`);
        }

        if (response.ok) {
            responseArea.className = 'response-area success';
            responseTitle.textContent = 'Feedback Summary';
            responseMessage.textContent = data.message || 'Thank you for your feedback.';

            form.style.display = 'none';
            document.querySelector('.rating-group').style.display = 'none';
            document.querySelector('h1').textContent = 'System Response';
            document.querySelector('p').textContent = 'Your submission details:';

            form.reset();
        } else {
            // Try to extract useful error message
            let errorMsg = 'Failed to submit';
            if (data.detail) {
                if (typeof data.detail === 'string') errorMsg = data.detail;
                else if (Array.isArray(data.detail)) errorMsg = data.detail.map(e => e.msg).join(', ');
                else errorMsg = JSON.stringify(data.detail);
            }
            throw new Error(errorMsg);
        }
    } catch (error) {
        console.error("Submission error:", error);
        responseArea.className = 'response-area error';
        responseTitle.textContent = 'Error';
        responseMessage.textContent = error.message || 'Service temporarily unavailable. Please try again.';
    } finally {
        clearTimeout(slowLoadingTimeout);
        responseArea.style.display = 'block';
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        if (form.style.display !== 'none') {
            submitBtn.innerHTML = 'Submit';
        }
    }
});
