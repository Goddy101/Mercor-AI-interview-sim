# interfaces/cli_architect.py
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Adjust Python path to allow running directly from the interfaces directory
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.codebase_architect.generator import generate_report

# Terminal color codes for a premium CLI experience without extra dependencies
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=f"{Colors.CYAN}[%(asctime)s]{Colors.ENDC} %(message)s",
        datefmt="%H:%M:%S"
    )

async def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Autonomous Codebase Architect & Staff Auditor")
    parser.add_argument(
        "repo_path", 
        type=str, 
        help="Path to the local repository you want to audit (e.g., ../Frontier)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="ARCHITECTURE_AUDIT.md", 
        help="Name of the markdown file to generate (default: ARCHITECTURE_AUDIT.md)"
    )
    
    args = parser.parse_args()
    target_dir = Path(args.repo_path).resolve()
    
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{Colors.FAIL}Error: The directory '{target_dir}' does not exist.{Colors.ENDC}")
        sys.exit(1)

    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 Initializing Autonomous Codebase Architect...{Colors.ENDC}")
    print(f"Targeting: {Colors.BOLD}{target_dir}{Colors.ENDC}\n")

    try:
        # Run the async generator
        report = await generate_report(str(target_dir))
        
        # --- TERMINAL OUTPUT ---
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Audit Complete. Executive Summary:{Colors.ENDC}\n")
        print(f"{Colors.BLUE}System Overview:{Colors.ENDC}\n{report.system_overview}\n")
        
        print(f"{Colors.WARNING}{Colors.BOLD}🚨 Critical Vulnerabilities Found ({len(report.vulnerabilities)}):{Colors.ENDC}")
        if not report.vulnerabilities:
            print("  None detected! Solid architecture.")
        else:
            for v in report.vulnerabilities:
                color = Colors.FAIL if v.severity.upper() == "HIGH" else Colors.WARNING
                print(f"  {color}[{v.severity}] {v.issue_type} in {v.file_path}{Colors.ENDC}")
                print(f"      Fix: {v.recommendation}")
        
        # --- MARKDOWN FILE GENERATION ---
        output_path = target_dir / args.output
        
        md_content = f"# Architecture & Codebase Audit\n\n"
        md_content += f"**Repository:** `{target_dir.name}`\n\n"
        md_content += f"## System Overview\n{report.system_overview}\n\n"
        md_content += f"## Concurrency Model\n{report.concurrency_model}\n\n"
        md_content += f"## Data Flow\n{report.data_flow}\n\n"
        md_content += f"## Vulnerabilities & Tech Debt\n"
        
        if not report.vulnerabilities:
            md_content += "No critical vulnerabilities detected.\n"
        else:
            for v in report.vulnerabilities:
                md_content += f"### {v.issue_type} (`{v.severity}`)\n"
                md_content += f"- **Location:** `{v.file_path}`\n"
                md_content += f"- **Recommendation:** {v.recommendation}\n\n"

        output_path.write_text(md_content, encoding="utf-8")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}📄 Full report saved to: {output_path}{Colors.ENDC}\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Audit Failed: {e}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    # Future-proof Windows event loop policy
    if sys.platform == 'win32' and sys.version_info < (3, 16):
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())