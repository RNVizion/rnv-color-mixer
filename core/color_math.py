"""
Color mixing algorithms and color space conversions.
Handles RGB/HSV blending, weighted mixing, and color calculations.
"""

import colorsys
import math

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("ColorMath")
except ImportError:
    logger = None


class ColorMath:
    """Color mixing and manipulation utilities."""
    
    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string."""
        return "#{:02x}{:02x}{:02x}".format(*rgb)
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex string to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = ''.join(ch * 2 for ch in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """Convert RGB to HSV."""
        r, g, b = [c/255.0 for c in rgb]
        return colorsys.rgb_to_hsv(r, g, b)
    
    @staticmethod
    def hsv_to_rgb(hsv: tuple[float, float, float]) -> tuple[int, int, int]:
        """Convert HSV to RGB."""
        h, s, v = hsv
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """Convert RGB to HSL."""
        r, g, b = [c/255.0 for c in rgb]
        return colorsys.rgb_to_hls(r, g, b)
    
    @staticmethod
    def hsl_to_rgb(hsl: tuple[float, float, float]) -> tuple[int, int, int]:
        """Convert HSL to RGB."""
        h, l, s = hsl
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def weighted_rgb_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors using weighted RGB averaging.
        
        Single-pass algorithm (was 5 passes, now 1 pass).
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Single-pass: accumulate weights and color sums simultaneously
        total_weight = 0
        sum_r = 0
        sum_g = 0
        sum_b = 0
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                sum_r += color[0] * weight
                sum_g += color[1] * weight
                sum_b += color[2] * weight
        
        if total_weight == 0:
            return None
        
        return (
            max(0, min(255, sum_r // total_weight)),
            max(0, min(255, sum_g // total_weight)),
            max(0, min(255, sum_b // total_weight))
        )
    
    @staticmethod
    def weighted_hsv_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors using weighted HSV averaging.
        Better for perceptually uniform color mixing.
        
        Single-pass algorithm (was 6+ passes, now 1 pass).
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Single-pass: accumulate all values simultaneously
        total_weight = 0
        x_sum = 0.0  # For circular hue averaging
        y_sum = 0.0
        sum_s = 0.0
        sum_v = 0.0
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                h, s, v = ColorMath.rgb_to_hsv(color)
                # Circular averaging for hue using Cartesian coordinates
                x_sum += weight * s * v * math.cos(h * 2 * math.pi)
                y_sum += weight * s * v * math.sin(h * 2 * math.pi)
                sum_s += s * weight
                sum_v += v * weight
        
        if total_weight == 0:
            return None
        
        # Calculate averages
        avg_s = sum_s / total_weight
        avg_v = sum_v / total_weight
        
        # Convert back to hue
        if x_sum == 0 and y_sum == 0:
            avg_h = 0  # Undefined hue, use 0
        else:
            avg_h = math.atan2(y_sum, x_sum) / (2 * math.pi)
            if avg_h < 0:
                avg_h += 1
        
        # Convert back to RGB
        return ColorMath.hsv_to_rgb((avg_h, avg_s, avg_v))
    
    # ==========================================================================
    # PHASE 2: REALISTIC COLOR MIXING ALGORITHMS
    # ==========================================================================
    
    @staticmethod
    def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """
        Convert RGB to CIE LAB color space.
        LAB is perceptually uniform - equal distances = equal perceived differences.
        
        Args:
            rgb: RGB tuple (0-255)
            
        Returns:
            LAB tuple (L: 0-100, a: -128 to 127, b: -128 to 127)
        """
        import math
        
        # RGB to XYZ (sRGB with D65 illuminant)
        r, g, b = [c / 255.0 for c in rgb]
        
        # Apply gamma correction (sRGB)
        def gamma_correct(c: float) -> float:
            if c > 0.04045:
                return ((c + 0.055) / 1.055) ** 2.4
            else:
                return c / 12.92
        
        r, g, b = gamma_correct(r), gamma_correct(g), gamma_correct(b)
        
        # RGB to XYZ matrix (sRGB, D65)
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # XYZ to LAB (D65 reference white)
        xn, yn, zn = 0.95047, 1.0, 1.08883
        x, y, z = x / xn, y / yn, z / zn
        
        def f(t: float) -> float:
            if t > 0.008856:
                return t ** (1/3)
            else:
                return (903.3 * t + 16) / 116
        
        fx, fy, fz = f(x), f(y), f(z)
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b_val = 200 * (fy - fz)
        
        return (L, a, b_val)
    
    @staticmethod
    def lab_to_rgb(lab: tuple[float, float, float]) -> tuple[int, int, int]:
        """
        Convert CIE LAB to RGB color space.
        
        Args:
            lab: LAB tuple (L: 0-100, a: -128 to 127, b: -128 to 127)
            
        Returns:
            RGB tuple (0-255)
        """
        import math
        
        L, a, b_val = lab
        
        # LAB to XYZ
        fy = (L + 16) / 116
        fx = a / 500 + fy
        fz = fy - b_val / 200
        
        def f_inv(t: float) -> float:
            if t > 0.206893:
                return t ** 3
            else:
                return (116 * t - 16) / 903.3
        
        # D65 reference white
        xn, yn, zn = 0.95047, 1.0, 1.08883
        x = xn * f_inv(fx)
        y = yn * f_inv(fy)
        z = zn * f_inv(fz)
        
        # XYZ to RGB matrix (inverse of sRGB matrix)
        r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
        g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
        b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
        
        # Apply inverse gamma correction
        def gamma_inverse(c: float) -> float:
            if c > 0.0031308:
                return 1.055 * (c ** (1/2.4)) - 0.055
            else:
                return 12.92 * c
        
        r, g, b = gamma_inverse(r), gamma_inverse(g), gamma_inverse(b)
        
        # Clamp and convert to 0-255
        return (
            max(0, min(255, int(r * 255 + 0.5))),
            max(0, min(255, int(g * 255 + 0.5))),
            max(0, min(255, int(b * 255 + 0.5)))
        )
    
    @staticmethod
    def lab_perceptual_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors in LAB color space for perceptually uniform blending.
        
        LAB mixing produces more natural-looking gradients and blends than RGB.
        Colors mixed in LAB won't have unexpected hue shifts or muddy transitions.
        
        Single-pass algorithm.
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Single-pass: accumulate all values simultaneously
        total_weight = 0
        total_L = 0.0
        total_a = 0.0
        total_b = 0.0
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                L, a, b = ColorMath.rgb_to_lab(color)
                total_L += L * weight
                total_a += a * weight
                total_b += b * weight
        
        if total_weight == 0:
            return None
        
        avg_L = total_L / total_weight
        avg_a = total_a / total_weight
        avg_b = total_b / total_weight
        
        return ColorMath.lab_to_rgb((avg_L, avg_a, avg_b))
    
    @staticmethod
    def subtractive_cmy_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors using subtractive CMY model (like inks/dyes).
        
        Subtractive mixing simulates how pigments absorb light:
        - Yellow + Cyan = Green
        - Yellow + Magenta = Red  
        - Cyan + Magenta = Blue
        - All colors = Black
        
        Single-pass algorithm.
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Single-pass: accumulate all values simultaneously
        total_weight = 0
        total_c = 0.0
        total_m = 0.0
        total_y = 0.0
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                # Convert RGB to CMY (subtractive primaries)
                r, g, b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
                total_c += (1.0 - r) * weight
                total_m += (1.0 - g) * weight
                total_y += (1.0 - b) * weight
        
        if total_weight == 0:
            return None
        
        # Average CMY values and convert back to RGB
        avg_c = total_c / total_weight
        avg_m = total_m / total_weight
        avg_y = total_y / total_weight
        
        return (
            max(0, min(255, int((1.0 - avg_c) * 255))),
            max(0, min(255, int((1.0 - avg_m) * 255))),
            max(0, min(255, int((1.0 - avg_y) * 255)))
        )
    
    @staticmethod
    def rgb_to_ryb(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """
        Convert RGB to RYB (Red-Yellow-Blue) artist's color space.
        
        RYB is the traditional artist's color wheel where:
        - Primary: Red, Yellow, Blue
        - Secondary: Orange, Green, Purple
        
        Args:
            rgb: RGB tuple (0-255)
            
        Returns:
            RYB tuple (0-1 range)
        """
        r, g, b = [c / 255.0 for c in rgb]
        
        # Remove whiteness
        w = min(r, g, b)
        r, g, b = r - w, g - w, b - w
        
        max_g = max(r, g, b)
        
        # Get yellow out of red + green
        y = min(r, g)
        r, g = r - y, g - y
        
        # If blue and green, cut each in half and add to yellow
        if b > 0 and g > 0:
            b /= 2.0
            g /= 2.0
        
        # Redistribute remaining green
        y += g
        b += g
        
        # Normalize
        max_y = max(r, y, b)
        if max_y > 0:
            n = max_g / max_y
            r, y, b = r * n, y * n, b * n
        
        # Add whiteness back
        r, y, b = r + w, y + w, b + w
        
        return (r, y, b)
    
    @staticmethod
    def ryb_to_rgb(ryb: tuple[float, float, float]) -> tuple[int, int, int]:
        """
        Convert RYB (Red-Yellow-Blue) to RGB.
        
        Args:
            ryb: RYB tuple (0-1 range)
            
        Returns:
            RGB tuple (0-255)
        """
        r, y, b = ryb
        
        # Remove whiteness
        w = min(r, y, b)
        r, y, b = r - w, y - w, b - w
        
        max_y = max(r, y, b)
        
        # Get green from yellow + blue
        g = min(y, b)
        y, b = y - g, b - g
        
        # If blue and green, add to each other
        if b > 0 and g > 0:
            b *= 2.0
            g *= 2.0
        
        # Redistribute yellow to red and green
        r += y
        g += y
        
        # Normalize
        max_g = max(r, g, b)
        if max_g > 0:
            n = max_y / max_g
            r, g, b = r * n, g * n, b * n
        
        # Add whiteness back
        r, g, b = r + w, g + w, b + w
        
        return (
            max(0, min(255, int(r * 255))),
            max(0, min(255, int(g * 255))),
            max(0, min(255, int(b * 255)))
        )
    
    @staticmethod
    def weighted_ryb_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors using RYB (artist's color wheel) model.
        
        RYB mixing produces results closer to traditional paint mixing:
        - Yellow + Blue = Green (not gray!)
        - Red + Yellow = Orange
        - Red + Blue = Purple
        
        This is ideal for artists and designers working with physical media.
        
        Single-pass algorithm.
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Single-pass: accumulate all values simultaneously
        total_weight = 0
        total_r = 0.0
        total_y = 0.0
        total_b = 0.0
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                r, y, b = ColorMath.rgb_to_ryb(color)
                total_r += r * weight
                total_y += y * weight
                total_b += b * weight
        
        if total_weight == 0:
            return None
        
        avg_r = total_r / total_weight
        avg_y = total_y / total_weight
        avg_b = total_b / total_weight
        
        return ColorMath.ryb_to_rgb((avg_r, avg_y, avg_b))
    
    @staticmethod
    def kubelka_munk_mix(colors_weights: list[tuple[tuple[int, int, int], int]]) -> tuple[int, int, int] | None:
        """
        Mix colors using Kubelka-Munk theory for realistic paint/pigment simulation.
        
        Kubelka-Munk models how light interacts with pigments, accounting for:
        - Light absorption (K coefficient)
        - Light scattering (S coefficient)
        
        This produces the most realistic paint mixing results:
        - Yellow + Blue = Green (natural, not muddy)
        - Colors darken when mixed (like real paint)
        - Handles opacity and coverage naturally
        
        Simplified implementation using reflectance model.
        
        Single-pass algorithm.
        
        Args:
            colors_weights: List of (color, weight) tuples where color is (r, g, b)
            
        Returns:
            Mixed color as RGB tuple, or None if no valid colors
        """
        if not colors_weights:
            return None
        
        # Helper functions defined once (not per-iteration)
        def rgb_to_ks_channel(c: float) -> float:
            """Convert single RGB channel to K/S ratio."""
            R = max(0.001, min(0.999, c / 255.0))
            return ((1 - R) ** 2) / (2 * R)
        
        def ks_to_rgb_channel(ks_val: float) -> float:
            """Convert K/S ratio back to RGB channel."""
            ks_val = max(0, ks_val)
            discriminant = ks_val * ks_val + 2 * ks_val
            R = 1 + ks_val - math.sqrt(discriminant) if discriminant >= 0 else 0
            return int(max(0, min(1, R)) * 255)
        
        # Single-pass: accumulate weights and K/S values simultaneously
        total_weight = 0
        total_ks = [0.0, 0.0, 0.0]
        
        for color, weight in colors_weights:
            if weight > 0:
                total_weight += weight
                # Convert each channel to K/S and accumulate
                for i in range(3):
                    total_ks[i] += rgb_to_ks_channel(color[i]) * weight
        
        if total_weight == 0:
            return None
        
        # Normalize K/S values and convert back to RGB
        return (
            ks_to_rgb_channel(total_ks[0] / total_weight),
            ks_to_rgb_channel(total_ks[1] / total_weight),
            ks_to_rgb_channel(total_ks[2] / total_weight)
        )
    
    # ==========================================================================
    # END PHASE 2: REALISTIC COLOR MIXING ALGORITHMS
    # ==========================================================================
    
    @staticmethod
    def calculate_average_region_color(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int] | None:
        """
        Calculate average color of a region from pixel data.
        
        Single-pass algorithm (was 3 passes, now 1).
        
        Args:
            pixels: List of RGB tuples
            
        Returns:
            Average color as RGB tuple, or None if no pixels
        """
        if not pixels:
            return None
        
        # Single-pass accumulation
        total_r = 0
        total_g = 0
        total_b = 0
        
        for pixel in pixels:
            total_r += pixel[0]
            total_g += pixel[1]
            total_b += pixel[2]
        
        count = len(pixels)
        return (total_r // count, total_g // count, total_b // count)
    
    @staticmethod
    def color_distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
        """
        Calculate Euclidean distance between two RGB colors.
        
        Args:
            color1, color2: RGB tuples
            
        Returns:
            Distance as float
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5
    
    @staticmethod
    def generate_color_palette(base_color: tuple[int, int, int], count: int = 5) -> list[tuple[int, int, int]]:
        """
        Generate a color palette based on a base color.
        
        Args:
            base_color: Base RGB color
            count: Number of colors to generate
            
        Returns:
            List of RGB color tuples
        """
        # Guard against invalid count
        if count <= 0:
            return []
        
        h, s, v = ColorMath.rgb_to_hsv(base_color)
        colors = []
        
        for i in range(count):
            # Vary hue while keeping saturation and value similar
            new_h = (h + (i / count)) % 1.0
            new_s = max(0.1, min(1.0, s + (i - count//2) * 0.1))
            new_v = max(0.1, min(1.0, v + (i - count//2) * 0.1))
            colors.append(ColorMath.hsv_to_rgb((new_h, new_s, new_v)))
            
        return colors
    
    @staticmethod
    def validate_rgb(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Validate and clamp RGB values to valid range.
        
        Args:
            rgb: RGB tuple (may contain invalid values)
            
        Returns:
            Valid RGB tuple with values clamped to 0-255
        """
        return tuple(max(0, min(255, int(c))) for c in rgb)    
    @staticmethod
    def clamp_rgb(r: float, g: float, b: float) -> tuple[int, int, int]:
        """
        Clamp individual RGB values to 0-255 range.
        
        Args:
            r, g, b: RGB values (may be float or out of range)
        
        Returns:
            Valid RGB tuple with values clamped to 0-255
        
        Example:
            r, g, b = ColorMath.clamp_rgb(300, -50, 128.7)
            # Returns: (255, 0, 129)
        """
        return (
            max(0, min(255, int(r))),
            max(0, min(255, int(g))),
            max(0, min(255, int(b)))
        )
    
    @staticmethod
    def clamp_value(value: float, min_val: float = 0, max_val: float = 255) -> int:
        """
        Clamp a single value to a range.
        
        Args:
            value: Value to clamp
            min_val: Minimum value (default: 0)
            max_val: Maximum value (default: 255)
        
        Returns:
            Clamped integer value
        
        Example:
            r = ColorMath.clamp_value(300)  # Returns 255
            g = ColorMath.clamp_value(-50)  # Returns 0
        """
        return max(int(min_val), min(int(max_val), int(value)))
    
    @staticmethod
    def safe_rgb(r: float, g: float, b: float, default: tuple[int, int, int] = (0, 0, 0)) -> tuple[int, int, int]:
        """
        Safely convert values to RGB, with fallback on error.
        
        Args:
            r, g, b: RGB values (may be invalid types)
            default: Default RGB to return on error
        
        Returns:
            Valid RGB tuple or default on error
        
        Example:
            rgb = ColorMath.safe_rgb("invalid", 128, 200)
            # Returns: (0, 0, 0) - the default
        """
        try:
            return ColorMath.clamp_rgb(r, g, b)
        except (TypeError, ValueError, AttributeError):
            return default
    
    @staticmethod
    def is_valid_rgb(r: int, g: int, b: int) -> bool:
        """
        Check if RGB values are valid (in 0-255 range).
        
        Args:
            r, g, b: RGB values to check
        
        Returns:
            True if all values are in valid range
        
        Example:
            if ColorMath.is_valid_rgb(r, g, b):
                use_color(r, g, b)
            else:
                r, g, b = ColorMath.clamp_rgb(r, g, b)
        """
        try:
            return (
                0 <= int(r) <= 255 and
                0 <= int(g) <= 255 and
                0 <= int(b) <= 255
            )
        except (TypeError, ValueError):
            return False