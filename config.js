
// Google API configuration
window.GOOGLE_CONFIG = {
    // You'll need to set these in Replit Secrets
    apiKey: window.location.hostname === 'localhost' ? 
        'YOUR_DEVELOPMENT_API_KEY' : 
        'YOUR_PRODUCTION_API_KEY',
    clientId: window.location.hostname === 'localhost' ?
        'YOUR_DEVELOPMENT_CLIENT_ID' :
        'YOUR_PRODUCTION_CLIENT_ID',
    // Add your authorized domain
    redirectUri: window.location.origin + '/oauth2callback',
    // Scopes for calendar access
    scopes: [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email'
    ]
};
