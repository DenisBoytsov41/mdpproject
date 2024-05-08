import http.server
import ssl

def get_ssl_context(certfile, keyfile):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile, keyfile)
    context.set_ciphers("@SECLEVEL=1:ALL")
    return context

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        print(post_data.decode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello, world! This is a basic text content.')

server_address = ("127.0.0.1", 5000)
httpd = http.server.HTTPServer(server_address, MyHandler)

context = get_ssl_context("cert.pem", "key.pem")
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

httpd.serve_forever()
