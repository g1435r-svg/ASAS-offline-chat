"""
ASAS – GUI launcher.
Opens the Flask web server in a background subprocess and launches the browser.
On first run (no model found) shows a download dialog so the user can fetch
a GGUF model without touching the command line.
"""

import os
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox


HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

MODELS = {
    "Mistral 7B Instruct Q4_K_M (~4.1 GB) – מומלץ": {
        "url": (
            "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
            "/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        ),
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    },
    "Llama 3.2 1B Instruct Q8_0 (~1.3 GB) – קטן ומהיר": {
        "url": (
            "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF"
            "/resolve/main/Llama-3.2-1B-Instruct-Q8_0.gguf"
        ),
        "filename": "Llama-3.2-1B-Instruct-Q8_0.gguf",
    },
}


def _app_dir() -> str:
    """Return the writable application directory.

    When running as a PyInstaller frozen executable the models live next to the
    EXE (``sys.executable``), not inside the bundled ``_MEIPASS`` resources.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _models_dir() -> str:
    return os.path.join(_app_dir(), "models")


def _has_model() -> bool:
    d = _models_dir()
    return os.path.isdir(d) and any(f.endswith(".gguf") for f in os.listdir(d))


def _run_server() -> "subprocess.Popen":
    """Start the Flask app in a child process and return the handle."""
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        # Frozen: run the bundled server entry-point executable
        exe_name = "ASAS_server.exe" if sys.platform == "win32" else "ASAS_server"
        server_exe = os.path.join(os.path.dirname(sys.executable), exe_name)
        cmd = [server_exe]
    else:
        cmd = [sys.executable, os.path.join(pkg_dir, "app.py")]
    return subprocess.Popen(cmd)


class DownloadDialog(tk.Toplevel):
    """Shown on first run when no model is present."""

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("ASAS – הורדת מודל")
        self.resizable(False, False)
        self.grab_set()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="לא נמצא מודל – יש להוריד מודל להפעלה",
            font=("Segoe UI", 11, "bold"),
            wraplength=380,
        ).pack(pady=(0, 12))

        ttk.Label(frame, text="בחר מודל:").pack(anchor="w")
        self._choice = tk.StringVar()
        choices = list(MODELS.keys())
        self._choice.set(choices[0])
        self._combo = ttk.Combobox(
            frame, textvariable=self._choice, values=choices,
            state="readonly", width=50,
        )
        self._combo.pack(fill="x", pady=(4, 12))

        self._progress = ttk.Progressbar(frame, mode="determinate", length=400)
        self._progress.pack(fill="x", pady=(0, 6))

        self._status = ttk.Label(frame, text="")
        self._status.pack(pady=(0, 12))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")
        self._dl_btn = ttk.Button(btn_row, text="הורד", command=self._start_download)
        self._dl_btn.pack(side="right", padx=(4, 0))
        ttk.Button(btn_row, text="ביטול", command=self.destroy).pack(side="right")

    def _start_download(self) -> None:
        import urllib.request

        self._dl_btn.config(state="disabled")
        self._combo.config(state="disabled")
        info = MODELS[self._choice.get()]
        dest_dir = _models_dir()
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, info["filename"])

        # Shared state updated by the worker thread; read by the UI via after().
        self._dl_state: dict = {"pct": 0, "mb": 0.0, "mb_total": 0.0, "done": False, "error": None}
        _lock = threading.Lock()

        def _hook(count: int, block: int, total: int) -> None:
            if total > 0:
                pct = min(100, count * block * 100 // total)
                mb = count * block / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                with _lock:
                    self._dl_state["pct"] = pct
                    self._dl_state["mb"] = mb
                    self._dl_state["mb_total"] = mb_total

        def _poll() -> None:
            with _lock:
                state = dict(self._dl_state)
            if state["error"] is not None:
                messagebox.showerror("שגיאה", f"ההורדה נכשלה:\n{state['error']}", parent=self)
                self._dl_btn.config(state="normal")
                self._combo.config(state="readonly")
                self._status.config(text="")
                self._progress["value"] = 0
                return
            if state["done"]:
                self._progress["value"] = 100
                self._status.config(text="ההורדה הושלמה!")
                messagebox.showinfo("הורדה הושלמה", f"המודל נשמר:\n{dest}", parent=self)
                self.destroy()
                return
            self._progress["value"] = state["pct"]
            self._status.config(text=f"{state['pct']}%  {state['mb']:.0f}/{state['mb_total']:.0f} MB")
            self.after(300, _poll)

        def _download() -> None:
            try:
                urllib.request.urlretrieve(info["url"], dest, reporthook=_hook)
                with _lock:
                    self._dl_state["done"] = True
            except Exception as exc:
                if os.path.isfile(dest):
                    os.remove(dest)
                with _lock:
                    self._dl_state["error"] = str(exc)

        threading.Thread(target=_download, daemon=True).start()
        self.after(300, _poll)


class LauncherApp(tk.Tk):
    def __init__(self, server_proc: "subprocess.Popen") -> None:
        super().__init__()
        self._server_proc = server_proc
        self.title("ASAS – בינה מלאכותית בעברית")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="ASAS – בינה מלאכותית בעברית",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 6))

        ttk.Label(
            frame,
            text=f"השרת פועל בכתובת {URL}",
        ).pack(pady=(0, 20))

        ttk.Button(
            frame, text="פתח בדפדפן", command=self._open_browser
        ).pack(fill="x", pady=4)
        ttk.Button(
            frame, text="הורד מודל", command=self._open_download
        ).pack(fill="x", pady=4)
        ttk.Button(
            frame, text="עצור ויצא", command=self._quit
        ).pack(fill="x", pady=4)

    def _open_browser(self) -> None:
        webbrowser.open(URL)

    def _open_download(self) -> None:
        DownloadDialog(self)

    def _quit(self) -> None:
        if messagebox.askyesno("יציאה", "לעצור את השרת ולצאת?"):
            try:
                self._server_proc.terminate()
                try:
                    self._server_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._server_proc.kill()
            finally:
                self.destroy()
                sys.exit(0)


def main() -> None:
    server_proc = _run_server()

    root = LauncherApp(server_proc)

    # Show download dialog on first run if no model exists.
    if not _has_model():
        root.after(200, lambda: DownloadDialog(root))
    else:
        # Open browser automatically after the server has had time to start.
        root.after(1500, lambda: webbrowser.open(URL))

    root.mainloop()


if __name__ == "__main__":
    main()
