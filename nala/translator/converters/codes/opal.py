from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Any, Literal
from ...utils.classes import getGrids

class opal_header(BaseModel):
    """
    Generic class for generating OPAL namelists

    See `OPAL manual`_ for more details.

    .. OPAL manual: https://amas.web.psi.ch/opal/Documentation/master/OPAL_Manual.html
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
    """Name of OPAL header"""

    exclude: List[str] = [
        "objectname",
        "objecttype",
        "opaldict",
        "header",
        "exclude",
        "breakstr",
    ]

    opaldict: Dict = {}
    """Dictionary containing values to be written to the header"""

    breakstr: str = "//----------------------------------------------------------------------------"
    """String used for separating headers in the input file"""

    def write_Opal(self) -> str:
        """
        Write the text for the Opal namelist based on its attributes.

        Returns
        -------
        str
            Opal-compatible string representing the namelist
        """
        output = f"{self.breakstr}\n// {self.header}\n"
        if self.objecttype != "":
            output += f"{self.header}: {self.objecttype}, \n"
        else:
            output += f"{self.header}, \n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                if key in self.opaldict:
                    output += f"\t{self.opaldict[key]} = {val},\n"
                elif key == "METHOD":
                    output += "METHOD = \"PARALLEL-T\",\n"
                else:
                    output += f"\t{key} = {val},\n"
        output = output[:-2] + ";\n"
        return output

class opal_option(opal_header):
    """
    Class for generating the OPTION namelist for OPAL. See `OPAL manual`_ for more details.
    """

    objectname: str = "option"
    """Name of object"""

    objecttype: str = "OPTION"
    """Type of object"""

    header: str = "OPTION"
    """Name of header"""

    VERSION: str = "202210"
    """Used to indicate for which version of OPAL the input file is written.The major and minor versions of OPAL 
    and of the input file have to match.The patch version of OPAL must be greater or equal to the patch version 
    of the input file.If the version doesn’t fulfill above criteria OPAL stops immediately and prints instructions 
    on how to convert the input file.Starting with version 1.6.0 of OPAL the option VERSION is mandatory in the 
    OPAL input file.The format is Mmmpp where M stands for the major, m for the minor and p for the patch version.
    For version 1.6.0 of OPAL VERSION should read 10600."""

    AMR: bool = False
    """Enable adaptive mesh refinement. Its default value is false."""

    AMR_REGRID_FREQ: int = None
    """Defines after how many steps an AMR regrid is performed."""

    AMR_YT_DUMP_FREQ: int = None
    """The frequency to dump grid and particle data for AMR."""

    ASCIIDUMP: bool = False
    """If true, instead of HDF5, ASCII output is generated for the following elements: 
    Collimator, Geometry, Monitor, Probe, Stripper, Vacuum and global losses."""

    AUTOPHASE: int = 6
    """Defines how accurate the search for the phase at which the maximal energy is gained should be. 
    The higher this number the more accurate the phase will be. 
    If it is set to 0 then the auto-phasing algorithm isn’t run."""

    BEAMHALOBOUNDARY: float = None
    """Defines in terms of sigma where the halo starts. Only used in OPAL-cycl."""

    BOUNDPDESTROYFQ: int = None
    """The frequency to delete particles which are too far away from the center of beam. 
    Only used in OPAL-cycl."""

    CLOTUNEONLY: bool = False
    """If set to true, stop after closed orbit finder and tune calculation. 
    Only used in OPAL-cycl."""

    COMPUTEPERCENTILES: bool = False
    """If true, the 68 (1 sigmas for normal distribution), the 95 (2 sigmas), the 99.7 (3 sigmas) and 
    the 99.99 (4 sigmas) percentiles of the bunch size and the normalized emittance are calculated. 
    The data are stored into .stat output file and loss file in HDF5 format (.h5). 
    The calculation is performed whenever the number of particles exceeds 100."""

    CSRDUMP: bool = False
    """If true the electric csr field component, Ez, line density and the derivative of the line density 
    is written into the data directory. The first line gives the average position of the beam bunch. 
    Subsequent lines list zz position of longitudinal mesh (with respect to the head of the beam bunch), 
    Ez, line density and the derivative of the line density. Note that currently the line density derivative 
    needs to be scaled by the inverse of the mesh spacing to get the correct value. T
    he CSR field is dumped at each time step of the calculation. E
    ach text file is named 'Bend Name' (from input file) + '-CSRWake' + 'time step number in that bend 
    (starting from 1)' + '.txt'."""

    CZERO: bool = False
    """If true the distributions are generated such that the centroid is exactly zero and not 
    statistically dependent."""

    DELPARTFREQ: int = None
    """The frequency to delete particles in OPAL-cycl."""

    DUMPBEAMMATRIX: bool = None
    """If true, the 6-dimensional beam matrix (upper triangle only) is stored in the statistics output file (.stat)."""

    EBDUMP: bool = None
    """If true the electric and magnetic field on the particle is saved each time a phase space is written."""

    ENABLEHDF5: bool = None
    """If true (default), HDF5 read and write is enabled."""

    ENABLEVTK: bool = None
    """If true (default), VTK write of geometry voxel mesh is enabled."""

    HALOSHIFT: float = None
    """Constant parameter to shift halo value. Its default value is 0.0."""

    IDEALIZED: bool = None
    """Instructs to use the hard edge model for the calculation of the path length in OPAL-t. T
    he path length is computed to place the elements in the three-dimensional space from ELEMEDGE."""

    LOGBENDTRAJECTORY: bool = None
    """Save the reference trajectory inside dipoles in an ASCII file. 
    For each dipole a separate file is written to the directory data/."""

    MEMORYDUMP: bool = None
    """If true, it writes the memory consumption of every core to a SDDS file (.mem). 
    The write frequency corresponds to STATDUMPFREQ."""

    MINBINEMITTED: int = None
    """The number of bins that have to be emitted before the bin are squashed into a single bin."""

    MINSTEPFORREBIN: int = None
    """The number of steps into the simulation before the bins are squashed into a single bin. 
    This should be used instead of the global variable of the same name. Its default value is 200."""

    MTSSUBSTEPS: int = None
    """Only used for multiple-time-stepping (MTS) integrator in OPAL-cycl. Specifies how many sub-steps 
    for external field integration are done per step. Making less steps per turn and increasing this value 
    is the recommended way to reduce space charge solve frequency. Its default value is 1."""

    NLHS: int = None
    """Number of stored old solutions for extrapolating the new starting vector. 
    Default value is 1 and just the last solution is used."""

    NUMBLOCKS: int = None
    """Maximum number of vectors in the Krylov space for ITSOLVER=CG or ITSOLVER=GMRES (see FIELDSOLVER command). 
    Its default value is 0."""

    PSDUMPFREQ: int = None
    """Defines after how many time steps the phase space is dumped into the H5hut file (.h5). 
    It also controls the frequency of phase space printed on the standard output. Its default value is 10."""

    PSDUMPEACHTURN: bool = None
    """Control option of phase space dumping. If true, dump phase space after each turn. 
    For the time being, this is only use for multi-bunch simulation in OPAL-cycl. Its default value is false."""

    PSDUMPFRAME: str = None
    """Control option that defines the frame in which the phase space data is written for .h5 and .stat files. 
    Beware that the data is written in a given time step. Most accelerator physics quantities are defined at a 
    given s-step where s is distance along the reference trajectory. For non-isochronous accelerators, 
    particles at a given time step can be quite a long way away from the reference particle, 
    yielding unexpected results. Currently only available for OPAL-cycl. 
    In OPAL-t the phase-space is always written in the frame of the reference particle.

        GLOBAL: data is written in the global Cartesian frame;

        BUNCH_MEAN: data is written in the bunch mean frame or;

        REFERENCE: data is written in the frame of the reference particle."""

    REBINFREQ: int = None
    """Defines after how many time steps we update the energy Bin ID of each particle. For the time being. 
    Only available for multi-bunch simulation in OPAL-cycl. Its default value is 100."""

    RECYCLEBLOCKS: int = None
    """Number of vectors in the recycle space for ITSOLVER=CG or ITSOLVER=GMRES (see FIELDSOLVER command). 
    Its default value is 0."""

    REMOTEPARTDEL: float = None
    """Artificially delete remote particles if their distances to the beam centroid is larger than 
    REMOTEPARTDEL times of the beam rms size. In OPAL-t only the longitudinal component of the particles 
    is considered. In OPAL-cycl all components are considered if the the value is negative 
    (further on using its absolute value) and only the transverse components if the value is positive. 
    Its default value is 0.0, i.e. no particles are deleted."""

    REPARTFREQ: int = None
    """Defines after how many time steps we do particles repartition to balance the computational 
    load of the computer nodes. Its default value is 10."""

    RHODUMP: bool = None
    """If true the scalar ρρ field is saved each time a phase space is written. There exists a reader in 
    Visit with versions greater or equal 1.11.1. Its default value is false."""

    RNGTYPE: str = None
    """The name (see String Attributes) of a random number generator can be provided. 
    The default random number generator (RANDOM) is a portable 48-bit generator. 
    Three quasi random generators are available: HALTON, SOBOL and NIEDERREITER. 
    For details see the GSL reference manual (18.5)."""

    SCSOLVEFREQ: int = None
    """If the space charge field is slowly varying w.r.t. external fields, this option allows to change the 
    frequency of space charge calculation, i.e. the space charge forces are evaluated every SCSOLVEFREQ 
    step and then reused for the following steps. Affects integrators LF2 and RK4 of OPAL-cycl. 
    Its default value is 1. Note: as the multiple-time-stepping (MTS) integrator maintains accuracy much 
    better with reduced space charge solve frequency, this option should probably not be used anymore."""

    SEED: int = None
    """Selects a particular sequence of random values. A SEED value is an integer in the range [0…999999999] 
    (default: 123456789). SEED can be an expression. If SEED == -1, the time is used as seed and the generator 
    is not portable anymore. See also Deferred Expressions and Random Values."""

    SPTDUMPFREQ: int = None
    """Defines after how many time steps we dump the phase space of single particle in OPAL-cycl. 
    It is always useful to record the trajectory of reference particle or some specified particle for primary study. 
    Its default value is 1."""

    STATDUMPFREQ: int = None
    """Defines after how many time steps we dump statistical data, such as RMS beam emittance, to the .stat file. 
    Its default value is 10."""

    def write_Opal(self) -> str:
        """
        Write the text for the Opal namelist based on its attributes.

        Returns
        -------
        str
            Opal-compatible string representing the namelist
        """
        output = f"{self.breakstr}\n// {self.header}\n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                output += f"{self.header}, {key} = {val};\n"
        return output

