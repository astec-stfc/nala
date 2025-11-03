from pydantic import computed_field
from warnings import warn
from .base import BaseElementTranslator
from nala.models.magnetic import MagneticElement, Solenoid_Magnet, Dipole_Magnet, Wiggler_Magnet
from nala.models.simulation import MagnetSimulationElement
from ..utils.functions import _rotation_matrix, chop, expand_substitution
import numpy as np
from .codes.gpt import gpt_ccs
from nala.translator.utils.fields import field
from ..converters import (
    elements_Genesis,
    elements_Opal,
)

def add(x, y):
    return x + y

class MagnetTranslator(BaseElementTranslator):
    magnetic: MagneticElement

    simulation: MagnetSimulationElement

    @computed_field
    @property
    def k1(self) -> float:
        try:
            return self.magnetic.KnL(1) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k1 = k1l")
            return self.magnetic.KnL(1)

    @computed_field
    @property
    def k2(self) -> float:
        try:
            return self.magnetic.KnL(2) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k2 = k2l")
            return self.magnetic.KnL(2)

    @computed_field
    @property
    def k3(self) -> float:
        try:
            return self.magnetic.KnL(3) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k3 = k3l")
            return self.magnetic.KnL(3)

    @property
    def k1l(self) -> float:
        return self.magnetic.KnL(1)

    @k1l.setter
    def k1l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K1L"), "normal", value)

    @property
    def k2l(self) -> float:
        return self.magnetic.KnL(2)

    @k2l.setter
    def k2l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K2L"), "normal", value)

    @property
    def k3l(self) -> float:
        return self.magnetic.KnL(3)

    @k3l.setter
    def k3l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K3L"), "normal", value)

    # TODO relate these to systematic_ and random_multipoles
    @computed_field
    @property
    def dk1(self) -> float:
        return 0.0

    @computed_field
    @property
    def dk2(self) -> float:
        return 0.0

    @computed_field
    @property
    def dk3(self) -> float:
        return 0.0

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the quadrupole element string for ASTRA.

        Note that in astra `Q_xrot` means a rotation about the y-axis and vice versa.

        Parameters
        ----------
        n: int
            Dipole index

        Returns
        -------
        str or None
            String representation of the element for ASTRA, or None if quadrupole strength is zero
        """
        self.start_write()
        if self.hardware_type.lower() == "quadrupole":
            return self._write_ASTRA_quadrupole(n, **kwargs)
        else:
            warn(f"Element type {self.hardware_type} of {self.name} not supported by ASTRA")
            return ""

    def to_csrtrack(self, n: int = 0) -> str:
        """
        Writes the quadrupole element string for CSRTrack.

        Parameters
        ----------
        n: int
            Marker index

        Returns
        -------
        str
            String representation of the element for CSRTrack
        """
        self.start_write()
        if self.hardware_type.lower() == "quadrupole":
            return self._write_CSRTrack_quadrupole(n)
        else:
            warn(f"Element type {self.hardware_type} of {self.name} not supported by CSRTrack")
            return ""

    def _write_ASTRA_quadrupole(self, n: int = 0, **kwargs: dict) -> str:
        field_ref_pos = self.get_field_reference_position()
        astradict = dict(
            [
                ["Q_pos", {"value": field_ref_pos[2] + self.dz, "default": 0}],
                [
                    "Q_xoff",
                    {"value": field_ref_pos[0], "default": 0, "type": "not_zero"},
                ],
                [
                    "Q_yoff",
                    {
                        "value": field_ref_pos[1] + self.dy,
                        "default": None,
                        "type": "not_zero",
                    },
                ],
                [
                    "Q_xrot",
                    {
                        "value": -1 * self.x_rot + self.dx_rot,
                        "default": None,
                        "type": "not_zero",
                    },
                ],
                [
                    "Q_yrot",
                    {
                        "value": -1 * self.y_rot + self.dy_rot,
                        "default": None,
                        "type": "not_zero",
                    },
                ],
                [
                    "Q_zrot",
                    {
                        "value": -1 * self.z_rot + self.dz_rot,
                        "default": None,
                        "type": "not_zero",
                    },
                ],
                ["Q_smooth", {"value": self.simulation.smooth, "default": None}],
                ["Q_bore", {"value": self.magnetic.bore, "default": 0.037, "type": "not_zero"}],
                ["Q_noscale", {"value": self.simulation.scale_field}],
                # TODO figure out multipoles
                # ["Q_mult_a", {"type": "list", "value": self.multipoles}],
            ]
        )
        dict_ready = False
        if self.simulation.field_definition and "momentum" in kwargs:
            field_file_name = self.generate_field_file_name(
                self.simulation.field_definition, code="astra"
            )
            astradict.update(
                dict(
                    [
                        [
                            "Q_type",
                            {"value": "'" + field_file_name + "'", "default": None},
                        ],
                        ["q_grad", {"value": self.magnetic.gradient(kwargs["momentum"]), "default": None}],
                    ]
                )
            )
            dict_ready = True
        elif abs(self.k1 + self.dk1) > 0:
            astradict.update(
                dict(
                    [
                        ["Q_k", {"value": self.k1 + self.dk1, "default": 0}],
                        ["Q_length", {"value": self.magnetic.length, "default": 0}],
                    ]
                )
            )
            dict_ready = True
        if dict_ready:
            return self._write_ASTRA_dictionary(astradict, n)
        else:
            return ""

    def _write_CSRTrack(self, n: int) -> str:
        """
        Writes the screen element string for CSRTrack.

        Parameters
        ----------
        n: int
            Modulator index

        Returns
        -------
        str
            String representation of the element for CSRTrack
        """
        z = self.physical.middle.z
        return (
            """quadrupole{\nposition{rho="""
            + str(z)
            + """, psi=0.0, marker=quad"""
            + str(n)
            + """a}\nproperties{strength="""
            + str(self.magnetic.k1l)
            + """, alpha=0, horizontal_offset=0,vertical_offset=0}\nposition{rho="""
            + str(z + self.physical.length)
            + """, psi=0.0, marker=quad"""
            + str(n)
            + """b}\n}\n"""
        )

    def to_gpt(self, Brho: float = 0, ccs: str="wcs", *args, **kwargs) -> str:
        self.start_write()
        ccs_label, value_text = self.ccs.ccs_text(
            self.physical.middle.model_dump(), self.physical.rotation.model_dump(),
        )
        knl = self.magnetic.KnL()
        if self.hardware_type.lower() == "sextupole":
            knl = knl / 2
        output = (
                str(self.hardware_type.lower())
                + "( "
                + ccs
                + ", "
                + ccs_label
                + ", "
                + value_text
                + ", "
                + str(self.magnetic.length)
                + ", "
                + str(-Brho * knl)
                + ");\n"
        )
        return output


class DipoleTranslator(BaseElementTranslator):
    magnetic: Dipole_Magnet

    simulation: MagnetSimulationElement

    @computed_field
    @property
    def angle(self) -> float:
        return self.magnetic.KnL(0)

    @computed_field
    @property
    def k1(self) -> float:
        try:
            return self.magnetic.KnL(1) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k1 = k1l")
            return self.magnetic.KnL(1)

    @computed_field
    @property
    def k2(self) -> float:
        try:
            return self.magnetic.KnL(2) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k2 = k2l")
            return self.magnetic.KnL(2)

    @computed_field
    @property
    def k3(self) -> float:
        try:
            return self.magnetic.KnL(3) / self.magnetic.length
        except ZeroDivisionError:
            warn("Magnet has zero length; returning k3 = k3l")
            return self.magnetic.KnL(3)

    @property
    def k1l(self) -> float:
        return self.magnetic.KnL(1)

    @k1l.setter
    def k1l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K1L"), "normal", value)

    @property
    def k2l(self) -> float:
        return self.magnetic.KnL(2)

    @k2l.setter
    def k2l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K2L"), "normal", value)

    @property
    def k3l(self) -> float:
        return self.magnetic.KnL(3)

    @k3l.setter
    def k3l(self, value: float) -> None:
        setattr(getattr(self.magnetic.multipoles, "K3L"), "normal", value)

    # TODO relate these to systematic_ and random_multipoles
    @computed_field
    @property
    def dk1(self) -> float:
        return 0.0

    @computed_field
    @property
    def dk2(self) -> float:
        return 0.0

    @computed_field
    @property
    def dk3(self) -> float:
        return 0.0

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the quadrupole element string for ASTRA.

        Note that in astra `Q_xrot` means a rotation about the y-axis and vice versa.

        Parameters
        ----------
        n: int
            Dipole index

        Returns
        -------
        str or None
            String representation of the element for ASTRA, or None if quadrupole strength is zero
        """
        self.start_write()
        return self._write_ASTRA_dipole(n, **kwargs)

    def _write_ASTRA_dipole(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the dipole element string for ASTRA.

        Parameters
        ----------
        n: int
            Dipole index

        Returns
        -------
        str or None
            String representation of the element for ASTRA, or None if dipole strength is zero
        """
        field_strength = 0
        if "momentum" in kwargs:
            field_strength = self.magnetic.field_strength(kwargs["momentum"])
        if field_strength > 0 or abs(self.magnetic.rho) > 0:
            corners = self.corners
            params = dict(
                [
                    [
                        "D_Type",
                        {"value": "'" + self.magnetic.plane + "'", "default": "'horizontal'"},
                    ],
                    [
                        "D_Gap",
                        {
                            "type": "list",
                            "value": [self.magnetic.gap, self.magnetic.gap],
                            "default": [0.0001, 0.0001],
                        },
                    ],
                    ["D1", {"type": "array", "value": [corners[3][0], corners[3][2]]}],
                    ["D3", {"type": "array", "value": [corners[2][0], corners[2][2]]}],
                    ["D4", {"type": "array", "value": [corners[1][0], corners[1][2]]}],
                    ["D2", {"type": "array", "value": [corners[0][0], corners[0][2]]}],
                    ["D_zrot", {"value": self.z_rot + self.dz_rot, "default": 0}],
                ]
            )
            if field_strength > 0 or not abs(self.magnetic.rho) > 0:
                params["D_strength"] = {
                    "value": field_strength,
                    "default": 1e6,
                }
            else:
                params["D_radius"] = {"value": 1 * self.magnetic.rho, "default": 1e6}
            return self._write_ASTRA_dictionary(params, n)
        else:
            return ""

    @property
    def corners(self) -> list[np.ndarray]:
        """
        Get the corner positions of the dipole for ASTRA.

        Returns
        -------
        np.ndarray
            Dipole corner positions
        """
        corners = [0, 0, 0, 0]
        rotation = self.physical.global_rotation.theta
        theta = self.e1 + rotation
        corners[0] = np.array(
            list(
                map(
                    add,
                    np.transpose([getattr(self.physical.start, p) for p in ["x", "y", "z"]]),
                    np.dot([-self.magnetic.width * self.magnetic.length, 0, 0], _rotation_matrix(theta)),
                )
            )
        )
        corners[3] = np.array(
            list(
                map(
                    add,
                    np.transpose([getattr(self.physical.start, p) for p in ["x", "y", "z"]]),
                    np.dot([self.magnetic.width * self.magnetic.length, 0, 0], _rotation_matrix(theta)),
                )
            )
        )
        theta = self.magnetic.angle - self.e2 + rotation
        corners[1] = np.array(
            list(
                map(
                    add,
                    np.transpose([getattr(self.physical.end, p) for p in ["x", "y", "z"]]),
                    np.dot([-self.magnetic.width * self.magnetic.length, 0, 0], _rotation_matrix(theta)),
                )
            )
        )
        corners[2] = np.array(
            list(
                map(
                    add,
                    np.transpose([getattr(self.physical.end, p) for p in ["x", "y", "z"]]),
                    np.dot([self.magnetic.width * self.magnetic.length, 0, 0], _rotation_matrix(theta)),
                )
            )
        )
        return corners

    @computed_field
    @property
    def e1(self) -> float:
        """
        Get the dipole entrance edge angle.

        Returns
        -------
        float
            The dipole entrance edge angle.
        """
        if isinstance(self.magnetic.entrance_edge_angle, str):
            if "angle" in self.magnetic.entrance_edge_angle:
                return eval(self.magnetic.entrance_edge_angle, {}, {"angle": self.magnetic.angle})
            warn(f"Could not determine the value of entrance_edge_angle for {self.name}; returning 0")
            return 0
        return self.magnetic.entrance_edge_angle

    @computed_field
    @property
    def e2(self) -> float:
        """
        Get the dipole exit edge angle.

        Returns
        -------
        float
            The dipole exit edge angle.
        """
        if isinstance(self.magnetic.exit_edge_angle, str):
            if "angle" in self.magnetic.exit_edge_angle:
                return eval(self.magnetic.exit_edge_angle, {}, {"angle": self.magnetic.angle})
            warn(f"Could not determine the value of exit_edge_angle for {self.name}; returning 0")
            return 0
        return self.magnetic.exit_edge_angle

    @property
    def intersect(self) -> float:
        return self.magnetic.length * np.tan(0.5 * self.magnetic.angle) / self.magnetic.angle

    def to_csrtrack(self, n: int = 0, **kwargs) -> str:
        """
        Writes the dipole element string for CSRTrack.

        Parameters
        ----------
        n: int
            Marker index

        Returns
        -------
        str
            String representation of the element for CSRTrack
        """
        z1 = self.physical.start.z
        z2 = self.physical.end.z
        return (
            """dipole{\nposition{rho="""
            + str(z1)
            + """, psi="""
            + str(chop(self.physical.rotation.theta + self.e1))
            + """, marker=d"""
            + str(n)
            + """a}\nproperties{r="""
            + str(self.magnetic.rho)
            + """}\nposition{rho="""
            + str(z2)
            + """, psi="""
            + str(chop(self.physical.rotation.theta + self.e2))
            + """, marker=d"""
            + str(n)
            + """b}\n}\n"""
        )

    def to_gpt(self, Brho: float = 0.0, ccs: str = "wcs", *args, **kwargs) -> str:
        self.start_write()
        field = 1.0 * self.magnetic.angle * Brho / self.magnetic.length
        if abs(field) > 0 and abs(self.rho) < 100:
            relpos, relrot = self.ccs.relative_position(
                self.physical.middle.model_dump(),
                self.physical.global_rotation.model_dump(),
            )
            coord = self.ccs.gpt_coordinates(relpos, relrot)
            new_ccs = self.new_ccs(self.ccs)
            b1 = np.round(
                (
                    1.0
                    / (
                            2
                            * self.magnetic.half_gap
                            * self.magnetic.edge_field_integral
                    )
                    if self.half_gap > 0
                    else 10000
                ),
                2,
            )
            dl = self.simulation.deltaL
            e1 = self.magnetic.entrance_edge_angle
            e2 = self.magnetic.exit_edge_angle
            # print(self.objectname, ' - deltaL = ', dl)
            # b1 = 0.
            """
            ccs( "wcs", 0, 0, startofdipole +  intersect1, Cos(theta), 0, -Sin(theta), 0, 1, 0, "bend1" ) ;
            sectormagnet( "wcs", "bend1", rho, field, e1, e2, 0., 100., 0 ) ;
            """
            output = "ccs( " + self.ccs.name + ", " + coord + ", " + new_ccs.name + ");\n"
            output += (
                    "sectormagnet( "
                    + self.ccs.name
                    + ", "
                    + new_ccs.name
                    + ", "
                    + str(abs(self.magnetic.rho))
                    + ", "
                    + str(abs(field))
                    + ", "
                    + str(e1)
                    + ", "
                    + str(e2)
                    + ", "
                    + str(dl)
                    + ", "
                    + str(b1)
                    + ", 0);\n"
            )
            self.ccs = new_ccs
        else:
            output = ""
        return output

    def new_ccs(self, ccs: gpt_ccs) -> gpt_ccs:
        if abs(self.magnetic.angle) > 0 and abs(self.magnetic.rho) < 100:
            # print('Creating new CCS')
            number = (
                str(int(ccs.name.split("_")[1]) + 1) if ccs.name != "wcs" else "1"
            )
            name = "ccs_" + number if ccs.name != "wcs" else "ccs_1"
            # print('middle position = ', self.start, self.middle)
            return gpt_ccs(
                name=name,
                position=self.physical.middle.model_dump(),
                rotation=list(self.physical.global_rotation.model_dump() + np.array([0, 0, -self.magnetic.angle])),
                intersect=0 * abs(self.intersect),
            )
        else:
            return ccs

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
        # wholestring = ""
        self.start_write()
        etype = self._convertType_Opal(self.hardware_type)
        if self.entrance_edge_angle == self.exit_edge_angle:
            etype = "sbend"
        wholestring = self.name.replace('-', '_') + ": " + etype
        if etype.lower() == "drift" or self.physical.length == 0 or self.magnetic.angle == 0:
            return ""
        keys = []
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Opal(key) in elements_Opal[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Opal(key)
                    if value == "angle":
                        value = self.magnetic.angle
                    elif value == "angle/2":
                        value = self.magnetic.angle / 2
                    elif key in ["k1", "k2", "k3", "k4", "k5", "k6"]:
                        value = getattr(self, f"{key}l")
                    val = 1 if value is True else value
                    val = 0 if value is False else val
                    tmpstring = ", " + key + " = " + str(val)
                    if key not in keys:
                        wholestring += tmpstring
                        keys.append(key)
        if etype == "monitor":
            wholestring += f", OUTFN = \"{self.name}_opal\""
        wholestring += f", DESIGNENERGY = {designenergy}"
        wholestring += f", ELEMEDGE = {sval}"
        wholestring += f", FMAPFN = \"1DPROFILE1-DEFAULT\";\n"
        return wholestring

    #
    # @computed_field
    # @property
    # def entrance_edge_angle(self) -> float:
    #     if self.magnetic.entrance_edge_angle == "angle":
    #         return self.magnetic.angle
    #     elif self.magnetic.entrance_edge_angle == "angle/2":
    #         return self.magnetic.angle / 2.0
    #     return self.magnetic.entrance_edge_angle
    #
    # @computed_field
    # @property
    # def exit_edge_angle(self) -> float:
    #     if self.magnetic.exit_edge_angle == "angle":
    #         return self.magnetic.angle
    #     elif self.magnetic.exit_edge_angle == "angle/2":
    #         return self.magnetic.angle / 2.0
    #     return self.magnetic.exit_edge_angle


class SolenoidTranslator(BaseElementTranslator):
    magnetic: Solenoid_Magnet

    simulation: MagnetSimulationElement

    @computed_field
    @property
    def ks(self) -> float:
        return self.magnetic.ks

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the quadrupole element string for ASTRA.

        Note that in astra `Q_xrot` means a rotation about the y-axis and vice versa.

        Parameters
        ----------
        n: int
            Dipole index

        Returns
        -------
        str or None
            String representation of the element for ASTRA, or None if quadrupole strength is zero
        """
        self.start_write()
        return self._write_ASTRA_solenoid(n, **kwargs)

    def _write_ASTRA_solenoid(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the solenoid element string for ASTRA.

        Note that in astra `S_xrot` means a rotation about the y-axis and vice versa.

        Parameters
        ----------
        n: int
            Solenoid index

        Returns
        -------
        str
            String representation of the element for ASTRA
        """
        field_ref_pos = self.get_field_reference_position()
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="astra"
        )
        if not isinstance(field_file_name, str):
            raise NotImplementedError(f"ASTRA solenoids require fieldmaps; see element {self.name}")
        efield_def = [
            "FILE_BFieLD",
            {"value": "'" + field_file_name + "'", "default": ""},
        ]
        return self._write_ASTRA_dictionary(
            dict(
                [
                    ["S_pos", {"value": field_ref_pos[2] + self.dz, "default": 0}],
                    efield_def,
                    ["MaxB", {"value": self.get_field_amplitude / self.magnetic.length, "default": 0}],
                    ["S_smooth", {"value": self.simulation.smooth, "default": 10}],
                    ["S_xoff", {"value": field_ref_pos[0] + self.dx, "default": 0}],
                    ["S_yoff", {"value": field_ref_pos[1] + self.dy, "default": 0}],
                    ["S_xrot", {"value": self.x_rot + self.dx_rot, "default": 0}],
                    ["S_yrot", {"value": self.y_rot + self.dy_rot, "default": 0}],
                ]
            ),
            n,
        )

    def to_gpt(self, Brho: float = 0.0, ccs: str = "wcs", *args, **kwargs) -> str:
        self.start_write()
        field_ref_pos = self.get_field_reference_position()
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="gpt"
        )
        ccs_label, value_text = self.ccs.ccs_text(field_ref_pos, self.physical.rotation.model_dump())
        if self.simulation.field_definition.field_type.lower() == "1dmagnetostatic":
            array_names = ["z", "Bz"]
            array_names_string = ", ".join(['"' + name + '"' for name in array_names])
            """
            map1D_B("wcs",xOffset,0,zOffset+0.,cos(angle),0,-sin(angle),0,1,0,"bas_sol_norm.gdf","Z","Bz",gunSolField);
            """
            output = (
                    "map1D_B"
                    + "( "
                    + ccs
                    + ", "
                    + ccs_label
                    + ", "
                    + value_text
                    + ", "
                    + '"'
                    + str(field_file_name)
                    + '", '
                    + array_names_string
                    + ", "
                    + str(expand_substitution(self, self.get_field_amplitude))
                    + ");\n"
            )
        elif self.simulation.field_definition.field_type.lower() == "3dmagnetostatic":
            array_names = ["x", "y", "z", "Bx", "By", "Bz"]
            array_names_string = ", ".join(['"' + name + '"' for name in array_names])
            """
            map3D_B("wcs", xOffset,0,zOffset+0.,cos(angle),0,-sin(angle),0,1,0, "sol3.gdf", "x", "y", "z", "Bx", "By", "Bz", scale3);
            """
            output = (
                    "map3D_B"
                    + "( "
                    + ccs
                    + ", "
                    + ccs_label
                    + ", "
                    + value_text
                    + ", "
                    + '"'
                    + str(field_file_name)
                    + '", '
                    + array_names_string
                    + ", "
                    + str(expand_substitution(self, self.get_field_amplitude))
                    + ");\n"
            )
        else:
            raise ValueError(f"Solenoid field type {self.field_type} not supported for GPT; see {self.name}")
        return output

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
        wholestring = self.name.replace('-', '_') + ": " + etype
        field_file_name = self.generate_field_file_name(
            self.simulation.field_definition, code="opal"
        )
        keys = []
        for key, value in self.full_dump().items():
            if (
                    not key == "name"
                    and not key == "type"
                    and not key == "commandtype"
                    and self._convertKeyword_Opal(key) in elements_Opal[etype]
            ):
                if value is not None:
                    key = self._convertKeyword_Opal(key)
                    val = 1 if value is True else value
                    val = 0 if value is False else val
                    if key == "ks":
                        val = self.magnetic.field_amplitude / self.magnetic.length
                    if val is not None and key not in keys:
                        tmpstring = ", " + key + " = " + str(val)
                        wholestring += tmpstring
                        keys.append(key)
        if isinstance(self.simulation.field_definition, field):
            wholestring += ", fmapfn = \"" + self.generate_field_file_name(
                self.simulation.field_definition, code="opal"
            ) + "\""
        wholestring += f", ELEMEDGE = {sval};\n"
        return wholestring


class WigglerTranslator(BaseElementTranslator):
    magnetic: Wiggler_Magnet

    simulation: MagnetSimulationElement

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
                    key = self._convertKeyword_Genesis(key)
                    if key == "aw" and not self.magnetic.helical:
                        value *= np.sqrt(2)
                    value = 1 if value is True else value
                    value = 0 if value is False else value
                    if key not in keys:
                        string += key + " = " + str(value) + ', '
                    keys.append(key)
        wholestring += string[:-2] + "};\n"
        return wholestring