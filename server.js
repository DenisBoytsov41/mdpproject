const http = require('http');
const url = require('url');

const PORT = 8080;

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);

  if (parsedUrl.pathname === '/') {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end('<html><body><h1>Hello, World!</h1></body></html>');
  } else {
    res.writeHead(404, {'Content-Type': 'text/plain'});
    res.end('Not found');
  }
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});
