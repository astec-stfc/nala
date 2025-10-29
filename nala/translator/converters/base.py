import os
import numpy as np
from pydantic import computed_field, Field

from nala.models.physical import PhysicalElement, Position  # noqa E402
from nala.models.element import flatten, Element
from typing import Dict
from warnings import warn

from ..converters import (
    type_conversion_rules,
    type_conversion_rules_Elegant,
    type_conversion_rules_Genesis,
    elements_Elegant,
    elements_Genesis,
    keyword_conversion_rules_elegant,
    keyword_conversion_rules_genesis,
    keyword_conversion_rules_ocelot,
    keyword_conversion_rules_cheetah,
    keyword_conversion_rules_xsuite,
    keyword_conversion_rules_wake_t,
)
from ..utils.fields import field
from ..utils.functions import expand_substitution, checkValue
from ..converters.codes.gpt import gpt_ccs


class BaseElementTranslator(Element):
    type_conversion_rules: Dict = {}
    """Conversion rules for keywords when exporting to different code formats."""

    conversion_rules: Dict = {}
    """Conversion rules for keywords when exporting to different code formats."""

    counter: int = Field(ge=1, default=1)

    master_lattice_location: str = None

    directory: str = './'

    ccs: gpt_ccs = None

    def model_post_init(self, __context):
        self.type_conversion_rules = type_conversion_rules
        self.conversion_rules["elegant"] = keyword_conversion_rules_elegant["general"]
        self.conversion_rules["ocelot"] = keyword_conversion_rules_ocelot["general"]
        self.conversion_rules["cheetah"] = keyword_conversion_rules_cheetah["general"]
        self.conversion_rules["xsuite"] = keyword_conversion_rules_xsuite["general"]
        self.conversion_rules["wake_t"] = keyword_conversion_rules_wake_t["general"]
        self.conversion_rules["genesis"] = keyword_conversion_rules_genesis["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_elegant:
            self.conversion_rules["elegant"] = keyword_conversion_rules_elegant[self.hardware_type.lower()] | \
                                               keyword_conversion_rules_elegant["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_ocelot:
            self.conversion_rules["ocelot"] = keyword_conversion_rules_ocelot[self.hardware_type.lower()] | \
                                              keyword_conversion_rules_ocelot["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_cheetah:
            self.conversion_rules["cheetah"] = keyword_conversion_rules_cheetah[self.hardware_type.lower()] | \
                                               keyword_conversion_rules_cheetah["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_xsuite:
            self.conversion_rules["xsuite"] = keyword_conversion_rules_xsuite[self.hardware_type.lower()] | \
                                              keyword_conversion_rules_xsuite["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_wake_t:
            self.conversion_rules["wake_t"] = keyword_conversion_rules_wake_t[self.hardware_type.lower()] | \
                                              keyword_conversion_rules_wake_t["general"]
        if self.hardware_type.lower() in keyword_conversion_rules_genesis:
            self.conversion_rules["genesis"] = keyword_conversion_rules_genesis[self.hardware_type.lower()] | \
                                              keyword_conversion_rules_genesis["general"]
        self.ccs = gpt_ccs(name="wcs", position=[0, 0, 0], rotation=[0, 0, 0])
        super().model_post_init(__context)

    def full_dump(self) -> Dict:
        return flatten({**self.model_dump()}, parent_key="", separator="_")

    def start_write(self) -> None:
        self.update_field_definition()

    def to_elegant(self) -> str:
        """
        Generates a string representation of the object's properties in the Elegant format.

        Returns
        -------
        str
            A formatted string representing the object's properties in Elegant format.
        """
        self.start_write()
        wholestring = ""
        etype = self._convertType_Elegant(self.hardware_type)
        string = self.name + ": " + etype
        keys = []
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Elegant(key) in elements_Elegant[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Elegant(key)
                    if value == "angle":
                        value = self.magnetic.angle
                    elif value == "angle/2":
                        value = self.magnetic.angle / 2
                    elif key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                        value = getattr(self, f"{key}l")
                    value = 1 if value is True else value
                    value = 0 if value is False else value
                    if key not in keys:
                        tmpstring = ", " + key + " = " + str(value)
                        if len(string + tmpstring) > 76:
                            wholestring += string + ",&\n"
                            string = ""
                            string += tmpstring[2::]
                        else:
                            string += tmpstring
                    keys.append(key)
        wholestring += string + ";\n"
        return wholestring

    def to_ocelot(self) -> object:
        """
        Generates an Ocelot object based on the element's properties and type.

        Returns
        -------
        object
            An Ocelot object representing the element, initialized with its properties.
        """
        from ocelot.cpbd.elements import Marker, Aperture
        from ..conversion_rules.codes import ocelot_conversion

        type_conversion_rules_Ocelot = ocelot_conversion.ocelot_conversion_rules
        self.start_write()
        obj = type_conversion_rules_Ocelot[self.hardware_type](eid=self.name)
        for key, value in self.full_dump().items():
            if (key not in ["name", "type", "commandtype"]) and (
                not type(obj) in [Aperture, Marker] and
                self._convertKeyword_Ocelot(key) in obj.__class__().element.__dict__
            ):
                if value is not None:
                    key = self._convertKeyword_Ocelot(key)
                    if value == "angle":
                        value = self.magnetic.angle
                    if key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                        value = getattr(self, f"{key}l")
                    setattr(obj, self._convertKeyword_Ocelot(key), value)
        return obj

    def to_cheetah(self) -> object:
        """
        Generates a Cheetah object based on the element's properties and type.

        Returns
        -------
        object
            A Cheetah object representing the element, initialized with its properties.
        """
        from cheetah.accelerator import Aperture as Aperture_Cheetah
        from cheetah.accelerator import Screen as Screen_Cheetah
        from cheetah.accelerator import Drift as Drift_Cheetah
        from ..conversion_rules.codes import cheetah_conversion
        from torch import tensor, float64

        type_conversion_rules_Cheetah = cheetah_conversion.cheetah_conversion_rules
        self.start_write()
        try:
            obj = type_conversion_rules_Cheetah[self.hardware_type](
                name=self.name,
                length=tensor(self.physical.length, dtype=float64),
                sanitize_name=True
            )
        except Exception as e:
            if self.hardware_type in type_conversion_rules_Cheetah:
                if self.physical.length > 0:
                    obj = Drift_Cheetah(
                        name=self.name,
                        length=tensor(self.physical.length, dtype=float64),
                        sanitize_name=True,
                    )
                else:
                    obj = Screen_Cheetah(
                        name=self.name,
                        sanitize_name=True,
                    )
                    obj.is_active = True
                    return obj
            else:
                raise NotImplementedError(f"Cheetah element {self.hardware_type} not implemented, {e}")
        buffers = obj.__class__(length=tensor(self.physical.length, dtype=float64))._buffers
        for key, value in self.full_dump().items():
            if (key not in ["name", "type", "commandtype"]) and (
                not type(obj) in [Aperture_Cheetah] and
                self._convertKeyword_Cheetah(key) in buffers
            ):
                key = self._convertKeyword_Cheetah(key)
                if key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                    value = getattr(self, f"{key}l")
                if isinstance(value, float):
                    dt = float64
                    setattr(obj, self._convertKeyword_Cheetah(key), tensor(value, dtype=dt))
                elif isinstance(value, int):
                    from torch import int64
                    dt = int64
                    setattr(obj, self._convertKeyword_Cheetah(key), tensor(value, dtype=dt))
                    # else:
                    #     from torch import get_default_dtype
                    #     dt = get_default_dtype()
        if isinstance(obj, Screen_Cheetah):
            obj.is_active = True
        return obj

    def to_xsuite(self, beam_length: int) -> tuple:
        """
        Generates an Xsuite object based on the element's properties and type.

        Parameters
        ----------
        beam_length: int
            Number of macroparticles in the beam

        Returns
        -------
        tuple
            (objectname, Xsuite object, properties[dict])
        """
        from ..conversion_rules.codes import xsuite_conversion

        type_conversion_rules_Xsuite = xsuite_conversion.xsuite_conversion_rules
        self.start_write()
        obj = type_conversion_rules_Xsuite[self.hardware_type]
        properties = {}
        from xtrack.monitors import ParticlesMonitor
        if obj == ParticlesMonitor:
            properties = {
                "num_particles": beam_length,
                "start_at_turn": 0,
                "stop_at_turn": 1,
                # "store_particles": True,
            }
            return self.name, obj, properties
        for key, value in self.full_dump().items():
            if (key not in ["name", "type", "commandtype"]) and (
                self._convertKeyword_Xsuite(key) in list(obj.__dict__.keys())
            ):
                key = self._convertKeyword_Xsuite(key)
                # if key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                #     value = getattr(self, f"{key}l")
                if key == "angle":
                    if self.length > 0:
                        properties.update({"k0": self.magnetic.angle / self.length})
                if self.hardware_type.lower() == "dipole":
                    properties.update({"num_multipole_kicks": 10})
                if "edge" in key and isinstance(value, str):
                    if value == "angle":
                        value = self.magnetic.angle
                    elif value == "angle/2":
                        value = self.magnetic.angle / 2
                properties.update({key: value})
        return self.name, obj, properties

    def to_genesis(self) -> str:
        """
        Generates a string representation of the object's properties in the Genesis format.

        Returns
        -------
        str
            A formatted string representing the object's properties in Elegant format.
        """
        self.start_write()
        wholestring = ""
        etype = self._convertType_Genesis(self.hardware_type)
        if "mark" in etype.lower():
            return f"{self.name}: {etype} = " + "{};\n"
        string = f"{self.name}: {etype} = " + "{"
        keys = []
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Genesis(key) in elements_Genesis[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Elegant(key)
                    if value == "angle":
                        value = self.magnetic.angle
                    elif value == "angle/2":
                        value = self.magnetic.angle / 2
                    elif key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                        value = getattr(self, f"{key}l")
                    value = 1 if value is True else value
                    value = 0 if value is False else value
                    if key not in keys:
                        string += key + " = " + str(value) + ', '
                    keys.append(key)
        wholestring += string[:-2] + "};\n"
        return wholestring

    def to_csrtrack(self, n: int = 0, **kwargs) -> str:
        return ""

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        return ""

    def to_gpt(self, Brho: float=0.0, ccs: str = "wcs", *args, **kwargs) -> str:
        return ""

    def to_wake_t(self) -> object:
        from ..conversion_rules.codes import wake_t_conversion

        type_conversion_rules_Wake_T = wake_t_conversion.wake_t_conversion_rules
        if self.hardware_type in type_conversion_rules_Wake_T:
            obj = type_conversion_rules_Wake_T[self.hardware_type]()
        else:
            if "drift" not in self.hardware_type.lower():
                warn(f"Element type {self.hardware_type} not in Wake-T; setting as drift")
            from wake_t.beamline_elements import Drift as Drift_WakeT
            obj = Drift_WakeT()
        obj.element_name = self.name
        for key, value in self.full_dump().items():
            if key not in ["name", "type", "commandtype"]:
                key = self._convertKeyword_WakeT(key)
                setattr(obj, self._convertKeyword_WakeT(key), value)
        return obj

    def _convertType_Elegant(self, etype: str) -> str:
        """
        Converts the element type to the corresponding Elegant type using predefined rules.

        Parameters
        ----------
        etype: str
            The type of the element to be converted.

        Returns
        -------
        str
            The converted type of the element, or the original type if no conversion rule exists.
        """
        return (
            type_conversion_rules_Elegant[etype]
            if etype in type_conversion_rules_Elegant
            else etype
        )

    def _convertKeyword_Elegant(self, keyword: str, updated_type: str = "") -> str:
        """
        Converts a keyword to its corresponding Elegant keyword using predefined rules.

        Parameters
        ----------
        keyword: str:
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Elegant, or the original keyword if no conversion rule exists.

        """
        if updated_type.lower() in keyword_conversion_rules_elegant:
            conversion_rules = keyword_conversion_rules_elegant[updated_type.lower()] | \
                               keyword_conversion_rules_elegant["general"]
            element = elements_Elegant[self._convertType_Elegant(updated_type)]
        else:
            conversion_rules = self.conversion_rules["elegant"]
            element = elements_Elegant[self._convertType_Elegant(self.hardware_type)]
        for strip in ["", "simulation_", "cavity_", "magnetic_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
            elif stripped in element.keys():
                return stripped
        return keyword

    def _convertType_Genesis(self, etype: str) -> str:
        """
        Converts the element type to the corresponding Genesis type using predefined rules.

        Parameters
        ----------
        etype: str
            The type of the element to be converted.

        Returns
        -------
        str
            The converted type of the element, or the original type if no conversion rule exists.
        """
        return (
            type_conversion_rules_Genesis[etype]
            if etype in type_conversion_rules_Genesis
            else etype
        )

    def _convertKeyword_Genesis(self, keyword: str, updated_type: str = "") -> str:
        """
        Converts a keyword to its corresponding Genesis keyword using predefined rules.

        Parameters
        ----------
        keyword: str:
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Genesis, or the original keyword if no conversion rule exists.

        """
        if updated_type.lower() in keyword_conversion_rules_genesis:
            conversion_rules = keyword_conversion_rules_genesis[updated_type.lower()] | \
                               keyword_conversion_rules_genesis["general"]
            element = elements_Genesis[self._convertType_Genesis(updated_type)]
        else:
            conversion_rules = self.conversion_rules["genesis"]
            element = elements_Genesis[self._convertType_Genesis(self.hardware_type)]
        for strip in ["", "simulation_", "cavity_", "magnetic_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
            elif stripped in element.keys():
                return stripped
        return keyword

    def _convertType_Ocelot(self, etype: str) -> object:
        """
        Converts the element type to the corresponding Ocelot type using predefined rules.

        Parameters
        ----------
        etype: str
            The type of the element to be converted.

        Returns
        -------
        object
            The Ocelot element, or the original type if no conversion rule exists.
        """
        from ..conversion_rules.codes import ocelot_conversion
        from ocelot.cpbd.elements.drift import Drift as Drift_Oce

        type_conversion_rules_Ocelot = ocelot_conversion.ocelot_conversion_rules
        return (
            type_conversion_rules_Ocelot[etype]
            if etype in type_conversion_rules_Ocelot
            else Drift_Oce
        )

    def _convertKeyword_Ocelot(self, keyword: str, updated_type: str = "") -> str:
        """
        Converts a keyword to its corresponding Ocelot keyword using predefined rules.

        Parameters
        ----------
        keyword: str:
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Ocelot, or the original keyword if no conversion rule exists.

        """
        conversion_rules = self.conversion_rules["ocelot"]
        for strip in ["", "simulation_", "cavity_", "magnetic_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
        return keyword

    def _convertType_Cheetah(self, etype: str) -> object:
        """
        Converts the element type to the corresponding Cheetah type using predefined rules.

        Parameters
        ----------
        etype: str
            The type of the element to be converted.

        Returns
        -------
        object
            The Cheetah element, or the original type if no conversion rule exists.
        """
        from ..conversion_rules.codes import cheetah_conversion
        from cheetah.accelerator import Drift as Drift_Che

        type_conversion_rules_Cheetah = cheetah_conversion.cheetah_conversion_rules
        return (
            type_conversion_rules_Cheetah[etype]
            if etype in type_conversion_rules_Cheetah
            else Drift_Che
        )

    def _convertKeyword_Cheetah(self, keyword: str) -> str:
        """
        Converts a keyword to its corresponding Cheetah keyword using predefined rules.

        Parameters
        ----------
        keyword: str
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Cheetah, or the original keyword if no conversion rule exists.
        """
        conversion_rules = self.conversion_rules["cheetah"]
        for strip in ["", "simulation_", "cavity_", "magnetic_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
        return keyword

    def _convertKeyword_Xsuite(self, keyword: str) -> str:
        """
        Converts a keyword to its corresponding Xsuite keyword using predefined rules.

        Parameters
        ----------
        keyword: str:
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Xsuite, or the original keyword if no conversion rule exists.

        """
        conversion_rules = self.conversion_rules["xsuite"]
        for strip in ["", "simulation_", "cavity_", "magnetic_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
        return keyword

    def _convertKeyword_WakeT(self, keyword: str) -> str:
        """
        Converts a keyword to its corresponding Wake-T keyword using predefined rules.

        Parameters
        ----------
        keyword: str:
            The keyword to be converted.

        Returns
        -------
        str
            The converted keyword for Wake-T, or the original keyword if no conversion rule exists.

        """
        conversion_rules = self.conversion_rules["wake_t"]
        for strip in ["", "simulation_", "cavity_", "magnetic_", "plasma_", "laser_"]:
            stripped = keyword.replace(strip, "")
            if stripped in conversion_rules:
                return conversion_rules[stripped]
        return keyword

    def _write_ASTRA_dictionary(self, d: dict, n: int | None = 1) -> str:
        """
        Generates a string representation of the object's properties in the ASTRA format.

        Parameters
        ----------
        d: dict
            A dictionary containing the properties of the object to be formatted.
        n: int, optional
            An optional integer to specify the index for ASTRA objects. Default is 1.

        Returns
        -------
        str
            A formatted string representing the object's properties in ASTRA format.
        """
        output = ""
        for k, v in list(d.items()):
            if checkValue(self, v) is not None:
                if "type" in v and v["type"] == "list":
                    for i, l in enumerate(checkValue(self, v)):
                        if n is not None:
                            param_string = (
                                k
                                + "("
                                + str(i + 1)
                                + ","
                                + str(n)
                                + ") = "
                                + str(l)
                                + ", "
                            )
                        else:
                            param_string = k + " = " + str(l) + "\n"
                        if len((output + param_string).splitlines()[-1]) > 70:
                            output += "\n"
                        output += param_string
                elif "type" in v and v["type"] == "array":
                    if n is not None:
                        param_string = k + "(" + str(n) + ") = ("
                    else:
                        param_string = k + " = ("
                    for i, l in enumerate(checkValue(self, v)):
                        param_string += str(l) + ", "
                        if len((output + param_string).splitlines()[-1]) > 70:
                            output += "\n"
                    output += param_string[:-2] + "),\n"
                elif "type" in v and v["type"] == "not_zero":
                    if abs(checkValue(self, v)) > 0:
                        if n is not None:
                            param_string = (
                                k
                                + "("
                                + str(n)
                                + ") = "
                                + str(checkValue(self, v))
                                + ", "
                            )
                        else:
                            param_string = k + " = " + str(checkValue(self, v)) + ",\n"
                        if len((output + param_string).splitlines()[-1]) > 70:
                            output += "\n"
                        output += param_string
                else:
                    if n is not None:
                        param_string = (
                            k + "(" + str(n) + ") = " + str(checkValue(self, v)) + ", "
                        )
                    else:
                        param_string = k + " = " + str(checkValue(self, v)) + ",\n"
                    if len((output + param_string).splitlines()[-1]) > 70:
                        output += "\n"
                    output += param_string
        return output[:-2] + "\n"

    def __getattr__(self, item):
        found = []
        for key, value in self.model_dump().items():
            if isinstance(value, dict):
                for k1, v1 in value.items():
                    if k1 == item:
                        found.append(v1)
            else:
                if key == item:
                    found.append(value)
        if len(found) == 1:
            return found[0]
        elif len(found) > 1:
            warn(f"Multiple attributes found for {item}, returning first")
            return found[0]

    @computed_field
    @property
    def length(self) -> float:
        return self.physical.length

    @computed_field
    @property
    def dx(self) -> float:
        return self.physical.error.position.x

    @computed_field
    @property
    def dy(self) -> float:
        return self.physical.error.position.y

    @computed_field
    @property
    def dz(self) -> float:
        return self.physical.error.position.z

    @computed_field
    @property
    def x_rot(self) -> float:
        return self.physical.rotation.theta

    @computed_field
    @property
    def y_rot(self) -> float:
        return self.physical.rotation.phi

    @computed_field
    @property
    def z_rot(self) -> float:
        return self.physical.rotation.psi

    @computed_field
    @property
    def dx_rot(self) -> float:
        return self.physical.error.rotation.theta

    @computed_field
    @property
    def dy_rot(self) -> float:
        return self.physical.error.rotation.phi

    @computed_field
    @property
    def dz_rot(self) -> float:
        return self.physical.error.rotation.psi

    def get_field_reference_position(self) -> np.ndarray:
        """
        Returns the position of the field reference point based on the `field_reference_position` attribute.

        Returns
        -------
        list
            The position of the field reference point, which can be 'start', 'middle', or 'end'.
            If `field_reference_position` is not set, it defaults to the start position.

        Raises
        ------
        ValueError
            If `field_reference_position` is set to an invalid value that is not 'start', 'middle', or 'end'.
        """
        if (
                hasattr(self, "field_reference_position")
                and self.field_reference_position is not None
        ):
            try:
                return getattr(self.physical, self.field_reference_position.lower()).model_dump()
            except AttributeError:
                warn(
                    "field_reference_position should be (start/middle/end) not" +
                    self.field_reference_position +
                    "; returning start"
                )
        return self.physical.start.model_dump()

    def update_field_definition(self) -> None:
        """
        Updates the field definitions to allow for the relative sub-directory location
        """
        if hasattr(self, "simulation"):
            if (
                hasattr(self.simulation, "field_definition")
                and self.simulation.field_definition is not None
                and isinstance(self.simulation.field_definition, str)
            ):
                field_kwargs = {
                    "filename": expand_substitution(self, self.simulation.field_definition),
                    # "field_type": self.field_type,
                }
                if "cavity" in self.hardware_type.lower():
                    field_kwargs.update(
                        {
                            "frequency": self.cavity.frequency,
                            "cavity_type": self.cavity.structure_Type,
                            "n_cells": self.cavity.n_cells,
                        }
                    )
                self.simulation.field_definition = field(**field_kwargs)
            if (
                hasattr(self.simulation, "wakefield_definition")
                and self.simulation.wakefield_definition is not None
                and isinstance(self.simulation.wakefield_definition, str)
            ):
                if hasattr(self, "cavity"):
                    self.simulation.wakefield_definition = field(
                        filename=expand_substitution(self, self.simulation.wakefield_definition),
                        # field_type=self.field_type,
                        frequency=self.cavity.frequency,
                        cavity_type=self.cavity.structure_Type,
                        n_cells=self.cavity.n_cells,
                    )
                else:
                    self.simulation.wakefield_definition = field(
                        filename=expand_substitution(self, self.simulation.wakefield_definition),
                    )

    def generate_field_file_name(self, param: field, code: str) -> str | None:
        """
        Generates a field file name based on the provided frameworkElement and tracking code.

        Parameters
        ----------
        param: field
            The :class:`~nala.translator.utils.fields.field` object for which the field file is being generated.
        code: str
            The tracking code for which the field file is being generated (e.g., 'elegant', 'ocelot').

        Returns
        -------
        str | None
            The name of the field file if it exists, otherwise None.
        """
        if hasattr(param, "filename"):
            self.make_directory()
            basename = (
                os.path.basename(param.filename).replace('"', "").replace("'", "")
            )
            efield_basename = os.path.abspath(
                os.path.join(self.directory.replace("\\", "/"), basename.replace("\\", "/"))
            )
            return os.path.basename(
                param.write_field_file(code=code, location=efield_basename)
            )
        else:
            warn(
                f"param does not have a filename: {param}, it must be a `field` object"
            )
        return None

    @property
    def get_field_amplitude(self) -> float:
        """
        Returns the field amplitude of the element, scaled by `field_scale` if it exists.

        Returns
        -------
        float or None
            The field amplitude of the element, which is either scaled by `field_scale`
            or directly taken from `field_amplitude`.
            Returns None if `field_amplitude` is not defined

        """
        if hasattr(self, "magnetic"):
            if hasattr(self.magnetic, "fields"):
                if hasattr(self.magnetic.fields, "S0L"):
                    if type(self.simulation.scale_field) in [int, float]:
                        return float(self.field_scale) * float(
                            expand_substitution(self, self.magnetic.fields.S0L)
                        )
                    else:
                        return float(expand_substitution(self, self.magnetic.fields.S0L))
                return 0.0
            return 0.0
        return 0.0

    def make_directory(self) -> None:
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)