#!/usr/bin/env python3
"""
Unified System Tray Application for Electronic Component Inventory
Combines server management and tray functionality in a single script.

Features:
- Starts Flask server automatically
- System tray icon with menu options
- Native view support with browser fallback
- Automatic server health checking
"""

import os
import sys
import threading
import time
import webbrowser
import subprocess
from PIL import Image, ImageDraw
import pystray

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

URL = 'http://localhost:5000'
TITLE = 'Electronic Component Inventory'

class UnifiedTrayApp:
    """Unified application that combines server management and system tray functionality"""

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.script_dir, 'frontend', 'static', 'images', 'electronic-inventory-tray.png')
        self.server_process = None
        self.icon = None
        self.server_thread = None

    def create_icon(self):
        """Create the system tray icon with better error handling"""
        print(f"[TrayApp] Looking for icon at: {self.icon_path}")

        # Try to load the tray icon image
        if os.path.exists(self.icon_path):
            try:
                image = Image.open(self.icon_path)
                print(f"[TrayApp] Icon loaded successfully: {image.size}, mode: {image.mode}")
                return image
            except Exception as e:
                print(f"[TrayApp] Error loading PNG icon: {e}")

        # Fallback: Create a simple colored icon
        print("[TrayApp] Creating default icon")
        image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a circuit board pattern
        draw.rectangle([4, 4, 28, 28], fill=(30, 58, 138, 255))  # Blue background
        draw.rectangle([8, 8, 24, 24], fill=(59, 130, 246, 255))  # Lighter blue

        # Draw some "components" (small rectangles)
        draw.rectangle([10, 10, 14, 14], fill=(239, 68, 68, 255))  # Red resistor
        draw.rectangle([18, 10, 22, 14], fill=(34, 197, 94, 255))  # Green capacitor
        draw.rectangle([10, 18, 14, 22], fill=(251, 191, 36, 255))  # Yellow IC
        draw.rectangle([18, 18, 22, 22], fill=(168, 85, 247, 255))  # Purple transistor

        return image

    def is_server_running(self):
        """Check if Flask server is running on port 5000"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"[TrayApp] Error checking server status: {e}")
            return False

    def start_server(self):
        """Start the Flask server in background thread"""
        if self.is_server_running():
            print("[TrayApp] Server already running")
            return

        def run_server():
            try:
                print("[TrayApp] Starting Flask server...")
                sys.stdout.flush()

                # Use the new backend structure
                app_path = os.path.join(self.script_dir, 'backend', 'app.py')
                if not os.path.exists(app_path):
                    # Fallback to old structure
                    app_path = os.path.join(self.script_dir, 'app.py')
                    print(f"[TrayApp] Using fallback app path: {app_path}")

                print(f"[TrayApp] Executing: {sys.executable} {app_path}")
                sys.stdout.flush()

                # Prepare environment with correct Python path
                env = os.environ.copy()
                env['PYTHONPATH'] = self.script_dir
                env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output

                print(f"[TrayApp] PYTHONPATH: {env['PYTHONPATH']}")
                sys.stdout.flush()

                # Start server with output capture for logging
                self.server_process = subprocess.Popen(
                    [sys.executable, app_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stdout and stderr
                    cwd=self.script_dir,
                    env=env,  # Use modified environment
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                print("[TrayApp] Server process started")
                sys.stdout.flush()

                # Log server output in background
                def log_server_output():
                    if self.server_process.stdout:
                        for line in self.server_process.stdout:
                            print(f"[Server] {line.strip()}")
                            sys.stdout.flush()

                log_thread = threading.Thread(target=log_server_output, daemon=True)
                log_thread.start()

                # Wait for server to initialize
                print("[TrayApp] Waiting for server to initialize...")
                sys.stdout.flush()
                time.sleep(5)  # Increased wait time

                if self.is_server_running():
                    print("[TrayApp] ✅ Server is running and accessible at http://localhost:5000")
                    sys.stdout.flush()
                else:
                    print("[TrayApp] ⚠️  Warning: Server may not be accessible")
                    sys.stdout.flush()

            except Exception as e:
                print(f"[TrayApp] ❌ Error starting server: {e}")
                sys.stdout.flush()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Give thread time to start
        time.sleep(1)

    def open_browser(self, icon=None, item=None):
        """Open application in web browser"""
        print("[TrayApp] Opening in web browser...")
        webbrowser.open(URL)

    def open_about_page(self, icon=None, item=None):
        """Open the about page in the browser"""
        print("[TrayApp] Opening about page...")
        webbrowser.open(f"{URL}/about")

    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        print("[TrayApp] Shutting down...")

        # Stop server process
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("[TrayApp] Server stopped")
            except Exception as e:
                print(f"[TrayApp] Error stopping server: {e}")
                try:
                    self.server_process.kill()
                except:
                    pass

        # Stop tray icon
        if self.icon:
            self.icon.stop()

        print("[TrayApp] Application closed")
        sys.exit(0)

    def run(self):
        """Run the unified tray application"""
        print(f"\n{'='*60}")
        print(f"[TrayApp] Starting {TITLE}")
        print(f"{'='*60}")
        print("[TrayApp] Features:")
        print("  ✅ Automatic Flask server management")
        print("  ✅ System tray icon with menu options")
        print("  ✅ Opens in your default web browser")
        print("  ✅ Real-time server logging")
        print(f"{'='*60}\n")
        sys.stdout.flush()

        try:
            # Start server immediately
            print("[TrayApp] Starting server in background...")
            sys.stdout.flush()
            self.start_server()

            # Create the icon
            print("[TrayApp] Creating system tray icon...")
            sys.stdout.flush()
            image = self.create_icon()

            # Create menu with more options
            menu = pystray.Menu(
                pystray.MenuItem("Open in Browser", self.open_browser, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("About", self.open_about_page),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self.quit_app)
            )

            # Create and run the icon
            self.icon = pystray.Icon(TITLE, image, menu=menu)
            self.icon.title = TITLE

            print("✅ [TrayApp] System tray icon created!")
            print("🔍 Look for the Electronic Component Inventory icon in your system tray.")
            print("👆 Right-click the icon to access menu options.")
            print("🛑 Press Ctrl+C to quit.")
            print()
            sys.stdout.flush()

            # Run the icon (this blocks until quit)
            self.icon.run()

        except KeyboardInterrupt:
            print("\n[TrayApp] Received keyboard interrupt")
            sys.stdout.flush()
            self.quit_app()
        except Exception as e:
            print(f"[TrayApp] Error running system tray: {e}")
            sys.stdout.flush()
            print("[TrayApp] Falling back to browser mode...")
            if not self.is_server_running():
                self.start_server()
                time.sleep(3)
            webbrowser.open(URL)

def main():
    """Main function"""
    print("=" * 60)
    print(f"  {TITLE}")
    print("  Unified System Tray Application")
    print("=" * 60)

    app = UnifiedTrayApp()
    app.run()

if __name__ == '__main__':
    main()
