// OAuth configuration
const WHOP_AUTH_URL = 'https://api.whop.com/oauth/authorize';
const CLIENT_ID = 'your_client_id_here'; // You'll get this from Whop Dashboard
const REDIRECT_URI = window.API_BASE_URL + '/auth/callback';
const SCOPE = 'read write';

// Function to handle login
function handleLogin() {
    // Construct the OAuth authorization URL
    const authUrl = `${WHOP_AUTH_URL}?client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=${encodeURIComponent(SCOPE)}&response_type=token`;
    
    // Open the authorization URL in a new window
    window.location.href = authUrl;
}

// Function to check authentication state
function checkAuthState() {
    const token = localStorage.getItem('whop_token');
    if (token) {
        document.getElementById('lblAuthState').textContent = 'Welcome back!';
        document.getElementById('btnLogin').style.display = 'none';
        // Enable features
        document.querySelectorAll('.feature').forEach(feature => {
            feature.style.pointerEvents = 'auto';
            feature.style.opacity = '1';
        });
    } else {
        document.getElementById('lblAuthState').textContent = 'Please sign in to continue';
        document.getElementById('btnLogin').style.display = 'block';
        // Disable features
        document.querySelectorAll('.feature').forEach(feature => {
            feature.style.pointerEvents = 'none';
            feature.style.opacity = '0.5';
        });
    }
}

// Check auth state when page loads
window.addEventListener('load', checkAuthState);
