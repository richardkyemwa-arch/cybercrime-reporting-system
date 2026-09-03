"""
Generate QR codes for the CyberReport app.
Usage:
  python generate_qr.py --url https://your-app.onrender.com
  python generate_qr.py  (uses the default placeholder URL)
"""
import sys
import os
import argparse
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw

def generate_qr(url: str, output_path: str = "static/qr/app_qr.png"):
    """Generate a styled QR code image for the given URL."""
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

    # Add a rounded white background
    size = img.size
    bg = Image.new("RGBA", size, (255, 255, 255, 255))
    bg.paste(img, (0, 0), img)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bg.convert("RGB").save(output_path)
    print(f"[OK] QR code saved to: {output_path}")
    print(f"[OK] URL encoded:      {url}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QR code for CyberReport app")
    parser.add_argument("--url", default="https://cyber-crime-reporting.onrender.com",
                        help="The public URL of the deployed app")
    parser.add_argument("--output", default="static/qr/app_qr.png",
                        help="Output path for the QR image")
    args = parser.parse_args()
    generate_qr(args.url, args.output)
