"""
Main CLI entry point for Guided Component Architect
"""

import sys
import argparse
from agent_loop import AgentLoop


def main():
    """CLI interface for the agentic code generation system."""
    parser = argparse.ArgumentParser(
        description="Guided Component Architect - Generate Angular components from natural language"
    )
    parser.add_argument(
        "request",
        type=str,
        help="Natural language description of the UI component to generate"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for generated component (optional)"
    )
    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Suppress progress output"
    )
    parser.add_argument(
        "--max-retries",
        "-r",
        type=int,
        default=2,
        help="Maximum correction attempts (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Initialize and run agent loop
    loop = AgentLoop(max_retries=args.max_retries)
    result = loop.run(args.request, verbose=not args.silent)
    
    # Handle results
    if result["success"]:
        print("\n" + "="*60)
        print("GENERATED COMPONENT CODE:")
        print("="*60)
        print(result["code"])
        print("="*60)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result["code"])
            print(f"\n✅ Code saved to: {args.output}")
        
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ GENERATION FAILED")
        print("="*60)
        print(f"Error: {result.get('error', 'Unknown error')}")
        
        if result.get("code"):
            print("\nLast generated code (invalid):")
            print("-"*60)
            print(result["code"])
            print("-"*60)
        
        sys.exit(1)


if __name__ == "__main__":
    main()