class opal_distribution(opal_header):
    """
    Class for generating the OPTION namelist for OPAL. See `OPAL manual`_ for more details.

    Note that only FROMFILE distributions are currently supported.
    """

    header: str = "DIST"
    """Name of header"""

    objectname: str = "distribution"
    """Name of object"""

    objecttype: str = "DISTRIBUTION"
    """Type of object"""

    TYPE: Literal["FROMFILE"] = "FROMFILE"

    input_particle_definition: str

    def model_post_init(self, context: Any, /) -> None:
        self.opaldict = {"input_particle_definition": "FNAME"}

    def write_Opal(self) -> str:
        if not self.input_particle_definition:
            raise ValueError("input_particle_definition must be defined for opal_distribution")
        return super().write_Opal()

class opal_fieldsolver(opal_header):
    """
    Class for generating the FIELDSOLVER namelist for OPAL. See `OPAL manual`_ for more details.

    Note that the AMR solve is not currently supported; only FFT has really been tested.
    """

    objectname: str = "fieldsolver"
    """Name of object"""

    objecttype: str = "FIELDSOLVER"
    """Type of object"""

    header: str = "FS"
    """Name of header"""

    npart: int
    """Number of particles in the bunch"""

    space_charge_mode: str = "False"
    """Space charge mode"""

    grids: getGrids | None = None
    """Space charge grids"""

    sample_interval: int = 1
    """Downsampling interval calculated as 2 ** (3 * sample_interval)"""

    FSTYPE: Literal["FFT", "FFTPERIODIC", "SAAMG", "P3M", "NONE"] = "FFT"
    """Specify the type of field solver: FFT, FFTPERIODIC, SAAMG, P3M and NONE. 
    Further arguments are enabled with the AMR solver (cf. Adaptive Mesh Refinement (AMR) Solver)."""

    PARFFTX: bool = True
    """If TRUE, the dimension x is distributed among the processors"""

    PARFFTY: bool = True
    """If TRUE, the dimension y is distributed among the processors"""

    PARFFTT: bool = True
    """If TRUE, the dimension t is distributed among the processors"""

    MX: int = None
    """Number of grid points in x specifying rectangular grid"""

    MY: int = None
    """Number of grid points in y specifying rectangular grid"""

    MT: int = None
    """Number of grid points in t specifying rectangular grid"""

    BCFFTX: str = "open"
    """Boundary condition in x [OPEN] (FFT + AMR_MG only)."""

    BCFFTY: str = "open"
    """Boundary condition in y [OPEN] (FFT + AMR_MG only)."""

    BCFFTZ: str = "open"
    """Boundary condition in z [OPEN,PERIODIC] (FFT + AMR_MG only)."""

    GREENSF: str = "Integrated"
    """Defines the Greens function for the FFT-based solvers (FFT + P3M only)."""

    BBOXINCR: float = None
    """Enlargement of the bounding box in %."""

    ITSOLVER: str = None
    """Type of iterative solver (SAAMG + AMR_MG only)."""

    RC: float = None
    """Defines the cut-off radius in the boosted frame for the P3M solver (P3M only)."""

    ALPHA: float = None
    """Defines the interaction splitting parameter for the P3M solver with standard Green’s function 
    (P3M + GREENSF=STANDARD only)."""

    def model_post_init(self, context: Any, /) -> None:
        self.grids = getGrids()
        self.opaldict = {"input_particle_definition": "FNAME"}
        self.exclude.extend(["npart", "space_charge_mode", "grids", "sample_interval"])
        self.MX = self.grid_size
        self.MY = self.grid_size
        self.MT = self.grid_size
        if self.space_charge:
            self.FSTYPE = "FFT"
        else:
            self.FSTYPE = "NONE"

    def write_Opal(self) -> str:
        if not self.npart:
            raise ValueError("npart must be defined for opal_fieldsolver")
        return super().write_Opal()

    @property
    def space_charge(self) -> bool:
        """
        Flag to indicate whether space charge is enabled.

        Returns
        -------
        bool
            True if enabled
        """
        return not (
                self.space_charge_mode == "False"
                or self.space_charge_mode is False
                or self.space_charge_mode is None
                or self.space_charge_mode == "None"
        )

    @property
    def grid_size(self) -> int:
        """
        Get the number of space charge bins.

        Returns
        -------
        int
            The number of space charge bins based on the number of particles
        """
        # print('asking for grid sizes n = ', self.npart, ' is ', self.grids.getGridSizes(self.npart))
        return self.grids.getGridSizes(self.npart / self.sample_interval)

