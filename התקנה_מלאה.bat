@echo off
chcp 65001 >nul
cd /d "%~dp0"
title התקנה מלאה - בינה מלאכותית בעברית

echo ============================================
echo   התקנה מלאה - בינה מלאכותית בעברית
echo   צעד אחד - הכל אוטומטי!
echo ============================================
echo.

:: ── 1. Check Python ────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo שגיאה: Python לא מותקן או לא נמצא ב-PATH.
    echo הורד Python מ: https://www.python.org/downloads/
    echo.
    echo טיפ: בהתקנת Python - סמן "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/5] Python נמצא:
python --version
echo.

:: ── 2. Create venv ─────────────────────────────────────────────────────────
echo [2/5] מכין סביבה וירטואלית...
if not exist "ai_chat\venv\" (
    python -m venv ai_chat\venv
    if errorlevel 1 (
        echo שגיאה: יצירת הסביבה הוירטואלית נכשלה.
        pause
        exit /b 1
    )
)
call ai_chat\venv\Scripts\activate.bat
echo       הסביבה הוירטואלית מוכנה.
echo.

:: ── 3. Install dependencies ────────────────────────────────────────────────
echo [3/5] מתקין תלויות (זה עשוי לקחת מספר דקות)...
echo       שלב 1: מתקין llama-cpp-python (גרסה מוכנה - ללא קומפילציה)...
pip install --prefer-binary --no-cache-dir "llama-cpp-python>=0.2.0" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
if errorlevel 1 (
    echo.
    echo שגיאה: התקנת llama-cpp-python נכשלה.
    pause
    exit /b 1
)
echo       שלב 2: מתקין שאר התלויות...
pip install --no-cache-dir flask colorama
if errorlevel 1 (
    echo.
    echo שגיאה: התקנת התלויות נכשלה.
    pause
    exit /b 1
)
echo       התלויות הותקנו בהצלחה.
echo.

:: ── 4. Download the default model ──────────────────────────────────────────
echo [4/5] מוריד את המודל הקטן והמהיר בפעם הראשונה...
python ai_chat\download_model.py --small
if errorlevel 1 (
    echo.
    echo שגיאה: הורדת המודל נכשלה.
    echo בדוק את חיבור האינטרנט ונסה שוב.
    pause
    exit /b 1
)
echo.

:: ── 5. Launch automatically ────────────────────────────────────────────────
echo [5/5] ההתקנה הושלמה בהצלחה!
echo.
echo מפעיל את ממשק השיחה בדפדפן...
call "%~dp0הפעל_WEB.bat"
exit /b %errorlevel%

:done
echo.
echo להפעלה מחדש בעתיד:
echo   הפעל_WEB.bat  - ממשק ווב
echo   הפעל_CLI.bat  - שורת פקודה
echo.
pause
