from PIL import Image
import math
import argparse


# Project a shadow using vertical scaling and horizontal shearing
def project_shadow(image: Image.Image, angle: float = 45.0, length: float = 0.5, shadow_alpha: int = 85):
    image = image.convert("RGBA")
    W, H = image.size
    alpha = image.split()[3].point(lambda a: 255 if a > 128 else 0)

    bbox = alpha.getbbox()
    if not bbox:
        return image

    l, t, r, b = bbox
    mask_h = b - t

    angle_rad = math.radians(angle)
    length = length * (0.8 + abs(math.cos(angle_rad)) * 0.2)

    target_h = max(3, int(round(mask_h * length * abs(math.cos(angle_rad)))))
    region = alpha.crop(bbox).resize((r - l, target_h), resample=Image.BICUBIC)

    squished = Image.new("L", (W, H), 0)
    paste_y = b - target_h
    squished.paste(region, (l, paste_y))

    shear_span_px = mask_h * length * abs(math.sin(angle_rad))
    direction = -1 if math.sin(angle_rad) >= 0 else 1
    den = max(1, target_h - 1)
    k = direction * (shear_span_px / den)
    if abs(k) < 1e-6:
        k = 0.0

    max_shift = int(math.ceil(abs(k) * (target_h - 1)))
    wide_W = W + 2 * max_shift
    wide_canvas = Image.new("L", (wide_W, H), 0)
    wide_canvas.paste(squished, (max_shift, 0))

    y0 = paste_y + target_h - 1
    sheared_wide = wide_canvas.transform(
        (wide_W, H),
        Image.AFFINE,
        (1.0, -k, k * y0, 0.0, 1.0, 0.0),
        resample=Image.NEAREST,
        fillcolor=0
    )

    sb = sheared_wide.getbbox()
    if sb is None:
        left_crop, right_crop = max_shift, max_shift + W
    else:
        orig_l, orig_r = max_shift, max_shift + W
        need_l = min(sb[0], orig_l)
        need_r = max(sb[2], orig_r)
        need_w = max(1, need_r - need_l)
        oc = orig_l + W * 0.5
        left_crop = int(math.floor(oc - need_w * 0.5))
        right_crop = left_crop + need_w
        if left_crop < 0:
            right_crop -= left_crop
            left_crop = 0
        if right_crop > wide_W:
            shift = right_crop - wide_W
            left_crop = max(0, left_crop - shift)
            right_crop = wide_W

    sheared_mask = sheared_wide.crop((left_crop, 0, right_crop, H))
    scaled_alpha = sheared_mask.point(lambda a: (a * shadow_alpha) // 255)

    shadow = Image.new("RGBA", (sheared_mask.width, H), (0, 0, 0, 0))
    shadow.putalpha(scaled_alpha)

    shadow = shadow.quantize(colors=3, method=Image.FASTOCTREE, dither=Image.NONE)
    return shadow.convert("RGBA")

# Sprite sheet helper
def shadow_sheet(image, grid, padding=0, shadow_alpha=85):
    img = image.convert("RGBA")
    W, H = img.size
    rows, cols = len(grid), len(grid[0]) if grid else 0

    # First pass: build shadows and find max tile size
    all_shadows = []
    maxW, maxH = W, H
    for row in grid:
        srow = []
        for deg, length in row:
            sh = project_shadow(img, angle=deg, length=length, shadow_alpha=shadow_alpha)
            srow.append(sh)
            sw, shh = sh.size
            if sw > maxW: maxW = sw
            if shh > maxH: maxH = shh
        all_shadows.append(srow)

    tileW, tileH = maxW, maxH
    sheet_W = cols * tileW + (cols - 1) * padding
    sheet_H = rows * tileH + (rows - 1) * padding
    sheet = Image.new("RGBA", (sheet_W, sheet_H), (255, 255, 255, 0))

    # Second pass: place centered tiles
    for r, row in enumerate(grid):
        for c, (deg, length) in enumerate(row):
            sh = all_shadows[r][c]
            tile = Image.new("RGBA", (tileW, tileH), (0, 0, 0, 0))
            # Center both shadow and original so alignment remains correct
            tile.alpha_composite(sh, ((tileW - sh.width) // 2, (tileH - sh.height) // 2))
            tile.alpha_composite(img, ((tileW - W) // 2, (tileH - H) // 2))
            sheet.alpha_composite(tile, (c * (tileW + padding), r * (tileH + padding)))
    return sheet


def main():
    ap = argparse.ArgumentParser(description="Add projected shadows to pixel art with transparency.")
    ap.add_argument("--input", required=True, help="Input image file or directory.")
    ap.add_argument("--output", default="out.png", help="Output image file or directory.")
    ap.add_argument("--angle", type=float, default=45.0, help="Shadow angle in degrees. Positive is to the right.")
    ap.add_argument("--length", type=float, default=0.5, help="Fraction of opaque height to scale shadow and reach.")
    ap.add_argument("--opacity", type=int, default=85, help="Alpha value for the shadows.")
    ap.add_argument("--sheet", action='store_true', help="Option to create a sheet or not.")
    args = ap.parse_args()


    SHADOW_GRID = [[(-45, 0.7), (0, 0.6), (45, 0.7)],
                [(-45, 0.5), (0, 0.5), (45, 0.5)],
                [(-45, 0.2), (0, 0.2), (45, 0.2)]]

    input_image = Image.open(args.input)

    if args.sheet:
        out = shadow_sheet(input_image, SHADOW_GRID, 0, args.opacity)
    else:
        out = project_shadow(input_image, args.angle, args.length, args.opacity)
        

    out.save(args.output)

if __name__ == "__main__":
    main()