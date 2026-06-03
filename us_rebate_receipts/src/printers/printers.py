import os
from PIL import Image

class PngPrinter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def print_receipt(self, img: Image.Image, filename: str):
        path = os.path.join(self.output_dir, filename)
        img.save(path)
        return path

class DirectPrinter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def print_receipt(self, data: bytes, filename: str):
        """Mock implementation that saves raw bytes to a .bin file and logs."""
        path = os.path.join(self.output_dir, filename)
        with open(path, "wb") as f:
            f.write(data)
        print(f"[DirectPrinter Mock] Sent {len(data)} bytes to printer (saved to {path})")
        return path
