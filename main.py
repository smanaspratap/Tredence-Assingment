from __future__ import annotations

import asyncio
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket

from .config import settings
from .logging_config import setup_logging
from .models import GraphCreateRequest, RunInfo
from .graph_engine import (
    graphs,
    runs,
    init_run,
    workflow_background_task,
    create_default_code_review_graph,
)


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    async def on_startup() -> None:
        create_default_code_review_graph()

    @app.post("/graph/create")
    async def create_graph(config: GraphCreateRequest) -> Dict[str, Any]:
        graph_id = f"graph_{len(graphs) + 1}"
        graphs[graph_id] = {
            "nodes": config.nodes,
            "edges": config.edges,
            "max_iterations": config.max_iterations,
        }
        return {"graph_id": graph_id}

    @app.post("/graph/{graph_id}/run")
    async def run_graph(
        graph_id: str,
        initial_state: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        if graph_id not in graphs:
            raise HTTPException(status_code=404, detail="Graph not found")

        run_id = init_run()
        background_tasks.add_task(
            workflow_background_task,
            graph_id,
            run_id,
            initial_state,
        )
        return {"run_id": run_id, "status": "queued"}

    @app.get("/graph/run/{run_id}/state", response_model=RunInfo)
    async def get_run_state(run_id: str) -> RunInfo:
        run = runs.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return RunInfo(
            run_id=run_id,
            status=run["status"],
            log=run["log"],
            state=run["state"],
        )

    @app.websocket("/ws/run/{run_id}")
    async def websocket_logs(websocket: WebSocket, run_id: str) -> None:
        await websocket.accept()
        if run_id not in runs:
            await websocket.close(code=1008)
            return

        runs[run_id]["ws"].append(websocket)
        try:
            while True:
                await asyncio.sleep(60)
        finally:
            if websocket in runs[run_id]["ws"]:
                runs[run_id]["ws"].remove(websocket)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
