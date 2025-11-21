"""
NALA Element Module

The main class for representing accelerator elements in NALA.
"""
import os
from typing import Type, List, Union, Dict, Tuple, Any, get_args, get_origin
from pydantic import field_validator, Field, BaseModel
import types
from .control import ControlsInformation

from .baseModels import T, Aliases, IgnoreExtra
from .manufacturer import ManufacturerElement
from .electrical import ElectricalElement
from .degauss import DegaussableElement
from .physical import PhysicalElement, Rotation
from .reference import ReferenceElement
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
        if isinstance(key, str):
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

    # Define cascading rules: (source_path, target_path)
    CASCADING_RULES: Dict = {}

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

    def _resolve_attribute_path(self, attr_name: str) -> List[Tuple[str, ...]]:
        """
        Helper to get the full path(s) for a given attribute name.
        """
        return self._find_field_paths(attr_name, self.__class__)

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
            origin = get_origin(field_annotation)

            # Unwrap Union/Optional types to get the actual class
            is_union = origin is Union or isinstance(field_annotation, types.UnionType)
            if is_union:
                args = get_args(field_annotation)
                for arg in args:
                    if arg is not type(None):
                        try:
                            if isinstance(arg, type) and issubclass(arg, BaseModel):
                                paths.extend(cls._find_field_paths(attr_name, arg, new_path))
                        except TypeError:
                            # arg might not be a class, skip it
                            pass
            else:
                try:
                    if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModel):
                        paths.extend(cls._find_field_paths(attr_name, field_annotation, new_path))
                except TypeError:
                    pass

        for name, attr in vars(current_model).items():
            if isinstance(attr, property) and name == attr_name:
                paths.append(current_path + (name,))

        return paths

    def _get_nested_attribute(self, path: Tuple[str, ...]) -> Any:
        """
        Accesses a nested attribute using its path.
        """
        value = self
        for step in path:
            if value is None:
                raise AttributeError(f"Cannot access '{step}' on None value at path '{'.'.join(path)}'")
            value = getattr(value, step)
        return value

    def _set_nested_attribute(self, path: Tuple[str, ...], value: Any):
        """
        Sets a nested attribute using its path.
        """
        target_model = self

        # Traverse to the second to last element
        for step in path[:-1]:
            target_model = getattr(target_model, step)
            if target_model is None:
                raise AttributeError(f"Cannot set attribute at path '{'.'.join(path)}': intermediate value is None")

        # Set the attribute
        setattr(target_model, path[-1], value)

    def __getattr__(self, name: str) -> Any:
        """
        Custom getter: Looks for the attribute in nested models.
        """
        # Avoid recursion on special attributes
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        paths = self._resolve_attribute_path(name)

        if not paths:
            raise AttributeError(f"'{self.__class__.__name__}' object and its nested models have no attribute '{name}'")

        if len(paths) > 1:
            path_strings = [f"'{'.'.join(p)}'" for p in paths]
            raise AttributeError(
                f"Attribute '{name}' is ambiguous. Found at: {', '.join(path_strings)}. "
                "Access explicitly (e.g., `element.simulation.field_amplitude`)."
            )

        return self._get_nested_attribute(paths[0])

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Custom setter with cascading updates for related attributes.
        """
        cls = self.__class__

        # Allow Pydantic to handle direct fields and internal attributes
        if name in cls.model_fields or name.startswith('_'):
            super().__setattr__(name, value)
            return

        # Try nested lookup
        try:
            paths = self._resolve_attribute_path(name)
        except Exception:
            super().__setattr__(name, value)
            return

        if not paths:
            super().__setattr__(name, value)
            return

        if len(paths) > 1:
            path_strings = [f"'{'.'.join(p)}'" for p in paths]
            raise AttributeError(
                f"Cannot set ambiguous attribute '{name}'. Found at: {', '.join(path_strings)}. "
                "Set explicitly."
            )

        # Set the nested attribute
        self._set_nested_attribute(paths[0], value)

        # Handle cascading updates
        self._handle_cascading_updates(paths[0], value)

    def _handle_cascading_updates(self, path: Tuple[str, ...], value: Any) -> None:
        """
        Handle cascading attribute updates across nested models.
        """

        for source_path, target_path in self.CASCADING_RULES.items():
            if path == source_path:
                self._set_nested_attribute(target_path, value)

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
        cls = self.__class__
        return (
            self.__class__.__name__
            + "("
            + " ".join(
                [
                    k + "=" + getattr(self, k).__repr__()
                    for k in cls.model_fields.keys()
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
    def hardware_info(self) -> Dict[str, str]:
        """
        Retrieve the `hardware_class` and `hardware_type` of the object as a dict

        Returns
        -------
            Dict[str, str]: {"class": `hardware_class`, "type": `hardware_type`}
        """
        return {"class": self.hardware_class, "type": self.hardware_type}

    def flat(self) -> Dict[str, Any]:
        """
        Dump the entire element model as a flat dictionary, with sub-models separated by "_".

        For example, if an element has `element.electrical.maxI` this will be keyed in the dictionary as
        `eletrical_maxI: value`

        Returns
        -------
            Dict[str, Any]: Flattened dictionary representing the element.
        """
        return flatten(self.model_dump(), parent_key="", separator="_")

    def is_subelement(self) -> bool:
        """
        Flag to indicate whether the element is a subelement of another, such as a solenoid surrounding
        an RF cavity or a BPM embedded inside a magnet. This precludes it from being included when calculating
        the full length of a beamline.

        Returns
        -------
            bool: True if the element is a subelement.
        """
        if str(self.subelement).lower() == "false":
            return False
        elif str(self.subelement).lower() == "true":
            return True
        if isinstance(self.subelement, bool):
            return self.subelement
        else:
            return isinstance(self.subelement, str)


class Element(baseElement):
    """
    Standard class for representing elements.

    Attributes:
        simulation: :class:`~nala.models.simulation.SimulationElement`: The simulation attributes of the element.
        electrical: :class:`~nala.models.electrical.ElectricalElement`: The electrical attributes of the element.
        manufacturer: :class:`~nala.models.manufacturer.Manufacturer`: The manufacturer attributes of the element.
        controls: :class:`~nala.models.control.ControlsInformation` | None: The control system attributes of the element.
        reference: :class:`~nala.models.reference.ReferenceElement` | None: Reference information for the element.
    """

    simulation: SimulationElement = Field(default_factory=SimulationElement)
    """Simulation attributes of the element."""

    electrical: ElectricalElement | None = Field(default_factory=ElectricalElement)
    """Electrical attributes of the element."""

    manufacturer: ManufacturerElement | None = Field(default_factory=ManufacturerElement)
    """Manufacturer attributes of the element."""

    controls: ControlsInformation | None = None
    """Control system attributes of the element."""

    reference: ReferenceElement | None = None
    """Additional reference information for the element."""

    def to_CATAP(self):
        catap_dict = super().to_CATAP()
        catap_dict.update(
            {
                "manufacturer": self.manufacturer.manufacturer,
                "serial_number": self.manufacturer.serial_number,
            }
        )
        return catap_dict

class PhysicalBaseElement(Element):
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
        #TODO this probably doesn't do what it should.

        Returns
        -------
            :class:`~nala.models.physical.Rotation`: The rotation attribute of the element.
        """
        return Rotation.from_list([0, 0, 0])

    @property
    def start_angle(self) -> Rotation:
        """
        Initial global rotation angle of the element.
        #TODO this probably doesn't do what it should.
        """
        return self.physical.rotation + self.physical.global_rotation

    @property
    def end_angle(self) -> Rotation:
        """
        Final global rotation angle of the element
        #TODO this probably doesn't do what it should.
        """
        return self.start_angle



