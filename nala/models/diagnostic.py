from pydantic import (
    Field,
    AliasChoices,
    field_validator,
    model_validator,
)
from typing import List, Type, Union
from .baseModels import IgnoreExtra, T, DeviceList


class DiagnosticElement(IgnoreExtra):
    """
    Base class for diagnostic elements.
    """
    pass


class Beam_Position_Monitor_Diagnostic(DiagnosticElement):
    """
    BPM Diagnostic model.
    """

    type: str = Field(alias="bpm_type", default="Stripline")
    """BPM type"""


class Beam_Arrival_Monitor_Diagnostic(DiagnosticElement):
    """
    BAM Diagnostic model.
    """

    type: str = Field(alias="bam_type", default="DESY")
    """BAM type"""


class Bunch_Length_Monitor_Diagnostic(DiagnosticElement):
    """
    BLM Diagnostic model.
    """

    type: str = Field(alias="blm_type", default="CDR")
    """BLM type"""


class Camera_Pixel_Results_Indices(IgnoreExtra):
    """
    Class defining the names of analysis results for the camera pixel data
    """

    x: int = Field(default=0, alias="X_POS")
    """Beam centroid in x [pix]."""

    y: int = Field(default=1, alias="Y_POS")
    """Beam centroid in y [pix]."""

    x_sigma: int = Field(default=2, alias="X_SIGMA_POS")
    """Beam sigma in x [pix]."""

    y_sigma: int = Field(default=3, alias="Y_SIGMA_POS")
    """Beam sigma in y [pix]."""

    covariance: int = Field(default=4, alias="COV_POS")
    """Beam covariance [pix^2]."""


class Camera_Pixel_Results_Names(IgnoreExtra):
    """
    Class defining the names of the analysis results for the camera data in SI units (or mm)
    """

    x: str = Field(default="X", alias="X_NAME")
    """Beam centroid in x."""

    y: str = Field(default="Y", alias="Y_NAME")
    """Beam centroid in y."""

    x_sigma: str = Field(default="X_SIGMA", alias="X_SIGMA_NAME")
    """Beam sigma in x."""

    y_sigma: str = Field(default="Y_SIGMA", alias="Y_SIGMA_NAME")
    """Beam sigma in y."""

    covariance: str = Field(default="COV", alias="COV_NAME")
    """Beam covariance."""


class Camera_Mask(IgnoreExtra):
    """
    Class defining the camera analysis mask parameters.
    """

    middle: List[Union[float, int]] = [1280, 1080]  # X_MASK_DEF, Y_MASK_DEF
    """Center of the mask in pixels."""

    radius: List[Union[float, int]] = [1240, 1040]  # X_MASK_RAD_DEF, Y_MASK_RAD_DEF
    """Mask radius in pixels."""

    maximum: List[Union[float, int]] = [300, 300]  # X_MASK_RAD_MAX, Y_MASK_RAD_MAX
    """Maximum mask radius in pixels."""

    use_maximum_values: bool = Field(default=True, alias="USE_MASK_RAD_LIMITS")
    """Flag to indicate whether to use maximum mask radius values."""

    @classmethod
    def from_CATAP(cls: Type[T], fields: dict) -> T:
        cls._create_field(cls, fields, "middle", ["X_MASK_DEF", "Y_MASK_DEF"])
        cls._create_field(cls, fields, "radius", ["X_MASK_RAD_DEF", "Y_MASK_RAD_DEF"])
        cls._create_field(cls, fields, "maximum", ["X_MASK_RAD_MAX", "Y_MASK_RAD_MAX"])
        return super().from_CATAP(fields)


