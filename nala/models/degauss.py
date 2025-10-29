from pydantic import Field, field_validator
from typing import List, Union

from .baseModels import IgnoreExtra


class DegaussableElement(IgnoreExtra):
    """
    Model for elements that can be degaussed.
    """

    tolerance: float = Field(default=0.5, alias="degauss_tolerance")
    """Current tolerance for degaussing process."""

    values: List[float] = Field(default=[], alias="degauss_values")
    """List of degaussing current values."""

    steps: int = Field(default=11, alias="num_degauss_steps")
    """Number of degaussing steps."""

    @field_validator("values", mode="before")
    @classmethod
    def validate_degauss_values(cls, v: Union[str, List]) -> list:
        if isinstance(v, str):
            return list(map(float, v.split(",")))
        elif isinstance(v, (list, tuple)):
            return list(v)
        else:
            raise ValueError("degauss_values should be a string or a list of floats")
