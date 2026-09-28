const http = require("http");

const server = http.createServer((req, res) => {
  res.end("Hello from demoapp v2.0");
});

server.listen(80);