class Camera_Sensor(IgnoreExtra):
    """
    Camera Sensor model. Contains information about the number of pixels, scale factors, bit depth, etc.
    """

    x_pixels: int = Field(alias="BINARY_NUM_PIX_X", default=2160)
    """Number of pixels in x direction."""

    y_pixels: int = Field(alias="BINARY_NUM_PIX_Y", default=2560)
    """Number of pixels in y direction."""

    x_scale_factor: int = Field(alias="X_PIX_SCALE_FACTOR", default=2)
    """Scaling factor for pixels in x direction."""

    y_scale_factor: int = Field(alias="Y_PIX_SCALE_FACTOR", default=2)
    """Scaling factor for pixels in y direction."""

    beam_pixel_average: float = Field(alias="AVG_PIXEL_VALUE_FOR_BEAM", default=97.2)
    """Average pixel value for beam."""

    middle: List[Union[float, int]] = [0, 0]  # X_CENTER_DEF, Y_CENTER_DEF
    """Center definitions for the camera."""

    pixels_to_mm: List[float] = [
        0.0134,
        0.0134,
    ]  # ARRAY_DATA_X_PIX_2_MM, ARRAY_DATA_Y_PIX_2_MM
    """Pixel to millimeter conversion factors."""

    minimum: List[Union[float, int]] = [150, 150]  # MIN_X_PIXEL_POS, MIN_Y_PIXEL_POS
    """Minimum pixel positions in x and y directions."""

    maximum: List[Union[float, int]] = [2400, 2000]  # MAX_X_PIXEL_POS, MAX_Y_PIXEL_POS
    """Maximum pixel positions in x and y directions."""

    bit_depth: int = 16
    """Camera bit depth."""

    operating_middle: List[Union[float, int]] = [
        1000,
        1000,
    ]  # OPERATING_CENTER_X, OPERATING_CENTER_Y
    """Operating center positions in x and y"""

    mechanical_middle: List[Union[float, int]] = [
        1000,
        1000,
    ]  # MECHANICAL_CENTER_X, MECHANICAL_CENTER_Y
    """Mechanical center of the camera in x and y"""

    @classmethod
    def from_CATAP(cls: Type[T], fields: dict) -> T:
        cls._create_field(cls, fields, "middle", ["X_CENTER_DEF", "Y_CENTER_DEF"])
        cls._create_field(
            cls,
            fields,
            "pixels_to_mm",
            ["ARRAY_DATA_X_PIX_2_MM", "ARRAY_DATA_Y_PIX_2_MM"],
        )
        cls._create_field(
            cls, fields, "minimum", ["MIN_X_PIXEL_POS", "MIN_Y_PIXEL_POS"]
        )
        cls._create_field(
            cls, fields, "maximum", ["MAX_X_PIXEL_POS", "MAX_Y_PIXEL_POS"]
        )
        cls._create_field(
            cls,
            fields,
            "operating_middle",
            ["OPERATING_CENTER_X", "OPERATING_CENTER_Y"],
        )
        cls._create_field(
            cls,
            fields,
            "mechanical_middle",
            ["MECHANICAL_CENTER_X", "MECHANICAL_CENTER_Y"],
        )
        return super().from_CATAP(fields)


def PCO_Camera_Sensor():
    """
    A specific instantiation of `~nala.models.diagnostic.Camera_Sensor` for PCO cameras.
    """

    return Camera_Sensor(
        x_pixels=2560,
        y_pixels=2160,
        x_scale_factor=2,
        y_scale_factor=2,
        beam_pixel_average=97.2,
        pixels_to_mm=[0.013, 0.013],
        minimum=[150, 150],
        maximum=[2400, 2000],
        bit_depth=12,
        operating_middle=[1000, 1000],
        mechanical_middle=[1000, 1000],
    )


def Manta_Camera_Sensor():
    """
    A specific instantiation of `~nala.models.diagnostic.Camera_Sensor` for Manta cameras.
    """

    return Camera_Sensor(
        x_pixels=1936,
        y_pixels=1216,
        x_scale_factor=2,
        y_scale_factor=2,
        beam_pixel_average=97.2,
        pixels_to_mm=[0.0233, 0.0177],
        minimum=[136, 116],
        maximum=[1800, 1100],
        bit_depth=12,
        operating_middle=[900, 550],
        mechanical_middle=[900, 550],
    )


