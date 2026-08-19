"""
download_model.py – Download a GGUF model into ai_chat/models/.

Usage:
    python download_model.py           # Mistral 7B Instruct Q4_K_M  (~4.1 GB)  – recommended
    python download_model.py --small   # Llama 3.2 1B Instruct Q8_0  (~1.3 GB)  – fast & light
"""

import argparse
import os
import sys
import urllib.request

MODELS = {
    "mistral": {
        "url": (
            "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
            "/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        ),
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "desc": "Mistral 7B Instruct Q4_K_M (~4.1 GB) – מומלץ",
    },
    "llama1b": {
        "url": (
            "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF"
            "/resolve/main/Llama-3.2-1B-Instruct-Q8_0.gguf"
        ),
        "filename": "Llama-3.2-1B-Instruct-Q8_0.gguf",
        "desc": "Llama 3.2 1B Instruct Q8_0 (~1.3 GB) – קטן ומהיר",
    },
}


def models_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def _progress_hook(count: int, block_size: int, total_size: int) -> None:
    if total_size <= 0:
        print(f"\r  הורד: {count * block_size // (1024 * 1024)} MB", end="", flush=True)
        return
    pct = min(100, count * block_size * 100 // total_size)
    done = pct // 5
    bar = "█" * done + "░" * (20 - done)
    mb_done = count * block_size / (1024 * 1024)
    mb_total = total_size / (1024 * 1024)
    print(f"\r  [{bar}] {pct:3d}%  {mb_done:.0f}/{mb_total:.0f} MB", end="", flush=True)


def download(key: str) -> str:
    """Download the model and return the local file path."""
    info = MODELS[key]
    dest_dir = models_dir()
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, info["filename"])

    if os.path.isfile(dest):
        print(f"המודל כבר קיים: {dest}")
        return dest

    print(f"מוריד: {info['desc']}")
    print(f"כתובת: {info['url']}")
    print(f"יעד:   {dest}")
    print()

    try:
        urllib.request.urlretrieve(info["url"], dest, reporthook=_progress_hook)
    except Exception as exc:
        print(f"\nשגיאה בהורדה: {exc}", file=sys.stderr)
        if os.path.isfile(dest):
            os.remove(dest)
        sys.exit(1)

    print(f"\n\nההורדה הושלמה: {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="הורדת מודל GGUF לשימוש עם ASAS"
    )
    parser.add_argument(
        "--small",
        action="store_true",
        help="הורד את המודל הקטן (Llama 1B) במקום Mistral 7B",
    )
    parser.add_argument(
        "--url",
        default="",
        help="כתובת URL מותאמת אישית להורדת מודל GGUF",
    )
    parser.add_argument(
        "--filename",
        default="",
        help="שם קובץ מותאם אישית (נדרש עם --url)",
    )
    args = parser.parse_args()

    if args.url:
        if not args.filename:
            args.filename = args.url.split("/")[-1].split("?")[0] or "model.gguf"
        dest_dir = models_dir()
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, args.filename)
        if os.path.isfile(dest):
            print(f"הקובץ כבר קיים: {dest}")
            return
        print(f"מוריד: {args.url}")
        try:
            urllib.request.urlretrieve(args.url, dest, reporthook=_progress_hook)
        except Exception as exc:
            print(f"\nשגיאה: {exc}", file=sys.stderr)
            if os.path.isfile(dest):
                os.remove(dest)
            sys.exit(1)
        print(f"\nההורדה הושלמה: {dest}")
        return

    key = "llama1b" if args.small else "mistral"
    download(key)


if __name__ == "__main__":
    main()
