"""Optional offline launcher for browsers that restrict sibling file:// frames."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser
root = Path(__file__).resolve().parent
for port in range(8000, 8011):
    try:
        server = ThreadingHTTPServer(('127.0.0.1', port), partial(SimpleHTTPRequestHandler, directory=str(root)))
        break
    except OSError:
        continue
else:
    raise SystemExit('8000–8010 端口均被占用，请关闭旧的实验台服务后重试。')
url = f'http://127.0.0.1:{port}/DOE_Catapult_Analysis.html'
print(f'离线投射器 DOE：{url}\n仅监听本机；按 Ctrl+C 关闭。', flush=True)
webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