class Camera_Diagnostic(DiagnosticElement):
    """
    Camera Diagnostic model.
    """

    type: str = Field(alias="CAM_TYPE")
    """Camera type."""

    pixel_results_indices: Camera_Pixel_Results_Indices = Camera_Pixel_Results_Indices()
    """Pixel results indices."""

    pixel_results_names: Camera_Pixel_Results_Names = Camera_Pixel_Results_Names()
    """Pixel results names."""

    mask: Camera_Mask = Camera_Mask()
    """Camera analysis mask."""

    sensor: Camera_Sensor = Camera_Sensor()
    """Camera sensor information."""

    x_pixels: int = Field(validation_alias=AliasChoices("ARRAY_DATA_NUM_PIX_X", "epics_x_pixels"), default=1080)
    """Number of pixels from the control system in x direction."""

    y_pixels: int = Field(validation_alias=AliasChoices("ARRAY_DATA_NUM_PIX_Y", "epics_y_pixels"), default=1280)
    """Number of pixels from the control system in y direction."""

    rotation: Union[float, int] = 0
    """Camera rotation in degrees."""

    flipped_horizontally: bool = Field(alias="IMAGE_FLIP_LR", default=True)
    """Flag to indicate if the image is flipped horizontally."""

    flipped_vertically: bool = Field(alias="IMAGE_FLIP_UD", default=False)
    """Flag to indicate if the image is flipped vertically."""

    @classmethod
    def from_CATAP(cls: Type[T], fields: dict) -> T:
        cls._create_field_class(
            cls, fields, "pixel_results_indices", Camera_Pixel_Results_Indices
        )
        cls._create_field_class(
            cls, fields, "pixel_results_names", Camera_Pixel_Results_Names
        )
        cls._create_field_class(cls, fields, "mask", Camera_Mask)
        cls._create_field_class(cls, fields, "sensor", Camera_Sensor)
        return super().from_CATAP(fields)


def Camera_Diagnostic_Type(type: str = "PCO", **kwargs) -> Camera_Diagnostic:
    if type.lower() == "pco":
        return PCO_Camera_Diagnostic(type=type, **kwargs)
    if type.lower() == "manta":
        return Manta_Camera_Diagnostic(type=type, **kwargs)
    return Manta_Camera_Diagnostic(type=type, **kwargs)


def PCO_Camera_Diagnostic(**kwargs):
    return Camera_Diagnostic(sensor=PCO_Camera_Sensor(), **kwargs)


def Manta_Camera_Diagnostic(**kwargs):
    return Camera_Diagnostic(sensor=Manta_Camera_Sensor(), **kwargs)


class Screen_Diagnostic(DiagnosticElement):
    """
    Screen Diagnostic model.
    """

    type: str = Field(alias="screen_type", default="CLARA_HV_MOVER")
    """Screen type"""

    has_camera: bool = True
    """Flag to indicate if the screen has a camera attached."""

    camera_name: str = ""
    """Name of the camera attached to the screen."""

    devices: Union[str, list, DeviceList] = DeviceList()
    """Devices associated with the screen."""

    @model_validator(mode="before")
    def update_camera_name_if_not_defined(cls, data):
        if (
            "camera_name" in data and data["camera_name"] == ""
        ) or "camera_name" not in data:
            data["camera_name"] = data["name"].replace("-SCR-", "-CAM-")
        return data

    @field_validator("devices", mode="before")
    @classmethod
    def validate_devices(cls, v: Union[str, List]) -> DeviceList:
        if isinstance(v, str):
            return DeviceList(devices=list(map(str.strip, v.split(","))))
        elif isinstance(v, (list, tuple)):
            return DeviceList(devices=list(v))
        elif isinstance(v, (dict)):
            return DeviceList(**v)
        elif isinstance(v, (DeviceList)):
            return v
        else:
            raise ValueError("devices should be a string or a list of strings")


class Charge_Diagnostic(DiagnosticElement):
    """
    Charge Diagnostic model.
    """

    type: str = Field(alias="charge_type")
    """Charge diagnostic type."""
