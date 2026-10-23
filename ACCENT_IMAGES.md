# Images that carry the accent

Written by `tools/accent_images.py` (#86 A). Do not edit by hand: after adding or changing an image, run `python tools/accent_images.py`. `tests/test_accent_images.py` fails until this file is what the tool writes.

If the accent ever moves, the code moves it in ten lines; these images do not move with it. **shaded** art is hand-made and is remade by hand (#84). **flat** art could be recolored by swapping exact colors. A **screenshot** is retaken. A **fixture** is a test input. Accent: hue within 6 degrees of `BRAND_GOLD` or `BRAND_DARK_GOLD`, saturation and value at least 0.15; an image carries it from 1% of its pixels; flat means its three commonest accent colors cover at least 90% of them. The tool's docstring says why.

**39 images of art carry the accent, 38 of them distinct.**

| folder | files | shaded | flat | screenshot | fixture | none |
|---|---|---|---|---|---|---|
| `resources/background_images` | 1 | 1 | 0 | 0 | 0 | 0 |
| `resources/button_images` | 33 | 33 | 0 | 0 | 0 | 0 |
| `resources/icons` | 5 | 4 | 1 | 0 | 0 | 0 |
| `resources/screenshots` | 6 | 0 | 0 | 6 | 0 | 0 |
| `resources/test` | 2 | 0 | 0 | 0 | 2 | 0 |

## `resources/background_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `background.png` | 3840x2169 | 13.6% | 4748 | shaded |  |

## `resources/button_images`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `add-color-slot_base.png` | 834x167 | 29.8% | 2443 | shaded |  |
| `add-color-slot_hover.png` | 834x167 | 31.6% | 2259 | shaded |  |
| `add-color-slot_pressed.png` | 834x167 | 37.1% | 2447 | shaded |  |
| `copy-hex-color_base.png` | 834x167 | 30.9% | 2387 | shaded |  |
| `copy-hex-color_hover.png` | 834x167 | 30.9% | 2392 | shaded |  |
| `copy-hex-color_pressed.png` | 834x167 | 36.2% | 2131 | shaded |  |
| `export-palette_base.png` | 834x167 | 34.3% | 2120 | shaded |  |
| `export-palette_hover.png` | 834x167 | 32.0% | 2120 | shaded |  |
| `export-palette_pressed.png` | 834x167 | 39.0% | 2120 | shaded |  |
| `import-palette_base.png` | 834x167 | 31.9% | 2524 | shaded |  |
| `import-palette_hover.png` | 834x167 | 31.2% | 2358 | shaded |  |
| `import-palette_pressed.png` | 834x167 | 36.5% | 2120 | shaded |  |
| `remove_base.png` | 334x167 | 39.4% | 1638 | shaded |  |
| `remove_hover.png` | 334x167 | 43.4% | 1638 | shaded |  |
| `remove_pressed.png` | 334x167 | 51.4% | 1662 | shaded |  |
| `reset-canvas_base.png` | 834x167 | 33.7% | 2140 | shaded |  |
| `reset-canvas_hover.png` | 834x167 | 34.2% | 2135 | shaded |  |
| `reset-canvas_pressed.png` | 834x167 | 41.1% | 2811 | shaded |  |
| `reset-zoom_base.png` | 834x167 | 30.6% | 2361 | shaded |  |
| `reset-zoom_hover.png` | 834x167 | 30.9% | 2657 | shaded |  |
| `reset-zoom_pressed.png` | 834x167 | 39.8% | 2418 | shaded |  |
| `save-color-swatch_base.png` | 834x167 | 33.3% | 2281 | shaded |  |
| `save-color-swatch_hover.png` | 834x167 | 33.6% | 2281 | shaded |  |
| `save-color-swatch_pressed.png` | 834x167 | 40.2% | 2120 | shaded |  |
| `save-instruction_base.png` | 834x167 | 34.2% | 2298 | shaded |  |
| `save-instruction_hover.png` | 834x167 | 34.7% | 2444 | shaded |  |
| `save-instruction_pressed.png` | 834x167 | 39.0% | 2376 | shaded |  |
| `settings_gear_base.png` | 512x512 | 93.4% | 3390 | shaded |  |
| `settings_gear_hover.png` | 512x512 | 92.9% | 2888 | shaded |  |
| `settings_gear_pressed.png` | 512x512 | 93.1% | 3418 | shaded |  |
| `upload-image_base.png` | 834x167 | 31.5% | 2140 | shaded |  |
| `upload-image_hover.png` | 834x167 | 31.6% | 2554 | shaded |  |
| `upload-image_pressed.png` | 834x167 | 36.9% | 2140 | shaded |  |

## `resources/icons`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `app_icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `custom_logo.png` | 1667x1667 | 30.3% | 93 | flat |  |
| `icon.ico` | 256x256 | 81.5% | 1363 | shaded |  |
| `icon.png` | 512x512 | 81.1% | 3602 | shaded |  |
| `special_slot.png` | 512x512 | 81.1% | 3602 | shaded | `icon.png` |

## `resources/screenshots`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `01_main_window.png` | 1920x1080 | 14.0% | 7059 | screenshot |  |
| `02_image_sampling.png` | 1920x1080 | 12.3% | 9129 | screenshot |  |
| `03_screen_picker.png` | 1920x1080 | 12.7% | 12178 | screenshot |  |
| `04_color_harmonies.png` | 1920x1080 | 12.9% | 8212 | screenshot |  |
| `05_palette_export.png` | 1920x1080 | 15.8% | 7865 | screenshot |  |
| `06_themes.png` | 1920x1080 | 5.3% | 3994 | screenshot |  |

## `resources/test`

| file | size | accent | shades | kind | same as |
|---|---|---|---|---|---|
| `analyzer_test.png` | 400x300 | 3.1% | 1995 | fixture |  |
| `crash_test.png` | 300x200 | 4.3% | 2567 | fixture |  |