class Magnet(PhysicalBaseElement):
    """
    Base class for representing magnets.

    Attributes:
        degauss: :class:`~nala.models.degauss.DegaussableElement`: The degaussing attributes of the magnet.
        simulation: :class:`~nala.models.simulation.MagnetSimulationElement`: The simulation attributes of the magnet.
        magnetic: :class:`~nala.models.magnetic.MagneticElement` | None: The magnetic attributes of the magnet.
    """

    hardware_class: str = Field(default="Magnet", frozen=True)
    """Magnet hardware class."""

    degauss: DegaussableElement | None = Field(default_factory=DegaussableElement)
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

    Attributes:
        hardware_type (str): The hardware type of the dipole.
        magnetic (:class:`~nala.models.magnetic.Dipole_Magnet`): The magnetic attributes of the dipole.
    """

    hardware_type: str = Field(default="Dipole", frozen=True)
    """Dipole hardware type."""

    magnetic: Dipole_Magnet = Field(default_factory=Dipole_Magnet)


class Quadrupole(Magnet):
    """
    Quadrupole element.

    Attributes:
        hardware_type (str): The hardware type of the quadrupole.
        magnetic (:class:`~nala.models.magnetic.Quadrupole_Magnet`): The magnetic attributes of the quadrupole.
    """

    hardware_type: str = Field(default="Quadrupole", frozen=True)
    """Quadrupole hardware type."""

    magnetic: Quadrupole_Magnet = Field(default_factory=Quadrupole_Magnet)
    """Magnetic attributes of the quadrupole."""



class Sextupole(Magnet):
    """
    Sextupole element.

    Attributes:
        hardware_type (str): The hardware type of the sextupole.
        magnetic (:class:`~nala.models.magnetic.Sextupole_Magnet`): The magnetic attributes of the sextupole.
    """

    hardware_type: str = Field(default="Sextupole", frozen=True)
    """Sextupole hardware type."""

    magnetic: Sextupole_Magnet = Field(default_factory=Sextupole_Magnet)
    """Magnetic attributes of the sextupole."""


class Octupole(Magnet):
    """
    Octupole element.

    Attributes:
        hardware_type (str): The hardware type of the octupole.
        magnetic (:class:`~nala.models.magnetic.Octupole_Magnet`): The magnetic attributes of the octupole.
    """

    hardware_type: str = Field(default="Octupole", frozen=True)
    """Octupole hardware type."""

    magnetic: Octupole_Magnet = Field(default_factory=Octupole_Magnet)
    """Magnetic attributes of the octupole."""


class Horizontal_Corrector(Dipole):
    """
    Horizontal corrector element.

    Attributes:
        hardware_type (str): The hardware type of the corrector.
    """

    hardware_type: str = Field(default="Horizontal_Corrector", frozen=True)
    """Horizontal corrector hardware type."""


class Vertical_Corrector(Dipole):
    """
    Vertical corrector element.

    Attributes:
        hardware_type (str): The hardware type of the corrector.
    """

    hardware_type: str = Field(default="Vertical_Corrector", frozen=True)
    """Vertical corrector hardware type."""


class Combined_Corrector(Dipole):
    """
    Horizontal corrector element.

    Attributes:
        hardware_type (str): The hardware type of the corrector.
        Horizontal_Corrector (str): The horizontal corrector.
        Vertical_Corrector (str): The vertical corrector.
    """

    hardware_type: str = Field(default="Combined_Corrector", frozen=True)
    """Combined corrector hardware type."""

    Horizontal_Corrector: str | None = Field(default=None, frozen=True)
    """Name of horizontal corrector."""

    Vertical_Corrector: str | None = Field(default=None, frozen=True)
    """Name of vertical corrector."""


class Solenoid(Magnet):
    """
    Solenoid element.

    Attributes:
        hardware_type (str): The hardware type of the solenoid.
        magnetic (:class:`~nala.models.magnetic.Solenoid_Magnet`): The magnetic attributes of the solenoid.
    """

    hardware_type: str = Field(default="Solenoid", frozen=True)
    """Solenoid hardware type."""

    magnetic: Solenoid_Magnet = Field(default_factory=Solenoid_Magnet)
    """Magnetic attributes of the solenoid."""


class NonLinearLens(Magnet):
    """
    Non-linear lens element.

    Attributes:
        hardware_type (str): The hardware type of the NLL.
        magnetic (:class:`~nala.models.magnetic.NonLinearLens_Magnet`): The magnetic attributes of the NLL.
    """

    hardware_type: str = Field(default="NonLinearLens", frozen=True)
    """Non-linear lens hardware type."""

    magnetic: NonLinearLens_Magnet = Field(default_factory=NonLinearLens_Magnet)
    """Magnetic attributes of the non-linear-lens."""


class Wiggler(Magnet):
    """
    Wiggler element.

    Attributes:
        hardware_type (str): The hardware type of the wiggler.
        magnetic (:class:`~nala.models.magnetic.Wiggler_Magnet`): The magnetic attributes of the wiggler.
        laser (:class:`~nala.models.laser.Laser_Magnet` or None): The laser associated with the wiggler.
    """

    hardware_type: str = Field(default="Undulator", frozen=True)
    """Wiggler hardware type."""

    magnetic: Wiggler_Magnet = Field(default_factory=Wiggler_Magnet)
    """Magnetic attributes of the wiggler."""

    laser: LaserElement | None = None
    """Laser attached to the wiggler."""


class TwissMatch(PhysicalBaseElement):
    """
    Twiss matching element. Used for changing the Twiss parameters of the beam.

    Attributes:
        hardware_type (str): The hardware type of the element.
        hardware_class (str): The hardware class of the element.
        simulation (:class:`~nala.models.simulation.TwissMatchSimulationElement`):
        The simulation attributes of the matching element.
    """

    hardware_type: str = Field(default="TwissMatch", frozen=True)
    """Twiss match hardware type."""

    hardware_class: str = Field(default="TwissMatch", frozen=True)
    """Twiss match hardware class."""

    simulation: TwissMatchSimulationElement = Field(default_factory=TwissMatchSimulationElement)
    """Simulation attributes of the matching element."""


class Diagnostic(PhysicalBaseElement):
    """
    Base class for representing diagnostics.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_class (str): The hardware class of the diagnostic.
        simulation: (:class:`~nala.models.simulation.DiagnosticSimulationElement`): The simulation
        attributes of the diagnostic (including its `output_filename`).
    """

    hardware_type: str = Field(default="Diagnostic", frozen=True)
    """Diagnostic hardware type."""

    hardware_class: str = Field(default="Diagnostic", frozen=True)
    """Diagnostic hardware class."""

    simulation: DiagnosticSimulationElement = Field(default_factory=DiagnosticSimulationElement)
    """Simulation attributes of the diagnostic."""


class Beam_Position_Monitor(Diagnostic):
    """
    BPM element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_model (str): The specific hardware model of the diagnostic (i.e. Stripline, Cavity).
        diagnostic: (:class:`~nala.models.diagnostic.Beam_Position_Monitor_Diagnostic`): The diagnostic
        attributes of the BPM.
    """

    hardware_type: str = Field(default="Beam_Position_Monitor", frozen=True, alias="BPM")
    """BPM hardware type."""

    hardware_model: str = Field(default="Stripline", frozen=True)
    """BPM hardware model."""

    diagnostic: Beam_Position_Monitor_Diagnostic = Field(default_factory=Beam_Position_Monitor_Diagnostic)
    """Diagnostic attributes of the BPM."""


class Beam_Arrival_Monitor(Diagnostic):
    """
    BAM element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_model (str): The specific hardware model of the diagnostic.
        diagnostic: (:class:`~nala.models.diagnostic.Beam_Arrival_Monitor_Diagnostic`): The diagnostic
        attributes of the BAM.
    """

    hardware_type: str = Field(default="Beam_Arrival_Monitor", frozen=True, alias="BAM")
    """BAM hardware type."""

    hardware_model: str = Field(default="DESY", frozen=True)
    """BAM hardware model."""

    diagnostic: Beam_Arrival_Monitor_Diagnostic = Field(default_factory=Beam_Arrival_Monitor_Diagnostic)
    """Diagnostic attributes of the BAM."""


class Bunch_Length_Monitor(Diagnostic):
    """
    BLM element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_model (str): The specific hardware model of the diagnostic.
        diagnostic: (:class:`~nala.models.diagnostic.Bunch_Length_Monitor_Diagnostic`): The diagnostic
        attributes of the BLM.
    """

    hardware_type: str = Field(default="Bunch_Length_Monitor", frozen=True, alias="BLM")
    """BLM hardware type."""

    hardware_model: str = Field(default="CDR", frozen=True)
    """BLM hardware model."""

    diagnostic: Bunch_Length_Monitor_Diagnostic = Field(default_factory=Bunch_Length_Monitor_Diagnostic)
    """Diagnostic attributes of the BLM."""


class Camera(Diagnostic):
    """
    Camera element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_model (str): The specific hardware model of the diagnostic.
        diagnostic: (:class:`~nala.models.diagnostic.Camera_Diagnostic`): The diagnostic
        attributes of the Camera.
    """

    hardware_type: str = Field(default="Camera", frozen=True)
    """Camera hardware type."""

    hardware_model: str = Field(default="PCO", frozen=True)
    """Camera hardware model."""

    diagnostic: Camera_Diagnostic = Field(default_factory=Camera_Diagnostic)
    """Diagnostic attributes of the camera."""


class Screen(Diagnostic):
    """
    Screen element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        hardware_model (str): The specific hardware model of the diagnostic.
        diagnostic: (:class:`~nala.models.diagnostic.Screen_Diagnostic`): The diagnostic
        attributes of the Screen.
    """

    hardware_type: str = Field(default="Screen", frozen=True)
    """Screen hardware type."""

    hardware_model: str = Field(default="YAG", frozen=True)
    """Screen hardware model."""

    diagnostic: Screen_Diagnostic = Field(default_factory=Screen_Diagnostic)
    """Diagnostic attributes of the screen."""

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
    """
    Generic charge diagnostic element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
        diagnostic: (:class:`~nala.models.diagnostic.Charge_Diagnostic`): The diagnostic
        attributes of the diagnostic.
    """

    hardware_type: str = Field(default="ChargeDiagnostic", frozen=True)
    """Charge diagnostic hardware type."""

    diagnostic: Charge_Diagnostic = Field(default_factory=Charge_Diagnostic)
    """Diagnostic attributes of the charge diagnostic."""


class Wall_Current_Monitor(ChargeDiagnostic):
    """
    WCM charge diagnostic element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
    """

    hardware_type: str = Field(default="Wall_Current_Monitor", frozen=True, alias="WCM")
    """WCM hardware type."""


class Faraday_Cup_Monitor(ChargeDiagnostic):
    """
    FCM charge diagnostic element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
    """

    hardware_type: str = Field(default="Faraday_Cup_Monitor", frozen=True, alias="FCM")
    """FCM hardware type."""


class Integrated_Current_Transformer(ChargeDiagnostic):
    """
    ICT charge diagnostic element.

    Attributes:
        hardware_type (str): The hardware type of the diagnostic.
    """

    hardware_type: str = Field(default="Integrated_Current_Transformer", frozen=True, alias="ICT")
    """ICT hardware type."""


class VacuumGauge(PhysicalBaseElement):
    """
    Vacuum gauge element.

    Attributes:
        hardware_type (str): The hardware type of the gauge.
        hardware_model (str): The hardware model of the gauge.
    """

    hardware_type: str = Field(default="VacuumGauge", frozen=True)
    """Vacuum gauge hardware type."""

    hardware_model: str = Field(default="IMG", frozen=True)
    """Vacuum gauge hardware model."""


class Laser(PhysicalBaseElement):
    """
    Laser element.

    Attributes:
        hardware_type (str): The hardware type of the laser.
        hardware_model (str): The hardware model of the laser.
        laser (:class:`~nala.models.laser.LaserElement`): The laser attributes of the laser.
    """

    hardware_type: str = Field(default="Laser", frozen=True)
    """Laser hardware type."""

    hardware_model: str = Field(default="Laser", frozen=True)
    """Laser hardware model."""

    laser: LaserElement = Field(default_factory=LaserElement)
    """Laser attributes of the laser."""


class LaserEnergyMeter(Element):
    """
    Laser energy meter element.

    Attributes:
        hardware_type (str): The hardware type of the laser energy meter.
        hardware_model (str): The hardware model of the laser energy meter.
        laser (:class:`~nala.models.laser.LaserEnergyMeterElement`): The laser-related attributes of the
        energy meter.
    """

    hardware_type: str = Field(default="LaserEnergyMeter", frozen=True)
    """Laser energy meter hardware type."""

    hardware_model: str = Field(default="Gentec Photodiode", frozen=True)
    """Laser energy meter hardware model.
    #TODO should be manufacturer?"""

    laser: LaserEnergyMeterElement = Field(default_factory=LaserEnergyMeterElement)
    """Laser energy meter attributes of the element."""


