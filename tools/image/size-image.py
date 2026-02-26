#!/usr/bin/env python3
"""Resize a PNG image to 640x400."""

import sys
from PIL import Image


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <image.png>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    img = Image.open(path)
    img = img.resize((640, 400), Image.LANCZOS)
    img.save(path)
    print(f"Resized {path} to 640x400")


if __name__ == "__main__":
    main()
