from pydantic import BaseModel
from typing import Dict, Any, List
from pytao import Tao, TaoCommandError
from collections import Counter
from . import magnetic_orders
import nala.models.element as NALA_elements
from nala.models.elementList import SectionLattice, MachineLayout, ElementList
from nala.models.element import (
    Element,
    Combined_Corrector,
    Vertical_Corrector,
    Horizontal_Corrector,
)
import math
def norm(v):
    n = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if n == 0:
        return (0.0, 0.0, 0.0)
    return (v[0]/n, v[1]/n, v[2]/n)

def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def deg(r): return math.degrees(r)

def rotation_angles(forward):
    f = norm(forward)
    # yaw (heading around Y): atan2(x, z)
    yaw = math.atan2(f[0], f[2])

    # pitch (elevation): atan2(y, sqrt(x^2+z^2))
    pitch = math.atan2(f[1], math.sqrt(f[0] * f[0] + f[2] * f[2]))

    # build a local right/up so we can compute roll.
    # choose world_up = (0,1,0)
    world_up = (0.0, 1.0, 0.0)

    right = norm(cross(world_up, f))
    up = cross(f, right)  # orthogonal up for the object frame

    # roll = signed angle around forward that rotates object's up -> world_up
    cr = cross(up, world_up)
    roll = math.atan2(dot(cr, f), dot(up, world_up))
    return pitch, roll, yaw