class LaserHalfWavePlate(Element):
    """
    Laser half-wave plate element.

    Attributes:
        hardware_type (str): The hardware type of the HWP.
        hardware_model (str): The hardware model of the HWP.
        laser (:class:`~nala.models.laser.LaserHalfWavePlateElement`): The laser-related attributes of the
        HWP.
    """

    hardware_type: str = Field(default="LaserHalfWavePlate", frozen=True)
    """Laser half-wave plate element type."""

    hardware_model: str = Field(default="Newport", frozen=True)
    """Laser half-wave plate hardware model.
    #TODO should be manufacturer?"""

    laser: LaserHalfWavePlateElement = Field(default_factory=LaserHalfWavePlateElement)
    """Laser half-wave plate element attributes of the element."""


class LaserMirror(Element):
    """
    Laser mirror element.

    Attributes:
        hardware_type (str): The hardware type of the mirror.
        hardware_model (str): The hardware model of the mirror.
        laser (:class:`~nala.models.laser.LaserMirrorElement`): The laser-related attributes of the
        mirror.
    """

    hardware_type: str = Field(default="LaserMirror", frozen=True)
    """Laser mirror hardware type."""

    hardware_model: str = Field(default="Planar", frozen=True)
    """Laser mirror hardware model."""

    laser: LaserMirrorElement = Field(default_factory=LaserMirrorElement)
    """Laser mirror attributes of the element."""


