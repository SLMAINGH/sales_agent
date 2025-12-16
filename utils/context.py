"""
Tool context manager for saving and loading tool outputs.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from agent.schemas import SelectedContexts
from model.llm import call_llm


class ContextPointer:
    """Lightweight pointer to a context file."""
    def __init__(
        self,
        filepath: str,
        filename: str,
        tool_name: str,
        tool_description: str,
        args: Dict[str, Any],
        task_id: Optional[int] = None,
        lead_id: Optional[str] = None,
        company: Optional[str] = None,
    ):
        self.filepath = filepath
        self.filename = filename
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.args = args
        self.task_id = task_id
        self.lead_id = lead_id
        self.company = company


class ContextData:
    """Full context data loaded from file."""
    def __init__(self, data: Dict[str, Any]):
        self.tool_name = data.get("tool_name")
        self.tool_description = data.get("tool_description")
        self.args = data.get("args", {})
        self.timestamp = data.get("timestamp")
        self.task_id = data.get("task_id")
        self.lead_id = data.get("lead_id")
        self.company = data.get("company")
        self.result = data.get("result")


class ToolContextManager:
    """Manages tool output persistence and retrieval."""

    def __init__(self, context_dir: str = ".leads/context", model: str = "gpt-4o-mini"):
        self.context_dir = context_dir
        self.model = model
        self.pointers: List[ContextPointer] = []

        # Create context directory
        Path(context_dir).mkdir(parents=True, exist_ok=True)

    def _hash_args(self, args: Dict[str, Any]) -> str:
        """Create hash from arguments."""
        args_str = json.dumps(args, sort_keys=True)
        return hashlib.md5(args_str.encode()).hexdigest()[:12]

    def hash_query(self, query: str) -> str:
        """Create hash from query string."""
        return hashlib.md5(query.encode()).hexdigest()[:12]

    def _generate_filename(
        self,
        tool_name: str,
        args: Dict[str, Any],
        lead_id: Optional[str] = None,
        company: Optional[str] = None,
    ) -> str:
        """Generate unique filename for tool output."""
        args_hash = self._hash_args(args)

        # Include identifier in filename for readability
        if lead_id:
            return f"{lead_id}_{tool_name}_{args_hash}.json"
        elif company:
            company_clean = company.replace(" ", "_").replace("/", "_")
            return f"{company_clean}_{tool_name}_{args_hash}.json"
        else:
            return f"{tool_name}_{args_hash}.json"

    def _get_tool_description(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create human-readable description of tool call."""
        parts = [tool_name.replace("_", " ")]

        # Add key arguments
        if "linkedin_url" in args:
            parts.append(f"for {args['linkedin_url']}")
        if "company_name" in args:
            parts.append(f"for {args['company_name']}")
        if "query" in args:
            parts.append(f'query="{args["query"]}"')

        return " ".join(parts)

    def save_context(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        task_id: Optional[int] = None,
        lead_id: Optional[str] = None,
        company: Optional[str] = None,
    ) -> str:
        """Save tool output to filesystem."""
        filename = self._generate_filename(tool_name, args, lead_id, company)
        filepath = os.path.join(self.context_dir, filename)
        tool_description = self._get_tool_description(tool_name, args)

        context_data = {
            "tool_name": tool_name,
            "args": args,
            "tool_description": tool_description,
            "timestamp": None,  # Could add datetime.now().isoformat()
            "task_id": task_id,
            "lead_id": lead_id,
            "company": company,
            "result": result,
        }

        with open(filepath, "w") as f:
            json.dump(context_data, f, indent=2)

        # Create pointer
        pointer = ContextPointer(
            filepath=filepath,
            filename=filename,
            tool_name=tool_name,
            tool_description=tool_description,
            args=args,
            task_id=task_id,
            lead_id=lead_id,
            company=company,
        )
        self.pointers.append(pointer)

        return filepath

    def get_all_pointers(self) -> List[ContextPointer]:
        """Get all context pointers."""
        return self.pointers.copy()

    def get_pointers_for_lead(self, lead_id: str) -> List[ContextPointer]:
        """Get pointers for a specific lead."""
        return [p for p in self.pointers if p.lead_id == lead_id]

    def get_pointers_for_company(self, company: str) -> List[ContextPointer]:
        """Get pointers for a specific company."""
        return [p for p in self.pointers if p.company == company]

    def load_contexts(self, filepaths: List[str]) -> List[ContextData]:
        """Load full context data from files."""
        contexts = []
        for filepath in filepaths:
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    contexts.append(ContextData(data))
            except Exception as e:
                print(f"Warning: Failed to load context {filepath}: {e}")
        return contexts

    async def select_relevant_contexts(
        self,
        query: str,
        available_pointers: List[ContextPointer],
    ) -> List[str]:
        """Use LLM to select relevant contexts."""
        if not available_pointers:
            return []

        pointers_info = [
            {
                "id": i,
                "tool_name": p.tool_name,
                "tool_description": p.tool_description,
                "args": p.args,
            }
            for i, p in enumerate(available_pointers)
        ]

        prompt = f"""
Original user query: "{query}"

Available tool outputs:
{json.dumps(pointers_info, indent=2)}

Select which tool outputs are relevant for answering the query.
Return a JSON object with a "context_ids" field containing a list of IDs (0-indexed) of the relevant outputs.
Only select outputs that contain data directly relevant to answering the query.
"""

        system_prompt = """You are a context selection agent.
Your job is to identify which tool outputs are relevant for answering a user's query.
Analyze which tool outputs contain data directly relevant to answering the query.
Select only the outputs that are necessary - avoid selecting irrelevant data."""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                output_schema=SelectedContexts,
                model=self.model,
            )

            selected_ids = response.context_ids

            return [
                available_pointers[idx].filepath
                for idx in selected_ids
                if 0 <= idx < len(available_pointers)
            ]
        except Exception as e:
            print(f"Warning: Context selection failed: {e}, loading all contexts")
            return [p.filepath for p in available_pointers]

    def get_context_for_lead(self, lead_id: str, context_type: str = "profile") -> Dict[str, Any]:
        """Get aggregated context data for a lead."""
        pointers = self.get_pointers_for_lead(lead_id)
        contexts = self.load_contexts([p.filepath for p in pointers])

        # Aggregate all results
        aggregated = {}
        for ctx in contexts:
            if ctx.result:
                aggregated[ctx.tool_name] = ctx.result

        return aggregated

    def get_context_for_company(self, company: str) -> Dict[str, Any]:
        """Get aggregated context data for a company."""
        pointers = self.get_pointers_for_company(company)
        contexts = self.load_contexts([p.filepath for p in pointers])

        # Aggregate all results
        aggregated = {}
        for ctx in contexts:
            if ctx.result:
                aggregated[ctx.tool_name] = ctx.result

        return aggregated
