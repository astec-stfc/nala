from pydantic import BaseModel, ConfigDict, computed_field
from typing import List
import numpy as np
from ...utils.classes import getGrids
from ...utils.functions import chop


class gpt_ccs(BaseModel):

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    name: str

    position: List[float] = [0.0, 0.0, 0.0]

    rotation: List[float] = [0.0, 0.0, 0.0]

    intersect: float = 0.0

    @computed_field
    @property
    def psi(self) -> float:
        return self.rotation[0]

    @computed_field
    @property
    def phi(self) -> float:
        return self.rotation[1]

    @computed_field
    @property
    def theta(self) -> float:
        return self.rotation[2]

    @computed_field
    @property
    def x(self) -> float:
        return self.position[0]

    @computed_field
    @property
    def y(self) -> float:
        return self.position[1]

    @computed_field
    @property
    def z(self) -> float:
        return self.position[2]

    def relative_position(
        self, position: np.ndarray | list, rotation: np.ndarray | list
    ) -> tuple:
        x, y, z = position
        pitch, yaw, roll = rotation
        length = np.sqrt((x - self.x) ** 2 + (y - self.y) ** 2 + (z - self.z) ** 2)
        finalrot = np.array([pitch - self.psi, yaw - self.phi, roll - self.theta])
        finalpos = np.array(
            [0, 0, abs(self.intersect) + length]
        )
        return finalpos, finalrot

    @property
    def name_as_str(self):
        return '"' + self.name + '"'

    def ccs_text(self, position, rotation):
        finalpos, finalrot = self.relative_position(position, rotation)
        x, y, z = finalpos
        psi, phi, theta = finalrot
        ccs_label = ""
        value_text = ""
        if abs(x) > 0:
            ccs_label += "x"
            value_text += "," + str(x)
        if abs(y) > 0:
            ccs_label += "y"
            value_text += "," + str(y)
        if abs(z) > 0:
            ccs_label += "z"
            value_text += "," + str(z)
        if abs(psi) > 0:
            ccs_label += "X"
            value_text += "," + str(psi)
        if abs(phi) > 0:
            ccs_label += "Y"
            value_text += "," + str(phi)
        if abs(theta) > 0:
            ccs_label += "Z"
            value_text += "," + str(theta)
        if ccs_label == "" and value_text == "":
            ccs_label = "z"
            value_text = "," + str(0)
        return '"' + ccs_label + '"', value_text.strip(",")

    def gpt_coordinates(self, position: list | np.ndarray, rotation: list | np.ndarray) -> str:
        """
        Get the GPT coordinates for a given position and rotation

        Parameters
        ----------
        position: list | np.ndarray
            The lattice position.
        rotation: float
            The element rotation

        Returns
        -------
        str
            A GPT-formatted position string.
        """
        x, y, z = chop(position, 1e-6)
        psi, phi, theta = rotation
        output = ""
        for c in [-x, y, z]:
            output += str(c) + ", "
        output += "cos(" + str(theta) + "), 0, -sin(" + str(theta) + "), 0, 1 ,0"
        return output