class Plasma(PhysicalBaseElement):
    """
    Plasma element.

    Attributes:
        hardware_type (str): The hardware type of the element.
        simulation (:class:`~nala.models.simulation.PlasmaSimulationElement`): The simulation
        attributes of the plasma.
        plasma (:class:`~nala.models.plasma.PlasmaElement`): The plasma attributes of the plasma.
        laser (:class:`~nala.models.laser.LaserElement` or None): The laser assosicated with the plasma
    """

    hardware_type: str = Field(default="Plasma", frozen=True)
    """Plasma hardware type."""

    simulation: PlasmaSimulationElement = Field(default_factory=PlasmaSimulationElement)
    """Simulation attributes of the plasma."""

    plasma: PlasmaElement = Field(default_factory=PlasmaElement)
    """Plasma attribute of the plasma."""

    laser: LaserElement | None = None
    """Laser attached to the plasma element."""


class Lighting(Element):
    """
    Lighting element.

    Attributes:
        hardware_type (str): The hardware type of the element.
        hardware_model (str): The hardware model of the element.
        lights (:class:`~nala.models.lighting.LightingElement`): The lighting element.
    """

    hardware_type: str = Field(default="Lighting", frozen=True)
    """Lighting hardware type."""

    hardware_model: str = Field(default="LED", frozen=True)
    """Lighting hardware model."""

    lights: LightingElement = Field(default_factory=LightingElement)
    """Lighting attributes of the element."""


