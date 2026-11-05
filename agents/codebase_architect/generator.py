# agents/codebase_architect/generator.py
import asyncio
import logging
from pathlib import Path
from typing import List

from core.llm_client import llm
from core.schemas import ArchitectureReport
from utils.file_handlers import CodebaseParser, CodeChunker

logger = logging.getLogger(__name__)

# The strict persona prompt forces Staff-level analysis
STAFF_ENGINEER_PROMPT = """
You are an elite Staff AI Engineer and Systems Architect conducting a brutal, high-level codebase audit.
You are reviewing a raw repository dump.

YOUR MISSION:
1. Map the System Architecture: Identify the core frameworks, microservices, and databases.
2. Analyze Concurrency & State: How does the system handle concurrent loads, state management, and caching?
3. Map the Data Flow: Trace how data moves from the persistence layer to the client/API layer.
4. Hunt for Vulnerabilities: Identify critical architectural flaws, such as N+1 queries, synchronous blocking in async loops, race conditions, or unhandled exceptions.

CONSTRAINTS:
- Do NOT just summarize the code syntax. Analyze the SYSTEM.
- Be harsh, precise, and quantifiable.
- Output strictly in the requested JSON format.
"""

class CodebaseArchitect:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.parser = CodebaseParser(max_concurrent_reads=100)

    async def analyze_repository(self) -> ArchitectureReport:
        """
        Orchestrates the entire flow: Parse -> Chunk -> Analyze -> Return Pydantic Model.
        """
        logger.info(f"Starting architectural audit for: {self.root_dir.name}")
        
        # 1. Parse the local directory asynchronously
        parsed_repo_dict = await self.parser.parse_directory(self.root_dir)
        if not parsed_repo_dict:
            raise ValueError("Repository is empty or unreadable.")

        # 2. Chunk the codebase to inject file headers and prevent token loss
        chunks = CodeChunker.chunk_repo_for_llm(parsed_repo_dict)
        
        # 3. Aggregate chunks for the LLM context window
        # For a 1-day MVP targeting GPT-4o (128k context), we join chunks up to ~300,000 characters 
        # (roughly 75,000 tokens) to leave plenty of room for the structured output.
        aggregated_code = ""
        max_chars = 300000 
        
        for chunk in chunks:
            if len(aggregated_code) + len(chunk) < max_chars:
                aggregated_code += chunk + "\n"
            else:
                logger.warning("Context limit reached. Truncating remaining files for this macro-audit.")
                break

        # 4. Construct the user payload
        user_payload = (
            f"Here is the codebase dump for the '{self.root_dir.name}' repository.\n\n"
            f"{aggregated_code}\n\n"
            "Analyze this system and return the structured ArchitectureReport."
        )

        logger.info("Codebase mapped. Sending context to AI for Staff-level audit...")
        
        # 5. Call the LLM with enforced structured outputs
        report: ArchitectureReport = await llm.generate_structured(
            system_prompt=STAFF_ENGINEER_PROMPT,
            user_prompt=user_payload,
            response_model=ArchitectureReport
        )
        
        logger.info("Audit complete. Architecture Report generated successfully.")
        return report

# Utility wrapper to easily run this from other scripts
async def generate_report(repo_path: str) -> ArchitectureReport:
    architect = CodebaseArchitect(repo_path)
    return await architect.analyze_repository()