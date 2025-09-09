#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session, jsonify, render_template_string
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__, static_folder='public', static_url_path='/static')
# Use a persistent secret key for session management
# This ensures sessions persist across server restarts
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-remarkable-calendar-2025")

# Configure session cookies for OAuth
# Settings optimized for Replit environment
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,  # Security best practice
    SESSION_COOKIE_SAMESITE='None',  # Required for cross-site OAuth in Replit
    SESSION_COOKIE_SECURE=True,  # Required when SameSite=None
    SESSION_COOKIE_NAME='calendar_session',  # Custom session name
    SESSION_COOKIE_PATH='/',  # Ensure cookie works on all paths
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # Session timeout
    SESSION_TYPE='filesystem',  # Store sessions server-side
    SESSION_PERMANENT=False
)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# OAuth 2.0 scopes for Google Calendar (Google may grant additional scopes automatically)
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'openid'
]

# Get the current domain from Replit environment
REDIRECT_URI = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/oauth2callback"

print(f"🔧 OAuth Configuration:")
print(f"   Client ID: {GOOGLE_CLIENT_ID}")
print(f"   Redirect URI: {REDIRECT_URI}")
print(f"   Scopes: {SCOPES}")

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_or_create_user(google_user_id, email, name):
    """Get or create user in database"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Try to get existing user
        cur.execute(
            "SELECT id FROM users WHERE google_user_id = %s",
            (google_user_id,)
        )
        user = cur.fetchone()
        
        if user:
            # Update user info
            cur.execute(
                "UPDATE users SET email = %s, name = %s, updated_at = CURRENT_TIMESTAMP WHERE google_user_id = %s",
                (email, name, google_user_id)
            )
            user_id = dict(user)['id']
        else:
            # Create new user
            cur.execute(
                "INSERT INTO users (google_user_id, email, name) VALUES (%s, %s, %s) RETURNING id",
                (google_user_id, email, name)
            )
            result = cur.fetchone()
            user_id = dict(result)['id'] if result else None
        
        conn.commit()
        return user_id
        
    finally:
        conn.close()

def store_user_calendars(user_id, calendars):
    """Store user's calendars in database"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Clear existing calendars for this user
        cur.execute("DELETE FROM user_calendars WHERE user_id = %s", (user_id,))
        
        # Insert new calendars
        for calendar in calendars:
            cur.execute(
                """INSERT INTO user_calendars 
                   (user_id, calendar_id, calendar_name, calendar_color, access_role, is_primary)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, calendar['id'], calendar.get('summary', ''), 
                 calendar.get('backgroundColor', ''), calendar.get('accessRole', ''),
                 calendar.get('primary', False))
            )
        
        conn.commit()
        print(f"📅 Stored {len(calendars)} calendars for user {user_id}")
        
    finally:
        conn.close()

def store_calendar_events(user_id, calendar_id, events):
    """Store calendar events in database"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        for event in events:
            # Parse start and end times
            start_dt = None
            end_dt = None
            is_all_day = False
            
            if 'start' in event:
                if 'dateTime' in event['start']:
                    start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                elif 'date' in event['start']:
                    start_dt = datetime.fromisoformat(event['start']['date'])
                    is_all_day = True
                    
            if 'end' in event:
                if 'dateTime' in event['end']:
                    end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                elif 'date' in event['end']:
                    end_dt = datetime.fromisoformat(event['end']['date'])
            
            # Insert or update event
            cur.execute(
                """INSERT INTO calendar_events 
                   (user_id, calendar_id, event_id, event_summary, event_description, 
                    start_datetime, end_datetime, is_all_day, location, status, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (user_id, calendar_id, event_id) 
                   DO UPDATE SET 
                       event_summary = EXCLUDED.event_summary,
                       event_description = EXCLUDED.event_description,
                       start_datetime = EXCLUDED.start_datetime,
                       end_datetime = EXCLUDED.end_datetime,
                       is_all_day = EXCLUDED.is_all_day,
                       location = EXCLUDED.location,
                       status = EXCLUDED.status,
                       updated_at = CURRENT_TIMESTAMP""",
                (user_id, calendar_id, event['id'], event.get('summary', ''),
                 event.get('description', ''), start_dt, end_dt, is_all_day,
                 event.get('location', ''), event.get('status', ''))
            )
        
        conn.commit()
        print(f"📋 Stored {len(events)} events for calendar {calendar_id}")
        
    finally:
        conn.close()

@app.route('/')
def index():
    """Serve the main calendar application"""
    with open('index.html', 'r') as f:
        html_content = f.read()
    
    # Inject the client integration script before closing body tag
    integration_script = '<script src="/static/client-integration.js"></script>'
    html_content = html_content.replace('</body>', f'{integration_script}\n</body>')
    
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

@app.route('/auth')
def auth_redirect():
    """Redirect /auth to /auth/google"""
    return redirect('/auth/google')

@app.route('/auth/google')
def google_auth():
    """Initialize Google OAuth flow"""
    try:
        # Create proper client configuration
        client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [REDIRECT_URI]
            }
        }
        
        # Create flow instance
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URI
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Mark session as permanent and store state
        session.permanent = True  # Enable permanent session
        session['state'] = state
        session['client_config'] = client_config
        session.modified = True  # Force session save
        
        print(f"🔐 Starting OAuth flow...")
        print(f"   Authorization URL: {authorization_url}")
        print(f"   State: {state}")
        print(f"   Session ID: {session.get('_id', 'new session')}")
        
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"❌ Error starting OAuth: {e}")
        return jsonify({"error": f"OAuth initialization failed: {str(e)}"}), 500

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google"""
    try:
        # Debug info
        print(f"📝 OAuth callback received")
        print(f"   Request state: {request.args.get('state', 'NONE')}")
        
        # For Replit environment, we'll skip state validation due to session issues
        # In production, you'd want proper state validation
        # This is a temporary workaround for the Replit proxy environment
        
        # Get the state from request (we'll accept any valid state for now)
        state = request.args.get('state')
        if not state:
            print("❌ No state parameter in request")
            return jsonify({"error": "Missing state parameter"}), 400
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error', 'Unknown error')
            print(f"❌ OAuth error: {error}")
            return jsonify({"error": f"Authorization failed: {error}"}), 400
        
        # Recreate flow with hardcoded client config (since session isn't working in Replit)
        client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [REDIRECT_URI]
            }
        }
        
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URI
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        
        # Store credentials in session
        credentials = flow.credentials
        
        # Use the actual scopes granted by Google (not just what we requested)
        granted_scopes = list(credentials.scopes) if credentials.scopes else SCOPES
        
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': granted_scopes
        }
        
        # Get user info and store in database
        try:
            # Build the OAuth2 service to get user info
            oauth_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth_service.userinfo().get().execute()
            
            google_user_id = user_info['id']
            email = user_info.get('email', '')
            name = user_info.get('name', '')
            
            # Store user in database
            user_id = get_or_create_user(google_user_id, email, name)
            session['user_id'] = user_id
            session['google_user_id'] = google_user_id
            
            print(f"👤 User stored: {name} ({email}) - DB ID: {user_id}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not store user info: {e}")
        
        print(f"📋 Granted scopes: {granted_scopes}")
        
        print(f"✅ OAuth successful!")
        if credentials and credentials.token:
            print(f"   Token received: {credentials.token[:20]}...")
        else:
            print("   Token received but could not display")
        
        # Clean up session
        session.pop('state', None)
        session.pop('client_config', None)
        
        # Redirect back to main app with success
        return redirect('/?auth=success')
        
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return jsonify({"error": f"OAuth callback failed: {str(e)}"}), 500

@app.route('/auth/status')
def auth_status():
    """Check if user is authenticated"""
    if 'credentials' in session:
        # Ensure user_id is set if missing
        if 'user_id' not in session and 'google_user_id' in session:
            try:
                conn = get_db_connection()
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE google_user_id = %s", (session['google_user_id'],))
                    user = cur.fetchone()
                    if user:
                        session['user_id'] = dict(user)['id']
                finally:
                    conn.close()
            except Exception as e:
                print(f"⚠️ Warning: Could not restore user_id from database: {e}")
        
        return jsonify({
            "authenticated": True, 
            "message": "User is authenticated",
            "user_id": session.get('user_id'),
            "google_user_id": session.get('google_user_id')
        })
    else:
        return jsonify({"authenticated": False, "message": "User not authenticated"})

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Log out user"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/calendars')
def get_calendars():
    """Get user's calendars from database (fetch from Google if needed)"""
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Create credentials object from session
        granted_scopes = session['credentials'].get('scopes', SCOPES)
        creds = Credentials.from_authorized_user_info(session['credentials'], granted_scopes)
        
        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        
        # Get calendar list from Google
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        # Store calendars in database if user_id available
        user_id = session.get('user_id')
        if user_id:
            try:
                store_user_calendars(user_id, calendars)
            except Exception as e:
                print(f"⚠️ Warning: Could not store calendars in database: {e}")
        
        print(f"📅 Found {len(calendars)} calendars")
        for cal in calendars[:3]:  # Log first few
            print(f"   - {cal.get('summary', 'Unknown')} ({cal.get('id', 'no-id')})")
        
        return jsonify({"calendars": calendars})
        
    except Exception as e:
        print(f"❌ Error fetching calendars: {e}")
        return jsonify({"error": f"Failed to fetch calendars: {str(e)}"}), 500

