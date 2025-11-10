from pydantic import computed_field
import numpy as np
from .base import BaseElementTranslator
from nala.models.RF import RFCavityElement
from nala.models.simulation import RFCavitySimulationElement
from nala.translator.utils.fields import field

from ..converters import (
    elements_Elegant,
    elements_Opal,
)

class RFCavityTranslator(BaseElementTranslator):
    """
    Translator class for converting a :class:`~nala.models.element.RFCavity` element instance into a string or
    object that can be understood by various simulation codes.
    """

    cavity: RFCavityElement
    """Cavity element."""

    simulation: RFCavitySimulationElement
    """Cavity simulation element"""

    wakefile: str = None
    """Name of wakefile associated with the cavity."""

    trwakefile: str = None
    """Name of transverse wakefile associated with the cavity."""

    zwakefile: str = None
    """Name of longitudinal wakefile associated with the cavity."""

    @computed_field
    @property
    def structure_type(self) -> str:
        return self.cavity.structure_Type

    @computed_field
    @property
    def tcolumn(self) -> str | None:
        return f'"{self.simulation.t_column}"' if self.simulation.t_column else None

    @computed_field
    @property
    def zcolumn(self) -> str | None:
        return f'"{self.simulation.z_column}"' if self.simulation.z_column else None

    @computed_field
    @property
    def wxcolumn(self) -> str | None:
        return f'"{self.simulation.wx_column}"' if self.simulation.wx_column else None

    @computed_field
    @property
    def wycolumn(self) -> str | None:
        return f'"{self.simulation.wy_column}"' if self.simulation.wy_column else None

    @computed_field
    @property
    def wzcolumn(self) -> str | None:
        return f'"{self.simulation.wz_column}"' if self.simulation.wz_column else None


    def set_wakefield_column_names(self, wakefield_file_name: str) -> None:
        """
        Set the column names for the wakefield file, based on `wakefield_definition.

        Parameters
        ----------
        wakefield_file_name: str
            Name of the wakefield file
        """
        if all([x is not None for x in [self.wxcolumn, self.wycolumn, self.wzcolumn]]):
            self.wakefile = '"' + wakefield_file_name + '"'
            return
        elif self.wzcolumn is not None and all([x is None for x in [self.wxcolumn, self.wycolumn]]):
            self.zwakefile = '"' + wakefield_file_name + '"'
            return
        elif self.wzcolumn is None and all([x is not None for x in [self.wxcolumn, self.wycolumn]]):
            self.trwakefile = '"' + wakefield_file_name + '"'
            return

    def to_elegant(self) -> str:
        """
        Writes the cavity element string for ELEGANT.

        Returns
        -------
        str
            String representation of the element for ELEGANT
        """
        self.start_write()
        wholestring = ""
        etype = self._convertType_Elegant(self.hardware_type)
        if (
                self.simulation.wakefield_definition is None or
                self.simulation.wakefield_definition == ""
        ):
            etype = "rfca"
            if self.simulation.field_definition is not None:
                etype = "rftmez0"
                if ".sdds" not in self.simulation.field_definition:
                    field_file_name = self.generate_field_file_name(
                    self.simulation.field_definition, code="elegant"
                )
        else:
            wakefield_file_name = self.generate_field_file_name(
                self.simulation.wakefield_definition, code="elegant"
            )
            self.set_wakefield_column_names(wakefield_file_name)
        string = self.name + ": " + etype
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Elegant(key, updated_type=self.hardware_type) in elements_Elegant[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Elegant(key, updated_type=self.hardware_type).lower()
                    # rftmez0 uses frequency instead of freq
                    if etype == "rftmez0" and key == "freq":
                        key = "frequency"

                    if self.hardware_type in ["RFCavity", "RFDeflectingCavity"]:
                        if key == "phase":
                            if etype == "rftmez0":
                                # If using rftmez0 or similar
                                value = (value / 360.0) * (2 * 3.14159)
                            else:
                                # In ELEGANT all phases are +90degrees!!
                                value = 90 - value

                    # In ELEGANT the voltages need to be compensated
                    if key == "volt":
                        if self.structure_type == "TravellingWave":
                            value = abs(
                                (self.get_cells() + 3.8)
                                * self.cavity.cell_length
                                * (1 / np.sqrt(2))
                                * value
                            )
                        else:
                            value = value
                    # If using rftmez0 or similar
                    if key == "ez_peak":
                        value = abs(1e-3 / (np.sqrt(2)) * value)

                    if key == "wakefile":
                        value = value

                    # In CAVITY NKICK = n_cells
                    if key == "n_kicks" and self.get_cells() > 1:
                        value = 3 * self.get_cells()

                    if key == "n_bins" and value > 0:
                        print(
                            "WARNING: Cavity n_bins is not zero - check log file to ensure correct behaviour!"
                        )
                    value = 1 if value is True else value
                    value = 0 if value is False else value
                    # print("elegant cavity", key, value)
                    tmpstring = ", " + key + " = " + str(value)
                # if len(string + tmpstring) > 156:
                #     wholestring += string + ",&\n"
                #     print(wholestring)
                #     string = ""
                #     string += tmpstring[2::]
                # else:
                    string += tmpstring
        wholestring += string + ";\n"
        return wholestring

    def to_ocelot(self) -> object:
        """
        Creates the cavity element for Ocelot.

        Returns
        -------
        tuple
            Ocelot Cavity object
        """
        from ..conversion_rules.codes import ocelot_conversion

        type_conversion_rules_Ocelot = ocelot_conversion.ocelot_conversion_rules
        self.start_write()
        self.generate_field_file_name(
            self.simulation.wakefield_definition, code="astra"
        )
        obj = type_conversion_rules_Ocelot[self.hardware_type](eid=self.name)
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Ocelot(key) in obj.__class__().element.__dict__
            ):
                if value:
                    key = self._convertKeyword_Ocelot(key).lower()
                    if self.hardware_type in ["RFCavity", "RFDeflectingCavity"]:
                        if key == "v":
                            if self.structure_type == "TravellingWave":
                                value = (
                                        value
                                        * 1e-9
                                        * abs(
                                    (self.get_cells() + 3.8)
                                    * self.cavity.cell_length
                                    * (1 / np.sqrt(2))
                                )
                                )
                            else:
                                value = value * 1e-9
                    setattr(obj, key, value)
        return obj

    def to_cheetah(self) -> object:
        """
        Creates the cavity element for Cheetah.

        Returns
        -------
        tuple
            Cheetah Cavity object
        """
        from ..conversion_rules.codes import cheetah_conversion
        from torch import tensor, float64

        type_conversion_rules_Cheetah = cheetah_conversion.cheetah_conversion_rules
        self.start_write()
        obj = type_conversion_rules_Cheetah[self.hardware_type](
            name=self.name,
            length=tensor(self.physical.length, dtype=float64),
            sanitize_name=True
        )
        buffers = obj.__class__(length=tensor(self.physical.length, dtype=float64))._buffers
        for key, value in self.full_dump().items():
            if (key not in ["name", "type", "commandtype"]) and (
                    self._convertKeyword_Cheetah(key) in buffers
            ):
                key = self._convertKeyword_Cheetah(key)
                value = (
                    getattr(self, key)
                    if hasattr(self, key) and getattr(self, key) is not None
                    else value
                )
                if key == "voltage":
                    if self.structure_type == "TravellingWave":
                        value = (
                                value
                                * abs(
                            (self.get_cells() + 5.5)
                            * self.cavity.cell_length
                            * (1 / np.sqrt(2))
                        )
                        )
                    else:
                        value = value
                if isinstance(value, float):
                    dt = float64
                    setattr(obj, self._convertKeyword_Cheetah(key), tensor(value, dtype=dt))
                elif isinstance(value, int):
                    from torch import int64
                    dt = int64
                    setattr(obj, self._convertKeyword_Cheetah(key), tensor(value, dtype=dt))
        return obj

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the cavity element string for ASTRA.

        Parameters
        ----------
        n: int
            Element index number
        **kwargs: dict
            Keyword args

        Returns
        -------
        str
            String representation of the element for ASTRA
        """
        self.start_write()
        field_ref_pos = self.get_field_reference_position()
        auto_phase = kwargs["auto_phase"] if "auto_phase" in kwargs else True
        crest = self.cavity.crest if not auto_phase else 0
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="astra"
        )
        efield_def = [
            "FILE_EFieLD",
            {"value": "'" + field_file_name + "'", "default": ""},
        ]
        return self._write_ASTRA_dictionary(
            dict(
                [
                    ["C_pos", {"value": field_ref_pos[2] + self.dz, "default": 0}],
                    efield_def,
                    ["C_numb", {"value": self.get_cells()}],
                    ["Nue", {"value": float(self.cavity.frequency) / 1e9, "default": 2998.5}],
                    [
                        "MaxE",
                        {"value": float(self.simulation.field_amplitude) / 1e6, "default": 0},
                    ],
                    ["Phi", {"value": crest - self.cavity.phase, "default": 0.0}],
                    ["C_smooth", {"value": self.simulation.smooth, "default": None}],
                    [
                        "C_xoff",
                        {
                            "value": field_ref_pos[0] + self.dx,
                            "default": None,
                            "type": "not_zero",
                        },
                    ],
                    [
                        "C_yoff",
                        {
                            "value": field_ref_pos[1] + self.dy,
                            "default": None,
                            "type": "not_zero",
                        },
                    ],
                    [
                        "C_xrot",
                        {
                            "value": self.x_rot + self.dx_rot,
                            "default": None,
                            "type": "not_zero",
                        },
                    ],
                    [
                        "C_yrot",
                        {
                            "value": self.y_rot + self.dy_rot,
                            "default": None,
                            "type": "not_zero",
                        },
                    ],
                    [
                        "C_zrot",
                        {
                            "value": self.z_rot + self.dz_rot,
                            "default": None,
                            "type": "not_zero",
                        },
                    ],
                ]
            ),
            n,
        )

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
        for key, value in self.full_dump().items():
            if (key not in ["name", "type", "commandtype"]) and (
                    self._convertKeyword_Xsuite(key) in key in list(obj.__dict__.keys())
            ):
                key = self._convertKeyword_Xsuite(key)
                if key == "phase":
                    value = 90 - value
                if key == "field_amplitude":
                    if self.structure_type == "TravellingWave":
                        value = (
                            value
                            * abs(
                                (self.get_cells() + 3.8)
                                * self.cavity.cell_length
                                * (1 / np.sqrt(2))
                            )
                        )
                    else:
                        value = value
                if key == "n_kicks" and self.get_cells() > 1:
                    value = 3 * self.get_cells()
                properties.update({key: value})
        return self.name, obj, properties

    def to_opal(self, sval: float, designenergy: float | None = None) -> str:
        """
        Generates a string representation of the object's properties in the OPAL format.

        Parameters
        ----------
        sval: float
            S-position of the element
        designenergy: float, optional
            Beam energy at element in MeV

        Returns
        -------
        str
            A formatted string representing the object's properties in OPAL format.
        """
        self.start_write()
        etype = self._convertType_Opal(self.hardware_type)
        if self.structure_type == "TravellingWave":
            etype = "travelingwave"
        wholestring = self.name.replace('-', '_') + ": " + etype
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="opal"
        )
        if etype.lower() == "drift" or self.simulation.field_definition is None:
            return ""
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Opal(key) in elements_Opal[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Opal(key)
                    if key == "lag":
                        value = -value * np.pi / 180
                    if key == "freq":
                        value = value / 1e6
                    if key == "volt":
                        value = value / 1e6
                    val = 1 if value is True else value
                    val = 0 if value is False else val
                    if val is not None:
                        tmpstring = ", " + key + " = " + str(val)
                        wholestring += tmpstring
        if isinstance(self.simulation.field_definition, field):
            wholestring += ", fmapfn = \"" + self.generate_field_file_name(
                self.simulation.field_definition, code="opal"
            ) + "\""
            if self.structure_type == "TravellingWave":
                mode = float(self.simulation.field_definition.mode_numerator) / float(
                    self.simulation.field_definition.mode_denominator)
                wholestring += f", mode = {mode}"
        wholestring += f", ELEMEDGE = {sval};\n"
        return wholestring

    def get_cells(self) -> int:
        """
        Get the number of cavity cells.

        Returns
        -------
        int or None
            The number of cavity cells, or None if not defined.
        """
        if (self.cavity.n_cells == 0 or self.cavity.n_cells is None) and self.cavity.cell_length > 0:
            cells = round((self.physical.length - self.cavity.cell_length) / self.cavity.cell_length)
            cells = int(cells - (cells % 3))
        elif self.cavity.n_cells:
            if self.cavity.cell_length == self.physical.length:
                cells = 1
            else:
                cells = int(self.cavity.n_cells - (self.cavity.n_cells % 3))
        else:
            cells = 0
        return cells

    def to_gpt(self, Brho: float=0.0, ccs: str = "wcs", *args, **kwargs) -> str:
        """
        Write a string representation of the cavity for GPT

        #TODO note that not all possible ways of writing a cavity in GPT are currently supported.

        Parameters
        ----------
        Brho: float
            Magnetic rigidity; not used
        ccs: str
            Name of co-ordinate system of the cavity

        Returns
        -------
        str
            String representation of the cavity for GPT.
        """
        self.start_write()
        field_ref_pos = self.get_field_reference_position()
        ccs_label, value_text = self.ccs.ccs_text(field_ref_pos, self.physical.rotation.model_dump())
        relpos, _ = self.ccs.relative_position(field_ref_pos, self.physical.global_rotation.model_dump())
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="gpt"
        )
        self.generate_field_file_name(self.simulation.wakefield_definition, code="gpt")
        """
        map1D_TM("wcs","z",linacposition,"mockup2m.gdf","Z","Ez",ffacl,phil,w);
        wakefield("wcs","z",  6.78904 + 4.06667 / 2, 4.06667, 50, "Sz5um10mm.gdf", "z","","","Wz", "FieldFactorWz", 10 * 122 / 4.06667) ;
        """
        subname = str(relpos[2]).replace(".", "")
        output = ""
        if field_file_name is not None:
            output = (
                    "f"
                    + subname
                    + " = "
                    + str(self.cavity.frequency)
                    + ";\n"
                    + "w"
                    + subname
                    + " = 2*pi*f"
                    + subname
                    + ";\n"
                    + "phi"
                    + subname
                    + " = "
                    + str((self.cavity.crest + 90 - self.cavity.phase + 0) % 360.0)
                    + "/deg;\n"
            )
            if self.structure_type == "TravellingWave":
                output += (
                        "ffac"
                        + subname
                        + " = 1.007 * "
                        + str((9.0 / (2.0 * np.pi)) * self.simulation.field_amplitude)
                        + ";\n"
                )
            else:
                output += "ffac" + subname + " = " + str(self.simulation.field_amplitude) + ";\n"

            # if False and self.Structure_Type == 'TravellingWave' and hasattr(self, 'attenuation_constant') and hasattr(self, 'shunt_impedance') and hasattr(self, 'design_power') and hasattr(self, 'design_gamma'):
            #     '''
            #     trwlinac(ECS,ao,Rs,Po,P,Go,thetao,phi,w,L)
            #     '''
            #     relpos, relrot = ccs.relative_position(self.middle, self.global_rotation)
            #     power = float(self.field_amplitude) / 25e6 * float(self.design_power)
            #     output += 'trwlinac' + '( ' + ccs.name + ', "z", '+ str(relpos[2]+self.coupling_cell_length) + ', ' + str(self.attenuation_constant / self.length) + ', ' + str(float(self.shunt_impedance) / self.length)\
            #             + ', ' + str(float(self.design_power) / self.length) + ', ' + str(power / self.length) + ', ' + str(1000/0.511) + ', ' + str(self.crest)\
            #             + ', '+str(self.phase)+', w'+subname+', ' + str(self.length) + ');\n'
            # else:
            output += (
                    "map1D_TM"
                    + "(\""
                    + self.ccs.name
                    + "\", "
                    + ccs_label
                    + ", "
                    + value_text
                    + ', "'
                    + str(field_file_name)
                    + '", "z", "Ez", ffac'
                    + subname
                    + ", phi"
                    + subname
                    + ", w"
                    + subname
                    + ");\n"
            )
        else:
            output = ""
        return output

