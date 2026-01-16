import http.server
import socketserver
import webbrowser
import os
import sys

# Change directory to the script's directory (frontend/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 5500
Handler = http.server.SimpleHTTPRequestHandler
try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Frontend serving at http://localhost:{PORT}")
        print("Opening browser...")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()
except OSError as e:
    print(f"Error starting server: {e}")
    print(f"Try running: python -m http.server {PORT}")
