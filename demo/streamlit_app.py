"""
Streamlit Inspection Layer for Governed Angular UI Generator

IMPORTANT: This is NOT the product. This is a read-only visual debugger.
The core system (agent_loop.py, generator.py, validator.py) is backend-first.
This UI exists ONLY to visualize agent execution for evaluation purposes.
"""

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_loop import AgentLoop


# ---------------------------------------------------------------------------
# CodeSandbox API
# WHY CodeSandbox instead of StackBlitz:
# StackBlitz requires a form POST from the browser — impossible from inside
# Streamlit's sandboxed iframe. CodeSandbox has a server-side POST API that
# Python calls directly, returning a sandbox URL. We then show it with
# st.link_button (renders in Streamlit's main DOM, not iframe) and embed
# it inline with st.components.v1.iframe (src= GET request, no JS needed).
# Zero popup blockers. Zero sandbox restrictions. Live preview in the page.
# ---------------------------------------------------------------------------

def create_codesandbox(component_code: str) -> str | None:
    """
    Create a CodeSandbox project via their define API and return the sandbox URL.

    This is a server-side Python HTTP request — completely unaffected by
    browser sandbox restrictions.

    Args:
        component_code: Generated Angular TypeScript component code

    Returns:
        Sandbox URL string, or None if the API call fails
    """
    # Extract the selector from the component to use in index.html
    import re
    selector_match = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", component_code)
    selector = selector_match.group(1) if selector_match else "app-root"

    files = {
        "src/app/app.component.ts": {
            "content": component_code
        },
        "src/app/app.module.ts": {
            "content": (
                "import { NgModule } from '@angular/core';\n"
                "import { BrowserModule } from '@angular/platform-browser';\n"
                "import { AppComponent } from './app.component';\n\n"
                "@NgModule({\n"
                "  declarations: [AppComponent],\n"
                "  imports: [BrowserModule],\n"
                "  bootstrap: [AppComponent]\n"
                "})\n"
                "export class AppModule {}\n"
            )
        },
        "src/main.ts": {
            "content": (
                "import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';\n"
                "import { AppModule } from './app/app.module';\n"
                "platformBrowserDynamic().bootstrapModule(AppModule)\n"
                "  .catch(err => console.error(err));\n"
            )
        },
        "src/index.html": {
            "content": (
                "<!doctype html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "  <meta charset=\"utf-8\">\n"
                "  <title>Angular Component Preview</title>\n"
                "  <base href=\"/\">\n"
                "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "</head>\n"
                "<body>\n"
                f"  <{selector}></{selector}>\n"
                "</body>\n"
                "</html>\n"
            )
        },
        "src/styles.css": {
            "content": (
                "@import url('https://fonts.googleapis.com/css2?family=Inter:"
                "wght@400;500;600;700&display=swap');\n\n"
                "* { font-family: 'Inter', sans-serif; "
                "box-sizing: border-box; margin: 0; padding: 0; }\n\n"
                "body { background-color: #0f172a; "
                "color: #f1f5f9; padding: 2rem; }\n"
            )
        },
        "tsconfig.json": {
            "content": json.dumps({
                "compileOnSave": False,
                "compilerOptions": {
                    "outDir": "./dist/out-tsc",
                    "forceConsistentCasingInFileNames": True,
                    "strict": True,
                    "noImplicitOverride": True,
                    "noPropertyAccessFromIndexSignature": True,
                    "noImplicitReturns": True,
                    "noFallthroughCasesInSwitch": True,
                    "esModuleInterop": True,
                    "sourceMap": True,
                    "declaration": False,
                    "downlevelIteration": True,
                    "experimentalDecorators": True,
                    "moduleResolution": "node",
                    "importHelpers": True,
                    "target": "ES2022",
                    "module": "ES2022",
                    "useDefineForClassFields": False,
                    "lib": ["ES2022", "dom"]
                }
            }, indent=2)
        },
        "package.json": {
            "content": json.dumps({
                "name": "angular-component-preview",
                "version": "0.0.0",
                "scripts": {
                    "ng": "ng",
                    "start": "ng serve",
                    "build": "ng build"
                },
                "dependencies": {
                    "@angular/animations": "^17.0.0",
                    "@angular/common": "^17.0.0",
                    "@angular/compiler": "^17.0.0",
                    "@angular/core": "^17.0.0",
                    "@angular/platform-browser": "^17.0.0",
                    "@angular/platform-browser-dynamic": "^17.0.0",
                    "rxjs": "~7.8.0",
                    "tslib": "^2.3.0",
                    "zone.js": "~0.14.0"
                },
                "devDependencies": {
                    "@angular/cli": "^17.0.0",
                    "@angular/compiler-cli": "^17.0.0",
                    "typescript": "~5.2.0"
                }
            }, indent=2)
        },
        "angular.json": {
            "content": json.dumps({
                "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
                "version": 1,
                "newProjectRoot": "projects",
                "projects": {
                    "app": {
                        "projectType": "application",
                        "root": "",
                        "sourceRoot": "src",
                        "architect": {
                            "build": {
                                "builder": "@angular-devkit/build-angular:application",
                                "options": {
                                    "outputPath": "dist/app",
                                    "index": "src/index.html",
                                    "browser": "src/main.ts",
                                    "polyfills": ["zone.js"],
                                    "tsConfig": "tsconfig.json",
                                    "styles": ["src/styles.css"],
                                    "scripts": []
                                }
                            },
                            "serve": {
                                "builder": "@angular-devkit/build-angular:dev-server",
                                "configurations": {
                                    "production": {"buildTarget": "app:build:production"},
                                    "development": {"buildTarget": "app:build:development"}
                                },
                                "defaultConfiguration": "development"
                            }
                        }
                    }
                }
            }, indent=2)
        }
    }

    payload = json.dumps({"files": files}).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://codesandbox.io/api/v1/sandboxes/define?json=1",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read())
            sandbox_id = result.get("sandbox_id")
            if sandbox_id:
                return f"https://codesandbox.io/s/{sandbox_id}"
            return None
    except urllib.error.URLError as e:
        return None
    except Exception:
        return None


