"""
ASAS – GUI launcher.
Opens the Flask web server in a background thread and launches the browser.
Provides a simple Tkinter system-tray-style window to stop the server.
"""

import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox


HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"


def _run_server() -> None:
    """Start the Flask app (imported here to keep the GUI responsive)."""
    # Ensure the ai_chat package directory is on the path when running
    # as a frozen PyInstaller executable.
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)

    from app import app  # noqa: PLC0415

    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ASAS – Offline Hebrew AI Chat")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="ASAS – Offline Hebrew AI Chat",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 10))

        ttk.Label(
            frame,
            text=f"Server running at {URL}",
        ).pack(pady=(0, 20))

        ttk.Button(frame, text="Open in browser", command=self._open_browser).pack(
            fill="x", pady=4
        )
        ttk.Button(frame, text="Stop server & quit", command=self._quit).pack(
            fill="x", pady=4
        )

    def _open_browser(self) -> None:
        webbrowser.open(URL)

    def _quit(self) -> None:
        if messagebox.askyesno("Quit", "Stop the server and exit?"):
            self.destroy()
            os._exit(0)


def main() -> None:
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    app = LauncherApp()
    # Open browser automatically after a short delay so the server has time to start.
    app.after(1500, lambda: webbrowser.open(URL))
    app.mainloop()


if __name__ == "__main__":
    main()
