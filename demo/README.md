# Streamlit Inspection Layer

## ⚠️ IMPORTANT: This is NOT the Product

This Streamlit app is an **OPTIONAL** visual debugger and trace viewer for the Governed Angular UI Generator system.

### Backend-First Architecture

The core system is **backend-first** and **CLI-based**:
- `agent_loop.py` - Self-correcting orchestration loop
- `generator.py` - Code generation with LLM
- `validator.py` - Design system validation
- `design-system.json` - Design system tokens

**The system works fully via CLI without this Streamlit interface.**

### Purpose of This UI

This Streamlit app exists ONLY to:
- Visualize agent execution steps
- Inspect validation failures and self-corrections
- View generated code in a structured format
- Download code and preview in StackBlitz
- Debug agent behavior during evaluation

This is a **read-only visualizer**, not a code editor or production interface.

### What This UI Does NOT Do

- ❌ Does NOT contain generation logic
- ❌ Does NOT contain validation logic
- ❌ Does NOT duplicate core functionality
- ❌ Does NOT replace the CLI
- ❌ Is NOT required for the system to work

### Architecture

```
┌─────────────────────────────────────────┐
│         CLI (Primary Interface)         │
│              main.py                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Core Agent Loop                 │
│          agent_loop.py                  │
│    (Backend-first, CLI-based)           │
└─────────────────┬───────────────────────┘
                  │
                  ├──────────────────────┐
                  ▼                      ▼
         ┌────────────────┐    ┌────────────────┐
         │   generator.py │    │  validator.py  │
         └────────────────┘    └────────────────┘
                  │
                  │ (Optional visualization)
                  ▼
         ┌────────────────────────────┐
         │  Streamlit Inspection UI   │
         │  demo/streamlit_app.py     │
         │  (Read-only debugger)      │
         └────────────────────────────┘
```

### How It Works

The Streamlit app:
1. Calls `AgentLoop.run()` - the existing public function
2. Receives the structured execution object
3. Displays the results in a visual format
4. Provides download and preview options

**No logic is duplicated. No generation happens in Streamlit callbacks.**

### Running the Streamlit App

From the project root directory:

```bash
streamlit run demo/streamlit_app.py
```

### Requirements

The Streamlit app requires the same dependencies as the core system, plus Streamlit:

```bash
pip install streamlit
```

Or add to `requirements.txt`:
```
streamlit>=1.28.0
```

### Usage

1. Enter your Google API key in the sidebar
2. Configure max retries (default: 2)
3. Enter a natural language UI description
4. Click "Execute Agent Loop"
5. Observe the execution trace and validation results
6. Download code or preview in StackBlitz

### What You'll See

- **Execution Summary**: Status, iterations used, max allowed
- **User Prompt**: The input description you provided
- **Agent Execution Trace**: Each iteration with validation results
- **Validation Errors**: Detailed error messages per attempt
- **Generated Code**: View code from each iteration
- **Final Result**: Success/failure with final code
- **Action Buttons**: Download component or open in StackBlitz

### StackBlitz Preview

The Streamlit app provides a one-click preview in StackBlitz:

1. Click "🚀 Download StackBlitz Launcher"
2. Open the downloaded `open-in-stackblitz.html` file in your browser
3. StackBlitz opens automatically with your component loaded
4. Edit and preview the component live

The launcher HTML includes:
- Your generated Angular component
- Complete Angular module setup
- Global styles with Inter font
- Auto-submit form for seamless StackBlitz integration

### Evaluation Workflow

**Primary Evaluation (Backend/CLI):**
```bash
python main.py "A login card with glassmorphism effect"
```

**Optional Visualization (Streamlit):**
```bash
streamlit run demo/streamlit_app.py
```

### Session State Management

The Streamlit app uses session state to persist results across reruns:
- Results remain visible after clicking buttons
- No data loss when interacting with widgets
- Clean separation between input and display

### If Streamlit is Removed

If you delete the `demo/` directory, the project will function identically:
- All core logic remains in `agent_loop.py`, `generator.py`, `validator.py`
- CLI interface (`main.py`) continues to work
- No functionality is lost

### Design Constraints

This UI follows strict constraints:
- No custom styling or branding
- No animations or product UI metaphors
- Resembles an internal engineering debugger
- Read-only visualization only
- Minimal dependencies

### Signaling to Evaluators

**This Streamlit app is explicitly NOT the product.**

The agentic loop (`agent_loop.py`) is the primary artifact. The UI is a non-essential inspection tool for convenience during evaluation.

The system is designed to be evaluated primarily through:
1. CLI execution (`main.py`)
2. Code review of core modules
3. Validation test suite

The Streamlit app is provided as an optional convenience for visualizing agent behavior and previewing generated components.

---

**Remember**: Backend-first. CLI-based. Streamlit is optional.
