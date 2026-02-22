"""
Self-Correcting Agent Loop
Orchestrates the generation-validation-correction cycle.
"""

from typing import Dict, Any, Optional
from generator import CodeGenerator
from validator import CodeValidator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AgentLoop:
    """
    Orchestration agent that manages the self-correcting loop:
    Generate → Validate → Correct (if needed) → Re-validate
    """
    
    def __init__(self, design_system_path: str = "design-system.json", 
                 api_key: Optional[str] = None, max_retries: int = 2):
        """
        Initialize the agent loop with generator and validator.
        
        Args:
            design_system_path: Path to design system JSON
            api_key: Google API key
            max_retries: Maximum total iterations (generation + correction attempts)
                        Example: max_retries=2 means 1 generation + 1 correction attempt
                        Example: max_retries=3 means 1 generation + 2 correction attempts
        """
        self.generator = CodeGenerator(design_system_path, api_key)
        self.validator = CodeValidator(design_system_path)
        self.max_retries = max_retries
        
    def run(self, user_request: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Execute the self-correcting agent loop.
        
        Args:
            user_request: Natural language UI description
            verbose: Print progress information
            
        Returns:
            Dictionary containing:
                - success: bool
                - code: final generated code (if successful)
                - iterations: number of attempts
                - validation_report: final validation results
                - history: list of all attempts with their validation results
        """
        history = []
        current_code = None
        validation_errors = None
        
        for iteration in range(self.max_retries):
            if verbose:
                print(f"\n{'='*60}")
                print(f"ITERATION {iteration + 1}/{self.max_retries}")
                print(f"{'='*60}")
            
            # Generate code
            if verbose:
                if iteration == 0:
                    print(f"🤖 Generating code for: '{user_request}'")
                else:
                    print(f"🔧 Attempting to fix {len(validation_errors)} validation error(s)")
            
            try:
                current_code = self.generator.generate(
                    user_request=user_request,
                    previous_code=current_code if iteration > 0 else None,
                    validation_errors=validation_errors if iteration > 0 else None
                )
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Code generation failed: {str(e)}",
                    "iterations": iteration + 1,
                    "history": history
                }
            
            if verbose:
                print(f"✅ Code generated ({len(current_code)} characters)")
            
            # Validate code
            if verbose:
                print("🔍 Validating code...")
            
            validation_report = self.validator.get_validation_report(current_code)
            is_valid = validation_report["valid"]
            validation_errors = validation_report["errors"]
            
            # Record this iteration
            history.append({
                "iteration": iteration + 1,
                "code": current_code,
                "validation_report": validation_report
            })
            
            if verbose:
                if is_valid:
                    print("✅ Validation PASSED")
                else:
                    print(f"❌ Validation FAILED with {len(validation_errors)} error(s):")
                    for error in validation_errors:
                        print(f"   - {error}")
            
            # Check if we're done
            if is_valid:
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"🎉 SUCCESS after {iteration + 1} iteration(s)")
                    print(f"{'='*60}")
                
                return {
                    "success": True,
                    "code": current_code,
                    "iterations": iteration + 1,
                    "validation_report": validation_report,
                    "history": history
                }
            
            # Check if we've exhausted retries
            if iteration >= self.max_retries - 1:
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"❌ FAILED after {iteration + 1} iteration(s)")
                    print(f"{'='*60}")
                
                return {
                    "success": False,
                    "code": current_code,
                    "iterations": iteration + 1,
                    "validation_report": validation_report,
                    "history": history,
                    "error": f"Max retries ({self.max_retries}) exceeded. Final errors: {validation_errors}"
                }
        
        # Should never reach here, but just in case
        return {
            "success": False,
            "error": "Unexpected loop termination",
            "iterations": self.max_retries,
            "history": history
        }
    
    def run_silent(self, user_request: str) -> Dict[str, Any]:
        """Run the loop without verbose output."""
        return self.run(user_request, verbose=False)
