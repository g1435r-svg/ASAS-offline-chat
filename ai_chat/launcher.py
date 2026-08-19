"""
ASAS – GUI launcher.
Opens the Flask web server in a background thread and launches the browser.
On first run (no model found) shows a download dialog so the user can fetch
a GGUF model without touching the command line.
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


def _models_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def _has_model() -> bool:
    d = _models_dir()
    return os.path.isdir(d) and any(f.endswith(".gguf") for f in os.listdir(d))


def _run_server() -> None:
    """Start the Flask app (imported here to keep the GUI responsive)."""
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)

    from app import app  # noqa: PLC0415

    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


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

        def _hook(count: int, block: int, total: int) -> None:
            if total > 0:
                pct = min(100, count * block * 100 // total)
                self._progress["value"] = pct
                mb = count * block / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                self._status.config(text=f"{pct}%  {mb:.0f}/{mb_total:.0f} MB")
                self.update_idletasks()

        def _download() -> None:
            try:
                urllib.request.urlretrieve(info["url"], dest, reporthook=_hook)
                self._status.config(text="ההורדה הושלמה!")
                messagebox.showinfo(
                    "הורדה הושלמה",
                    f"המודל נשמר:\n{dest}",
                    parent=self,
                )
                self.destroy()
            except Exception as exc:
                if os.path.isfile(dest):
                    os.remove(dest)
                messagebox.showerror("שגיאה", f"ההורדה נכשלה:\n{exc}", parent=self)
                self._dl_btn.config(state="normal")
                self._combo.config(state="readonly")
                self._status.config(text="")
                self._progress["value"] = 0

        threading.Thread(target=_download, daemon=True).start()


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
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
            self.destroy()
            os._exit(0)


def main() -> None:
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    root = LauncherApp()

    # Show download dialog on first run if no model exists.
    if not _has_model():
        root.after(200, lambda: DownloadDialog(root))
    else:
        # Open browser automatically after the server has had time to start.
        root.after(1500, lambda: webbrowser.open(URL))

    root.mainloop()


if __name__ == "__main__":
    main()