class BmadLatticeImporter(BaseModel):

    floorplan_init: str
    """Name of Tao init file which produces floor coordinates"""

    libtao: str = None
    """libtao.so file"""

    elements: Dict = {}
    """Dictionary containing converted NALA element objects"""

    n_universes: int = 1

    names: Dict[int, Dict[str, List[str]]] = {}

    names_numbered: Dict[int, Dict[str, List[str]]] = {}

    types: Dict[int, Dict[str, List[str]]] = {}

    lengths: Dict[int, Dict[str, List[float]]] = {}

    xpos: Dict[int, Dict[str, List[float]]] = {}

    ypos: Dict[int, Dict[str, List[float]]] = {}

    zpos: Dict[int, Dict[str, List[float]]] = {}

    params: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}

    nala_elems: Dict[int, Dict[str, Dict[str, Element]]] = {}

    branches: Dict[int, List[str]] = {}

    def model_post_init(self, __context: Any) -> None:
        tao = Tao(
            f"-init {self.floorplan_init} -noplot",
            so_lib=self.libtao,
        )
        while True:
            try:
                tao.universe(str(self.n_universes))
                self.branches.update(
                    {
                        self.n_universes: [f'{i["branch_name"]}_{self.n_universes}' for i in
                                           tao.lat_branch_list(ix_uni=self.n_universes)]
                    }
                )
                self.names.update({self.n_universes: {}})
                self.names_numbered.update({self.n_universes: {}})
                self.types.update({self.n_universes: {}})
                self.lengths.update({self.n_universes: {}})
                self.xpos.update({self.n_universes: {}})
                self.ypos.update({self.n_universes: {}})
                self.zpos.update({self.n_universes: {}})
                self.params.update({self.n_universes: {}})
                self.nala_elems.update({self.n_universes: {}})
                for ind, b in enumerate(self.branches[self.n_universes]):
                    kwa = {"ix_uni": str(self.n_universes), "ix_branch": b.replace(f"_{self.n_universes}", "")}
                    names = [i for i in tao.lat_list("*", "ele.name", **kwa)]
                    names_numbered = [f"{x}.{(c := Counter(names[:i + 1]))[x]}" for i, x in enumerate(names)]
                    types = [i for i in tao.lat_list("*", "ele.key", **kwa)]
                    lengths = [i for i in tao.lat_list("*", "ele.l", **kwa)]
                    xpos = [i for i in tao.lat_list("*", "orbit.floor.x", **kwa)]
                    ypos = [i for i in tao.lat_list("*", "orbit.floor.y", **kwa)]
                    zpos = [i for i in tao.lat_list("*", "orbit.floor.z", **kwa)]
                    params = [tao.ele_gen_attribs(f"{str(self.n_universes)}@{ind}>>{i}") for i in range(len(names))]
                    self.names[self.n_universes].update({b: names})
                    self.names_numbered[self.n_universes].update({b: names_numbered})
                    self.types[self.n_universes].update({b: types})
                    self.lengths[self.n_universes].update({b: lengths})
                    self.xpos[self.n_universes].update({b: xpos})
                    self.ypos[self.n_universes].update({b: ypos})
                    self.zpos[self.n_universes].update({b: zpos})
                    self.params[self.n_universes].update({b: params})
                    self.nala_elems[self.n_universes].update({b: {}})
                self.n_universes += 1
            except TaoCommandError:
                break
        self.branches = {
            k: [f'{i["branch_name"]}_{k}' for i in tao.lat_branch_list(ix_uni=k)] for k in
            range(1, self.n_universes)
        }

    def create_element_dictionary(self, universe: int) -> None:
        for b in self.names_numbered[universe].keys():
            for i, nam in enumerate(self.names_numbered[universe][b]):
                middle = [
                    self.xpos[universe][b][i],
                    self.ypos[universe][b][i],
                    (self.zpos[universe][b][i] - self.lengths[universe][b][i] / 2)
                ]
                forward = (
                    self.xpos[universe][b][i],
                    self.ypos[universe][b][i],
                    self.zpos[universe][b][i] - self.lengths[universe][b][i],
                )
                pitch, roll, yaw = rotation_angles(forward)

                elem_data = {}
                parameters = self.params[universe][b][i]
                if self.types[universe][b][i] == "Kicker":
                    hardware_type = "Combined_Corrector"
                    horizontal = nam + "_H"
                    vertical = nam + "_V"
                    hcor = {
                        "magnetic": {
                            "order": 0,
                            "length": self.lengths[universe][b][i],
                            "kl": parameters["HKICK"],
                        }
                    }
                    vcor = {
                        "magnetic": {
                            "order": 0,
                            "length": float(self.lengths[universe][b][i]),
                            "kl": parameters["VKICK"],
                        }
                    }
                    elem_data = {
                        "hardware_type": hardware_type,
                        "Horizontal_Corrector": horizontal,
                        "Vertical_Corrector": vertical,
                        "hcor": hcor,
                        "vcor": vcor,
                    }
                elif self.types[universe][b][i] in magnetic_orders:
                    hardware_type = self.types[universe][b][i]
                    try:
                        kl = {"kl": parameters[f"K{magnetic_orders[hardware_type]}"]}
                    except KeyError:
                        kl = {
                            "kl": parameters["ANGLE"],
                            "entrance_edge_angle": parameters["E1"],
                            "exit_edge_angle": parameters["E2"],
                        }
                    if "GAP" in parameters:
                        kl.update({"GAP": parameters["GAP"]})
                    elem_data = {
                        "hardware_type": hardware_type,
                        "magnetic": {
                            "order": magnetic_orders[hardware_type],
                            "length": float(self.lengths[universe][b][i]),
                            **kl,
                        }
                    }

                elems = {
                        nam: {
                            "physical": {
                                "position": middle,
                                "global_rotation": [pitch, roll, yaw, ],
                                "length": float(self.lengths[universe][b][i]),
                            },
                            "name": nam,
                            "hardware_class": "Magnet",
                            "hardware_type": "Combined_Corrector",
                            "machine_area": "test",
                        }
                    }
                elems.update(**elem_data)
                if self.types[universe][b][i] == "Kicker":
                    helem = elems.copy()
                    helem.update(
                        {
                            "name": horizontal,
                            "hardware_type": "Horizontal_Corrector",
                            "magnetic": hcor,
                        }
                    )
                    velem = elems.copy()
                    velem.update(
                        {
                            "name": vertical,
                            "hardware_type": "Vertical_Corrector",
                            "magnetic": vcor,
                        }
                    )
                    comb = Combined_Corrector(**elems[nam])
                    hori = Horizontal_Corrector(**elems[nam])
                    vert = Vertical_Corrector(**elems[nam])
                    self.nala_elems[universe][b].update(
                        {
                            nam: comb,
                            horizontal: hori,
                            vertical: vert,
                        },
                    )
                elif self.types[universe][b][i] in magnetic_orders:
                    if self.types[universe][b][i] in ["RBend", "SBend"]:
                        self.types[universe][b][i] = "Dipole"
                    self.nala_elems[universe][b].update(
                        {
                            nam: getattr(NALA_elements, self.types[universe][b][i])(**elems[nam])
                        }
                    )

    def create_section(self, universe: int, branch: str) -> Dict[str, SectionLattice]:
        if not self.elements:
            self.create_element_dictionary(universe)
        order = list(self.nala_elems[universe][branch].keys())
        elems = self.nala_elems[universe][branch]
        seclat = SectionLattice(order=order, elements=ElementList(elements=elems), name=branch)
        return {branch: seclat}

    def create_layout(self, universe: int) -> Dict[str, MachineLayout]:
        layout = {}
        for branch in list(self.names_numbered[universe].keys()):
            layout.update(**self.create_section(universe, branch))
        return {str(universe): MachineLayout(name=str(universe), sections=layout)}
