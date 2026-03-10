import asyncio
import json
from typing import Dict, List, Tuple

from openai import OpenAI

from agents import pm, architect, dev, tester, debugger, reviewer, manager


AGENT_ORDER: List[Tuple[str, object]] = [
    (pm.NAME, pm),
    (architect.NAME, architect),
]

PARALLEL_AGENTS: List[Tuple[str, object]] = [
    (dev.NAME, dev),
    (tester.NAME, tester),
    (debugger.NAME, debugger),
    (reviewer.NAME, reviewer),
]

FINAL_AGENT: Tuple[str, object] = (manager.NAME, manager)


def _format_context(context: Dict[str, str]) -> str:
    if not context:
        return "(none)"
    return json.dumps(context, indent=2, sort_keys=True)


def _extract_output_text(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text.strip()
    output = getattr(response, "output", None) or []
    parts: List[str] = []
    for item in output:
        item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
        if item_type != "message":
            continue
        content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else None) or []
        for chunk in content:
            chunk_type = getattr(chunk, "type", None) or (chunk.get("type") if isinstance(chunk, dict) else None)
            if chunk_type == "output_text":
                chunk_text = getattr(chunk, "text", None) or (chunk.get("text") if isinstance(chunk, dict) else None)
                if chunk_text:
                    parts.append(chunk_text)
    return "\n".join(parts).strip()


def _build_input(user_input: str, context: Dict[str, str]) -> str:
    return (
        "User Request:\n"
        f"{user_input}\n\n"
        "Context (prior agent outputs, JSON):\n"
        f"{_format_context(context)}\n"
    )


def _call_agent(client: OpenAI, model: str, agent_module, user_input: str, context: Dict[str, str]) -> str:
    response = client.responses.create(
        model=model,
        instructions=agent_module.SYSTEM_PROMPT,
        input=_build_input(user_input, context),
    )
    return _extract_output_text(response)


async def _call_agent_async(client: OpenAI, model: str, agent_module, user_input: str, context: Dict[str, str]) -> str:
    return await asyncio.to_thread(_call_agent, client, model, agent_module, user_input, context)


async def run_pipeline_async(user_input: str, model: str, mode: str = "parallel") -> Dict[str, str]:
    client = OpenAI()
    outputs: Dict[str, str] = {}

    for name, agent_module in AGENT_ORDER:
        outputs[name] = await _call_agent_async(client, model, agent_module, user_input, outputs)

    if mode == "sequential":
        for name, agent_module in PARALLEL_AGENTS:
            outputs[name] = await _call_agent_async(client, model, agent_module, user_input, outputs)
    else:
        tasks = [
            _call_agent_async(client, model, agent_module, user_input, outputs)
            for _, agent_module in PARALLEL_AGENTS
        ]
        results = await asyncio.gather(*tasks)
        for (name, _), result in zip(PARALLEL_AGENTS, results):
            outputs[name] = result

    final_name, final_module = FINAL_AGENT
    outputs[final_name] = await _call_agent_async(client, model, final_module, user_input, outputs)

    return outputs


def run_pipeline(user_input: str, model: str, mode: str = "parallel") -> Dict[str, str]:
    return asyncio.run(run_pipeline_async(user_input, model, mode))
