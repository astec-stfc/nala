"""
NALA Element Module

The main class for representing accelerator elements in NALA.
"""
import os
from typing import Type, List, Union, Dict, Tuple, Any
from pydantic import field_validator, Field, BaseModel
import warnings
from .control import ControlsInformation

from .baseModels import T, Aliases, IgnoreExtra
from .manufacturer import ManufacturerElement
from .electrical import ElectricalElement
from .degauss import DegaussableElement
from .physical import PhysicalElement, Rotation
from .magnetic import (
    MagneticElement,
    Dipole_Magnet,
    Quadrupole_Magnet,
    Sextupole_Magnet,
    Octupole_Magnet,
    Solenoid_Magnet,
    NonLinearLens_Magnet,
    Wiggler_Magnet,
)
from .plasma import PlasmaElement
from .diagnostic import (
    Beam_Position_Monitor_Diagnostic,
    Beam_Arrival_Monitor_Diagnostic,
    Bunch_Length_Monitor_Diagnostic,
    Camera_Diagnostic,
    Screen_Diagnostic,
    Charge_Diagnostic,
)
from .laser import LaserElement, LaserEnergyMeterElement, LaserMirrorElement, LaserHalfWavePlateElement
from .lighting import LightingElement
from .RF import (
    PIDElement,
    Low_Level_RF_Element,
    RFModulatorElement,
    RFProtectionElement,
    RFHeartbeatElement,
    RFCavityElement,
    RFDeflectingCavityElement,
    WakefieldElement,
)
from .shutter import ShutterElement, ValveElement
from .simulation import (
    ApertureElement,
    RFCavitySimulationElement,
    WakefieldSimulationElement,
    MagnetSimulationElement,
    DriftSimulationElement,
    DiagnosticSimulationElement,
    PlasmaSimulationElement,
    SimulationElement,
    TwissMatchSimulationElement,
)
import yaml
from collections.abc import MutableMapping


def flatten(dictionary: Dict, parent_key: str="", separator: str="_") -> Dict:
    """
    Flatten a nested dictionary -- used for expanding the nested `BaseModel` structure.

    Args:
        dictionary (Dict): The dictionary to flatten.
        parent_key (str, optional): The base key to use for the flattened keys. Defaults to "".
        separator (str, optional): The separator to use between keys. Defaults to "_".

    Returns:
        Dict: The flattened dictionary.
    """
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


class string_with_quotes(str):
    pass


class flow_list(list):
    pass


