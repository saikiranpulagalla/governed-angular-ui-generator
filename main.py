"""
Main CLI entry point for Governed Angular UI Generator
"""

import sys
import argparse
from agent_loop import AgentLoop


def main():
    """CLI interface for the agentic code generation system."""
    parser = argparse.ArgumentParser(
        description="Governed Angular UI Generator — Generate Angular components from natural language"
    )
    parser.add_argument(
        "request",
        type=str,
        help="Natural language description of the UI component to generate"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path for generated component (optional)"
    )
    parser.add_argument(
        "--silent", "-s",
        action="store_true",
        help="Suppress progress output"
    )
    parser.add_argument(
        "--max-retries", "-r",
        type=int,
        default=2,
        help="Maximum total iterations (default: 2 = 1 generation + 1 correction)"
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Open generated component in StackBlitz for instant live preview"
    )

    args = parser.parse_args()

    # Initialize and run agent loop
    loop = AgentLoop(max_retries=args.max_retries)
    result = loop.run(args.request, verbose=not args.silent)

    # Handle results
    if result["success"]:
        print("\n" + "=" * 60)
        print("GENERATED COMPONENT CODE:")
        print("=" * 60)
        print(result["code"])
        print("=" * 60)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["code"])
            print(f"\n✅ Code saved to: {args.output}")

        # Open StackBlitz preview if requested
        if args.preview:
            try:
                from stackblitz_preview import open_stackblitz_preview
                html_file = open_stackblitz_preview(result["code"])
                print(f"\n🚀 StackBlitz preview opened in your browser")
                print(f"📄 Temp file: {html_file}")
            except ImportError:
                print(
                    "\n⚠️  stackblitz_preview.py not found in project root. "
                    "Make sure it exists alongside main.py."
                )
            except Exception as e:
                print(f"\n⚠️  Could not open preview: {e}")
                if args.output:
                    print(
                        f"   Try manually: "
                        f"python stackblitz_preview.py {args.output}"
                    )

        sys.exit(0)

    else:
        print("\n" + "=" * 60)
        print("❌ GENERATION FAILED")
        print("=" * 60)
        print(f"Error: {result.get('error', 'Unknown error')}")

        if result.get("code"):
            print("\nLast generated code (invalid):")
            print("-" * 60)
            print(result["code"])
            print("-" * 60)

        sys.exit(1)


if __name__ == "__main__":
    main()