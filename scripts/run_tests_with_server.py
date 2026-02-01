"""
Start the backend Flask app in a background thread (no reloader), wait for it to be ready,
then run pytest programmatically and exit with the pytest return code.
"""
import threading
import time
import requests
import sys

# Ensure project root on sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.app as backend_app

from werkzeug.serving import make_server


def start_server():
    server = make_server('127.0.0.1', 5000, backend_app.app)
    server.serve_forever()


def wait_for_server(url='http://127.0.0.1:5000', timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code in (200, 404):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def main():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    print('Waiting for server to be ready on http://127.0.0.1:5000')
    if not wait_for_server('http://127.0.0.1:5000'):
        print('Server did not become ready in time', file=sys.stderr)
        sys.exit(2)

    print('Server ready — running pytest')

    import pytest
    return_code = pytest.main(['-q'])
    print(f'pytest finished with code {return_code}')
    sys.exit(return_code)


if __name__ == '__main__':
    main()