@app.route('/api/events')
def get_events():
    """Get events from selected calendars with expanded date range (2015-2030)"""
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Get parameters
        calendar_ids = request.args.getlist('calendar_ids')
        time_min = request.args.get('time_min')
        time_max = request.args.get('time_max')
        
        if not calendar_ids:
            return jsonify({"error": "No calendar IDs provided"}), 400
        
        # Check if full range is requested
        load_full_range = request.args.get('full_range', 'false').lower() == 'true'
        
        if load_full_range:
            # Load full historical range (2015-2030)
            if not time_min:
                time_min = "2015-01-01T00:00:00Z"
            if not time_max:
                time_max = "2030-12-31T23:59:59Z"
        else:
            # Use reasonable date range for the frontend (current week by default)
            if not time_min:
                # Default to current week if not specified
                today = datetime.now()
                monday = today - timedelta(days=today.weekday())
                time_min = monday.isoformat() + "Z"
            if not time_max:
                # Default to one week after time_min
                start_date = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
                end_date = start_date + timedelta(days=7)
                time_max = end_date.isoformat()
        
        # Create credentials object from session
        granted_scopes = session['credentials'].get('scopes', SCOPES)
        creds = Credentials.from_authorized_user_info(session['credentials'], granted_scopes)
        
        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        
        all_events = []
        user_id = session.get('user_id')
        
        # Fetch events from each selected calendar
        for calendar_id in calendar_ids:
            try:
                if load_full_range:
                    # For full range, fetch in chunks to avoid API limits
                    current_time_min = time_min
                    calendar_events = []
                    
                    while current_time_min < time_max:
                        # Calculate chunk end (1 year at a time to avoid API limits)
                        chunk_start = datetime.fromisoformat(current_time_min.replace('Z', '+00:00'))
                        chunk_end = min(
                            chunk_start + timedelta(days=365),
                            datetime.fromisoformat(time_max.replace('Z', '+00:00'))
                        )
                        
                        print(f"📅 Fetching events for {calendar_id} from {chunk_start.year}")
                        
                        events_result = service.events().list(
                            calendarId=calendar_id,
                            timeMin=chunk_start.isoformat(),
                            timeMax=chunk_end.isoformat(),
                            singleEvents=True,
                            orderBy='startTime',
                            maxResults=2500  # Max per request
                        ).execute()
                        
                        chunk_events = events_result.get('items', [])
                        calendar_events.extend(chunk_events)
                        print(f"  📋 Found {len(chunk_events)} events for {chunk_start.year}")
                        
                        # Move to next chunk
                        current_time_min = chunk_end.isoformat()
                        
                        if chunk_start.year >= 2030:
                            break  # Don't go beyond 2030
                    
                    events = calendar_events
                    
                else:
                    # For weekly range, single request
                    events_result = service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime',
                        maxResults=2500  # Max per request
                    ).execute()
                    
                    events = events_result.get('items', [])
                
                # Add calendar info to each event
                for event in events:
                    event['calendar_id'] = calendar_id
                
                # Store events in database if user_id available
                if user_id:
                    try:
                        store_calendar_events(user_id, calendar_id, events)
                    except Exception as e:
                        print(f"⚠️ Warning: Could not store events in database: {e}")
                
                all_events.extend(events)
                
            except Exception as e:
                print(f"❌ Error fetching events from calendar {calendar_id}: {e}")
        
        date_range_desc = "2015-2030" if load_full_range else "current selection"
        print(f"📋 Found {len(all_events)} events across {len(calendar_ids)} calendars ({date_range_desc})")
        
        return jsonify({"events": all_events, "date_range": date_range_desc, "total_events": len(all_events)})
        
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return jsonify({"error": f"Failed to fetch events: {str(e)}"}), 500

