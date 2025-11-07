from pydantic import Field, field_validator
from typing import Any
from .baseModels import IgnoreExtra


class ManufacturerElement(IgnoreExtra):
    """Manufacturer info model."""

    manufacturer: str = ""
    """Name of manufacturer."""

    serial_number: str = ""
    """Serieal number of element."""

    hardware_class: str = Field(alias="hardware_type", default="")

    @field_validator("serial_number", mode="before")
    @classmethod
    def validate_serial_number(cls, v: str | int) -> str:
        if isinstance(v, int):
            return str(v)
        return v

    @field_validator("manufacturer", mode="before")
    @classmethod
    def validate_manufacturer(cls, v: str | int) -> str:
        if isinstance(v, int):
            return str(v)
        return v