def get_embed_url(sandbox_url: str) -> str:
    """Convert a CodeSandbox URL to an embed URL."""
    sandbox_id = sandbox_url.rstrip("/").split("/")[-1]
    return (
        f"https://codesandbox.io/embed/{sandbox_id}"
        f"?fontsize=14&hidenavigation=1&theme=dark"
        f"&view=preview&codemirror=1"
    )


def build_stackblitz_launcher(component_code: str) -> str:
    """
    Fallback: build a standalone HTML file that opens StackBlitz when
    opened directly in a browser (outside any iframe).
    """
    import re
    files = {
        "src/app/app.component.ts": component_code,
        "src/app/app.module.ts": (
            "import { NgModule } from '@angular/core';\n"
            "import { BrowserModule } from '@angular/platform-browser';\n"
            "import { AppComponent } from './app.component';\n\n"
            "@NgModule({\n"
            "  declarations: [AppComponent],\n"
            "  imports: [BrowserModule],\n"
            "  bootstrap: [AppComponent]\n"
            "})\n"
            "export class AppModule {}\n"
        ),
        "src/styles.css": (
            "@import url('https://fonts.googleapis.com/css2?family=Inter:"
            "wght@400;500;600;700&display=swap');\n"
            "* { font-family: 'Inter', sans-serif; box-sizing: border-box; "
            "margin: 0; padding: 0; }\n"
            "body { background-color: #0f172a; color: #f1f5f9; padding: 2rem; }\n"
        ),
    }

    inputs = ""
    for path, content in files.items():
        safe = (content.replace("&", "&amp;").replace('"', "&quot;")
                .replace("<", "&lt;").replace(">", "&gt;"))
        inputs += (
            f'    <input type="hidden" name="project[files][{path}]" '
            f'value="{safe}">\n'
        )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Opening StackBlitz...</title>
  <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:sans-serif; background:#0f172a; color:#f1f5f9;
            display:flex; justify-content:center; align-items:center; min-height:100vh; }}
    .card {{ text-align:center; padding:2.5rem 2rem;
              background:rgba(255,255,255,0.05); border-radius:12px; max-width:420px; }}
    .spinner {{ width:44px; height:44px; border:3px solid rgba(99,102,241,0.25);
                border-top-color:#6366f1; border-radius:50%;
                animation:spin 0.8s linear infinite; margin:0 auto 1.5rem; }}
    @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
    p {{ color:#94a3b8; font-size:0.875rem; margin-top:0.5rem; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="spinner"></div>
    <h2>Opening StackBlitz...</h2>
    <p>Your Angular component is loading.<br>You can close this tab afterward.</p>
  </div>
  <form id="sb" method="POST" action="https://stackblitz.com/run">
    <input type="hidden" name="project[title]" value="Generated Angular Component">
    <input type="hidden" name="project[template]" value="angular-cli">
{inputs}
  </form>
  <script>
    window.addEventListener('load', function() {{
      document.getElementById('sb').submit();
    }});
  </script>
</body>
</html>"""


def main():
    st.title("Agent Execution Inspector")
    st.caption("Read-only debugger for agentic code generation system")

    st.warning(
        "⚠️ This is an OPTIONAL inspection tool. "
        "The core system is backend-first and CLI-based."
    )

    # Session state — persists result across Streamlit reruns
    if "result" not in st.session_state:
        st.session_state.result = None
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None
    if "sandbox_url" not in st.session_state:
        st.session_state.sandbox_url = None

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
            min_value=1, max_value=5, value=2,
            help="Maximum total iterations (1 generation + N-1 corrections)"
        )
        verbose = st.checkbox("Verbose Mode", value=False)

        st.divider()
        st.caption("Backend-First Architecture")
        st.caption("Agent loop is the primary artifact")
        st.caption("UI is non-essential inspection tool")

    st.header("1. Input Prompt")
    user_prompt = st.text_area(
        "Natural Language UI Description",
        placeholder="Example: A login card with email and password fields, no interactions",
        height=100
    )

    if st.button("Execute Agent Loop", type="primary", disabled=not user_prompt):
        if not api_key:
            st.error("Please provide a Google API key in the sidebar")
        else:
            if model_name:
                os.environ["MODEL_NAME"] = model_name

            # Reset sandbox on new generation
            st.session_state.sandbox_url = None

            with st.spinner("Initializing agent loop..."):
                try:
                    loop = AgentLoop(
                        design_system_path="design-system.json",
                        api_key=api_key,
                        max_retries=max_retries
                    )
                except Exception as e:
                    st.error(f"Failed to initialize agent loop: {e}")
                    st.stop()

            with st.spinner("Executing agent loop..."):
                try:
                    result = loop.run(user_prompt, verbose=verbose)
                except Exception as e:
                    st.error(f"Agent loop execution failed: {e}")
                    st.stop()

            st.session_state.result = result
            st.session_state.last_prompt = user_prompt

            # If generation succeeded, create CodeSandbox in the background
            if result.get("success") and result.get("code"):
                with st.spinner("Creating live preview..."):
                    sandbox_url = create_codesandbox(result["code"])
                    st.session_state.sandbox_url = sandbox_url

    if st.session_state.result is not None:
        display_execution_results(
            st.session_state.result,
            st.session_state.last_prompt,
            st.session_state.sandbox_url,
            max_retries
        )


def display_execution_results(
    result: dict,
    prompt: str,
    sandbox_url: str | None,
    max_retries: int
):
    st.header("2. Execution Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "✅ SUCCESS" if result["success"] else "❌ FAILED")
    with col2:
        st.metric("Iterations Used", result["iterations"])
    with col3:
        st.metric("Max Allowed", max_retries)

    st.subheader("User Prompt")
    st.code(prompt, language=None)

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

        status_icon = "✅" if is_valid else "❌"
        with st.expander(
            f"{status_icon} Iteration {iteration_num} — "
            f"{'VALID' if is_valid else f'INVALID ({len(errors)} error(s))'}",
            expanded=(iteration_num == 1 or not is_valid)
        ):
            if is_valid:
                st.success("Validation PASSED")
            else:
                st.error(f"Validation FAILED — {len(errors)} error(s)")
                st.subheader("Validation Errors")
                for i, error in enumerate(errors, 1):
                    st.markdown(f"{i}. `{error}`")

            st.subheader("Generated Code")
            code = attempt.get("code", "")
            if code:
                st.code(code, language="typescript", line_numbers=True)
            else:
                st.warning("No code generated")

            with st.expander("Raw Validation Report"):
                st.json(validation_report)

    st.header("4. Final Result")

    if result["success"]:
        st.success(
            f"✅ Code generation successful after {result['iterations']} iteration(s)"
        )

        final_code = result.get("code", "")
        if final_code:
            st.subheader("Generated Code")
            with st.expander("📄 View Full Code", expanded=True):
                st.code(final_code, language="typescript", line_numbers=True)
            st.caption(f"Code length: {len(final_code)} characters")

            # ---------------------------------------------------------------
            # LIVE PREVIEW SECTION
            # ---------------------------------------------------------------
            st.subheader("🚀 Live Preview")

            if sandbox_url:
                embed_url = get_embed_url(sandbox_url)

                col1, col2 = st.columns(2)
                with col1:
                    st.link_button(
                        "🔗 Open in CodeSandbox",
                        sandbox_url,
                        use_container_width=True
                    )
                with col2:
                    launcher = build_stackblitz_launcher(final_code)
                    st.download_button(
                        "📦 Download StackBlitz Launcher",
                        data=launcher,
                        file_name="open-in-stackblitz.html",
                        mime="text/html",
                        use_container_width=True
                    )

                st.info(
                    "Live preview below — your Angular component running in CodeSandbox. "
                    "First load takes ~30 seconds while Angular compiles."
                )

                # Embed the live running component directly in the page
                components.iframe(
                    src=embed_url,
                    height=500,
                    scrolling=True
                )

            else:
                st.warning(
                    "Live preview unavailable — CodeSandbox API could not be reached. "
                    "Use the download option below."
                )
                launcher = build_stackblitz_launcher(final_code)
                st.download_button(
                    "📦 Download StackBlitz Launcher",
                    data=launcher,
                    file_name="open-in-stackblitz.html",
                    mime="text/html"
                )
                st.caption(
                    "Open the downloaded file in your browser — "
                    "StackBlitz loads your component automatically."
                )

            # Download component file
            st.divider()
            st.download_button(
                label="📥 Download Component (.ts)",
                data=final_code,
                file_name="generated.component.ts",
                mime="text/plain"
            )

    else:
        st.error(
            f"❌ Code generation failed after {result['iterations']} iteration(s)"
        )
        st.error(f"Error: {result.get('error', 'Unknown error')}")

        if result.get("code"):
            st.subheader("Last Generated Code (Invalid)")
            st.code(result["code"], language="typescript", line_numbers=True)

    with st.expander("Raw Execution Object (Debug)"):
        st.json(result)


if __name__ == "__main__":
    if not os.path.exists("design-system.json"):
        st.error(
            "❌ design-system.json not found. Run from project root:\n\n"
            "```\nstreamlit run demo/streamlit_app.py\n```"
        )
        st.stop()

    main()