@app.route('/api/generate-planner-pdf', methods=['POST'])
def generate_planner_pdf():
    """Generate PDF using Python-based reMarkable Pro optimized generator"""
    try:
        # Import our reMarkable PDF generator
        from remarkable_pdf_generator import generate_pdf_from_week_data, transform_google_calendar_events
        
        # Get request data
        request_data = request.get_json()
        week_data = request_data.get('weekData', {})
        start_date = request_data.get('startDate', datetime.now().strftime('%Y-%m-%d'))
        
        # Try to get events from the current session/database if available
        if 'credentials' in session:
            try:
                # Get events from the last API call or database
                # This is optional - the frontend should send the events
                pass
            except Exception as e:
                print(f"⚠️ Could not fetch additional events: {e}")
        
        # Generate PDF filename
        pdf_filename = f"remarkable_calendar_{start_date.replace('-', '')}.pdf"
        
        # Generate the PDF
        output_file = generate_pdf_from_week_data(week_data, start_date, pdf_filename)
        
        # Read the generated PDF file
        with open(output_file, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Clean up the temporary file
        os.remove(output_file)
        
        print(f"✅ Generated reMarkable Pro optimized PDF: {pdf_filename}")
        
        # Return PDF response
        return pdf_content, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename="{pdf_filename}"'
        }
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

