"""
Code Generation Agent
Converts natural language UI descriptions into Angular components
using strict design system constraints.
"""

import json
import os
import re
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class CodeGenerator:
    """Agent responsible for generating Angular component code from natural language."""
    
    def __init__(self, design_system_path: str = "design-system.json", api_key: Optional[str] = None):
        """
        Initialize the code generator with design system.
        
        Args:
            design_system_path: Path to design system JSON file
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.design_system = self._load_design_system(design_system_path)
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
        
        # Configure Gemini
        genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.3")),
                "max_output_tokens": int(os.getenv("MODEL_MAX_TOKENS", "2000")),
            }
        )
        
    def _load_design_system(self, path: str) -> Dict[str, Any]:
        """Load and parse the design system JSON."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _build_system_prompt(self) -> str:
        """
        Construct the system prompt that enforces design system compliance.
        This prompt is locked and cannot be modified by user input.
        """
        design_system_str = json.dumps(self.design_system, indent=2)
        
        return f"""You are a code generation agent that produces ONLY valid Angular component code.

CRITICAL RULES:
1. Output ONLY raw Angular TypeScript component code - NO markdown, NO explanations, NO comments outside the code
2. You MUST use ONLY the EXACT design tokens from this design system:

{design_system_str}

3. NEVER use hardcoded colors, spacing, fonts, or shadows outside this design system
4. Generate a complete Angular component with @Component decorator
5. Use inline template and styles
6. The component must be syntactically valid TypeScript/Angular code
7. Include proper imports from @angular/core

DESIGN SYSTEM ENFORCEMENT - USE EXACT VALUES:

Colors - Use ONLY these exact hex values (always include the # prefix):
- Primary: #6366f1
- Secondary: #8b5cf6
- Accent: #ec4899
- Background: #0f172a
- Text: #f1f5f9
- Text Secondary: #94a3b8
- Error: #ef4444
- Success: #10b981

Colors - Use ONLY these exact rgba values:
- Card Background: rgba(255, 255, 255, 0.15)
- Border: rgba(255, 255, 255, 0.2)

Border Radius - Use ONLY these exact values:
- sm: 4px
- md: 8px
- lg: 12px
- xl: 16px
- full: 9999px

Shadows - Use ONLY these exact values:
- sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
- lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
- glassmorphism: 0 8px 32px 0 rgba(31, 38, 135, 0.37)
- inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)

Typography - GLOBAL ENFORCEMENT (DO NOT INCLUDE IN COMPONENT CSS):
- Font Family: Inter
- IMPORTANT: Do NOT include font-family in component CSS styles.
- Typography is enforced globally in the application's global stylesheet.
- Component CSS should NOT include font-family declarations.

Font Sizes - Use ONLY these exact values:
- xs: 0.75rem
- sm: 0.875rem
- base: 1rem
- lg: 1.125rem
- xl: 1.25rem
- 2xl: 1.5rem
- 3xl: 1.875rem
- 4xl: 2.25rem

Spacing (padding, margin) - Use ONLY these exact values:
- xs: 0.25rem
- sm: 0.5rem
- input: 0.75rem
- md: 1rem
- lg: 1.5rem
- xl: 2rem
- 2xl: 3rem

IMPORTANT RULES:
- ALWAYS include # before hex color values: #6366f1 NOT 6366f1
- NEVER use rgba opacity values other than the exact ones listed above
- DO NOT use font-family in component CSS - typography is global
- DO NOT use CSS variables like var(--spacing-md) - use literal values
- DO NOT include fallback fonts
- GENERATE COMPLETE CODE - include all closing braces, tags, and statements
- Do NOT truncate or abbreviate the component code
- Ensure template is fully closed with backtick
- Ensure styles array is fully closed with bracket
- Ensure @Component decorator is fully closed with brace
- Ensure export class is fully closed with brace

If you violate the design system or output non-code text, your output is INVALID and will be rejected.

Start your response with "import" - no preamble, no markdown fences, just pure code."""

    def generate(self, user_request: str, previous_code: Optional[str] = None, 
                 validation_errors: Optional[list] = None) -> str:
        """
        Generate Angular component code from natural language description.
        
        Args:
            user_request: Natural language UI description
            previous_code: Previously generated code (for correction loop)
            validation_errors: List of validation errors to fix
            
        Returns:
            Generated Angular component code as string
        """
        # Sanitize user input to prevent prompt injection
        sanitized_request = self._sanitize_input(user_request)
        
        if previous_code and validation_errors:
            # Self-correction mode
            user_message = self._build_correction_prompt(
                sanitized_request, previous_code, validation_errors
            )
        else:
            # Initial generation mode
            user_message = f"""Generate an Angular component for: {sanitized_request}

Remember: Use ONLY design system tokens. Output pure TypeScript code only."""
        
        try:
            # Combine system prompt and user message for Gemini
            full_prompt = f"""{self._build_system_prompt()}

---

{user_message}"""
            
            response = self.model.generate_content(full_prompt)
            
            generated_code = response.text.strip()
            
            # Check if code appears incomplete (ends abruptly)
            if generated_code.endswith(('<', '`', '{', '[', '(', ',')):
                raise RuntimeError(
                    f"Generated code appears incomplete (ends with '{generated_code[-1]}'). "
                    "This may indicate the LLM response was truncated. "
                    f"Code length: {len(generated_code)} characters"
                )
            
            # Remove markdown code fences if LLM added them despite instructions
            generated_code = self._clean_code_output(generated_code)
            
            # DESIGN TOKEN NORMALIZER: Apply deterministic post-processing
            generated_code = self._normalize_code(generated_code)
            
            return generated_code
            
        except Exception as e:
            raise RuntimeError(f"Code generation failed: {str(e)}")
    
    def _build_correction_prompt(self, original_request: str, 
                                 invalid_code: str, errors: list) -> str:
        """Build prompt for self-correction iteration."""
        errors_str = "\n".join(f"- {error}" for error in errors)
        
        return f"""CORRECTION REQUIRED

Original request: {original_request}

Your previous code had these validation errors:
{errors_str}

SPECIFIC FIXES NEEDED:
1. If error mentions "Unauthorized color" or "Bare hex" - replace with EXACT values from design system
   Always include the # prefix: #6366f1 NOT 6366f1
2. If error mentions "font-family" - REMOVE font-family entirely from component CSS
   Typography is global - do NOT include font-family in any component styles
3. If error mentions rgba() - use ONLY these exact rgba values:
   - Card background: rgba(255, 255, 255, 0.15)
   - Border: rgba(255, 255, 255, 0.2)
   - Shadow values from the design system
4. If error mentions spacing - use ONLY: 0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem, 3rem
5. If error mentions font-size - use ONLY: 0.75rem, 0.875rem, 1rem, 1.125rem, 1.25rem, 1.5rem, 1.875rem, 2.25rem

Previous code:
{invalid_code}

Fix ONLY these specific errors. Use the EXACT literal values shown above.
Output the complete corrected component code."""
    
    def _sanitize_input(self, user_input: str) -> str:
        """
        Basic prompt injection hardening.
        Prevents common injection patterns.
        
        Args:
            user_input: User-provided text
            
        Returns:
            Sanitized input safe for prompt inclusion
        """
        dangerous_patterns = [
            r'ignore previous instructions',
            r'forget the system prompt',
            r'disregard the design system',
            r'override the validator',
            r'bypass validation',
            r'system prompt',
            r'ignore all',
        ]
        
        sanitized = user_input
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length to prevent token exhaustion attacks
        max_length = 500
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    def _clean_code_output(self, code: str) -> str:
        """Remove markdown fences and extra formatting from LLM output."""
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        code = code.strip()
        
        if not code.endswith("}"):
            raise ValueError(
                f"Generated code is incomplete - doesn't end with closing brace. "
                f"Last 50 chars: ...{code[-50:]}"
            )
        
        return code
    
    def _normalize_code(self, code: str) -> str:
        """
        DESIGN TOKEN NORMALIZER: Centralized post-processing for generated code.
        
        WHY: LLM pretraining bias causes it to emit patterns that violate design system rules.
        The prompt expresses policy; the normalizer enforces determinism.
        
        Normalizations applied:
        1. Strip font-family declarations (typography is global)
        2. Normalize spacing CSS variables to literal values
        3. Strip erroneous # prefix from spacing/numeric values
        4. Fix missing # on hex color CSS property values (safe, property-scoped)
        
        Args:
            code: Generated code that may contain design system violations
            
        Returns:
            Normalized code with design token violations corrected
        """
        # NORMALIZATION 1: Strip font-family declarations
        # Typography is enforced globally - do not include in component CSS
        code = re.sub(r'font-family:\s*[^;]+;', '', code)
        code = re.sub(r"['\"]font-family['\"]:\s*['\"][^'\"]+['\"]", '', code)
        
        # NORMALIZATION 2: Normalize spacing CSS variables to literal values
        # LLM pretraining bias causes it to emit var(--spacing-*) even when literals required
        spacing_map = {
            'var(--spacing-xs)': '0.25rem',
            'var(--spacing-sm)': '0.5rem',
            'var(--spacing-input)': '0.75rem',
            'var(--spacing-md)': '1rem',
            'var(--spacing-lg)': '1.5rem',
            'var(--spacing-xl)': '2rem',
            'var(--spacing-2xl)': '3rem',
        }
        for css_var, literal_value in spacing_map.items():
            code = code.replace(css_var, literal_value)
        
        # NORMALIZATION 3: Strip erroneous # prefix from spacing/numeric values
        # LLM sees # in design system JSON context and sometimes applies it to spacing
        # Pattern: colon followed by # then a digit (e.g., ": #1rem" -> ": 1rem")
        code = re.sub(r':\s*#(\d)', lambda m: ': ' + m.group(1), code)
        
        # NORMALIZATION 4: Fix missing # on hex color CSS property values
        # WHY: LLM sometimes emits "color: 0f172a;" instead of "color: #0f172a;"
        # 
        # SAFE APPROACH: Only fix known CSS color properties, not arbitrary values.
        # This avoids false positives on z-index, opacity, rgba() internals, etc.
        #
        # Step 1: Temporarily protect rgba/rgb values from the regex
        rgba_placeholders = {}
        rgba_counter = [0]
        
        def protect_rgba(match):
            key = f'__RGBA_{rgba_counter[0]}__'
            rgba_placeholders[key] = match.group(0)
            rgba_counter[0] += 1
            return key
        
        code = re.sub(r'rgba?\([^)]+\)', protect_rgba, code)
        
        # Step 2: Fix bare hex only in color-specific CSS properties
        color_property_pattern = (
            r'((?:background-color|(?<!\w)color|border-color|outline-color|fill|stroke):\s*)'
            r'([0-9a-fA-F]{6}|[0-9a-fA-F]{3})'
            r'(\s*[;,\)])'
        )
        code = re.sub(color_property_pattern, lambda m: m.group(1) + '#' + m.group(2) + m.group(3), code)
        
        # Step 3: Restore rgba values
        for key, value in rgba_placeholders.items():
            code = code.replace(key, value)
        
        # NORMALIZATION 5: Fix common rgba white-background opacity mistake
        # LLM frequently emits rgba(255,255,255,0.1) instead of rgba(255,255,255,0.15)
        # 0.1 opacity white is never valid in the design system - safe to correct
        code = re.sub(
            r'rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0\.1\s*\)',
            'rgba(255, 255, 255, 0.15)',
            code
        )
        
        # Clean up empty style properties left by font-family removal
        code = re.sub(r',\s*,', ',', code)
        code = re.sub(r'\{\s*,\s*\}', '{}', code)
        code = re.sub(r'\[\s*,\s*\]', '[]', code)
        
        return code
    
    def get_design_system(self) -> Dict[str, Any]:
        """Return the loaded design system for reference."""
        return self.design_system