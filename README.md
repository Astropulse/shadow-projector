# Pixel Shadow Projector

A tiny Python tool that projects soft, angled shadows for pixel art with alpha transparency. It includes a CLI and a helper to build sprite sheets that combine the original image with its projected shadow at multiple angles and lengths.

The core idea:
1. Extract the opaque silhouette from the input image.
2. Scale it vertically to the desired shadow length.
3. Shear horizontally based on the angle.
4. Recenter and composite as a semi transparent shadow behind the original art.
5. Optionally assemble a grid of variants into a sprite sheet.

### Usage

Simply run `python shadow.py --input path/to/some/image.png`

### Arguments

| Argument     | Type   | Default   | Description |
|--------------|--------|-----------|-------------|
| `--input`    | str    | required  | Path to the input image (must have transparency). |
| `--output`   | str    | out.png   | Path to save the output image. |
| `--angle`    | float  | 45.0      | Shadow angle in degrees (positive = right, negative = left). |
| `--length`   | float  | 0.5       | Fraction of opaque height to scale the shadow length. |
| `--opacity`  | int    | 85        | Shadow opacity (0–255). |
| `--sheet`    | flag   | false     | Generate a sprite sheet using the built-in shadow grid. |
