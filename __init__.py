from typing import Dict, Callable, Any

from .code_review import (
    extract_functions,
    check_complexity,
    detect_issues,
    suggest_improvements,
)


ToolRegistry = Dict[str, Callable[..., Any]]

tools: ToolRegistry = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_issues": detect_issues,
    "suggest_improvements": suggest_improvements,
}
