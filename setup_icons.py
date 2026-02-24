"""
Generate tray icons from the icon pack's pre-rendered PNGs.

Copies the base icon at multiple sizes and creates green/red
tinted versions as both ICO (multi-size) and individual PNGs.
"""

import os
from PIL import Image

SRC = r"C:\Tools\Trip - Tray IP\assets\icon_pack"
DST = r"C:\Tools\Trip - Tray IP\src\assets"

os.makedirs(DST, exist_ok=True)

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def load_source(size):
    """Load the pre-rendered PNG at the given size from the icon pack."""
    path = os.path.join(SRC, f"image3_flat_globe_magnifier_{size}x{size}.png")
    if os.path.isfile(path):
        return Image.open(path).convert("RGBA")
    # Fallback: resize from 256
    big = Image.open(os.path.join(SRC, "image3_flat_globe_magnifier_256x256.png")).convert("RGBA")
    return big.resize((size, size), Image.LANCZOS)


def tint_image(img, color):
    """Apply a colour tint preserving alpha."""
    r, g, b = color
    result = img.copy()
    pixels = result.load()
    for x in range(result.width):
        for y in range(result.height):
            pr, pg, pb, pa = pixels[x, y]
            if pa > 0:
                nr = min(255, int(pr * 0.35 + r * 0.65))
                ng = min(255, int(pg * 0.35 + g * 0.65))
                nb = min(255, int(pb * 0.35 + b * 0.65))
                pixels[x, y] = (nr, ng, nb, pa)
    return result


def save_multi_size_ico(get_frame, output_path):
    """Save an ICO with per-size frames (each from its own source PNG)."""
    frames = [get_frame(s) for s in ICO_SIZES]
    largest = frames[-1]  # 256x256
    largest.save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
    )


# ── Base (untinted) ─────────────────────────────────────────────
save_multi_size_ico(load_source, os.path.join(DST, "trip_icon.ico"))
load_source(256).save(os.path.join(DST, "trip_icon.png"), format="PNG")

# Also save individual PNG sizes for tray use
for s in [32, 48, 64]:
    load_source(s).save(os.path.join(DST, f"trip_icon_{s}.png"), format="PNG")

# ── Green tinted ─────────────────────────────────────────────────
green_color = (34, 197, 94)
save_multi_size_ico(
    lambda s: tint_image(load_source(s), green_color),
    os.path.join(DST, "trip_icon_green.ico"),
)
for s in [32, 48, 64]:
    tint_image(load_source(s), green_color).save(
        os.path.join(DST, f"trip_icon_green_{s}.png"), format="PNG"
    )

# ── Red tinted ───────────────────────────────────────────────────
red_color = (239, 68, 68)
save_multi_size_ico(
    lambda s: tint_image(load_source(s), red_color),
    os.path.join(DST, "trip_icon_red.ico"),
)
for s in [32, 48, 64]:
    tint_image(load_source(s), red_color).save(
        os.path.join(DST, f"trip_icon_red_{s}.png"), format="PNG"
    )

print("All icons generated!")
for f in sorted(os.listdir(DST)):
    if f.startswith("trip_icon"):
        size = os.path.getsize(os.path.join(DST, f))
        print(f"  {f} ({size:,} bytes)")
