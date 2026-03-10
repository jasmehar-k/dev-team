from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PipelineState:
    """In-memory state container for a single orchestration run."""

    user_input: str
    outputs: Dict[str, str] = field(default_factory=dict)