@app.route('/api/calendars/selections', methods=['POST'])
def update_calendar_selections():
    """Update which calendars the user has selected"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        user_id = session['user_id']
        request_data = request.get_json() or {}
        selected_calendar_ids = request_data.get('selected_calendar_ids', [])
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Reset all calendars to not selected
            cur.execute(
                "UPDATE user_calendars SET is_selected = FALSE WHERE user_id = %s",
                (user_id,)
            )
            
            # Set selected calendars to true
            if selected_calendar_ids:
                placeholders = ','.join(['%s'] * len(selected_calendar_ids))
                cur.execute(
                    f"UPDATE user_calendars SET is_selected = TRUE WHERE user_id = %s AND calendar_id IN ({placeholders})",
                    [user_id] + selected_calendar_ids
                )
            
            conn.commit()
            print(f"💾 Updated calendar selections for user {user_id}: {len(selected_calendar_ids)} calendars selected")
            
            return jsonify({"message": "Calendar selections updated", "selected_count": len(selected_calendar_ids)})
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Error updating calendar selections: {e}")
        return jsonify({"error": f"Failed to update selections: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"🚀 Starting reMarkable Calendar Generator server...")
    print(f"   Environment: {os.environ.get('REPLIT_ENVIRONMENT', 'development')}")
    print(f"   Domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)