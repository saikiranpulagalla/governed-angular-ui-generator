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
        
        # Build STRICT allowed value sets
        self._build_allowed_tokens()
        
    def _build_allowed_tokens(self):
        """Build strict sets of allowed tokens from design system."""
        # STRICT: Only use values explicitly listed in design-system.json
        
        # Colors - ONLY these exact values allowed
        self.allowed_hex_colors = set()
        colors = self.design_system.get("colors", {})
        for value in colors.values():
            if isinstance(value, str) and value.startswith('#'):
                self.allowed_hex_colors.add(value.lower())
        
        # Card background - ONLY this exact rgba allowed
        self.allowed_rgba_colors = set()
        card_bg = self.design_system.get("cardBackground", "")
        if card_bg.startswith('rgba'):
            # Normalize: remove all spaces for comparison
            self.allowed_rgba_colors.add(card_bg.lower().replace(" ", ""))
        
        # Also extract rgba from box-shadow (it contains rgba values)
        box_shadow = self.design_system.get("boxShadow", "")
        rgba_matches = re.findall(r'rgba?\([^)]+\)', box_shadow)
        for rgba in rgba_matches:
            self.allowed_rgba_colors.add(rgba.lower().replace(" ", ""))
        
        # Border radius - ONLY this exact value allowed
        self.allowed_border_radius = {self.design_system.get("borderRadius", "").lower()}
        
        # Box shadow - ONLY this exact value allowed
        self.allowed_shadows = {box_shadow.lower().strip()}
        # Also store normalized version for comparison
        self.allowed_shadows_normalized = {self._normalize_shadow(box_shadow)}
        
        # Font family - ONLY this exact value allowed (no commas, no fallbacks)
        self.allowed_font_family = self.design_system.get("fontFamily", "").strip()
        
    def _normalize_shadow(self, shadow: str) -> str:
        """
        Normalize shadow string for comparison.
        Handles spacing variations in rgba() and between values.
        
        Args:
            shadow: Shadow string to normalize
            
        Returns:
            Normalized shadow string
        """
        shadow = shadow.lower().strip()
        shadow = re.sub(r'\s+', ' ', shadow)
        
        def normalize_rgba(match):
            rgba_str = match.group(0)
            return rgba_str.replace(" ", "")
        
        shadow = re.sub(r'rgba?\([^)]+\)', normalize_rgba, shadow)
        
        return shadow
    
    def extract_colors(self, code: str) -> List[str]:
        """
        Extract ALL hex colors from code.
        
        Returns:
            List of hex color strings found in code
        """
        hex_pattern = r'#[0-9a-fA-F]{3,8}\b'
        return re.findall(hex_pattern, code)
    
    def extract_rgba(self, code: str) -> List[str]:
        """
        Extract ALL rgba/rgb color values from code.
        
        Returns:
            List of rgba/rgb strings found in code
        """
        rgba_pattern = r'rgba?\([^)]+\)'
        return re.findall(rgba_pattern, code)
    
    def extract_box_shadows(self, code: str) -> List[str]:
        """
        Extract ALL box-shadow values from code.
        
        Returns:
            List of box-shadow values found in code
        """
        shadows = []
        
        # Match CSS syntax: box-shadow: value;
        css_pattern = r'box-shadow:\s*([^;]+);'
        shadows.extend(re.findall(css_pattern, code))
        
        # Match TypeScript object literal: 'box-shadow': 'value'
        ts_pattern = r"['\"]box-shadow['\"]:\s*['\"]([^'\"]+)['\"]"
        shadows.extend(re.findall(ts_pattern, code))
        
        return shadows
    
    def extract_border_radius(self, code: str) -> List[str]:
        """
        Extract ALL border-radius values from code.
        
        Returns:
            List of border-radius values found in code
        """
        radius_values = []
        
        # Match CSS syntax: border-radius: value;
        css_pattern = r'border-radius:\s*([^;]+);'
        radius_values.extend(re.findall(css_pattern, code))
        
        # Match TypeScript object literal: 'border-radius': 'value'
        ts_pattern = r"['\"]border-radius['\"]:\s*['\"]([^'\"]+)['\"]"
        radius_values.extend(re.findall(ts_pattern, code))
        
        return radius_values
    
    def extract_font_family(self, code: str) -> List[str]:
        """
        Extract ALL font-family declarations from code.
        
        Returns:
            List of font-family values found in code
        """
        fonts = []
        
        # Match CSS syntax: font-family: value;
        css_pattern = r'font-family:\s*([^;]+);'
        fonts.extend(re.findall(css_pattern, code))
        
        # Match TypeScript object literal: 'font-family': 'value'
        ts_pattern = r"['\"]font-family['\"]:\s*['\"]([^'\"]+)['\"]"
        fonts.extend(re.findall(ts_pattern, code))
        
        return fonts
    
    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        STRICT validation against design system.
        STATELESS, EXHAUSTIVE, FULL-SCAN ON EVERY ITERATION.
        
        Args:
            code: Generated Angular component code
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # CRITICAL: Clear ALL state at the start
        errors = []
        
        # Run ALL checks EVERY TIME - NO EARLY RETURNS, NO SHORT-CIRCUITING
        
        # 1. STRICT HEX COLOR VALIDATION
        hex_colors = self.extract_colors(code)
        for color in hex_colors:
            if color.lower() not in self.allowed_hex_colors:
                errors.append(f"Unauthorized hex color: {color} (not in design system)")
        
        # 2. STRICT RGBA COLOR VALIDATION
        rgba_colors = self.extract_rgba(code)
        for rgba in rgba_colors:
            normalized = rgba.lower().replace(" ", "")
            if normalized not in self.allowed_rgba_colors:
                errors.append(f"Unauthorized rgba color: {rgba} (not in design system)")
        
        # 3. STRICT BORDER RADIUS VALIDATION
        border_radius_values = self.extract_border_radius(code)
        for radius in border_radius_values:
            radius_clean = radius.strip().lower()
            if radius_clean not in self.allowed_border_radius:
                allowed = list(self.allowed_border_radius)[0]
                errors.append(f"Invalid border-radius: {radius} (must be: {allowed})")
        
        # 4. STRICT BOX SHADOW VALIDATION
        shadows = self.extract_box_shadows(code)
        for shadow in shadows:
            shadow_normalized = self._normalize_shadow(shadow)
            if shadow_normalized not in self.allowed_shadows_normalized:
                allowed = list(self.allowed_shadows)[0]
                errors.append(f"Invalid box-shadow: {shadow} (must be: {allowed})")
        
        # 5. STRICT FONT-FAMILY VALIDATION (CRITICAL FIX)
        # WHY: LLM pretraining bias causes it to emit fallback fonts like
        # "Inter, system-ui, -apple-system, sans-serif" even when only "Inter" is allowed.
        # This is a SYSTEM-LEVEL issue, not a user prompt issue.
        # FIX: Detect component-level font-family and fail immediately.
        fonts = self.extract_font_family(code)
        for font in fonts:
            font_clean = font.strip()
            # Must match EXACTLY "Inter" (no commas, no fallbacks)
            if font_clean.lower() != self.allowed_font_family.lower():
                errors.append(f"Invalid font-family: {font} (must be: {self.allowed_font_family})")
                errors.append("NOTE: Typography is enforced globally. Do not include font-family in component CSS.")
        
        # FINAL DECISION: valid = true ONLY if error_count == 0
        is_valid = len(errors) == 0
        
        return is_valid, errors
    
    def get_validation_report(self, code: str) -> Dict[str, Any]:
        """
        Get detailed validation report with ALL violations listed.
        STATELESS, EXHAUSTIVE, FULL-SCAN.
        
        Args:
            code: Generated code to validate
            
        Returns:
            Dictionary with:
                - valid: bool (true ONLY if error_count == 0)
                - error_count: int (total violations found)
                - errors: List[str] (detailed error messages)
        """
        # CRITICAL: Fresh validation on every call
        is_valid, errors = self.validate(code)
        
        # TRUTHFUL report: valid = true ONLY if error_count == 0
        return {
            "valid": is_valid,
            "error_count": len(errors),
            "errors": errors
        }