from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import WebSocket
from loguru import logger

from .config import settings
from .tools import tools


GraphsStore = Dict[str, Dict[str, Any]]
RunsStore = Dict[str, Dict[str, Any]]

graphs: GraphsStore = {}
runs: RunsStore = {}


async def execute_node(
    graph_id: str,
    run_id: str,
    node_id: str,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    graph = graphs[graph_id]
    tool_name = graph["nodes"][node_id]
    tool = tools.get(tool_name)

    if tool is None:
        raise RuntimeError(f"Tool not registered: {tool_name}")

    msg = f"[graph={graph_id} run={run_id}] Executing node '{node_id}' with tool '{tool_name}'"
    logger.info(msg)
    runs[run_id]["log"].append(msg)

    for ws in runs[run_id]["ws"]:
        await safe_send(ws, {"event": "node_start", "node": node_id, "log": msg})

    result = await tool(**state)
    if result:
        state.update(result)

    msg_done = f"[graph={graph_id} run={run_id}] Finished node '{node_id}'"
    logger.info(msg_done)
    runs[run_id]["log"].append(msg_done)

    for ws in runs[run_id]["ws"]:
        await safe_send(ws, {"event": "node_end", "node": node_id, "log": msg_done, "state": result})

    return state


async def safe_send(ws: WebSocket, data: Dict[str, Any]) -> None:
    try:
        await ws.send_json(data)
    except Exception:
        # ignore broken connections
        pass


async def workflow_background_task(
    graph_id: str,
    run_id: str,
    initial_state: Dict[str, Any],
) -> None:
    graph = graphs[graph_id]
    max_iterations = graph.get("max_iterations", settings.max_iterations)
    state = dict(initial_state)

    runs[run_id]["status"] = "running"
    runs[run_id]["state"] = state

    current_node = "extract_functions"

    for i in range(max_iterations):
        state["iteration"] = i + 1
        runs[run_id]["state"] = state

        if current_node not in graph["nodes"]:
            break

        state = await execute_node(graph_id, run_id, current_node, state)

        quality = float(state.get("quality_score", 0.0))
        if quality >= 0.9:
            msg = f"[graph={graph_id} run={run_id}] Stopping: quality_score={quality:.3f}"
            logger.info(msg)
            runs[run_id]["log"].append(msg)
            break

        next_node = graph["edges"].get(current_node)
        if not next_node:
            break

        current_node = next_node

    runs[run_id]["status"] = "completed"
    runs[run_id]["state"] = state

    done_msg = f"[graph={graph_id} run={run_id}] Workflow completed"
    logger.info(done_msg)
    runs[run_id]["log"].append(done_msg)

    for ws in runs[run_id]["ws"]:
        await safe_send(ws, {"event": "completed", "state": state})


def create_default_code_review_graph() -> str:
    graph_id = "code_review"
    graphs[graph_id] = {
        "nodes": {
            "extract_functions": "extract_functions",
            "check_complexity": "check_complexity",
            "detect_issues": "detect_issues",
            "suggest_improvements": "suggest_improvements",
        },
        "edges": {
            "extract_functions": "check_complexity",
            "check_complexity": "detect_issues",
            "detect_issues": "suggest_improvements",
            "suggest_improvements": "suggest_improvements",
        },
        "max_iterations": 5,
    }
    logger.info(f"Default graph registered as {graph_id}")
    return graph_id


def init_run() -> str:
    run_id = str(uuid4())
    runs[run_id] = {"status": "queued", "log": [], "state": {}, "ws": []}
    return run_id
