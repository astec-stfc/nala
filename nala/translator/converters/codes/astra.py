from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Any
import numpy as np
from ...utils.classes import getGrids

section_header_text_ASTRA = {
    "&APERTURE": "LApert",
    "&CAVITY": "LEField",
    "&SOLENOID": "LBField",
    "&QUADRUPOLE": "LQuad",
    "&DIPOLE": "LDipole",
    "&WAKE": "LWAKE",
}

class astra_header(BaseModel):
    """
    Generic class for generating ASTRA namelists
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    objectname: str = Field(alias="name")
    """Name of the object, used as a unique identifier in the simulation."""

    objecttype: str = Field(alias="type")
    """Type of the object, which determines its behavior and properties in the simulation."""

    header: str
    """Name of astra header"""

    exclude: List[str] = [
        "objectname",
        "objecttype",
        "astradict",
        "header",
        "exclude",
        "offset",
        "starting_offset",
        "starting_rotation",
        "global_parameters",
        "particle_definition",
        "output_particle_definition",
    ]

    astradict: Dict = {}

    def write_ASTRA(self) -> str:
        """
        Write the text for the ASTRA namelist based on its attributes.

        Returns
        -------
        str
            ASTRA-compatible string representing the namelist
        """
        output = f"&{self.header}\n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                if key in self.astradict:
                    output += f"{self.astradict[key]} = {val},\n"
                else:
                    output += f"{key} = {val},\n"
        output = output[:-2] + "\n"
        output += "/\n"
        return output


class astra_newrun(astra_header):
    """
    Class for generating the &NEWRUN namelist for ASTRA. See `ASTRA manual`_ for more details.
    """

    header: str = "NEWRUN"

    sample_interval: int = 1
    """Downsampling factor (as 2**(3 * sample_interval))"""

    run: int = 1
    """Run number"""

    head: str = "trial"
    """Run name"""

    lprompt: bool = False
    """If true a pause statement is included at the end
    of the run to avoid vanishing of the window in case of an error."""

    input_particle_definition: str
    """Name of input particle definition"""

    high_res: bool = True
    """If true, particle distributions are saved with increased accuracy."""

    auto_phase: bool = True
    """Phase RF cavities automatically"""

    bunch_charge: float | None = None
    """Bunch charge"""

    toffset: float = 0.0
    """Time offset of reference particle"""

    offset: list | np.ndarray = [0, 0, 0]
    """Beam offset from nominal axis [x,y,z]"""

    track_all: bool = True
    """If false, only the reference particle will be tracked"""

    phase_scan: bool = False
    """If true, the RF phases of the cavities will be scanned between 0 and 360 degree.
    Results are saved in the PScan file. The tracking between cavities will be done
    with the user-defined phases."""

    check_ref_part: bool = False
    """If true, the run will be interrupted if the reference particle is lost during the on-
    and off-axis reference particle tracking."""

    h_max: float = 0.07
    """Maximum time step for the Runge-Kutta integration."""

    h_min: float = 0.07
    """Minimum time step for the Runge-Kutta integration."""

    objectname: str = "newrun"
    """Name of object"""

    objecttype: str = "astra_newrun"
    """Type of object"""

    exclude: List = [
        "objectname",
        "objecttype",
        "astradict",
        "header",
        "exclude",
        "offset",
        "starting_offset",
        "starting_rotation",
        "global_parameters",
        "particle_definition",
        "output_particle_definition",
    ]

    def model_post_init(self, context: Any, /) -> None:
        self.astradict = {
            "input_particle_definition": "Distribution",
            "sample_interval": "n_red",
            "toffset": "Toff",
        }

    def write_ASTRA(self) -> str:
        if not self.input_particle_definition:
            raise ValueError("input_particle_definition must be defined for astra_newrun")
        return super().write_ASTRA()

class astra_output(astra_header):
    """
    Class for generating the &OUTPUT namelist for ASTRA. See `ASTRA manual`_ for more details.
    """

    header: str = "OUTPUT"

    lmagnetized: bool = False
    """If true, solenoid fields are neglected in the calculation of the beam emittance."""

    refs: bool = True
    """If true, output files according to Table 3 and Table 4 are generated. See `ASTRA manual`_"""

    emits: bool = True
    """If true, output files according to Table 3 and Table 4 are generated. See `ASTRA manual`_"""

    phases: bool = True
    """If true, output files according to Table 3 and Table 4 are generated. See `ASTRA manual`_"""

    high_res: bool = True
    """If true, particle distributions are saved with increased accuracy."""

    tracks: bool = True
    """If true, output files according to Table 3 and Table 4 are generated. See `ASTRA manual`_"""

    screens: List = []
    """List of :class:`~nala.models.element.Diagnostic` objects"""

    Lsub_cor: bool = True

    objectname: str = "output"
    """Name of object"""

    objecttype: str = "astra_output"
    """Type of object"""

    offset: list | np.ndarray = [0, 0, 0]
    """Beam offset from nominal axis [x,y,z]"""

    # starting_offset: float = None

    zstart: float = None

    zstop: float = None

    zemit: int = None

    # section: SectionLatticeTranslator

    def model_post_init(self, context: Any, /) -> None:
        self.astradict = {
            "input_particle_definition": "Distribution",
            "sample_interval": "n_red",
            "toffset": "Toff",
        }
        self.exclude.extend(["screens", "section", "end_element", "start_element"])#, "starting_offset"])
        # self.zstart = list(self.section.elements.elements.values())[0].physical.start.z
        # self.zstop = list(self.section.elements.elements.values())[-1].physical.end.z
        # self.zemit = int((self.zstop - self.zstart) / 0.01)
        # self.screens = [e for e in self.section.elements.elements.values() if e.hardware_class == "Diagnostic"]

    def write_ASTRA(self) -> str:
        """
        Write the text for the ASTRA namelist based on its :attr:`~framework_dict`.

        Parameters
        ----------
        n: int
            Index of the ASTRA element

        Returns
        -------
        str
            ASTRA-compatible string representing the namelist
        """
        output = f"&{self.header}\n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                if key in self.astradict:
                    output += f"{self.astradict[key]} = {val},\n"
                else:
                    output += f"{key} = {val},\n"
        for i, element in enumerate(self.screens, 1):
            output += f"Screen({i}) = {element.physical.middle.z},\n"
        output = output[:-2] + "\n"
        output += "/\n"
        return output

class astra_charge(astra_header):
    """
    Class for generating the &CHARGE namelist for ASTRA. See `ASTRA manual`_ for more details.
    """

    header: str = "CHARGE"

    npart: int = 2 ** (3 * 5)
    """Number of particles"""

    sample_interval: int = 1
    """Downsampling interval calculated as 2 ** (3 * sample_interval)"""

    space_charge_mode: str = "False"
    """Space charge mode"""

    space_charge_2D: bool = True
    """Enable 2D space charge calculations"""

    space_charge_3D: bool = False
    """Enable 3D space charge calculations"""

    cathode: bool = False
    """Flag to indicate whether the bunch was emitted from a cathode."""

    min_grid: float = 3.424657e-13
    """Minimum grid length during emission."""

    max_scale: float = 0.1
    """If one of the space charge scaling factors exceeds the limit 1± max_scale a new
    space charge calculation is initiated."""

    cell_var: float = 2
    """Variation of the cell height in radial direction."""

    nrad: int | None = None
    """Number of grid cells in radial direction up to the bunch radius."""

    nlong_in: int | None = None
    """Maximum number of grid cells in longitudinal direction within the bunch length."""

    smooth_x: int = 2
    """Smoothing parameter for x-direction. Only for 3D FFT algorithm."""

    smooth_y: int = 2
    """Smoothing parameter for y-direction. Only for 3D FFT algorithm."""

    smooth_z: int = 2
    """Smoothing parameter for z-direction. Only for 3D FFT algorithm."""

    grids: getGrids | None = None
    """Space charge grids"""

    objectname: str = "charge"
    """Name of object"""

    objecttype: str = "astra_charge"
    """Type of object"""

    def model_post_init(self, context: Any, /) -> None:
        self.grids = getGrids()
        self.astradict = {
            "cathode": "Lmirror",
            "space_charge_2D": "LSPCH",
            "space_charge_3D": "LSPCH3D",
        }
        self.exclude.extend(["grids", "npart", "sample_interval", "space_charge_mode", "mirror_charge"])

    def write_ASTRA(self) -> str:
        """
        Write the text for the ASTRA namelist based on its :attr:`~framework_dict`.

        Parameters
        ----------
        n: int
            Index of the ASTRA element

        Returns
        -------
        str
            ASTRA-compatible string representing the namelist
        """
        self.space_charge()
        output = f"&{self.header}\n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                if key in self.astradict:
                    output += f"{self.astradict[key]} = {val},\n"
                else:
                    output += f"{key} = {val},\n"
        if self.space_charge_2D:
            output += f"nrad = {self.grid_size},\n"
            output += f"nlong_in = {self.grid_size},\n"
        elif self.space_charge_3D:
            output += f"nxf = {self.grid_size},\n"
            output += f"nyf = {self.grid_size},\n"
            output += f"nzf = {self.grid_size},\n"
        elif self.space_charge():
            output += f"nxf = {self.grid_size},\n"
            output += f"nyf = {self.grid_size},\n"
            output += f"nzf = {self.grid_size},\n"
        output = output[:-2] + "\n"
        output += "/\n"
        return output

    def space_charge(self) -> bool:
        """
        Flag to indicate whether space charge is enabled.

        Returns
        -------
        bool
            True if enabled
        """
        if not (
            self.space_charge_mode == "False"
            or self.space_charge_mode is False
            or self.space_charge_mode is None
            or self.space_charge_mode == "None"
        ):
            self.space_charge_3D = True
            if isinstance(self.space_charge_mode, str):
                if "2d" in self.space_charge_mode.lower():
                    self.space_charge_2D = True
                    self.space_charge_3D = False
            return True
        self.space_charge_2D = False
        self.space_charge_3D = False
        return False


    @property
    def grid_size(self) -> int:
        """
        Get the number of space charge bins, see
        :func:`~SimulationFramework.Framework_objects.getGrids.getGridSizes`.

        Returns
        -------
        int
            The number of space charge bins based on the number of particles
        """
        # print('asking for grid sizes n = ', self.npart, ' is ', self.grids.getGridSizes(self.npart))
        return self.grids.getGridSizes(self.npart / self.sample_interval)

class astra_errors(astra_header):
    """
    Class for generating the &ERROR namelist for ASTRA. See `ASTRA manual`_ for more details.
    """

    header: str = "ERROR"

    global_errors: bool = True
    """If false, no errors will be generated."""

    log_error: bool = True
    """If true an additional log file will be generated which contains the actual
    element and bunch setting"""

    generate_output: bool = True
    """If true an output file will be generated"""

    suppress_output: bool = False
    """If true any generation of output other than the error file is suppressed."""

    objectname: str = "astra_error"
    """Name of object"""

    objecttype: str = "global_error"
    """Type of object"""

    def model_post_init(self, context: Any, /) -> None:
        self.exclude.extend(["element"])
        self.astradict = {
            "global_errors": "errors",
            "generate_output": "lerror",
        }