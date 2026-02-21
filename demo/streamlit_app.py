"""
Streamlit Inspection Layer for Guided Component Architect

IMPORTANT: This is NOT the product. This is a read-only visual debugger.
The core system (agent_loop.py, generator.py, validator.py) is backend-first.
This UI exists ONLY to visualize agent execution for evaluation purposes.

The system works fully via CLI without this interface.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_loop import AgentLoop


def main():
    """Streamlit app for visualizing agent execution."""
    
    st.title("Agent Execution Inspector")
    st.caption("Read-only debugger for agentic code generation system")
    
    # Warning banner
    st.warning(
        "⚠️ This is an OPTIONAL inspection tool. "
        "The core system is backend-first and CLI-based. "
        "This UI is for visualization only."
    )
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        api_key = st.text_input(
            "Google API Key",
            type="password",
            help="Required for code generation with Gemini"
        )
        
        model_name = st.text_input(
            "Model Name",
            value="gemini-2.5-flash-lite",
            help="Gemini model to use"
        )
        
        max_retries = st.number_input(
            "Max Retries",
            min_value=0,
            max_value=5,
            value=2,
            help="Maximum self-correction attempts"
        )
        
        verbose = st.checkbox(
            "Verbose Mode",
            value=False,
            help="Print execution logs to console"
        )
        
        st.divider()
        st.caption("Backend-First Architecture")
        st.caption("Agent loop is the primary artifact")
        st.caption("UI is non-essential inspection tool")
    
    # Main input
    st.header("1. Input Prompt")
    user_prompt = st.text_area(
        "Natural Language UI Description",
        placeholder="Example: A login card with glassmorphism effect",
        height=100
    )
    
    # Execution trigger
    if st.button("Execute Agent Loop", type="primary", disabled=not user_prompt):
        if not api_key:
            st.error("Please provide a Google API key in the sidebar")
            return
        
        # Set environment variable for model name if provided
        if model_name:
            os.environ["MODEL_NAME"] = model_name
        
        # Initialize agent loop (calls existing backend)
        with st.spinner("Initializing agent loop..."):
            try:
                loop = AgentLoop(
                    design_system_path="design-system.json",
                    api_key=api_key,
                    max_retries=max_retries
                )
            except Exception as e:
                st.error(f"Failed to initialize agent loop: {e}")
                return
        
        # Execute agent loop (calls existing backend function)
        with st.spinner("Executing agent loop..."):
            try:
                # Call the EXISTING public function - no logic duplication
                result = loop.run(user_prompt, verbose=verbose)
            except Exception as e:
                st.error(f"Agent loop execution failed: {e}")
                return
        
        # Display results (read-only visualization)
        display_execution_results(result, user_prompt)


def display_execution_results(result: dict, prompt: str):
    """
    Display execution results in a structured format.
    This function ONLY reads the result object - no generation logic.
    """
    
    st.header("2. Execution Summary")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "✅ SUCCESS" if result["success"] else "❌ FAILED")
    
    with col2:
        st.metric("Iterations", result["iterations"])
    
    with col3:
        st.metric("Max Allowed", result.get("iterations", 0))
    
    # Display prompt
    st.subheader("User Prompt")
    st.code(prompt, language=None)
    
    # Display iteration history
    st.header("3. Agent Execution Trace")
    
    history = result.get("history", [])
    
    if not history:
        st.warning("No execution history available")
        return
    
    for attempt in history:
        iteration_num = attempt["iteration"]
        validation_report = attempt["validation_report"]
        is_valid = validation_report["valid"]
        errors = validation_report.get("errors", [])
        
        # Iteration header
        status_icon = "✅" if is_valid else "❌"
        with st.expander(
            f"{status_icon} Iteration {iteration_num} - "
            f"{'VALID' if is_valid else f'INVALID ({len(errors)} errors)'}",
            expanded=(iteration_num == 1 or not is_valid)
        ):
            # Validation status
            if is_valid:
                st.success("Validation PASSED")
            else:
                st.error(f"Validation FAILED with {len(errors)} error(s)")
                
                # Display errors
                st.subheader("Validation Errors")
                for i, error in enumerate(errors, 1):
                    st.markdown(f"{i}. `{error}`")
            
            # Display generated code
            st.subheader("Generated Code")
            code = attempt.get("code", "")
            if code:
                st.code(code, language="typescript", line_numbers=True)
            else:
                st.warning("No code generated")
            
            # Display validation report JSON
            with st.expander("Raw Validation Report"):
                st.json(validation_report)
    
    # Final result
    st.header("4. Final Result")
    
    if result["success"]:
        st.success(f"✅ Code generation successful after {result['iterations']} iteration(s)")
        
        # Display final code
        st.subheader("Final Generated Code")
        final_code = result.get("code", "")
        if final_code:
            st.code(final_code, language="typescript", line_numbers=True)
            
            # Download button
            st.download_button(
                label="Download Component",
                data=final_code,
                file_name="generated.component.ts",
                mime="text/plain"
            )
    else:
        st.error(f"❌ Code generation failed after {result['iterations']} iteration(s)")
        
        error_msg = result.get("error", "Unknown error")
        st.error(f"Error: {error_msg}")
        
        # Display last attempt
        if result.get("code"):
            st.subheader("Last Generated Code (Invalid)")
            st.code(result["code"], language="typescript", line_numbers=True)
    
    # Display full result object for debugging
    with st.expander("Raw Execution Object (Debug)"):
        st.json(result)


if __name__ == "__main__":
    # Check if running from correct directory
    if not os.path.exists("design-system.json"):
        st.error(
            "❌ design-system.json not found. "
            "Please run this app from the project root directory:\n\n"
            "```\nstreamlit run demo/streamlit_app.py\n```"
        )
        st.stop()
    
    main()
