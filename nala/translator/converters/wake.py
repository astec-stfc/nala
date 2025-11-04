from .base import BaseElementTranslator
from nala.models.RF import WakefieldElement
from ..utils.fields import field

class WakefieldTranslator(BaseElementTranslator):
    cavity: WakefieldElement

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        self.start_write()
        return self._write_ASTRA(n=n)

    def _write_ASTRA(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the wakefield element string for ASTRA. Each cell in a cavity gets its own &WAKE element.

        Parameters
        ----------
        n: int
            Wake index

        Returns
        -------
        str
            String representation of the element for ASTRA
        """
        field_ref_pos = self.get_field_reference_position()
        field_file_name = self.generate_field_file_name(
            self.simulation.wakefield_definition, code="astra"
        )
        efield_def = [
            "Wk_filename",
            {"value": "'" + field_file_name + "'", "default": ""},
        ]
        output = ""
        if self.simulation.wakefield_definition.field_type == "LongitudinalWake":
            waketype = "Monopole_Method_F"
        elif self.simulation.wakefield_definition.field_type == "TransverseWake":
            waketype = "Dipole_Method_F"
        else:
            waketype = "Taylor_Method_F"
        if self.simulation.scale_kick > 0:
            for n in range(n, n + int(self.cavity.n_cells)):
                output += self._write_ASTRA_dictionary(
                    dict(
                        [
                            [
                                "Wk_Type",
                                {
                                    "value": '"' + waketype + '"',
                                    "default": "'Taylor_Method_F'",
                                },
                            ],
                            efield_def,
                            ["Wk_x", {"value": self.dx, "default": 0}],
                            ["Wk_y", {"value": self.dx, "default": 0}],
                            [
                                "Wk_z",
                                {
                                    "value": self.physical.start.z
                                             + (0.5 + n - 1) * self.cavity.cell_length
                                },
                            ],
                            ["Wk_ex", {"value": self.simulation.scale_field_ex, "default": 0}],
                            ["Wk_ey", {"value": self.simulation.scale_field_ey, "default": 0}],
                            ["Wk_ez", {"value": self.simulation.scale_field_ez, "default": 1}],
                            ["Wk_hx", {"value": self.simulation.scale_field_hx, "default": 1}],
                            ["Wk_hy", {"value": self.simulation.scale_field_hy, "default": 0}],
                            ["Wk_hz", {"value": self.simulation.scale_field_hz, "default": 0}],
                            [
                                "Wk_equi_grid",
                                {"value": self.simulation.equal_grid, "default": 0.66},
                            ],
                            ["Wk_N_bin", {"value": 10, "default": 100}],
                            [
                                "Wk_ip_method",
                                {"value": self.simulation.interpolation_method, "default": 2},
                            ],
                            ["Wk_smooth", {"value": self.simulation.smooth, "default": 0.25}],
                            ["Wk_sub", {"value": self.simulation.subbins, "default": 10}],
                            [
                                "Wk_scaling",
                                {"value": 1 * self.simulation.scale_kick, "default": 1},
                            ],
                        ]
                    ),
                    n,
                )
                output += "\n"
            output += "\n"
        return output

    def to_gpt(self, Brho: float = 0.0, ccs: str="wcs", *args, **kwargs) -> str:
        self.start_write()
        field_ref_pos = self.get_field_reference_position()
        field_file_name = self.generate_field_file_name(
            self.simulation.wakefield_definition, code="gpt"
        )
        fringe_field_coefficient = 3.0 / self.cavity.cell_length
        output = ""
        if self.simulation.scale_kick > 0:
            zcolumn = "z"
            wzcolumn = "Wz"
            wxcolumn = "Wx" if self.simulation.wakefield_definition.Wx.value is not None else ""
            wycolumn = "Wy" if self.simulation.wakefield_definition.Wy.value is not None else ""
            for n in range(self.cavity.n_cells):
                ccs_label, value_text = self.ccs.ccs_text(
                    [
                        field_ref_pos[0],
                        field_ref_pos[1],
                        field_ref_pos[2]
                        + self.cavity.coupling_cell_length
                        + n * self.cavity.cell_length,
                    ],
                    self.physical.rotation.model_dump(),
                )
                output += (
                        "wakefield"
                        + '("'
                        + self.ccs.name
                        + '", '
                        + ccs_label
                        + ", "
                        + value_text
                        + ", "
                        + str(self.cavity.cell_length)
                        + ", "
                        + str(fringe_field_coefficient)
                        + ', "'
                        + str(field_file_name)
                        + '", "'
                        + zcolumn
                        + '", "'
                        + wxcolumn
                        + '", "'
                        + wycolumn
                        + '", "'
                        + wzcolumn
                        + '");\n'
                )
        return output
