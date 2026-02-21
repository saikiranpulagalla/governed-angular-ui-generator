"""
Code Generation Agent
Converts natural language UI descriptions into Angular components
using strict design system constraints.
"""

import json
import os
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
        self.last_normalization_applied = False  # Track if post-processing modified output
        
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

Colors - Use ONLY these exact values:
- Primary: #6366f1
- Secondary: #8b5cf6
- Accent: #ec4899
- Background: #0f172a
- Card Background: rgba(255, 255, 255, 0.15)
- Text: #f1f5f9
- Text Secondary: #94a3b8
- Border: rgba(255, 255, 255, 0.2)
- Error: #ef4444
- Success: #10b981

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

Spacing - Use ONLY these exact values:
- xs: 0.25rem
- sm: 0.5rem
- md: 1rem
- lg: 1.5rem
- xl: 2rem
- 2xl: 3rem

IMPORTANT:
- DO NOT use font-family in component CSS - typography is global
- DO NOT use template literals like ${{}} for font-family
- DO NOT use CSS variables like var(--typography-fontFamily)
- DO NOT include fallback fonts (system-ui, -apple-system, sans-serif, etc.)
- If you include font-family in component CSS, validation will FAIL

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
        if previous_code and validation_errors:
            # Self-correction mode
            user_message = self._build_correction_prompt(
                user_request, previous_code, validation_errors
            )
        else:
            # Initial generation mode
            user_message = f"""Generate an Angular component for: {user_request}

Remember: Use ONLY design system tokens. Output pure TypeScript code only."""
        
        try:
            # Combine system prompt and user message for Gemini
            full_prompt = f"""{self._build_system_prompt()}

---

{user_message}"""
            
            response = self.model.generate_content(full_prompt)
            
            generated_code = response.text.strip()
            
            # Remove markdown code fences if LLM added them despite instructions
            generated_code = self._clean_code_output(generated_code)
            
            # DESIGN TOKEN NORMALIZER: Apply deterministic post-processing
            # This handles LLM pretraining bias that causes it to emit fallback fonts
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
1. If error mentions "Unauthorized color" - replace with EXACT values from design system
2. If error mentions "font-family" - REMOVE font-family entirely from component CSS
   Typography is global - do NOT include font-family in any component styles
3. If error mentions rgba() colors - use ONLY these exact rgba values:
   - Card background: rgba(255, 255, 255, 0.15)
   - Border: rgba(255, 255, 255, 0.2)
   - Shadow rgba values from design system shadows

Previous code:
{invalid_code}

Fix ONLY these specific errors. Use the EXACT literal values shown above.
Output the complete corrected component code."""
    
    def _clean_code_output(self, code: str) -> str:
        """Remove markdown fences and extra formatting from LLM output."""
        # Remove markdown code fences
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line if it's a fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        return code.strip()
    
    def _normalize_code(self, code: str) -> str:
        """
        DESIGN TOKEN NORMALIZER: Centralized post-processing for generated code.
        
        WHY: LLM pretraining bias causes it to emit patterns that violate design system rules.
        The prompt expresses policy; the normalizer enforces determinism.
        
        Current normalizations:
        - Strip font-family declarations (typography is global)
        - Normalize spacing CSS variables to literal values
        
        Future normalizations (extensible):
        - Standardize color formats
        - etc.
        
        Args:
            code: Generated code that may contain design system violations
            
        Returns:
            Normalized code with design token violations corrected
        """
        import re
        
        original_code = code
        self.last_normalization_applied = False
        
        # NORMALIZATION 1: Strip font-family declarations
        # Typography is enforced globally - do not include in component CSS
        code = re.sub(r'font-family:\s*[^;]+;', '', code)
        code = re.sub(r"['\"]font-family['\"]:\s*['\"][^'\"]+['\"]", '', code)
        
        # NORMALIZATION 2: Normalize spacing CSS variables to literal values
        # WHY: LLM pretraining bias causes it to emit CSS variables like var(--spacing-md)
        # even when literal values (1rem) are required by the design system.
        # This is a SYSTEM-LEVEL fix - spacing tokens are deterministic.
        # Only known spacing variables are normalized; unknown variables pass through.
        spacing_map = {
            'var(--spacing-sm)': '0.5rem',
            'var(--spacing-md)': '1rem',
            'var(--spacing-lg)': '1.5rem',
            'var(--spacing-xl)': '2rem',
            'var(--spacing-2xl)': '3rem',
        }
        for css_var, literal_value in spacing_map.items():
            code = code.replace(css_var, literal_value)
        
        # Clean up any empty style properties left behind
        code = re.sub(r',\s*,', ',', code)
        code = re.sub(r'\{\s*,\s*\}', '{}', code)
        code = re.sub(r'\[\s*,\s*\]', '[]', code)
        
        # Track if any normalization was applied
        if code != original_code:
            self.last_normalization_applied = True
        
        return code
    
    def _strip_font_family(self, code: str) -> str:
        """
        DEPRECATED: Use _normalize_code() instead.
        Kept for backward compatibility.
        """
        return self._normalize_code(code)
    
    def get_design_system(self) -> Dict[str, Any]:
        """Return the loaded design system for reference."""
        return self.design_system
