import qrcode
import os

# Change this to your computer's local IP (find using `ipconfig` on Windows or `ifconfig` on Mac/Linux)
LOCAL_IP = "111.111.11.11"  # Replace with your actual local IP

# Define menu URL
menu_url = f"https://random-subdomain.ngrok.io/static/index.html"

# Define folder to save the QR code
qr_folder = "static/qrcodes"
os.makedirs(qr_folder, exist_ok=True)

# Generate the QR Code
qr = qrcode.make(menu_url)

# Save QR Code
qr_path = os.path.join(qr_folder, "menu_qr.png")
qr.save(qr_path)

print(f"✅ QR Code generated successfully and saved at: {qr_path}")



