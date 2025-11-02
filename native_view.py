import os
import sys
import webbrowser

URL = os.environ.get('APP_URL', 'http://localhost:5000')
TITLE = 'Electronic Components Inventory'

def open_browser():
    try:
        webbrowser.open(URL)
    except Exception:
        pass

def open_app_mode():
    # Try Chromium/Chrome/Brave app mode (no chrome UI)
    candidates = [
        'google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium', 'brave-browser'
    ]
    for exe in candidates:
        path = None
        try:
            import shutil
            path = shutil.which(exe)
        except Exception:
            path = None
        if path:
            args = [
                path,
                f'--app={URL}',
                '--new-window',
                '--window-size=1200,800',
            ]
            try:
                import subprocess
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
    return False

def launch_webview():
    try:
        import webview
    except Exception as e:
        print('[native_view] pywebview not available:', e)
        open_browser()
        return

    try:
        window = webview.create_window(
            TITLE,
            URL,
            width=1200,
            height=800,
            resizable=True,
            frameless=True,
            easy_drag=True,
            background_color='#0f172a'
        )
        # Prefer QT if present (with PyQt5/qtpy), else fallback to GTK
        try:
            webview.start(gui='qt')
            return
        except Exception as e_qt:
            print('[native_view] Qt backend failed, trying GTK:', e_qt)
            try:
                webview.start(gui='gtk')
                return
            except Exception as e_gtk:
                print('[native_view] GTK backend failed:', e_gtk)
    except Exception as e:
        print('[native_view] error creating window:', e)

    # Final fallback
    if not open_app_mode():
        open_browser()

if __name__ == '__main__':
    launch_webview()


