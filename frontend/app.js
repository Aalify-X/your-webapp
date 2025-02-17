// frontend/app.js
// Replace with your actual Render backend URL when deployed
const API_URL = process.env.REACT_APP_API_URL || 'https://progrify-backend.onrender.com';

async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/api/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('API Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', checkHealth);