class PID(Element):
    """
    Proportional-integral-derivative feedback element.

    Attributes:
        hardware_type (str): The hardware type of the element.
        hardware_model (str): The hardware model of the element.
        PID (:class:`~nala.models.RF.PIDElement`): The PID element.
    """

    hardware_type: str = Field(default="PID", frozen=True)
    """PID hardware type."""

    hardware_model: str = Field(default="RF", frozen=True)
    """PID hardware model."""

    PID: PIDElement = Field(default_factory=PIDElement)
    """PID attributes of the element."""


class Low_Level_RF(Element):
    """
    Low-level RF element.

    Attributes:
        hardware_type (str): The hardware type of the element.
        hardware_model (str): The hardware model of the element.
        LLRF (:class:`~nala.models.RF.Low_Level_RF_Element`): The LLRF element.
    """

    hardware_type: str = Field(default="Low_Level_RF", frozen=True)
    """LLRF hardware type."""

    hardware_model: str = Field(default="Libera", frozen=True)
    """LLRF hardware model."""

    LLRF: Low_Level_RF_Element = Field(default_factory=Low_Level_RF_Element)
    """LLRF attributes of the element."""


class RFCavity(PhysicalBaseElement):
    """
    RFCavity element.

    Attributes:
        hardware_type (str): The hardware type of the RF cavity.
        hardware_model (str): The specific hardware model of the RF cavity.
        cavity (:class:`~nala.models.RF.RFCavityElement`): The RF cavity attributes of the element.
        simulation: (:class:`~nala.models.simulation.RFCavitySimulationElement`): The simulation
        attributes of the RF cavity.
    """

    hardware_type: str = Field(default="RFCavity", frozen=True)
    """RF cavity hardware type."""

    hardware_model: str = Field(default="SBand", frozen=True)
    """RF cavity hardware model."""

    cavity: RFCavityElement = Field(default_factory=RFCavityElement)
    """Cavity attributes of the RF cavity."""

    simulation: RFCavitySimulationElement = Field(default_factory=RFCavitySimulationElement)
    """Simulation attributes of the RF cavity."""


