"""
Palette import/export functionality for various formats.
Supports: ACO, ACB, ASE, CLR, .COLORS, GPL, CSS, JSON, HSV, SVG, 
HEX, HSL, TXT, XML, Procreate, and Affinity formats.
NOW WITH OPTIONAL IMPORTS FOR SVG, CLR, and SWATCHES!
"""

import json
import struct
import os
import re
import xml.etree.ElementTree as ET
from core.color_math import ColorMath

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("PaletteFormats")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class PaletteFormats:
    """Handles import and export of various palette formats."""
    
    @staticmethod
    def get_export_formats() -> list[tuple[str, str]]:
        """Get list of supported export formats."""
        return [
            ("Adobe Swatch Exchange", "*.ase"),
            ("Adobe Color", "*.aco"),
            ("Adobe Color Book", "*.acb"),
            ("GIMP Palette", "*.gpl"),
            ("Procreate Swatches", "*.swatches"),
            ("Affinity Palette", "*.afpalette"),
            ("macOS Colors", "*.clr"),
            ("Colors File", "*.colors"),
            ("CSS Variables", "*.css"),
            ("JSON", "*.json"),
            ("XML", "*.xml"),
            ("SVG Palette", "*.svg"),
            ("HEX Text", "*.hex"),
            ("HSV Text", "*.hsv"),
            ("HSL Text", "*.hsl"),
            ("Plain Text", "*.txt"),
            ("All Files", "*.*")
        ]
    
    @staticmethod
    def get_import_formats() -> list[tuple[str, str]]:
        """Get list of supported import formats."""
        return [
            ("All Supported Formats", "*.gpl *.ase *.aco *.afpalette *.colors *.css *.json *.xml *.hex *.hsv *.hsl *.txt *.svg *.clr *.swatches"),
            ("GIMP Palette", "*.gpl"),
            ("Adobe Swatch Exchange", "*.ase"),
            ("Adobe Color", "*.aco"),
            ("Affinity Palette", "*.afpalette"),
            ("Colors File", "*.colors"),
            ("CSS Variables", "*.css"),
            ("JSON", "*.json"),
            ("XML", "*.xml"),
            ("HEX Text", "*.hex"),
            ("HSV Text", "*.hsv"),
            ("HSL Text", "*.hsl"),
            ("Plain Text", "*.txt"),
            ("SVG Palette (basic extraction)", "*.svg"),
            ("macOS Colors (XML variant only)", "*.clr"),
            ("Procreate Swatches (simple format)", "*.swatches"),
            ("All Files", "*.*")
        ]
    
    @staticmethod
    def export_palette(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export palette based on file extension."""
        if not colors:
            raise ValueError("No colors to export")
        
        ext = os.path.splitext(path)[1].lower()
        
        export_methods = {
            '.ase': PaletteFormats._export_ase,
            '.aco': PaletteFormats._export_aco,
            '.acb': PaletteFormats._export_acb,
            '.gpl': PaletteFormats._export_gpl,
            '.clr': PaletteFormats._export_clr,
            '.colors': PaletteFormats._export_colors,
            '.css': PaletteFormats._export_css,
            '.json': PaletteFormats._export_json,
            '.xml': PaletteFormats._export_xml,
            '.hsv': PaletteFormats._export_hsv,
            '.svg': PaletteFormats._export_svg,
            '.hex': PaletteFormats._export_hex,
            '.hsl': PaletteFormats._export_hsl,
            '.txt': PaletteFormats._export_txt,
            '.swatches': PaletteFormats._export_procreate,
            '.afpalette': PaletteFormats._export_affinity,
        }
        
        export_method = export_methods.get(ext, PaletteFormats._export_json)
        export_method(path, colors)

    @staticmethod
    def import_palette(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import palette based on file extension."""
        ext = os.path.splitext(path)[1].lower()
        
        import_methods = {
            '.gpl': PaletteFormats._import_gpl,
            '.ase': PaletteFormats._import_ase,
            '.aco': PaletteFormats._import_aco,
            '.json': PaletteFormats._import_json,
            '.xml': PaletteFormats._import_xml,
            '.css': PaletteFormats._import_css,
            '.colors': PaletteFormats._import_colors,
            '.hex': PaletteFormats._import_hex,
            '.hsv': PaletteFormats._import_hsv,
            '.hsl': PaletteFormats._import_hsl,
            '.txt': PaletteFormats._import_txt,
            '.afpalette': PaletteFormats._import_affinity,
            # NEW: Optional imports with limitations
            '.clr': PaletteFormats._import_clr,
            '.svg': PaletteFormats._import_svg,
            '.swatches': PaletteFormats._import_procreate,
        }
        
        import_method = import_methods.get(ext, PaletteFormats._import_json)
        return import_method(path)

    # =========================================================================
    # EXPORT METHODS (unchanged from previous version)
    # =========================================================================

    @staticmethod
    def _export_ase(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export Adobe Swatch Exchange format."""
        with open(path, 'wb') as f:
            f.write(b'ASEF')
            f.write(struct.pack('>HH', 1, 0))
            f.write(struct.pack('>I', len(colors)))
            
            for i, (color, weight) in enumerate(colors):
                name = f"Color {i+1}".encode('utf-16be')
                name_len = len(name) // 2
                
                f.write(struct.pack('>H', 0x0001))
                f.write(struct.pack('>I', 22 + len(name)))
                f.write(struct.pack('>H', name_len))
                f.write(name)
                f.write(b'RGB ')
                f.write(struct.pack('>fff', color[0]/255.0, color[1]/255.0, color[2]/255.0))
                f.write(struct.pack('>H', 2))

    @staticmethod
    def _export_aco(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export Adobe Color format."""
        with open(path, 'wb') as f:
            f.write(struct.pack('>HH', 1, len(colors)))
            
            for color, weight in colors:
                f.write(struct.pack('>H', 0))
                f.write(struct.pack('>HHHH', 
                    color[0] * 257, color[1] * 257, color[2] * 257, 0))
            
            f.write(struct.pack('>HH', 2, len(colors)))
            
            for i, (color, weight) in enumerate(colors):
                f.write(struct.pack('>H', 0))
                f.write(struct.pack('>HHHH',
                    color[0] * 257, color[1] * 257, color[2] * 257, 0))
                
                name = f"Color {i+1}\0"
                name_utf16 = name.encode('utf-16be')
                f.write(struct.pack('>H', len(name)))
                f.write(name_utf16)

    @staticmethod
    def _export_acb(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export Adobe Color Book format."""
        with open(path, 'wb') as f:
            f.write(b'8BCB')
            f.write(struct.pack('>H', 1))
            f.write(struct.pack('>H', 0))
            
            title = b"Color Mixer Palette\0"
            f.write(struct.pack('>H', len(title)))
            f.write(title)
            
            f.write(struct.pack('>H', 0))
            f.write(struct.pack('>H', 0))
            
            desc = b"Generated by Color Mixer\0"
            f.write(struct.pack('>H', len(desc)))
            f.write(desc)
            
            f.write(struct.pack('>H', len(colors)))
            
            for i, (color, weight) in enumerate(colors):
                name = f"Color {i+1}\0".encode('ascii')
                f.write(struct.pack('>H', len(name)))
                f.write(name)
                
                code = f"C{i+1}\0".encode('ascii')
                f.write(struct.pack('>H', len(code)))
                f.write(code)
                
                f.write(struct.pack('>BBB', color[0], color[1], color[2]))

    @staticmethod
    def _export_gpl(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export GIMP Palette format."""
        with open(path, 'w') as f:
            f.write("GIMP Palette\n")
            f.write("Name: Color Mixer Palette\n")
            f.write("Columns: 0\n")
            f.write("#\n")
            for i, (color, weight) in enumerate(colors):
                f.write(f"{color[0]:3d} {color[1]:3d} {color[2]:3d}\tColor {i+1} (weight: {weight})\n")

    @staticmethod
    def _export_clr(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export macOS .clr format."""
        root = ET.Element('plist', version='1.0')
        dict_elem = ET.SubElement(root, 'dict')
        
        ET.SubElement(dict_elem, 'key').text = 'Colors'
        array_elem = ET.SubElement(dict_elem, 'array')
        
        for i, (color, weight) in enumerate(colors):
            color_dict = ET.SubElement(array_elem, 'dict')
            
            ET.SubElement(color_dict, 'key').text = 'Name'
            ET.SubElement(color_dict, 'string').text = f'Color {i+1}'
            
            ET.SubElement(color_dict, 'key').text = 'Red'
            ET.SubElement(color_dict, 'real').text = str(color[0] / 255.0)
            
            ET.SubElement(color_dict, 'key').text = 'Green'
            ET.SubElement(color_dict, 'real').text = str(color[1] / 255.0)
            
            ET.SubElement(color_dict, 'key').text = 'Blue'
            ET.SubElement(color_dict, 'real').text = str(color[2] / 255.0)
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(path, encoding='utf-8', xml_declaration=True)

    @staticmethod
    def _export_colors(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export .colors format."""
        with open(path, 'w') as f:
            f.write("# Color Mixer Palette\n")
            f.write(f"# Total colors: {len(colors)}\n")
            f.write("#\n")
            for i, (color, weight) in enumerate(colors):
                hex_color = ColorMath.rgb_to_hex(color)
                f.write(f"{hex_color} {color[0]:3d} {color[1]:3d} {color[2]:3d} {weight:3d} # Color {i+1}\n")

    @staticmethod
    def _export_css(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export CSS variables format."""
        with open(path, 'w') as f:
            f.write("/* Color Mixer Palette - CSS Variables */\n\n")
            f.write(":root {\n")
            for i, (color, weight) in enumerate(colors):
                hex_color = ColorMath.rgb_to_hex(color)
                f.write(f"  --color-{i+1}: {hex_color};\n")
                f.write(f"  --color-{i+1}-rgb: {color[0]}, {color[1]}, {color[2]};\n")
            f.write("}\n\n")
            
            f.write("/* Individual color classes */\n")
            for i, (color, weight) in enumerate(colors):
                hex_color = ColorMath.rgb_to_hex(color)
                f.write(f".color-{i+1} {{\n")
                f.write(f"  color: {hex_color};\n")
                f.write(f"}}\n\n")
                f.write(f".bg-color-{i+1} {{\n")
                f.write(f"  background-color: {hex_color};\n")
                f.write(f"}}\n\n")

    @staticmethod
    def _export_json(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export JSON format."""
        palette_data = {
            "name": "Color Mixer Palette",
            "version": "1.0",
            "colors": []
        }
        
        for i, (color, weight) in enumerate(colors):
            palette_data["colors"].append({
                "name": f"Color {i+1}",
                "hex": ColorMath.rgb_to_hex(color),
                "rgb": {"r": color[0], "g": color[1], "b": color[2]},
                "weight": weight
            })
        
        with open(path, 'w') as f:
            json.dump(palette_data, f, indent=2)

    @staticmethod
    def _export_xml(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export XML format."""
        root = ET.Element('palette')
        root.set('name', 'Color Mixer Palette')
        root.set('version', '1.0')
        
        colors_elem = ET.SubElement(root, 'colors')
        colors_elem.set('count', str(len(colors)))
        
        for i, (color, weight) in enumerate(colors):
            color_elem = ET.SubElement(colors_elem, 'color')
            color_elem.set('id', str(i + 1))
            color_elem.set('name', f'Color {i+1}')
            
            ET.SubElement(color_elem, 'hex').text = ColorMath.rgb_to_hex(color)
            
            rgb_elem = ET.SubElement(color_elem, 'rgb')
            ET.SubElement(rgb_elem, 'r').text = str(color[0])
            ET.SubElement(rgb_elem, 'g').text = str(color[1])
            ET.SubElement(rgb_elem, 'b').text = str(color[2])
            
            ET.SubElement(color_elem, 'weight').text = str(weight)
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(path, encoding='utf-8', xml_declaration=True)

    @staticmethod
    def _export_hsv(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export HSV format."""
        with open(path, 'w') as f:
            f.write("# HSV Color Palette\n")
            f.write("# Format: H(0-360) S(0-100) V(0-100) Weight Name\n")
            f.write("#\n")
            for i, (color, weight) in enumerate(colors):
                h, s, v = ColorMath.rgb_to_hsv(color)
                f.write(f"{h*360:6.1f} {s*100:5.1f} {v*100:5.1f} {weight:3d} # Color {i+1}\n")

    @staticmethod
    def _export_svg(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export SVG palette."""
        swatch_size = 60
        cols = 6
        rows = (len(colors) + cols - 1) // cols
        padding = 5
        
        width = cols * (swatch_size + padding) + padding
        height = rows * (swatch_size + padding) + padding + 30
        
        with open(path, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n')
            f.write('  <title>Color Mixer Palette</title>\n')
            f.write('  <rect width="100%" height="100%" fill="#ffffff"/>\n')
            
            for i, (color, weight) in enumerate(colors):
                row, col = divmod(i, cols)
                x = col * (swatch_size + padding) + padding
                y = row * (swatch_size + padding) + padding + 30
                hex_color = ColorMath.rgb_to_hex(color)
                
                f.write(f'  <rect x="{x}" y="{y}" width="{swatch_size}" height="{swatch_size}" ')
                f.write(f'fill="{hex_color}" stroke="#000000" stroke-width="1"/>\n')
                
                text_x = x + swatch_size // 2
                text_y = y + swatch_size // 2
                brightness = sum(color) / 3
                text_color = "#ffffff" if brightness < 128 else "#000000"
                
                f.write(f'  <text x="{text_x}" y="{text_y}" ')
                f.write(f'text-anchor="middle" dominant-baseline="central" ')
                f.write(f'font-family="monospace" font-size="10" fill="{text_color}">')
                f.write(f'{hex_color}</text>\n')
            
            f.write(f'  <text x="{width//2}" y="20" text-anchor="middle" ')
            f.write(f'font-family="sans-serif" font-size="16" font-weight="bold">')
            f.write('Color Mixer Palette</text>\n')
            
            f.write('</svg>\n')

    @staticmethod
    def _export_hex(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export HEX text format."""
        with open(path, 'w') as f:
            f.write("# HEX Color Palette\n")
            f.write("# Format: #RRGGBB Weight Name\n")
            f.write("#\n")
            for i, (color, weight) in enumerate(colors):
                hex_color = ColorMath.rgb_to_hex(color)
                f.write(f"{hex_color} {weight:3d} # Color {i+1}\n")

    @staticmethod
    def _export_hsl(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export HSL format."""
        with open(path, 'w') as f:
            f.write("# HSL Color Palette\n")
            f.write("# Format: H(0-360) S(0-100) L(0-100) Weight Name\n")
            f.write("#\n")
            for i, (color, weight) in enumerate(colors):
                h, l, s = ColorMath.rgb_to_hsl(color)
                f.write(f"{h*360:6.1f} {s*100:5.1f} {l*100:5.1f} {weight:3d} # Color {i+1}\n")

    @staticmethod
    def _export_txt(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export plain text format."""
        with open(path, 'w') as f:
            f.write("Color Mixer Palette\n")
            f.write("=" * 60 + "\n\n")
            for i, (color, weight) in enumerate(colors):
                hex_color = ColorMath.rgb_to_hex(color)
                f.write(f"Color {i+1:2d}: {hex_color}  RGB({color[0]:3d}, {color[1]:3d}, {color[2]:3d})  Weight: {weight:3d}\n")

    @staticmethod
    def _export_procreate(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export Procreate swatches format."""
        with open(path, 'wb') as f:
            f.write(b'SWCH')
            f.write(struct.pack('<I', len(colors)))
            
            for color, weight in colors:
                f.write(struct.pack('<ffff', 
                    color[0]/255.0, 
                    color[1]/255.0, 
                    color[2]/255.0,
                    1.0))

    @staticmethod
    def _export_affinity(path: str, colors: list[tuple[tuple[int, int, int], int]]) -> None:
        """Export Affinity Designer palette format."""
        palette_data = {
            "version": "1.0",
            "name": "Color Mixer Palette",
            "colors": []
        }
        
        for i, (color, weight) in enumerate(colors):
            palette_data["colors"].append({
                "name": f"Color {i+1}",
                "color": {
                    "model": "rgb",
                    "r": color[0] / 255.0,
                    "g": color[1] / 255.0,
                    "b": color[2] / 255.0,
                    "a": 1.0
                },
                "weight": weight
            })
        
        with open(path, 'w') as f:
            json.dump(palette_data, f, indent=2)

    # =========================================================================
    # IMPORT METHODS (Standard formats - unchanged)
    # =========================================================================

    @staticmethod
    def _import_gpl(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import GIMP Palette format."""
        colors = []
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            start_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('#') or line.startswith('GIMP') or line.startswith('Name:') or line.startswith('Columns:'):
                    start_idx = i + 1
                else:
                    break
            
            for line in lines[start_idx:]:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                            colors.append(((r, g, b), 50))
                        except ValueError:
                            continue
        return colors

    @staticmethod
    def _import_ase(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import Adobe Swatch Exchange format."""
        colors = []
        try:
            with open(path, 'rb') as f:
                signature = f.read(4)
                if signature != b'ASEF':
                    raise ValueError("Not a valid ASE file")
                
                version = struct.unpack('>HH', f.read(4))
                num_blocks = struct.unpack('>I', f.read(4))[0]
                
                for _ in range(num_blocks):
                    block_type = struct.unpack('>H', f.read(2))[0]
                    block_length = struct.unpack('>I', f.read(4))[0]
                    
                    if block_type == 0x0001:
                        name_length = struct.unpack('>H', f.read(2))[0]
                        name = f.read(name_length * 2).decode('utf-16be', errors='ignore')
                        
                        color_model = f.read(4)
                        
                        if color_model == b'RGB ':
                            r, g, b = struct.unpack('>fff', f.read(12))
                            colors.append((
                                (int(r * 255), int(g * 255), int(b * 255)),
                                50
                            ))
                        
                        color_type = struct.unpack('>H', f.read(2))[0]
                    else:
                        f.read(block_length - 4)
        except Exception as e:
            logger.error(f"Error importing ASE: {e}")
        
        return colors

    @staticmethod
    def _import_aco(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import Adobe Color format."""
        colors = []
        try:
            with open(path, 'rb') as f:
                version = struct.unpack('>H', f.read(2))[0]
                num_colors = struct.unpack('>H', f.read(2))[0]
                
                for _ in range(num_colors):
                    color_space = struct.unpack('>H', f.read(2))[0]
                    
                    if color_space == 0:
                        r, g, b, _ = struct.unpack('>HHHH', f.read(8))
                        colors.append((
                            (r // 257, g // 257, b // 257),
                            50
                        ))
                    else:
                        f.read(8)
        except Exception as e:
            logger.error(f"Error importing ACO: {e}")
        
        return colors

    @staticmethod
    def _import_json(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import JSON format."""
        colors = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
                if isinstance(data, dict) and 'colors' in data:
                    for item in data['colors']:
                        if 'rgb' in item:
                            rgb = item['rgb']
                            colors.append((
                                (rgb['r'], rgb['g'], rgb['b']),
                                item.get('weight', 50)
                            ))
                        elif 'hex' in item:
                            rgb = ColorMath.hex_to_rgb(item['hex'])
                            colors.append((rgb, item.get('weight', 50)))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            if 'color' in item:
                                colors.append((tuple(item['color']), item.get('weight', 50)))
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
        
        return colors

    @staticmethod
    def _import_xml(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import XML format."""
        colors = []
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            for color_elem in root.findall('.//color'):
                rgb_elem = color_elem.find('rgb')
                if rgb_elem is not None:
                    r = int(rgb_elem.find('r').text)
                    g = int(rgb_elem.find('g').text)
                    b = int(rgb_elem.find('b').text)
                    weight_elem = color_elem.find('weight')
                    weight = int(weight_elem.text) if weight_elem is not None else 50
                    colors.append(((r, g, b), weight))
                else:
                    hex_elem = color_elem.find('hex')
                    if hex_elem is not None:
                        rgb = ColorMath.hex_to_rgb(hex_elem.text)
                        colors.append((rgb, 50))
        except Exception as e:
            logger.error(f"Error importing XML: {e}")
        
        return colors

    @staticmethod
    def _import_css(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import CSS variables format."""
        colors = []
        try:
            with open(path, 'r') as f:
                content = f.read()
                hex_pattern = r'#[0-9a-fA-F]{6}'
                matches = re.findall(hex_pattern, content)
                
                seen = set()
                for hex_color in matches:
                    if hex_color not in seen:
                        seen.add(hex_color)
                        try:
                            rgb = ColorMath.hex_to_rgb(hex_color)
                            colors.append((rgb, 50))
                        except ValueError:
                            continue
        except Exception as e:
            logger.error(f"Error importing CSS: {e}")
        
        return colors

    @staticmethod
    def _import_colors(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import .colors format."""
        colors = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                hex_color = parts[0]
                                r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
                                weight = int(parts[4])
                                colors.append(((r, g, b), weight))
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"Error importing .colors: {e}")
        
        return colors

    @staticmethod
    def _import_hex(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import HEX text format."""
        colors = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if parts:
                            hex_color = parts[0]
                            if hex_color.startswith('#') and len(hex_color) == 7:
                                try:
                                    rgb = ColorMath.hex_to_rgb(hex_color)
                                    weight = int(parts[1]) if len(parts) > 1 else 50
                                    colors.append((rgb, weight))
                                except (ValueError, IndexError):
                                    continue
        except Exception as e:
            logger.error(f"Error importing HEX: {e}")
        
        return colors

    @staticmethod
    def _import_hsv(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import HSV format."""
        colors = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                h = float(parts[0]) / 360.0
                                s = float(parts[1]) / 100.0
                                v = float(parts[2]) / 100.0
                                weight = int(parts[3]) if len(parts) > 3 else 50
                                rgb = ColorMath.hsv_to_rgb((h, s, v))
                                colors.append((rgb, weight))
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"Error importing HSV: {e}")
        
        return colors

    @staticmethod
    def _import_hsl(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import HSL format."""
        colors = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                h = float(parts[0]) / 360.0
                                s = float(parts[1]) / 100.0
                                l = float(parts[2]) / 100.0
                                weight = int(parts[3]) if len(parts) > 3 else 50
                                rgb = ColorMath.hsl_to_rgb((h, s, l))
                                colors.append((rgb, weight))
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"Error importing HSL: {e}")
        
        return colors

    @staticmethod
    def _import_txt(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import plain text format - tries to detect color formats."""
        colors = []
        try:
            with open(path, 'r') as f:
                content = f.read()
                
                hex_pattern = r'#[0-9a-fA-F]{6}'
                hex_matches = re.findall(hex_pattern, content)
                
                rgb_pattern = r'RGB\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)'
                rgb_matches = re.findall(rgb_pattern, content, re.IGNORECASE)
                
                for hex_color in hex_matches:
                    try:
                        rgb = ColorMath.hex_to_rgb(hex_color)
                        colors.append((rgb, 50))
                    except ValueError:
                        continue
                
                for rgb_match in rgb_matches:
                    try:
                        r, g, b = int(rgb_match[0]), int(rgb_match[1]), int(rgb_match[2])
                        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                            colors.append(((r, g, b), 50))
                    except ValueError:
                        continue
                
                unique_colors = []
                seen = set()
                for color, weight in colors:
                    if color not in seen:
                        seen.add(color)
                        unique_colors.append((color, weight))
                
                colors = unique_colors
        except Exception as e:
            logger.error(f"Error importing TXT: {e}")
        
        return colors

    @staticmethod
    def _import_affinity(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """Import Affinity Designer palette format."""
        colors = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
                for color_data in data.get("colors", []):
                    color_info = color_data.get("color", {})
                    if color_info.get("model") == "rgb":
                        r = int(color_info["r"] * 255)
                        g = int(color_info["g"] * 255)
                        b = int(color_info["b"] * 255)
                        weight = color_data.get("weight", 50)
                        colors.append(((r, g, b), weight))
        except Exception as e:
            logger.error(f"Error importing Affinity: {e}")
        
        return colors

    # =========================================================================
    # NEW: OPTIONAL IMPORT METHODS
    # =========================================================================

    @staticmethod
    def _import_clr(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """
        Import macOS .clr format (XML plist variant only).
        Note: Only works with XML-based .clr files, not binary NSArchived ones.
        """
        colors = []
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Look for color arrays in plist structure
            for array in root.findall('.//array'):
                for dict_elem in array.findall('dict'):
                    r, g, b = None, None, None
                    
                    # Parse key-value pairs in the dict
                    children = list(dict_elem)
                    for i in range(0, len(children) - 1, 2):
                        if children[i].tag == 'key':
                            key = children[i].text
                            value = children[i + 1]
                            
                            if key == 'Red' and value.tag == 'real':
                                r = float(value.text)
                            elif key == 'Green' and value.tag == 'real':
                                g = float(value.text)
                            elif key == 'Blue' and value.tag == 'real':
                                b = float(value.text)
                    
                    if r is not None and g is not None and b is not None:
                        colors.append((
                            (int(r * 255), int(g * 255), int(b * 255)),
                            50
                        ))
            
            if not colors:
                logger.warning("Warning: No colors found in CLR file")
                logger.debug("This may be a binary NSArchived format (not supported)")
                logger.debug("Try exporting as .gpl from your macOS app instead")
                
        except ET.ParseError as e:
            logger.error(f"Error: CLR file is not XML format (likely binary NSArchived)")
            logger.debug("Binary .clr files are not supported")
            logger.debug("Workaround: Export as .gpl or .ase from your macOS app")
        except Exception as e:
            logger.error(f"Error importing CLR: {e}")
        
        return colors

    @staticmethod
    def _import_svg(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """
        Import SVG palette (extracts colors from fill attributes).
        Note: This is best-effort; SVG is primarily a visual format.
        Only extracts hex colors from 'fill' attributes.
        """
        colors = []
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Define SVG namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Look for elements with fill colors
            for element in root.iter():
                fill = element.get('fill')
                if fill and fill.startswith('#') and len(fill) == 7:
                    try:
                        rgb = ColorMath.hex_to_rgb(fill)
                        colors.append((rgb, 50))
                    except ValueError:
                        continue
                
                # Also check style attribute
                style = element.get('style')
                if style:
                    fill_match = re.search(r'fill:\s*(#[0-9a-fA-F]{6})', style)
                    if fill_match:
                        try:
                            rgb = ColorMath.hex_to_rgb(fill_match.group(1))
                            colors.append((rgb, 50))
                        except ValueError:
                            continue
            
            # Remove duplicates while preserving order
            unique_colors = []
            seen = set()
            for color, weight in colors:
                if color not in seen:
                    seen.add(color)
                    unique_colors.append((color, weight))
            
            colors = unique_colors
            
            if not colors:
                logger.warning("Warning: No colors extracted from SVG")
                logger.debug("SVG may not contain fill colors or uses unsupported format")
            else:
                logger.debug(f"Extracted {len(colors)} colors from SVG palette")
            
        except Exception as e:
            logger.error(f"Error importing SVG: {e}")
        
        return colors

    @staticmethod
    def _import_procreate(path: str) -> list[tuple[tuple[int, int, int], int]]:
        """
        Import Procreate .swatches format (basic version only).
        Note: Only works with simple SWCH format; may not work with all Procreate versions.
        """
        colors = []
        try:
            with open(path, 'rb') as f:
                # Check header
                header = f.read(4)
                if header != b'SWCH':
                    logger.error("Error: Not a valid Procreate swatches file (missing SWCH header)")
                    return colors
                
                # Read color count
                num_colors_bytes = f.read(4)
                if len(num_colors_bytes) < 4:
                    logger.error("Error: Incomplete Procreate swatches file")
                    return colors
                
                num_colors = struct.unpack('<I', num_colors_bytes)[0]
                
                if num_colors > 1000:  # Sanity check
                    logger.warning(f"Warning: Unusually high color count ({num_colors}), may be incompatible format")
                    num_colors = min(num_colors, 1000)
                
                # Read colors (RGBA floats)
                for i in range(num_colors):
                    try:
                        color_data = f.read(16)
                        if len(color_data) < 16:
                            logger.warning(f"Warning: Incomplete color data at entry {i+1}")
                            break
                            
                        r, g, b, a = struct.unpack('<ffff', color_data)
                        
                        # Validate float ranges
                        if not (0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0):
                            logger.warning(f"Warning: Invalid color values at entry {i+1}, skipping")
                            continue
                        
                        colors.append((
                            (int(r * 255), int(g * 255), int(b * 255)),
                            50
                        ))
                    except struct.error as e:
                        logger.error(f"Warning: Error reading color {i+1}: {e}")
                        break
                
                if colors:
                    logger.info(f"Successfully imported {len(colors)} colors from Procreate swatches")
                else:
                    logger.warning("Warning: No valid colors found in Procreate swatches")
                    logger.debug("This may be an incompatible Procreate version")
                    
        except Exception as e:
            logger.error(f"Error importing Procreate swatches: {e}")
            logger.debug("Tip: This format may vary by Procreate version")
            logger.debug("Workaround: Export palette as image and sample colors manually")
        
        return colors

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    @staticmethod
    def detect_format(path: str) -> str | None:
        """Detect palette format from file content."""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext:
                return ext
            
            with open(path, 'rb') as f:
                header = f.read(8)
                
                if header.startswith(b'ASEF'):
                    return '.ase'
                elif header.startswith(b'8BCB'):
                    return '.acb'
                elif header.startswith(b'SWCH'):
                    return '.swatches'
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = ''.join([f.readline() for _ in range(5)])
                
                if 'GIMP Palette' in first_lines:
                    return '.gpl'
                elif '<?xml' in first_lines or '<palette' in first_lines:
                    return '.xml'
                elif '<svg' in first_lines:
                    return '.svg'
                elif '<plist' in first_lines:
                    return '.clr'
                elif ':root' in first_lines or 'var(--' in first_lines:
                    return '.css'
                elif first_lines.strip().startswith('{'):
                    return '.json'
                
        except Exception as e:
            logger.error(f"Error detecting format: {e}")
        
        return None

    @staticmethod
    def validate_colors(colors: list[tuple[tuple[int, int, int], int]]) -> list[tuple[tuple[int, int, int], int]]:
        """Validate and clean color data."""
        validated = []
        
        for color, weight in colors:
            r = max(0, min(255, int(color[0])))
            g = max(0, min(255, int(color[1])))
            b = max(0, min(255, int(color[2])))
            
            w = max(0, min(100, int(weight)))
            
            validated.append(((r, g, b), w))
        
        return validated

    @staticmethod
    def get_format_info(ext: str) -> dict:
        """Get information about a palette format."""
        format_info = {
            '.ase': {
                'name': 'Adobe Swatch Exchange',
                'type': 'binary',
                'support': 'full',
                'apps': ['Adobe Photoshop', 'Adobe Illustrator', 'Adobe InDesign']
            },
            '.aco': {
                'name': 'Adobe Color',
                'type': 'binary',
                'support': 'full',
                'apps': ['Adobe Photoshop']
            },
            '.acb': {
                'name': 'Adobe Color Book',
                'type': 'binary',
                'support': 'export',
                'apps': ['Adobe Photoshop']
            },
            '.gpl': {
                'name': 'GIMP Palette',
                'type': 'text',
                'support': 'full',
                'apps': ['GIMP', 'Inkscape', 'Krita']
            },
            '.clr': {
                'name': 'macOS Color List',
                'type': 'xml',
                'support': 'limited',
                'apps': ['macOS Apps'],
                'note': 'XML variant only, binary format not supported'
            },
            '.colors': {
                'name': 'Colors File',
                'type': 'text',
                'support': 'full',
                'apps': ['Various']
            },
            '.css': {
                'name': 'CSS Variables',
                'type': 'text',
                'support': 'full',
                'apps': ['Web Development']
            },
            '.json': {
                'name': 'JSON',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.xml': {
                'name': 'XML',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.svg': {
                'name': 'SVG Palette',
                'type': 'text',
                'support': 'limited',
                'apps': ['Web Browsers', 'Vector Editors'],
                'note': 'Best-effort color extraction only'
            },
            '.hex': {
                'name': 'HEX Text',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.hsv': {
                'name': 'HSV Text',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.hsl': {
                'name': 'HSL Text',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.txt': {
                'name': 'Plain Text',
                'type': 'text',
                'support': 'full',
                'apps': ['Universal']
            },
            '.swatches': {
                'name': 'Procreate Swatches',
                'type': 'binary',
                'support': 'limited',
                'apps': ['Procreate'],
                'note': 'Basic format only, may not work with all versions'
            },
            '.afpalette': {
                'name': 'Affinity Palette',
                'type': 'text',
                'support': 'full',
                'apps': ['Affinity Designer', 'Affinity Photo']
            }
        }
        
        return format_info.get(ext.lower(), {
            'name': 'Unknown',
            'type': 'unknown',
            'support': 'none',
            'apps': []
        })