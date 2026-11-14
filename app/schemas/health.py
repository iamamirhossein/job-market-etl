from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "unknown"]
    app_name: str
    version: str
    environment: str
    timestamp: datetime