class opal_beam(opal_header):
    """
    Class for generating the BEAM namelist for OPAL. See `OPAL manual`_ for more details.

    Note that only electrons, positrons and protons are currently supported.
    """

    objectname: str = "beam"
    """Name of object"""

    objecttype: str = "BEAM"
    """Type of object"""

    header: str = "BEAM1"
    """Name of header"""

    PARTICLE: Literal["ELECTRON", "POSITRON", "PROTON"]
    """The name of particles in the machine."""

    PC: float
    """Particle momentum in GeV/c."""

    NPART: int
    """Number of particles."""

    CHARGE: int
    """The particle charge expressed in elementary charges."""

    BFREQ: int = 1
    """The bunch frequency in MHz."""

    BCURRENT: float
    """The bunch current in A. BCURRENT=Q×BFREQBCURRENT=Q×BFREQ with Q the total charge.
    So essentially this is set to the charge of the bunch in micro-coulombs."""


class opal_track(opal_header):
    """
    Class for generating the TRACK namelist for OPAL. See `OPAL manual`_ for more details.
    """

    objectname: str = "track"
    """Name of object"""

    objecttype: str = ""
    """Type of object"""

    header: str = "TRACK"
    """Name of header"""

    LINE: str
    """The label of a preceding LINE (no default)."""

    BEAM: str = "BEAM1"
    """The named BEAM command defines the particle mass, charge and reference momentum.
    This should be the same as the name provided by opal_beam."""

    T0: float = None
    """The initial time [s] of the simulation, its default value is 0."""

    DT: float | str = 1e-12
    """Array of time step sizes for tracking, default length of the array is 1 and its only value is 1 ps."""

    MAXSTEPS: int = None
    """Array of maximal number of time steps, default length of the array is 1 and its only value is 10."""

    ZSTART: float = None
    """Initial position of the reference particle along the reference trajectory, default position is 0.0 m."""

    ZSTOP: float | str
    """Array of z-locations [m], default length of the array is 1 and its only value is 1E61E6 [m]. 
    The simulation switches to the next set, i+1i+1, of DT, MAXSTEPS and ZSTOP if either it has been t
    racking with the current set for more than MAXSTEPS steps or the mean position has reached a z-position 
    larger than ZSTOP. If set i is the last set of the array then the simulation stops."""

    TIMEINTEGRATOR: Literal["RK4", "LF2", "MTS"] = None
    """Define the time integrator. Currently only available in OPAL-cycl. The valid options are RK4, LF2 and MTS"""

    def write_Opal(self) -> str:
        self.DT = str(self.DT)
        self.ZSTOP = "{" + str(self.ZSTOP + 1e-1) + "}"
        return super().write_Opal()

