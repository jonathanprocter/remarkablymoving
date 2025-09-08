#!/usr/bin/env python3

import os
import json
import requests
from flask import Flask, request, redirect, session, jsonify, render_template_string
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# OAuth 2.0 scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Get the current domain from Replit environment
REDIRECT_URI = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/oauth2callback"

print(f"🔧 OAuth Configuration:")
print(f"   Client ID: {GOOGLE_CLIENT_ID}")
print(f"   Redirect URI: {REDIRECT_URI}")
print(f"   Scopes: {SCOPES}")

@app.route('/')
def index():
    """Serve the main calendar application"""
    with open('index.html', 'r') as f:
        html_content = f.read()
    return html_content

@app.route('/config.js')
def config():
    """Serve the configuration with backend endpoints"""
    config_js = f"""
// Backend API configuration (Server-side OAuth)
window.BACKEND_CONFIG = {{
    authUrl: '/auth/google',
    statusUrl: '/auth/status',
    calendarsUrl: '/api/calendars',
    eventsUrl: '/api/events',
    logoutUrl: '/auth/logout'
}};

// Legacy client config (not used with server-side auth)
window.GOOGLE_CONFIG = {{
    apiKey: 'server-side-only',
    clientId: 'server-side-only'
}};
"""
    return config_js, 200, {'Content-Type': 'application/javascript'}

@app.route('/auth/google')
def google_auth():
    """Initialize Google OAuth flow"""
    try:
        # Create flow instance
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES
        )
        
        flow.redirect_uri = REDIRECT_URI
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for security
        session['state'] = state
        session['flow_data'] = {
            'client_config': flow.client_config,
            'scopes': SCOPES
        }
        
        print(f"🔐 Starting OAuth flow...")
        print(f"   Authorization URL: {authorization_url}")
        print(f"   State: {state}")
        
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"❌ Error starting OAuth: {e}")
        return jsonify({"error": f"OAuth initialization failed: {str(e)}"}), 500

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google"""
    try:
        # Verify state parameter
        if 'state' not in session or request.args.get('state') != session['state']:
            return jsonify({"error": "Invalid state parameter"}), 400
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error', 'Unknown error')
            print(f"❌ OAuth error: {error}")
            return jsonify({"error": f"Authorization failed: {error}"}), 400
        
        # Recreate flow from session
        flow = Flow.from_client_config(
            session['flow_data']['client_config'],
            scopes=session['flow_data']['scopes']
        )
        flow.redirect_uri = REDIRECT_URI
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        
        # Store credentials in session
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else SCOPES
        }
        
        print(f"✅ OAuth successful!")
        print(f"   Token received: {credentials.token[:20]}...")
        
        # Clean up session
        session.pop('state', None)
        session.pop('flow_data', None)
        
        # Redirect back to main app with success
        return redirect('/?auth=success')
        
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return jsonify({"error": f"OAuth callback failed: {str(e)}"}), 500

@app.route('/auth/status')
def auth_status():
    """Check if user is authenticated"""
    if 'credentials' in session:
        return jsonify({"authenticated": True, "message": "User is authenticated"})
    else:
        return jsonify({"authenticated": False, "message": "User not authenticated"})

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Log out user"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/calendars')
def get_calendars():
    """Get user's calendars"""
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Create credentials object from session
        creds = Credentials.from_authorized_user_info(session['credentials'], SCOPES)
        
        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        
        # Get calendar list
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        print(f"📅 Found {len(calendars)} calendars")
        for cal in calendars[:3]:  # Log first few
            print(f"   - {cal.get('summary', 'Unknown')} ({cal.get('id', 'no-id')})")
        
        return jsonify({"calendars": calendars})
        
    except Exception as e:
        print(f"❌ Error fetching calendars: {e}")
        return jsonify({"error": f"Failed to fetch calendars: {str(e)}"}), 500

@app.route('/api/events')
def get_events():
    """Get events from selected calendars"""
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Get parameters
        calendar_ids = request.args.getlist('calendar_ids')
        time_min = request.args.get('time_min')
        time_max = request.args.get('time_max')
        
        if not calendar_ids:
            return jsonify({"error": "No calendar IDs provided"}), 400
        
        # Create credentials object from session
        creds = Credentials.from_authorized_user_info(session['credentials'], SCOPES)
        
        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        
        all_events = []
        
        # Fetch events from each selected calendar
        for calendar_id in calendar_ids:
            try:
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # Add calendar info to each event
                for event in events:
                    event['calendar_id'] = calendar_id
                
                all_events.extend(events)
                
            except Exception as e:
                print(f"❌ Error fetching events from calendar {calendar_id}: {e}")
        
        print(f"📋 Found {len(all_events)} events across {len(calendar_ids)} calendars")
        
        return jsonify({"events": all_events})
        
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return jsonify({"error": f"Failed to fetch events: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"🚀 Starting reMarkable Calendar Generator server...")
    print(f"   Environment: {os.environ.get('REPLIT_ENVIRONMENT', 'development')}")
    print(f"   Domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)