class Wakefield(PhysicalBaseElement):
    """
    Wakefield element.

    Attributes:
        hardware_type (str): The hardware type of the wakefield.
        hardware_model (str): The specific hardware model of the wakefield.
        cavity: (:class:`~nala.models.RF.WakefieldElement`): The wakefield cavity attributes of the element.
        simulation: (:class:`~nala.models.simulation.WakefieldSimulationElement`): The simulation
        attributes of the wakefield cavity.
    """

    hardware_type: str = Field(default="Wakefield", frozen=True)
    """Wakefield hardware type."""

    hardware_model: str = Field(default="Dielectric", frozen=True)
    """Wakefield hardware model."""

    cavity: WakefieldElement = Field(default_factory=WakefieldElement)
    """Wakefield attributes of the element."""

    simulation: WakefieldSimulationElement = Field(default_factory=WakefieldSimulationElement)
    """Simulation attributes of the wakefield element."""


class RFDeflectingCavity(RFCavity):
    """
    RF Deflecting Cavity element.

    Attributes:
        hardware_type (str): The hardware type of the RF cavity.
        hardware_model (str): The specific hardware model of the RF cavity.
        cavity (:class:`~nala.models.RF.RFDeflectingCavityElement`): The RF cavity attributes of the element.
        simulation: (:class:`~nala.models.simulation.RFCavitySimulationElement`): The simulation
        attributes of the RF cavity.
    """

    hardware_type: str = Field(default="RFDeflectingCavity", frozen=True)
    """RF deflecting cavity hardware type."""

    hardware_model: str = Field(default="SBand", frozen=True)
    """RF deflecting cavity hardware model."""

    cavity: RFDeflectingCavityElement = Field(default_factory=RFDeflectingCavityElement)
    """Cavity attributes of the RF deflecting cavity."""

    simulation: RFCavitySimulationElement = Field(default_factory=RFCavitySimulationElement)
    """Simulation attributes of the RF deflecting cavity."""


