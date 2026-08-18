"""
ASAS – CLI chat interface.
Run with:  python chat_cli.py
"""

import os
import sys

try:
    import colorama
    colorama.init()
    GREEN = colorama.Fore.GREEN
    CYAN = colorama.Fore.CYAN
    YELLOW = colorama.Fore.YELLOW
    RESET = colorama.Style.RESET_ALL
except ImportError:
    GREEN = CYAN = YELLOW = RESET = ""

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

SYSTEM_PROMPT = (
    "You are a helpful AI assistant that speaks Hebrew fluently. "
    "Always respond in Hebrew unless the user explicitly writes in another language. "
    "Be friendly, accurate, and concise."
)


def find_model() -> str:
    model_path = os.environ.get("MODEL_PATH", "")
    if model_path and os.path.isfile(model_path):
        return model_path
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if os.path.isdir(models_dir):
        for fname in os.listdir(models_dir):
            if fname.endswith(".gguf"):
                return os.path.join(models_dir, fname)
    return ""


def build_prompt(history: list, user_message: str) -> str:
    prompt = f"<<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n"
    for turn in history[-10:]:
        prompt += f"[INST] {turn['user']} [/INST] {turn['assistant']}\n"
    prompt += f"[INST] {user_message} [/INST]"
    return prompt


def main() -> None:
    if not LLAMA_AVAILABLE:
        print(
            f"{YELLOW}שגיאה: llama-cpp-python אינו מותקן. "
            f"הרץ: pip install llama-cpp-python{RESET}"
        )
        sys.exit(1)

    model_path = find_model()
    if not model_path:
        print(
            f"{YELLOW}לא נמצא מודל. הנח קובץ .gguf בתיקיית models/ "
            f"או הגדר את משתנה הסביבה MODEL_PATH.{RESET}"
        )
        sys.exit(1)

    print(f"{CYAN}טוען מודל: {model_path}{RESET}")
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_threads=os.cpu_count() or 4,
        verbose=False,
    )
    print(f"{GREEN}המודל נטען. כתוב הודעה (או /יציאה ליציאה).{RESET}\n")

    history: list = []

    print(f"{YELLOW}פקודות: /יציאה  /היסטוריה  /נקה{RESET}\n")

    while True:
        try:
            user_input = input(f"{CYAN}אתה: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nלהתראות!")
            break

        if not user_input:
            continue

        # Hebrew slash commands
        if user_input in {"/יציאה", "exit", "quit", "bye"}:
            print("להתראות!")
            break

        if user_input == "/היסטוריה":
            if not history:
                print(f"{YELLOW}אין היסטוריית שיחה.{RESET}\n")
            else:
                for i, turn in enumerate(history, 1):
                    print(f"{CYAN}[{i}] אתה:{RESET} {turn['user']}")
                    print(f"{GREEN}[{i}] עוזר:{RESET} {turn['assistant']}\n")
            continue

        if user_input == "/נקה":
            history.clear()
            print(f"{YELLOW}ההיסטוריה נמחקה.{RESET}\n")
            continue

        prompt = build_prompt(history, user_input)
        try:
            output = llm(
                prompt,
                max_tokens=1024,
                stop=["[INST]", "</s>"],
                echo=False,
            )
            reply = output["choices"][0]["text"].strip()
        except Exception as exc:  # noqa: BLE001
            print(f"{YELLOW}שגיאה ביצירת תגובה: {exc}{RESET}")
            continue

        print(f"{GREEN}עוזר: {RESET}{reply}\n")
        history.append({"user": user_input, "assistant": reply})


if __name__ == "__main__":
    main()