class opal_run(opal_header):
    """
    Class for generating the RUN namelist for OPAL. See `OPAL manual`_ for more details.

    Note that only OPAL-t is currently supported.
    """

    objectname: str = "run"
    """Name of object"""

    objecttype: str = ""
    """Type of object"""

    header: str = "RUN"
    """Name of header"""

    METHOD: str = "PARALLEL-T"
    """The name (a string, see String Attributes) of the tracking method to be used. 
    For the time being the following methods are known:

        PARALLEL-T This method puts OPAL in OPAL-t mode (see Chapter OPAL-t).

        CYCLOTRON-T This method puts OPAL in OPAL-cycl mode (see Chapter OPAL-cycl)."""

    FIELDSOLVER: str = "FS"
    """The field solver to be used. This should be the same as the name provided by opal_fieldsolver"""

    DISTRIBUTION: str = "DIST"
    """The particle distribution to be used. This should be the same as the name provided by opal_distribution"""

    BEAM: str = "BEAM1"
    """The particle beam to be used. This should be the same as the name provided by opal_beam"""

    TURNS: int = 1
    """The number of turns (integer) to be tracked (default: 1, namely single bunch).

    In OPAL-cycl, this parameter represents the number of bunches that will be injected into the cyclotron. 
    In restart mode, the code firstly reads an attribute NumBunch from .h5 file which records how many bunches 
    have already been injected. If NumBunch << TURNS, the last TURNS −− NumBunch bunches will be injected 
    in sequence by reading the initial distribution from the .h5 file."""

    MBMODE: Literal["AUTO", "FORCE"] = None
    """This defines which mode of multi-bunch runs. There are two options for it, namely, AUTO and FORCE. 
    See Multi-bunch Mode for their explanations in detail.
    For restarting run with TURNS larger than one, if the existing bunches of the read-in step is larger than one, 
    the mode is forcedly set to FORCE. Otherwise, it is forcedly set to AUTO.
    This argument is available for OPAL-cycl."""

    PARAMB: float = None
    """This is a control parameter to define when to start to transfer from single bunch to multi-bunches for 
    AUTO mode (default: 5.0). This argument is only available for AUTO mode multi-bunch run in OPAL-cycl."""

    MB_BINNING: Literal["GAMMA_BINNING", "BUNCH_BINNING"] = None
    """Type of energy binning in multi-bunch mode: GAMMA_BINNING or BUNCH_BINNING (default: GAMMA_BINNING). 
    When BUNCH_BINNING binning, then all particles of a bunch are in the same energy bin. When GAMMA_BINNING 
    binning, then the bin depends on the momentum of the particle. Only available in OPAL-cycl."""

    MB_ETA: float = None
    """The scale parameter for binning in multi-bunch mode (default: 0.01). Only used in MB_BINNING=GAMMA_BINNING. 
    Only available in OPAL-cycl."""

    TRACKBACK: bool = None
    """The particles are tracked backward in time if TRACKBACK=TRUE. OPAL starts at ZSTART and tracks the 
    bunch back in time. It changes the size of the time step when it crosses the thresholds given in the 
    ZSTOP attribute of the TRACK command and stops once it reaches the lowest item of ZSTOP. 
    Only available in OPAL-t. Default is FALSE."""
