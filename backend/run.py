import threading
import webbrowser
import uvicorn

from app.core.config import HOST, PORT
from app.main import app

def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, reload=False)