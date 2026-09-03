"""
start_local.py  –  Launch CyberReport locally with a public ngrok URL.

Usage:
    python start_local.py

What it does:
  1. Starts Flask on port 5000 (in the background)
  2. Starts an ngrok tunnel pointing to port 5000
  3. Reads the public ngrok URL from the ngrok API
  4. Regenerates the QR code with the real public URL
  5. Prints the install link to share with anyone
"""
import subprocess
import sys
import time
import os
import json
import threading
import urllib.request

PORT = 5000
NGROK_API = "http://127.0.0.1:4040/api/tunnels"


def start_flask():
    """Run Flask in a background thread."""
    env = os.environ.copy()
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in proc.stdout:
        print("[Flask]", line.decode(errors="ignore").rstrip())


def start_ngrok():
    """Start ngrok tunnel."""
    NGROK_FALLBACK = r"C:\Users\KYEMWA RICHARD\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
    import shutil
    ngrok_cmd = shutil.which("ngrok") or NGROK_FALLBACK
    proc = subprocess.Popen(
        [ngrok_cmd, "http", str(PORT), "--log=stdout"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for line in proc.stdout:
        txt = line.decode(errors="ignore").rstrip()
        if "error" in txt.lower() and "authtoken" in txt.lower():
            print("[ngrok] ERROR: Auth token not set.")
            print("[ngrok] Run:  ngrok config add-authtoken YOUR_TOKEN")
            print("[ngrok] Get a free token at: https://dashboard.ngrok.com/get-started/your-authtoken")
        # Only print important ngrok lines
        if any(k in txt for k in ["started", "tunnel", "err", "ERR", "url="]):
            print("[ngrok]", txt)


def get_ngrok_url(retries=15, delay=1.5):
    """Poll the ngrok local API until a tunnel URL is available."""
    for i in range(retries):
        try:
            with urllib.request.urlopen(NGROK_API, timeout=3) as r:
                data = json.loads(r.read())
                for tunnel in data.get("tunnels", []):
                    url = tunnel.get("public_url", "")
                    if url.startswith("https://"):
                        return url
        except Exception:
            pass
        time.sleep(delay)
    return None


def generate_qr(url):
    """Regenerate the QR code PNG for the given URL."""
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
        from PIL import Image

        qr_path = os.path.join("static", "qr", "app_qr.png")
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
        ).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, (0, 0), img)
        bg.convert("RGB").save(qr_path)
        print(f"[QR]    Saved to {qr_path}")
    except Exception as e:
        print(f"[QR]    WARNING: Could not generate QR: {e}")


def main():
    print("=" * 60)
    print("  CyberReport – Local + Public Launcher")
    print("=" * 60)

    # 1. Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print(f"[Flask] Starting on http://localhost:{PORT} ...")
    time.sleep(2)

    # 2. Start ngrok in background thread
    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()
    print("[ngrok] Starting tunnel ...")

    # 3. Get the public URL
    public_url = get_ngrok_url()

    if not public_url:
        print("\n[ERROR] Could not get ngrok URL.")
        print("  Make sure ngrok is installed and you have added your auth token:")
        print("  ngrok config add-authtoken YOUR_TOKEN")
        print("  Get token: https://dashboard.ngrok.com/get-started/your-authtoken")
        print(f"\n  App is still running locally: http://localhost:{PORT}")
    else:
        install_url = public_url + "/install"
        # Set env var so Flask serves the correct URL in the QR page
        os.environ["APP_PUBLIC_URL"] = public_url

        # 4. Regenerate QR code with real public URL
        print(f"[ngrok] Public URL: {public_url}")
        generate_qr(install_url)

        print()
        print("=" * 60)
        print("  ✅ YOUR APP IS LIVE!")
        print("=" * 60)
        print(f"  🌐 App URL:     {public_url}")
        print(f"  📲 Install URL: {install_url}")
        print(f"  📷 QR Code:     static/qr/app_qr.png")
        print()
        print("  Share the Install URL or QR code with anyone!")
        print("  They can scan it and install the app on their phone.")
        print("=" * 60)
        print()
        print("  Press Ctrl+C to stop the server.")
        print()

    # 5. Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")


if __name__ == "__main__":
    main()

