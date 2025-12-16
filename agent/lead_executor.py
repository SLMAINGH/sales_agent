"""
Lead executor for running research tasks.
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from agent.schemas import PlannedTask, ResearchPlan
from utils.context import ToolContextManager
from model.llm import call_llm
from tools import TOOLS


class LeadExecutor:
    """Executes research tasks and saves results."""

    def __init__(
        self,
        context_manager: ToolContextManager,
        model: str = "gpt-4o-mini",
    ):
        self.context_manager = context_manager
        self.model = model
        self.tool_map = {tool.name: tool for tool in TOOLS}

    async def execute_research(
        self,
        research_plan: ResearchPlan,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
    ):
        """Execute all research tasks."""
        # Execute all tasks in parallel
        await asyncio.gather(*[
            self._execute_task(task, on_task_start, on_task_complete)
            for task in research_plan.tasks
        ])

    async def _execute_task(
        self,
        task: PlannedTask,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
    ):
        """Execute a single task."""
        if on_task_start:
            on_task_start(task)

        try:
            # Ask LLM to resolve subtasks to tool calls
            tool_calls = await self._generate_tool_calls(task)

            # Execute tool calls in parallel
            await asyncio.gather(*[
                self._execute_tool_call(
                    tool_call["name"],
                    tool_call["args"],
                    task.id,
                    task.lead_id,
                    task.company,
                )
                for tool_call in tool_calls
            ])

            if on_task_complete:
                on_task_complete(task, success=True)
        except Exception as e:
            print(f"Task {task.id} failed: {e}")
            if on_task_complete:
                on_task_complete(task, success=False)

    async def _generate_tool_calls(self, task: PlannedTask) -> list:
        """Use LLM to resolve subtasks into tool calls."""
        subtask_list = "\n".join([
            f"- {st.description}"
            for st in task.sub_tasks
        ])

        prompt = f"""Task: {task.description}

Subtasks to complete:
{subtask_list}

Call the appropriate tools to gather data for these subtasks.
For each subtask, call ONE tool with the correct arguments."""

        system_prompt = """You are the execution component for a sales research agent.
Your job: Determine which tools to call to complete the given subtasks.
Call the appropriate tools with correct arguments based on the subtask descriptions.
Each subtask typically maps to one tool call."""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                tools=TOOLS,
                model=self.model,
            )

            # Extract tool calls from AIMessage
            if hasattr(response, 'tool_calls') and response.tool_calls:
                return [
                    {"name": tc.get("name"), "args": tc.get("args", {})}
                    for tc in response.tool_calls
                ]
            return []
        except Exception as e:
            print(f"Tool call generation failed: {e}")
            return []

    async def _execute_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        task_id: int,
        lead_id: Optional[str] = None,
        company: Optional[str] = None,
    ):
        """Execute a single tool call and save result."""
        tool = self.tool_map.get(tool_name)
        if not tool:
            print(f"Tool not found: {tool_name}")
            return

        try:
            # Invoke tool
            result = await asyncio.to_thread(tool.invoke, args)

            # Save to context manager
            self.context_manager.save_context(
                tool_name=tool_name,
                args=args,
                result=result,
                task_id=task_id,
                lead_id=lead_id,
                company=company,
            )
        except Exception as e:
            print(f"Tool execution failed for {tool_name}: {e}")
