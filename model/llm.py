"""
LLM interface layer supporting multiple providers.
"""
import os
from typing import Optional, Type, AsyncGenerator, Any, Dict, List
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool


DEFAULT_MODEL = "gpt-4o-mini"


def _get_llm(model: Optional[str] = None, temperature: float = 0.7):
    """Get LLM instance based on model name."""
    model_name = model or DEFAULT_MODEL

    # For now, using OpenAI. Can extend to support Anthropic, Google, etc.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )


async def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    tools: Optional[List[BaseTool]] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> Any:
    """
    Call LLM with optional structured output or tool binding.

    Args:
        prompt: User prompt
        system_prompt: System prompt
        output_schema: Pydantic model for structured output
        tools: List of tools to bind
        model: Model name
        temperature: Temperature for generation

    Returns:
        - If output_schema: Parsed Pydantic object
        - If tools: AIMessage with tool_calls
        - Otherwise: String response
    """
    llm = _get_llm(model, temperature)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    # Structured output
    if output_schema:
        structured_llm = llm.with_structured_output(output_schema)
        response = await structured_llm.ainvoke(messages)
        return response

    # Tool binding
    if tools:
        llm_with_tools = llm.bind_tools(tools)
        response = await llm_with_tools.ainvoke(messages)
        return response

    # Regular text response
    response = await llm.ainvoke(messages)
    return response.content


async def call_llm_stream(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """
    Stream LLM response.

    Args:
        prompt: User prompt
        system_prompt: System prompt
        model: Model name
        temperature: Temperature for generation

    Yields:
        String chunks from the LLM
    """
    llm = _get_llm(model, temperature)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    async for chunk in llm.astream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            yield chunk.content
