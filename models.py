from typing import Dict, Any, List
from pydantic import BaseModel


class GraphCreateRequest(BaseModel):
    nodes: Dict[str, str]          # node_id -> tool_name
    edges: Dict[str, str]          # from_node -> to_node
    max_iterations: int = 10


class RunInfo(BaseModel):
    run_id: str
    status: str
    log: List[str]
    state: Dict[str, Any]
