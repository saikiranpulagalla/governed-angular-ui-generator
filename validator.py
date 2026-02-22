"""
STRICT Validation Agent
Enforces design system compliance with zero tolerance.
Only explicitly listed tokens are allowed.
"""

import re
import json
from typing import Dict, List, Any, Tuple


class CodeValidator:
    """
    STRICT validator that enforces design system compliance.
    Only explicitly listed tokens are allowed.
    """
    
    def __init__(self, design_system_path: str = "design-system.json"):
        """
        Initialize validator with design system.
        
        Args:
            design_system_path: Path to design system JSON file
        """
        with open(design_system_path, 'r') as f:
            self.design_system = json.load(f)
        
        self._build_allowed_tokens()
        
    def _build_allowed_tokens(self):
        """
        Build strict sets of allowed tokens from design system.
        Handles both flat string values and nested dict structures.
        """
        self.allowed_hex_colors = set()
        self.allowed_rgba_colors = set()
        
        # Colors
        colors = self.design_system.get("colors", {})
        for value in colors.values():
            if isinstance(value, str):
                if value.startswith('#'):
                    self.allowed_hex_colors.add(value.lower())
                elif value.lower().startswith('rgba') or value.lower().startswith('rgb'):
                    self.allowed_rgba_colors.add(value.lower().replace(" ", ""))
        
        # Card background
        card_bg = self.design_system.get("cardBackground", "")
        if card_bg.lower().startswith('rgba') or card_bg.lower().startswith('rgb'):
            self.allowed_rgba_colors.add(card_bg.lower().replace(" ", ""))
        
        # Border radius - supports both dict and flat string
        self.allowed_border_radius = set()
        border_radius = self.design_system.get("borderRadius", {})
        if isinstance(border_radius, dict):
            for value in border_radius.values():
                self.allowed_border_radius.add(value.lower())
        elif isinstance(border_radius, str):
            self.allowed_border_radius.add(border_radius.lower())
        
        # Box shadow - supports both dict and flat string
        self.allowed_shadows = set()
        self.allowed_shadows_normalized = set()
        box_shadow = self.design_system.get("boxShadow", {})
        if isinstance(box_shadow, dict):
            for value in box_shadow.values():
                self.allowed_shadows.add(value.lower().strip())
                self.allowed_shadows_normalized.add(self._normalize_shadow(value))
        elif isinstance(box_shadow, str):
            self.allowed_shadows.add(box_shadow.lower().strip())
            self.allowed_shadows_normalized.add(self._normalize_shadow(box_shadow))
        
        # Extract rgba values embedded inside shadow values so shadow rgba
        # components don't trigger the rgba validator
        for shadow_value in self.allowed_shadows:
            rgba_matches = re.findall(r'rgba?\([^)]+\)', shadow_value)
            for rgba in rgba_matches:
                self.allowed_rgba_colors.add(rgba.lower().replace(" ", ""))
        
        # Font family
        self.allowed_font_family = self.design_system.get("fontFamily", "").strip()
        
        # Font sizes - supports both dict and flat
        self.allowed_font_sizes = set()
        font_sizes = self.design_system.get("fontSize", {})
        if isinstance(font_sizes, dict):
            for value in font_sizes.values():
                self.allowed_font_sizes.add(value.lower())
        elif isinstance(font_sizes, str):
            self.allowed_font_sizes.add(font_sizes.lower())
        
        # Spacing - supports both dict and flat
        self.allowed_spacing = set()
        spacing = self.design_system.get("spacing", {})
        if isinstance(spacing, dict):
            for value in spacing.values():
                self.allowed_spacing.add(value.lower())
        elif isinstance(spacing, str):
            self.allowed_spacing.add(spacing.lower())
        
    def _normalize_shadow(self, shadow: str) -> str:
        """
        Normalize shadow string for comparison.
        Handles spacing variations in rgba() and between values.
        """
        shadow = shadow.lower().strip()
        shadow = re.sub(r'\s+', ' ', shadow)
        
        def normalize_rgba(match):
            return match.group(0).replace(" ", "")
        
        shadow = re.sub(r'rgba?\([^)]+\)', normalize_rgba, shadow)
        return shadow
    
    def validate_spacing_value(self, spacing_value: str) -> List[str]:
        """
        Validate a spacing value, handling CSS shorthand notation.
        
        CSS spacing shorthand splits like:
          "1rem"           -> ["1rem"]
          "0.5rem 1rem"    -> ["0.5rem", "1rem"]
          "1rem 2rem 1rem" -> ["1rem", "2rem", "1rem"]
        
        Args:
            spacing_value: Raw spacing value string from CSS
            
        Returns:
            List of invalid parts (empty list = all valid)
        """
        parts = spacing_value.strip().lower().split()
        invalid = [part for part in parts if part not in self.allowed_spacing]
        return invalid
    
    def validate_font_size_value(self, font_size_value: str) -> bool:
        """
        Validate a font-size value.
        Handles shorthand like "font: 1rem/1.5 Inter" by checking only the size part.
        
        Args:
            font_size_value: Raw font-size value string
            
        Returns:
            True if valid, False otherwise
        """
        # Take only the first token (handles "1rem/1.5" shorthand)
        size_part = font_size_value.strip().lower().split('/')[0].split()[0]
        return size_part in self.allowed_font_sizes
    
    def extract_hex_colors(self, code: str) -> List[str]:
        """Extract all #-prefixed hex color values from code."""
        return re.findall(r'#[0-9a-fA-F]{3,8}\b', code)
    
    def extract_bare_hex_colors(self, code: str) -> List[str]:
        """
        Extract bare hex values (without # prefix) from CSS color properties.
        These indicate LLM generation errors.
        Only checks known CSS color properties to avoid false positives.
        """
        color_props = r'(?:background-color|(?<!\w)color|border-color|outline-color|fill|stroke)'
        pattern = rf'(?:{color_props}):\s*([0-9a-fA-F]{{6}}|[0-9a-fA-F]{{3}})\s*[;,\)]'
        return re.findall(pattern, code)
    
    def extract_rgba_colors(self, code: str) -> List[str]:
        """Extract all rgba/rgb color values from code."""
        return re.findall(r'rgba?\([^)]+\)', code)
    
    def extract_box_shadows(self, code: str) -> List[str]:
        """Extract all box-shadow values from code."""
        shadows = []
        shadows.extend(re.findall(r'box-shadow:\s*([^;]+);', code))
        shadows.extend(re.findall(r"['\"]box-shadow['\"]:\s*['\"]([^'\"]+)['\"]", code))
        return shadows
    
    def extract_border_radius(self, code: str) -> List[str]:
        """Extract all border-radius values from code."""
        values = []
        values.extend(re.findall(r'border-radius:\s*([^;]+);', code))
        values.extend(re.findall(r"['\"]border-radius['\"]:\s*['\"]([^'\"]+)['\"]", code))
        return values
    
    def extract_font_family(self, code: str) -> List[str]:
        """Extract all font-family declarations from code."""
        fonts = []
        fonts.extend(re.findall(r'font-family:\s*([^;]+);', code))
        fonts.extend(re.findall(r"['\"]font-family['\"]:\s*['\"]([^'\"]+)['\"]", code))
        return fonts
    
    def extract_font_sizes(self, code: str) -> List[str]:
        """Extract all font-size values from code."""
        sizes = []
        sizes.extend(re.findall(r'font-size:\s*([^;]+);', code))
        sizes.extend(re.findall(r"['\"]font-size['\"]:\s*['\"]([^'\"]+)['\"]", code))
        return sizes
    
    def extract_spacing(self, code: str) -> List[str]:
        """Extract all padding/margin values from code."""
        values = []
        values.extend(re.findall(r'(?:padding|margin)(?:-[a-z]+)?:\s*([^;]+);', code))
        values.extend(re.findall(r"['\"](?:padding|margin)(?:-[a-z]+)?['\"]:\s*['\"]([^'\"]+)['\"]", code))
        return values
    
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        STRICT validation against design system.
        STATELESS, EXHAUSTIVE, FULL-SCAN ON EVERY ITERATION.
        No early returns. All checks always run.
        
        Args:
            code: Generated Angular component code
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. HEX COLOR VALIDATION
        for color in self.extract_hex_colors(code):
            if color.lower() not in self.allowed_hex_colors:
                errors.append(
                    f"Unauthorized hex color: {color} "
                    f"(allowed: {', '.join(sorted(self.allowed_hex_colors))})"
                )
        
        # 2. BARE HEX DETECTION (missing # prefix - LLM generation error)
        for hex_val in self.extract_bare_hex_colors(code):
            errors.append(
                f"Bare hex color detected: {hex_val} "
                f"(missing # prefix - should be #{hex_val})"
            )
        
        # 3. RGBA COLOR VALIDATION
        for rgba in self.extract_rgba_colors(code):
            normalized = rgba.lower().replace(" ", "")
            if normalized not in self.allowed_rgba_colors:
                errors.append(
                    f"Unauthorized rgba color: {rgba} "
                    f"(allowed: {', '.join(sorted(self.allowed_rgba_colors))})"
                )
        
        # 4. BORDER RADIUS VALIDATION
        for radius in self.extract_border_radius(code):
            radius_clean = radius.strip().lower()
            if radius_clean not in self.allowed_border_radius:
                errors.append(
                    f"Invalid border-radius: {radius} "
                    f"(allowed: {', '.join(sorted(self.allowed_border_radius))})"
                )
        
        # 5. BOX SHADOW VALIDATION
        for shadow in self.extract_box_shadows(code):
            shadow_normalized = self._normalize_shadow(shadow)
            if shadow_normalized not in self.allowed_shadows_normalized:
                errors.append(
                    f"Invalid box-shadow: {shadow.strip()} "
                    f"(must be one of the design system shadow values)"
                )
        
        # 6. FONT-FAMILY VALIDATION
        # Font-family must not appear in component CSS at all (it's global)
        for font in self.extract_font_family(code):
            font_clean = font.strip()
            if font_clean.lower() != self.allowed_font_family.lower():
                errors.append(
                    f"Invalid font-family: '{font_clean}' "
                    f"(must be: {self.allowed_font_family})"
                )
            else:
                # Even correct font-family in component CSS is wrong - it's global
                errors.append(
                    f"font-family should not be in component CSS "
                    f"(typography is enforced globally - remove font-family entirely)"
                )
        
        # 7. FONT-SIZE VALIDATION
        for size in self.extract_font_sizes(code):
            if not self.validate_font_size_value(size):
                errors.append(
                    f"Invalid font-size: {size.strip()} "
                    f"(allowed: {', '.join(sorted(self.allowed_font_sizes))})"
                )
        
        # 8. SPACING VALIDATION (handles shorthand like "0.5rem 1rem")
        for spacing in self.extract_spacing(code):
            invalid_parts = self.validate_spacing_value(spacing)
            for part in invalid_parts:
                errors.append(
                    f"Invalid spacing value: '{part}' in '{spacing.strip()}' "
                    f"(allowed: {', '.join(sorted(self.allowed_spacing))})"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_validation_report(self, code: str) -> Dict[str, Any]:
        """
        Get detailed validation report with ALL violations listed.
        STATELESS, EXHAUSTIVE, FULL-SCAN.
        
        Args:
            code: Generated code to validate
            
        Returns:
            Dictionary with valid, error_count, and errors
        """
        is_valid, errors = self.validate(code)
        return {
            "valid": is_valid,
            "error_count": len(errors),
            "errors": errors
        }