class RFModulator(Element):
    """
    RF Modulator element.

    Attributes:
        hardware_type (str): The hardware type of the RF modulator.
        hardware_model (str): The specific hardware model of the RF modulator.
        modulator (:class:`~nala.models.RF.RFModulatorElement`): The RF modulator attributes of the element.
    """

    hardware_type: str = Field(default="RFModulator", frozen=True)
    """RF modulator hardware type."""

    hardware_model: str = Field(default="Thales", frozen=True)
    """RF modulator hardware model.
    #TODO move to manufacturer?"""

    modulator: RFModulatorElement = Field(default_factory=RFModulatorElement)
    """RF modulator attributes of the element."""


class RFProtection(Element):
    """
    RF Protection element.

    Attributes:
        hardware_type (str): The hardware type of the RF protection system.
        hardware_model (str): The specific hardware model of the RF protection system.
        modulator (:class:`~nala.models.RF.RFProtectionElement`): The RF protection attributes of the element.
    """

    hardware_type: str = Field(default="RFProtection", frozen=True)
    """RF protection hardware type."""

    hardware_model: str = Field(default="PROT", frozen=True)
    """RF protection hardware model."""

    modulator: RFProtectionElement = Field(default_factory=RFProtectionElement)
    """RF protection attributes of the element."""


