from pydantic import BaseModel, Field
from typing import Dict, List, Any, Literal


class csrtrack_element(BaseModel):
    """
    Base class for CSRTrack elements, including namelists for the lattice file.
    """

    header: str = ""
    """Header for CSRtrack file types"""

    objectname: str = Field(alias="name")
    """Name of the object, used as a unique identifier in the simulation."""

    objecttype: str = Field(alias="type")
    """Type of the object, which determines its behavior and properties in the simulation."""

    exclude: List[str] = [
        "objectname",
        "objecttype",
        "header",
        "exclude",
        "particle_definition",
        "csrtrackdict",
        "end_time_marker",
    ]

    csrtrackdict: Dict = {}

    def CSRTrack_str(self, s: Any) -> str:
        """
        Convert a boolean into a string for CSRTrack.

        Parameters
        ----------
        s: bool
            Boolean to convert

        Returns
        -------
        str
            'yes' for `True`, 'no' for `False`, or the original string if otherwise
        """
        if s is True:
            return "yes"
        elif s is False:
            return "no"
        else:
            return str(s)

    def write_CSRTrack(self) -> str:
        """
        Create the string for the header object in CSRTrack format.

        Returns
        -------
        str
            CSRTrack-compatible string for this element.
        """
        output = str(self.header) + "{\n"
        for key, val in self.model_dump().items():
            if key not in self.exclude and val is not None:
                if key in self.csrtrackdict:
                    output += key + "=" + self.CSRTrack_str(self.csrtrackdict[key]) + "\n"
                else:
                    output += key + "=" + self.CSRTrack_str(getattr(self, key)) + "\n"
        output += "}\n"
        return output


# class csrtrack_online_monitor(csrtrack_element):
#
#     def __init__(self, marker="", **kwargs):
#         super(csrtrack_online_monitor, self).__init__(
#             "online_monitor", "csrtrack_online_monitor", **kwargs
#         )
#         self.header = "online_monitor"
#         self.end_time_marker = marker + "b"


class csrtrack_forces(csrtrack_element):
    """
    Class for CSRTrack forces.
    """

    header: str = "forces"
    """Header for CSRtrack element"""

    objectname: str = "forces"
    """Name of object"""

    objecttype: str = "csrtrack_forces"
    """Type of object"""

    type: Literal["projected", "csr_g_to_p"] | None = None

    shape: Literal["ellipsoid"] = "ellipsoid"

    sigma_long: Literal["relative"] =  "relative"

    relative_long: float = 0.1


class csrtrack_track_step(csrtrack_element):
    """
    Class for defining CSRTrack the tracking step.
    """

    header: str = "track_step"
    """Header for CSRtrack element"""

    objectname: str = "track_step"
    """Name of object"""

    objecttype: str = "csrtrack_track_step"
    """Type of object"""

    precondition: bool = True

    iterative: int = 2

    error_per_ct: float = 0.001

    error_weight_momentum: float = 0.1

    ct_step_min: float = 0.002

    ct_step_max: float = 0.20

    ct_step_first: float = 0.010

    increase_factor: int = 2

    arc_factor: float = 0.3

    duty_steps: bool = True


class csrtrack_tracker(csrtrack_element):
    """
    Class for defining the CSRTrack tracker.
    """

    header: str = "tracker"
    """Header for CSRtrack element"""

    objectname: str = "tracker"
    """Name of object"""

    objecttype: str = "csrtrack_tracker"
    """Type of object"""

    end_time_marker: str = ""
    """Name of end marker"""

    end_time_shift_c0: str | float = 0.0
    """Time shift for end"""


class csrtrack_monitor(csrtrack_element):
    """
    Class for defining CSRTrack monitors.
    """

    header: str = "monitor"
    """Header for CSRtrack element"""

    objectname: str = "monitor"
    """Name of object"""

    objecttype: str = "csrtrack_monitor"
    """Type of object"""

    name: str = ""
    """File name for monitor"""

    end_time_marker: str = "screen"

    format: Literal["fmt2"] = "fmt2"



class csrtrack_particles(csrtrack_element):
    """
    Class for defining CSRTrack particles.
    """

    header: str = "particles"
    """Header for CSRtrack element"""

    objectname: str = "particles"
    """Name of object"""

    objecttype: str = "csrtrack_particles"
    """Type of object"""

    particle_definition: str = "laser.astra"
    """Particle definition file"""

    array: str = "#file{name=laser.astra}"
    """File name array"""

    reference_momentum: Literal["reference_particle"] = "reference_particle"

    reference_point_x: float = 0.0

    reference_point_y: float = 0.0

    reference_point_phi: float = 0.0

    format: Literal["astra"] = "astra"