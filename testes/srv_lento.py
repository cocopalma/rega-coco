# servidor local que pode atrasar as páginas (index.html e /) quando existe o ficheiro /tmp/.../lento
import http.server, socketserver, os, sys, time, functools
RAIZ, PORTA, FLAG, LOG = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        with open(LOG, 'a') as f: f.write(self.path + '\n')
        if os.path.exists(FLAG) and (self.path in ('/', '/index.html') or self.path.startswith('/index.html')): time.sleep(8)
        return super().do_GET()
    def log_message(self, *a): pass
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True
S(('', PORTA), functools.partial(H, directory=RAIZ)).serve_forever()
