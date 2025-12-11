from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Workflow Engine"
    max_iterations: int = 10
    log_file: str = "logs.json"


settings = Settings()
