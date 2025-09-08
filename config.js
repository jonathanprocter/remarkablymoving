
// Google API configuration
window.GOOGLE_CONFIG = {
    // Read from environment variables (Replit Secrets)
    clientId: window.location.hostname === 'localhost' ? 
        'YOUR_DEVELOPMENT_CLIENT_ID' : 
        (typeof process !== 'undefined' && process.env && process.env.GOOGLE_CLIENT_ID) || 'GOOGLE_CLIENT_ID_FROM_SECRETS',
    clientSecret: window.location.hostname === 'localhost' ?
        'YOUR_DEVELOPMENT_CLIENT_SECRET' :
        (typeof process !== 'undefined' && process.env && process.env.GOOGLE_CLIENT_SECRET) || 'GOOGLE_CLIENT_SECRET_FROM_SECRETS',
    // Your Replit domain for OAuth redirect
    redirectUri: window.location.origin + '/oauth2callback',
    // Scopes for calendar access
    scopes: [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email'
    ],
    // Discovery docs for Google Calendar API
    discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest']
};

// For client-side applications, we need to handle secrets differently
// Since this runs in the browser, we'll need to inject the secrets server-side
if (typeof window !== 'undefined') {
    // Check if secrets were injected by server
    if (window.INJECTED_GOOGLE_CLIENT_ID) {
        window.GOOGLE_CONFIG.clientId = window.INJECTED_GOOGLE_CLIENT_ID;
    }
}
