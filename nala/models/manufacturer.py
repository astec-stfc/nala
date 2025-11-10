from pydantic import field_validator
from .baseModels import IgnoreExtra


class ManufacturerElement(IgnoreExtra):
    """Manufacturer info model."""

    manufacturer: str = ""
    """Name of manufacturer."""

    serial_number: str = ""
    """Serial number of element."""

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