class gpt_element(BaseModel):
    """
    Generic class for generating headers for GPT.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    objectname: str = ""

    objecttype: str = ""

    exclude: List = ["objectname", "objecttype", "particle_definition"]

    def write_GPT(self, *args, **kwargs) -> str:
        """
        Write the text for the GPT namelist based on its
        :attr:`~objectdefaults`, :attr:`~objectname`.

        Returns
        -------
        str
            GPT-compatible string representing the namelist
        """
        output = str(self.objectname) + "("
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                k = key.lower()
                output += str(getattr(self, k)) + ", "
        output = output[:-2]
        output += ");\n"
        return output


class gpt_setfile(gpt_element):
    """
    Class for setting filenames in GPT via `setfile`.
    """

    objectname: str = "setfile"
    """Name of object"""

    objecttype: str = "gpt_setfile"
    """Type of object"""

    set: str = '"beam"'

    filename: str = '"output.gdf"'

    particle_definition: str = '"gdf"'


class gpt_charge(gpt_element):
    """
    Class for generating the `settotalcharge` namelist for GPT.
    """

    set: str = '"beam"'
    """Name of beam for `settotalcharge`"""

    charge: float = 0.0
    """Bunch charge"""

    objectname: str = "settotalcharge"
    """Name of object"""

    objecttype: str = "gpt_charge"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = str(self.objectname) + "("
        output += str(self.set) + ","
        output += str(-1 * abs(self.charge)) + ");\n"
        return output


class gpt_setreduce(gpt_element):
    """
    Class for reducing the number of particles via `setreduce`.

    """

    set: str = '"beam"'
    """Name of the beam for `setreduce`"""

    setreduce: int = 1
    """Factor by which to reduce the number of particles"""

    objectname: str = "setreduce"
    """Name of object"""

    objecttype: str = "gpt_setreduce"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = str(self.objectname) + "("
        output += str(self.set) + ","
        output += str(self.setreduce) + ");\n"
        return output


class gpt_accuracy(gpt_element):
    """
    Class for setting the accuracy of tracking via `accuracy` in GPT.
    """

    objectname: str = "accuracy"
    """Name of object"""

    objecttype: str = "gpt_accuracy"
    """Type of object"""

    accuracy: int = 6
    """Accuracy for GPT tracking"""

    def write_GPT(self, *args, **kwargs) -> str:
        output = (
            "accuracy(" + str(self.accuracy) + ");\n"
        )  # 'setrmacrodist(\"beam\","u",1e-9,0) ;\n'
        return output


class gpt_spacecharge(gpt_element):
    """
    Class for preparing space charge calculations in GPT via `spacecharge`.
    """

    grids: getGrids = None
    """Class for calculating the required number of space charge grids"""

    ngrids: int | None = None
    """Number of space charge grids"""

    space_charge_mode: str | None = None
    """Space charge mode ['2D', '3D']"""

    cathode: bool = False
    """Flag indicating whether the bunch was emitted from a cathode"""

    objectname: str = "spacecharge"
    """Name of object"""

    objecttype: str = "gpt_spacecharge"
    """Type of object"""

    def model_post_init(self, __context):
        super().model_post_init(__context)
        self.grids = getGrids()
        self.exclude.extend(["cathode", "grids", "ngrids", "space_charge_mode"])

    def write_GPT(self, *args, **kwargs) -> str:
        output = ""
        if isinstance(self.space_charge_mode, str) and self.cathode:
            if self.ngrids is None:
                self.ngrids = self.grids.getGridSizes(
                    (self.npart / self.sample_interval)
                )
            output += 'spacecharge3Dmesh("Cathode","RestMaxGamma",1000);\n'
        elif (
            isinstance(self.space_charge_mode, str)
            and self.space_charge_mode.lower() == "3d"
        ):
            output += "Spacecharge3Dmesh();\n"
        elif (
            isinstance(self.space_charge_mode, str)
            and self.space_charge_mode.lower() == "2d"
        ):
            output += "Spacecharge3Dmesh();\n"
        else:
            output = ""
        return output


class gpt_tout(gpt_element):
    """
    Class for setting up the beam dump rate via `tout`.
    """

    startpos: float = 0.0
    """Starting position"""

    endpos: float = 0.0
    """End position"""

    starttime: float = 0.0
    """Start time for dumping"""

    step: str = "0.1/c"
    """Dump step as a string [distance / c]"""

    objectname: str = "tout"
    """Name of object"""

    objecttype: str = "gpt_tout"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        self.starttime = 0 if self.starttime < 0 else self.starttime
        output = str(self.objectname) + "("
        if self.starttime is not None:
            output += str(self.starttime) + ","
        else:
            output += str(self.startpos) + "/c,"
        output += str(self.endpos) + ","
        output += str(self.step) + ");\n"
        return output


class gpt_csr1d(gpt_element):
    """
    Class for preparing CSR calculations via `csr1d`.
    """

    objectname: str = "csr1d"
    """Name of object"""

    objecttype: str = "gpt_csr1d"
    """Type of object"""

    def write_GPT(self, *args, **kwargs) -> str:
        output = str(self.objectname) + "();\n"
        return output


class gpt_writefloorplan(gpt_element):
    """
    Class for writing the lattice floor plan via `writefloorplan`.
    """

    filename: str = ""
    """Floor plan filename"""

    objectname: str = "writefloorplan"
    """Name of object"""

    objecttype: str = "gpt_writefloorplan"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = str(self.objectname) + "(" + self.filename + ");\n"
        return output


class gpt_Zminmax(gpt_element):
    """
    Class for setting the boundaries in z for discarding particles via `Zminmax`
    """

    zmin: float = 0.0
    """Minimum longitudinal position"""

    zmax: float = 0.0
    """Maximum longitudinal position"""

    ECS: str = '"wcs", "I"'
    """Element coordinate system as a string"""

    objectname: str = "Zminmax"
    """Name of object"""

    objecttype: str = "gpt_Zminmax"
    """Type of object"""


    def _write_GPT(self, *args, **kwargs):
        output = (
            str(self.objectname)
            + "("
            + self.ECS
            + ", "
            + str(self.zmin)
            + ", "
            + str(self.zmax)
            + ");\n"
        )
        return output


class gpt_forwardscatter(gpt_element):
    """
    Class for scattering particles via `forwardscatter`.
    """

    zmin: float = 0.0
    """Minimum longitudinal position"""

    zmax: float = 0.0
    """Maximum longitudinal position"""

    ECS: str = '"wcs", "I"'
    """Element coordinate system"""

    probability: float = 0.0
    """Scattering probability"""

    objectname: str = "forwardscatter"
    """Name of object"""

    objecttype: str = "gpt_forwardscatter"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = (
            str(self.objectname)
            + "("
            + self.ECS
            + ', "'
            + str(self.name)
            + '", '
            + str(self.probability)
            + ");\n"
        )
        return output


class gpt_scatterplate(gpt_element):
    """
    Class for scattering particles off a plate via `scatterplate`.
    """

    zmin: float = 0.0
    """Minimum longitudinal position"""

    zmax: float = 0.0
    """Maximum longitudinal position"""

    ECS: str = '"wcs", "I"'
    """Element coordinate system"""

    a: float = 0.0
    """Plate length in x-direction"""

    b: float = 0.0
    """Plate length in y-direction"""

    model: str = "cathode"
    """Scattering model to be used ['cathode', 'remove']"""

    objectname: str = "scatterplate"
    """Name of object"""

    objecttype: str = "gpt_scatterplate"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = (
            str(self.objectname)
            + "("
            + self.ECS
            + ", "
            + str(self.a)
            + ", "
            + str(self.b)
            + ') scatter="'
            + str(self.model)
            + '";\n'
        )
        return output


class gpt_dtmaxt(gpt_element):
    """
    Class for setting up minimum, maximmum temporal step sizes for tracking via `dtmaxt`.
    """

    tend: float = 0.0
    """Final time value"""

    tstart: float = 0.0
    """Initial time value"""

    dtmax: float = 0.0
    """Maximum temporal step size"""

    objectname: str = "dtmaxt"
    """Name of object"""

    objecttype: str = "gpt_dtmaxt"
    """Type of object"""


    def write_GPT(self, *args, **kwargs) -> str:
        output = (
            str(self.objectname)
            + "("
            + str(self.tstart)
            + ", "
            + str(self.tend)
            + ", "
            + str(self.dtmax)
            + ");\n"
        )
        return output