def flow_list_rep(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


def quoted_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(string_with_quotes, quoted_presenter)
yaml.add_representer(flow_list, flow_list_rep)


class baseElement(IgnoreExtra):
    """
    Base-level element class. All NALA elements derive from this.

    Attributes:
        name (str): The name of the element.
        hardware_class (str): The hardware class of the element.
        hardware_type (str): The hardware type of the element.
        hardware_model (str): The hardware model of the element.
        machine_area (str): The machine area of the element.
        virtual_name (str): The virtual name of the element.
        alias (Aliases): The alias(es) of the element.
        subelement (bool | str): Whether the element is a subelement.
    """

    name: str
    """Name of the element."""

    hardware_class: str
    """Hardware class of the element."""

    hardware_type: str
    """Hardware type of the element."""

    hardware_model: str = Field(default="Generic", frozen=True)
    """Specific model of the element."""

    machine_area: str
    """Machine are of the element."""

    virtual_name: str = ""
    """Name of the element in the virtual control system."""

    alias: Union[str, list, Aliases, None] = Field(alias="name_alias", default=None)
    """The alias(es) of the element"""

    subelement: bool | str = False
    """Flag to indicate whether the element is a subelement of another 
    (i.e. whether they overlap in physical space)."""

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        assert isinstance(v, str)
        # try:
        #     PV(pv=str(v) + ":")
        # except Exception:
        #     raise ValueError("name is not a valid element name")
        return v

    @field_validator("alias", mode="before")
    @classmethod
    def validate_alias(cls, v: Union[str, List, None]) -> Aliases:
        # print(list(map(str.strip, v.split(','))))
        if isinstance(v, str):
            return Aliases(aliases=list(map(str.strip, v.split(","))))
        elif isinstance(v, (list, tuple)):
            return Aliases(aliases=list(v))
        elif isinstance(v, (dict)):
            return Aliases(aliases=v["aliases"])
        elif v is None:
            return Aliases(aliases=[])
        else:
            raise ValueError("alias should be a string or a list of strings")

    def escape_string_list(self, escapes) -> str:
        if len(list(escapes)) > 0:
            return string_with_quotes(",".join(map(str, list(escapes))))
        return string_with_quotes("")

    @classmethod
    def from_CATAP(cls: Type[T], fields: dict) -> T:
        return cls(**fields)

    # def generate_aliases(self) -> list:
    #     magnetPV = PV.fromString(str(self.name) + ":")  # ('CLA', 'S07', 'QUAD', 1)
    #     return [
    #         magnetPV.area + "-" + magnetPV.typename + str(magnetPV.index).zfill(2),
    #         magnetPV.area + "-" + magnetPV.typename + str(magnetPV._indexString),
    #         magnetPV.area + "-" + magnetPV.typename + str(magnetPV.index),
    #     ]

    @classmethod
    def _find_field_paths(
            cls: Type['main'],
            attr_name: str,
            current_model: Type[BaseModel],
            current_path: Tuple[str, ...] = ()
    ) -> List[Tuple[str, ...]]:
        """
        Recursively searches for an attribute name within the model's structure
        and returns a list of its full access paths.
        """
        paths = []
        for field_name, field_info in current_model.model_fields.items():
            new_path = current_path + (field_name,)

            # 1. Check if the current field is the target attribute
            if field_name == attr_name:
                paths.append(new_path)

            # 2. Check if the field is a nested Pydantic model (recursive step)
            field_annotation = field_info.annotation
            if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModel):
                paths.extend(cls._find_field_paths(attr_name, field_annotation, new_path))

        return paths

    def _resolve_attribute_path(self, attr_name: str) -> List[Tuple[str, ...]]:
        """
        Helper to get the full path(s) for a given attribute name.
        """
        return self._find_field_paths(attr_name, self.__class__)

    def _get_nested_attribute(self, path: Tuple[str, ...]) -> Any:
        """
        Accesses a nested attribute using its path.
        """
        # path is guaranteed to have at least two elements (parent_model, field_name)
        value = self
        for step in path:
            value = getattr(value, step)
        return value

    def _set_nested_attribute(self, path: Tuple[str, ...], value: Any):
        """
        Sets a nested attribute using its path.
        """
        # path is guaranteed to have at least two elements (parent_model, field_name)
        target_model = self

        # Traverse to the second to last element (the parent model)
        for step in path[:-1]:
            target_model = getattr(target_model, step)

        # Set the attribute on the parent model using Pydantic's setter
        # This is CRUCIAL to allow Pydantic to run validation/coercion on the value.
        setattr(target_model, path[-1], value)

    # --- Overridden Methods ---

    def __getattr__(self, name: str) -> Any:
        """
        Custom getter: Looks for the attribute in nested models.
        """
        paths = self._resolve_attribute_path(name)

        if not paths:
            # If not found anywhere, raise the standard AttributeError
            raise AttributeError(f"'{self.__class__.__name__}' object and its nested models have no attribute '{name}'")

        elif len(paths) > 1:
            # Multiple locations found: Print warning and list paths
            path_strings = [f"'{'.'.join(p)}'" for p in paths]
            warning_msg = (
                f"**Ambiguity Warning for '{name}'**: "
                f"Multiple instances found at: {', '.join(path_strings)}. "
                f"Use the full path (e.g., `main.physical.length`) to access a specific one."
            )
            warnings.warn(warning_msg, UserWarning)
            # Standard practice is to return the first found value in ambiguous cases
            # or raise an error. We'll raise the standard error here to force
            # the user to be explicit when ambiguity exists.
            raise AttributeError(
                f"Attribute '{name}' is ambiguous. Found at: {', '.join(path_strings)}. "
                "Access explicitly (e.g., `main.physical.length`)."
            )
        else:
            # Exactly one location found: Return the nested value
            return self._get_nested_attribute(paths[0])

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Custom setter: Looks for the attribute in nested models and sets the value.
        """
        # First, allow Pydantic's internal __setattr__ to handle
        # attributes that belong directly to the 'main' model instance (e.g., private vars, dunder methods)
        # and its direct Pydantic fields ('physical', 'size').
        if name in self.__dict__ or name in self.model_fields:
            super().__setattr__(name, value)
            return

        # Find the path(s) for the nested attribute
        paths = self._resolve_attribute_path(name)

        if not paths:
            # Not found anywhere nested: Treat as a normal attribute assignment on the main model
            # This is how Pydantic handles setting a non-field attribute.
            super().__setattr__(name, value)
            return

        elif len(paths) > 1:
            # Multiple locations found: Print warning and raise error
            path_strings = [f"'{'.'.join(p)}'" for p in paths]
            warning_msg = (
                f"**Ambiguity Warning for '{name}'**: "
                f"Multiple instances found at: {', '.join(path_strings)}. "
                f"Cannot set a value. Use the full path (e.g., `main.physical.length = 10.0`) to set a specific one."
            )
            warnings.warn(warning_msg, UserWarning)
            raise AttributeError(
                f"Cannot set ambiguous attribute '{name}'. Found at: {', '.join(path_strings)}. "
                "Set explicitly (e.g., `main.physical.length = 10.0`)."
            )
        else:
            # Exactly one location found: Set the nested value
            try:
                self._set_nested_attribute(paths[0], value)
            except Exception as e:
                # Catch any potential Pydantic validation errors during setting
                raise ValueError(
                    f"Failed to set '{name}' at path '{'.'.join(paths[0])}' with value '{value}'. Error: {e}")

    def to_CATAP(self) -> dict:
        return {
            "machine_area": self.machine_area,
            "hardware_type": self.hardware_type,
            "name": self.name,
            # 'virtual_name': self.virtual_name,
            "name_alias": (
                self.alias.aliases if isinstance(self.alias, Aliases) else self.alias
            ),
        }

    @property
    def no_controls(self) -> str:
        return (
            self.__class__.__name__
            + "("
            + " ".join(
                [
                    k + "=" + getattr(self, k).__repr__()
                    for k in self.model_fields.keys()
                    if k != "controls"
                ]
            )
            + ")"
        )

    @property
    def subdirectory(self) -> str:
        if self.__class__.__name__ == self.hardware_type:
            return os.path.join(self.hardware_class, self.hardware_type)
        return os.path.join(
            self.hardware_class, self.__class__.__name__, self.hardware_type
        )

    @property
    def YAML_filename(self) -> str:
        return os.path.join(self.subdirectory, self.name + ".yaml")

    @property
    def hardware_info(self) -> dict:
        return {"class": self.hardware_class, "type": self.hardware_type}

    def flat(self):
        return flatten(self.model_dump(), parent_key="", separator="_")

    def is_subelement(self) -> bool:
        if str(self.subelement).lower() == "false":
            return False
        elif str(self.subelement).lower() == "true":
            return True
        if isinstance(self.subelement, bool):
            return self.subelement
        else:
            return isinstance(self.subelement, str)


class PhysicalBaseElement(baseElement):
    """
    Element with a physical attribute; see :class:`~nala.models.physical.PhysicalElement`.

    Attributes:
        physical: PhysicalElement: The physical attributes of the element.
    """

    physical: PhysicalElement = Field(default_factory=PhysicalElement)
    """Physical attributes of the element."""

    def to_CATAP(self):
        catap_dict = super().to_CATAP()
        catap_dict.update(
            {
                "position": list(self.physical.middle)[2],
            }
        )
        return catap_dict

    @property
    def bend_angle(self) -> Rotation:
        """
        Bending angle of the element.
        """
        return Rotation.from_list([0, 0, 0])

    @property
    def start_angle(self) -> float:
        """
        Initial global rotation angle of the element.
        """
        return self.physical.rotation + self.physical.global_rotation

    @property
    def end_angle(self) -> float:
        """
        Final global rotation angle of the element
        """
        return self.start_angle


class Element(PhysicalBaseElement):
    """
    Standard class for representing elements.

    Attributes:
        electrical: :class:`~nala.models.electrical.ElectricalElement`: The electrical attributes of the element.
        manufacturer: :class:`~nala.models.manufacturer.Manufacturer`: The manufacturer attributes of the element.
        simulation: :class:`~nala.models.simulation.SimulationElement`: The simulation attributes of the element.
        controls: :class:`~nala.models.control.ControlsInformation` | None: The control system attributes of the element.
    """

    electrical: ElectricalElement = Field(default_factory=ElectricalElement)
    """Electrical attributes of the element."""

    manufacturer: ManufacturerElement = Field(default_factory=ManufacturerElement)
    """Manufacturer attributes of the element."""

    simulation: SimulationElement = Field(default_factory=SimulationElement)
    """Simulation attributes of the element."""

    controls: ControlsInformation | None = None
    """Control system attributes of the element."""

    def to_CATAP(self):
        catap_dict = super().to_CATAP()
        catap_dict.update(
            {
                "manufacturer": self.manufacturer.manufacturer,
                "serial_number": self.manufacturer.serial_number,
            }
        )
        return catap_dict


class Magnet(Element):
    """
    Base class for representing magnets.

    Attributes:
        degauss: :class:`~nala.models.degauss.DegaussableElement`: The degaussing attributes of the magnet.
        simulation: :class:`~nala.models.simulation.MagnetSimulationElement`: The simulation attributes of the magnet.
        magnetic: :class:`~nala.models.magnetic.MagneticElement` | None: The magnetic attributes of the magnet.
    """

    hardware_class: str = Field(default="Magnet", frozen=True)
    """Magnet hardware class."""

    degauss: DegaussableElement = Field(default_factory=DegaussableElement)
    """Degaussing attributes of the magnet."""

    simulation: MagnetSimulationElement = Field(default_factory=MagnetSimulationElement)
    """Simulation attributes of the magnet."""

    magnetic: MagneticElement | None = None
    """Magnetic attributes of the magnet."""

    @property
    def bend_angle(self) -> Rotation:
        """
        Rotation of the magnet based on its bending angle.
        """
        return Rotation.from_list([0, 0, self.magnetic.angle])

    @property
    def end_angle(self) -> float:
        """End angle of the magnet"""
        return self.start_angle + self.bend_angle.theta

    # @field_validator('type', mode='before')
    # @classmethod
    # def validate_type(cls, v: str) -> str:
    #     # print(list(map(str.strip, v.split(','))))
    #     if isinstance(v, str):
    #         return v.upper()
    #     else:
    #         raise ValueError('alias should be a string or a list of strings')

    def to_CATAP(self):
        catap_dict = super().to_CATAP()
        catap_dict.update(
            {
                "mag_type": self.hardware_type,
                "degauss_tolerance": self.degauss.tolerance,
                "degauss_values": self.escape_string_list(self.degauss.values),
                "num_degauss_steps": self.degauss.steps,
                "field_integral_coefficients": self.escape_string_list(
                    self.magnetic.field_integral_coefficients
                ),
                "linear_saturation_coefficients": self.escape_string_list(
                    self.magnetic.linear_saturation_coefficients
                ),
                "mag_set_max_wait_time": self.magnetic.settle_time,
                "magnetic_length": 1000 * self.magnetic.length,
                "ri_tolerance": self.electrical.read_tolerance,
                "min_i": self.electrical.minI,
                "max_i": self.electrical.maxI,
            }
        )
        return catap_dict

    # @property
    # def subdirectory(self):
    #     return os.path.join(self.hardware_type,self.type)


class Dipole(Magnet):
    """
    Dipole element.
    """

    hardware_type: str = Field(default="Dipole", frozen=True)
    magnetic: Dipole_Magnet = Field(default_factory=Dipole_Magnet)


class Quadrupole(Magnet):
    """Quadrupole element."""

    hardware_type: str = Field(default="Quadrupole", frozen=True)
    magnetic: Quadrupole_Magnet = Field(default_factory=Quadrupole_Magnet)


class Sextupole(Magnet):
    """Sextupole element."""

    hardware_type: str = Field(default="Sextupole", frozen=True)
    magnetic: Sextupole_Magnet = Field(default_factory=Sextupole_Magnet)

class Octupole(Magnet):
    """Octupole element."""

    hardware_type: str = Field(default="Octupole", frozen=True)
    magnetic: Octupole_Magnet = Field(default_factory=Octupole_Magnet)

class Horizontal_Corrector(Dipole):
    """Horizontal Corrector element."""

    hardware_type: str = Field(default="Horizontal_Corrector", frozen=True)


class Vertical_Corrector(Dipole):
    """Vertical Corrector element."""

    hardware_type: str = Field(default="Vertical_Corrector", frozen=True)


class Combined_Corrector(Dipole):
    """H&V Corrector element."""

    hardware_type: str = Field(default="Combined_Corrector", frozen=True)
    Horizontal_Corrector: str | None = Field(default=None, frozen=True)
    Vertical_Corrector: str | None = Field(default=None, frozen=True)


class Solenoid(Magnet):
    """Solenoid element."""
    hardware_type: str = Field(default="Solenoid", frozen=True)
    magnetic: Solenoid_Magnet = Field(default_factory=Solenoid_Magnet)


class NonLinearLens(Magnet):
    """Non-linear lens element."""
    hardware_type: str = Field(default="NonLinearLens", frozen=True)
    magnetic: NonLinearLens_Magnet = Field(default_factory=NonLinearLens_Magnet)


class Wiggler(Magnet):
    """Undulator element."""
    hardware_type: str = Field(default="Undulator", frozen=True)
    magnetic: Wiggler_Magnet = Field(default_factory=Wiggler_Magnet)
    laser: LaserElement | None = None


class TwissMatch(Magnet):
    """Dipole element."""

    hardware_type: str = Field(default="TwissMatch", frozen=True)
    hardware_class: str = Field(default="TwissMatch", frozen=True)
    simulation: TwissMatchSimulationElement = Field(default_factory=TwissMatchSimulationElement)


class Diagnostic(Element):
    """
    Base class for representing diagnostics.

    Attributes:
        simulation: :class:`~nala.models.simulation.DiagnosticSimulationElement`: The simulation
        attributes of the diagnostic (including its `output_filename`).
    """
    hardware_type: str = Field(default="Diagnostic", frozen=True)
    hardware_class: str = Field(default="Diagnostic", frozen=True)
    simulation: DiagnosticSimulationElement = Field(default_factory=DiagnosticSimulationElement)


class Beam_Position_Monitor(Diagnostic):
    """BPM element."""

    hardware_type: str = Field(default="Beam_Position_Monitor", frozen=True, alias="BPM")
    hardware_model: str = Field(default="Stripline", frozen=True)
    diagnostic: Beam_Position_Monitor_Diagnostic = Field(default_factory=Beam_Position_Monitor_Diagnostic)


class Beam_Arrival_Monitor(Diagnostic):
    """Beam arrival monitor element."""

    hardware_type: str = Field(default="Beam_Arrival_Monitor", frozen=True, alias="BAM")
    hardware_model: str = Field(default="DESY", frozen=True)
    diagnostic: Beam_Arrival_Monitor_Diagnostic = Field(default_factory=Beam_Arrival_Monitor_Diagnostic)


class Bunch_Length_Monitor(Diagnostic):
    """Beam loss monitor element."""

    hardware_type: str = Field(default="Bunch_Length_Monitor", frozen=True, alias="BLM")
    hardware_model: str = Field(default="CDR", frozen=True)
    diagnostic: Bunch_Length_Monitor_Diagnostic = Field(default_factory=Bunch_Length_Monitor_Diagnostic)


class Camera(Diagnostic):
    """Camera element."""

    hardware_type: str = Field(default="Camera", frozen=True)
    hardware_model: str = Field(default="PCO", frozen=True)
    diagnostic: Camera_Diagnostic = Field(default_factory=Camera_Diagnostic)


class Screen(Diagnostic):
    """Screen element."""

    hardware_type: str = Field(default="Screen", frozen=True)
    hardware_model: str = Field(default="YAG", frozen=True)
    diagnostic: Screen_Diagnostic = Field(default_factory=Screen_Diagnostic)

    def to_CATAP(self):
        catap_dict = super().to_CATAP()
        catap_dict.update(
            {
                "screen_type": self.diagnostic.type,
                "has_camera": self.diagnostic.has_camera,
                "camera_name": self.diagnostic.camera_name,
                "devices": self.escape_string_list(self.diagnostic.devices),
            }
        )
        return catap_dict


class ChargeDiagnostic(Diagnostic):
    """Charge Diagnostic element."""

    hardware_type: str = Field(default="ChargeDiagnostic", frozen=True)
    diagnostic: Charge_Diagnostic = Field(default_factory=Charge_Diagnostic)


class Wall_Current_Monitor(ChargeDiagnostic):
    """WCM Charge Diagnostic element."""

    hardware_type: str = Field(default="Wall_Current_Monitor", frozen=True, alias="WCM")


class Faraday_Cup_Monitor(ChargeDiagnostic):
    """FCM Charge Diagnostic element."""

    hardware_type: str = Field(default="Faraday_Cup_Monitor", frozen=True, alias="FCM")


class Integrated_Current_Transformer(ChargeDiagnostic):
    """ICT Charge Diagnostic element."""

    hardware_type: str = Field(default="Integrated_Current_Transformer", frozen=True, alias="ICT")


class VacuumGauge(Element):
    """Vacuum Gauge element."""

    hardware_type: str = Field(default="VacuumGauge", frozen=True)
    hardware_model: str = Field(default="IMG", frozen=True)
    manufacturer: ManufacturerElement = Field(default_factory=ManufacturerElement)


class Laser(Element):
    """Laser Energy Meter element."""

    hardware_type: str = Field(default="Laser", frozen=True)
    hardware_model: str = Field(default="Laser", frozen=True)
    manufacturer: ManufacturerElement = Field(default_factory=ManufacturerElement)
    laser: LaserElement = Field(default_factory=LaserElement)


class LaserEnergyMeter(Element):
    """Laser Energy Meter element."""

    hardware_type: str = Field(default="LaserEnergyMeter", frozen=True)
    hardware_model: str = Field(default="Gentec Photodiode", frozen=True)
    laser: LaserEnergyMeterElement = Field(default_factory=LaserEnergyMeterElement)


class LaserHalfWavePlate(Element):
    """Laser Half Wave Plate element."""

    hardware_type: str = Field(default="LaserHalfWavePlate", frozen=True)
    hardware_model: str = Field(default="Newport", frozen=True)
    laser: LaserHalfWavePlateElement = Field(default_factory=LaserHalfWavePlateElement)


class LaserMirror(Element):
    """Laser Mirror element."""

    hardware_type: str = Field(default="LaserMirror", frozen=True)
    hardware_model: str = Field(default="Planar", frozen=True)
    laser: LaserMirrorElement = Field(default_factory=LaserMirrorElement)


class Plasma(Element):
    """Plasma element."""

    hardware_type: str = Field(default="Plasma", frozen=True)
    hardware_model: str = Field(default="Plasma", frozen=True)
    simulation: PlasmaSimulationElement = Field(default_factory=PlasmaSimulationElement)
    plasma: PlasmaElement = Field(default_factory=PlasmaElement)
    laser: LaserElement | None = None


class Lighting(baseElement):
    """Lighting element."""

    hardware_type: str = Field(default="Lighting", frozen=True)
    hardware_model: str = Field(default="LED", frozen=True)
    lights: LightingElement = Field(default_factory=LightingElement)


class PID(baseElement):
    """PID element."""

    hardware_type: str = Field(default="PID", frozen=True)
    hardware_model: str = Field(default="RF", frozen=True)
    PID: PIDElement = Field(default_factory=PIDElement)


class Low_Level_RF(baseElement):
    """LLRF element."""

    hardware_type: str = Field(default="Low_Level_RF", frozen=True)
    hardware_model: str = Field(default="Libera", frozen=True)
    LLRF: Low_Level_RF_Element = Field(default_factory=Low_Level_RF_Element)


class RFCavity(Element):
    """
    RFCavity element.

    Attributes:
        cavity: :class:`~nala.models.RF.RFCavityElement`: The RF cavity attributes of the element.
        simulation: :class:`~nala.models.simulation.RFCavitySimulationElement`: The simulation
        attributes of the RF cavity.
    """

    hardware_type: str = Field(default="RFCavity", frozen=True)
    hardware_model: str = Field(default="SBand", frozen=True)
    cavity: RFCavityElement = Field(default_factory=RFCavityElement)
    simulation: RFCavitySimulationElement = Field(default_factory=RFCavitySimulationElement)


class Wakefield(PhysicalBaseElement):
    """
    Wakefield element.

    Attributes:
        cavity: :class:`~nala.models.RF.WakefieldElement`: The wakefield cavity attributes of the element.
        simulation: :class:`~nala.models.simulation.WakefieldSimulationElement`: The simulation
        attributes of the wakefield cavity.
    """

    hardware_type: str = Field(default="Wakefield", frozen=True)
    hardware_model: str = Field(default="Dielectric", frozen=True)
    cavity: WakefieldElement = Field(default_factory=WakefieldElement)
    simulation: WakefieldSimulationElement = Field(default_factory=WakefieldSimulationElement)


class RFDeflectingCavity(RFCavity):
    """RFCavity element."""

    hardware_type: str = Field(default="RFDeflectingCavity", frozen=True)
    hardware_model: str = Field(default="SBand", frozen=True)
    cavity: RFDeflectingCavityElement = Field(default_factory=RFDeflectingCavityElement)


class RFModulator(baseElement):
    """RFModulator element."""

    hardware_type: str = Field(default="RFModulator", frozen=True)
    hardware_model: str = Field(default="Thales", frozen=True)
    modulator: RFModulatorElement = Field(default_factory=RFModulatorElement)


class RFProtection(baseElement):
    """RFProtection element."""

    hardware_type: str = Field(default="RFProtection", frozen=True)
    hardware_model: str = Field(default="PROT", frozen=True)
    modulator: RFProtectionElement = Field(default_factory=RFProtectionElement)


class RFHeartbeat(baseElement):
    """RFHeartbeat element."""

    hardware_type: str = Field(default="RFHeartbeat", frozen=True)
    heartbeat: RFHeartbeatElement = Field(default_factory=RFHeartbeatElement)


class Shutter(Element):
    """Shutter element."""

    hardware_type: str = Field(default="Shutter", frozen=True)
    shutter: ShutterElement = Field(default_factory=ShutterElement)


class Valve(Element):
    """Valve element."""

    hardware_type: str = Field(default="Valve", frozen=True)
    valve: ValveElement = Field(default_factory=ValveElement)


class Marker(PhysicalBaseElement):
    """Marker element."""

    hardware_type: str = Field(default="Marker", frozen=True)
    hardware_model: str = Field(default="Simulation", frozen=True)
    simulation: DiagnosticSimulationElement = Field(default_factory=DiagnosticSimulationElement)


class Aperture(PhysicalBaseElement):
    """Aperture element."""

    hardware_type: str = Field(default="Aperture", frozen=True)
    hardware_model: str = Field(default="Simulation", frozen=True)
    aperture: ApertureElement = Field(default_factory=ApertureElement)


class Collimator(Aperture):
    """Collimator element."""

    hardware_type: str = Field(default="Collimator", frozen=True)
    hardware_model: str = Field(default="Simulation", frozen=True)


class Drift(PhysicalBaseElement):
    hardware_type: str = Field(default="Drift", frozen=True)
    simulation: DriftSimulationElement = Field(default_factory=DriftSimulationElement)
