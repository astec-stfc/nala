from pydantic import BaseModel, ConfigDict
from typing import List

class ReferenceElement(BaseModel):
    """Reference information model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        populate_by_name=True,
    )

    drawings: List[str] = []
    """Paths to mechanical drawings of the element."""

    design_files: List[str] = []
    """Paths to design files for the element."""