
import os
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import json

class SecretInjectorHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # Read the HTML file
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Get secrets from environment variables
                google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
                
                # Inject the client ID into the HTML (never inject client secret to client-side)
                script_injection = f"""
                <script>
                    window.INJECTED_GOOGLE_CLIENT_ID = '{google_client_id}';
                </script>
                """
                
                # Insert before the closing head tag
                html_content = html_content.replace('</head>', script_injection + '</head>')
                
                # Send the modified HTML
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-Length', len(html_content.encode('utf-8')))
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
                
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            # For all other files, use default behavior
            super().do_GET()
    
    def do_POST(self):
        # Handle OAuth callback if needed
        if self.path == '/oauth2callback':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<script>window.close();</script>')
        else:
            super().do_POST()

def run_server(port=5000):
    handler = SecretInjectorHandler
    
    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        print(f"Server running at http://0.0.0.0:{port}")
        print(f"Google Client ID loaded: {'Yes' if os.getenv('GOOGLE_CLIENT_ID') else 'No'}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
