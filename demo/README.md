# Streamlit Inspection Layer

## ⚠️ IMPORTANT: This is NOT the Product

This Streamlit app is an **OPTIONAL** visual debugger and trace viewer for the Guided Component Architect system.

### Backend-First Architecture

The core system is **backend-first** and **CLI-based**:
- `agent_loop.py` - Self-correcting orchestration loop
- `generator.py` - Code generation agent
- `validator.py` - Validation agent
- `design-system.json` - Design system tokens

**The system works fully via CLI without this Streamlit interface.**

### Purpose of This UI

This Streamlit app exists ONLY to:
- Visualize agent execution steps
- Inspect validation failures and retries
- View generated code without running CLI
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

### What You'll See

- **Execution Summary**: Status, iterations, metrics
- **Agent Execution Trace**: Each iteration with validation results
- **Validation Errors**: Detailed error messages per attempt
- **Generated Code**: View code from each iteration
- **Final Result**: Success/failure with final code

### Evaluation Workflow

**Primary Evaluation (Backend/CLI):**
```bash
python main.py "A login card with glassmorphism effect"
```

**Optional Visualization (Streamlit):**
```bash
streamlit run demo/streamlit_app.py
```

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

### Signaling to Evaluators

**This Streamlit app is explicitly NOT the product.**

The agentic loop (`agent_loop.py`) is the primary artifact. The UI is a non-essential inspection tool for convenience during evaluation.

The system is designed to be evaluated primarily through:
1. CLI execution (`main.py`)
2. Test suite (`test_system.py`)
3. Code review of core modules

The Streamlit app is provided as an optional convenience for visualizing agent behavior.

---

**Remember**: Backend-first. CLI-based. Streamlit is optional.
