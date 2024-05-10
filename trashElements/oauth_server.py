import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8080

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    authorization_code = None

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        if 'code' in query:
            OAuthCallbackHandler.authorization_code = query['code'][0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Authentication Successful</title></head>')
            self.wfile.write(b'<body><p>Authentication successful! You can close this window now.</p></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

def run_authentication_server():
    httpd = HTTPServer(('localhost', PORT), OAuthCallbackHandler)
    print(f"Сервер запущен на порту {PORT}")

    try:
        httpd.handle_request()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run_authentication_server()