class RFHeartbeat(Element):
    """
    RF Heartbeat element.

    Attributes:
        hardware_type (str): The hardware type of the RF heartbeat system.
        heartbeat (:class:`~nala.models.RF.RFHeartbeatElement`): The RF heartbeat attributes of the element.
    """

    hardware_type: str = Field(default="RFHeartbeat", frozen=True)
    """RF heartbeat hardware type."""

    heartbeat: RFHeartbeatElement = Field(default_factory=RFHeartbeatElement)
    """RF heartbeat system attributes."""


class Shutter(PhysicalBaseElement):
    """
    Shutter element.

    Attributes:
        hardware_type (str): The hardware type of the shutter.
        shutter (:class:`~nala.models.shutter.ShutterElement`): The shutter attributes of the element.
    """

    hardware_type: str = Field(default="Shutter", frozen=True)
    """Shutter hardware type"""

    shutter: ShutterElement = Field(default_factory=ShutterElement)
    """Shutter attributes of the element."""


class Valve(PhysicalBaseElement):
    """
    Vacuum valve element.

    Attributes:
        hardware_type (str): The hardware type of the valve.
        valve (:class:`~nala.models.shutter.ValveElement`): The valve attributes of the element.
    """

    hardware_type: str = Field(default="Valve", frozen=True)
    """Valve hardware type."""

    valve: ValveElement = Field(default_factory=ValveElement)
    """Valve attributes of the element."""


class Marker(PhysicalBaseElement):
    """
    Marker element.

    Attributes:
        hardware_type (str): The hardware type of the marker.
        hardware_model (str): The hardware model of the marker.
        simulation (:class:`~nala.models.simulation.DiagnosticSimulationElement`): The simulation
        attributes of the marker.
    """

    hardware_type: str = Field(default="Marker", frozen=True)
    """Marker hardware type."""

    hardware_model: str = Field(default="Simulation", frozen=True)
    """Marker hardware model."""

    simulation: DiagnosticSimulationElement = Field(default_factory=DiagnosticSimulationElement)
    """Simulation attributes of the marker."""


class Aperture(PhysicalBaseElement):
    """
    Aperture element.

    Attributes:
        hardware_type (str): The hardware type of the aperture.
        hardware_model (str): The hardware model of the aperture.
        aperture (:class:`~nala.models.simulation.ApertureElement`): The simulation
        attributes of the aperture.
    """

    hardware_type: str = Field(default="Aperture", frozen=True)
    """Aperture hardware type."""

    hardware_model: str = Field(default="Simulation", frozen=True)
    """Aperture hardware model."""

    aperture: ApertureElement = Field(default_factory=ApertureElement)
    """Aperture attributes of the element."""


class Collimator(Aperture):
    """
    Collimator element.

    Attributes:
        hardware_type (str): The hardware type of the collimator.
        hardware_model (str): The hardware model of the collimator.
    """

    hardware_type: str = Field(default="Collimator", frozen=True)
    """Collimator hardware type."""

    hardware_model: str = Field(default="Simulation", frozen=True)
    """Collimator hardware model."""


class Drift(PhysicalBaseElement):
    """
    Drift element.

    Attributes:
        hardware_type (str): The hardware type of the marker.
        simulation (:class:`~nala.models.simulation.DriftSimulationElement`): The simulation
        attributes of the drift.
    """

    hardware_type: str = Field(default="Drift", frozen=True)
    """Drift hardware type."""

    simulation: DriftSimulationElement = Field(default_factory=DriftSimulationElement)
    """Simulation attributes of the drift."""
