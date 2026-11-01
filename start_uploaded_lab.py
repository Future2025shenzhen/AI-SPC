"""Optional localhost launcher for browsers that restrict file:// popups."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
import webbrowser

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
    address=f'http://127.0.0.1:{server.server_port}/'+quote('投射器实验_优化版.html')
    print('投射器实验 / Catapult: '+address,flush=True)
    print('Keep this window open. Press Ctrl+C to stop.',flush=True)
    webbrowser.open(address)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
