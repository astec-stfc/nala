import os
import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticUndefinedType
from typing import Dict, List
import xtrack as xt
from xtrack.beam_elements.elements import _HasKnlKsl, Bend
from nala.models.elementList import (
    SectionLattice,
    MachineLayout,
    ElementList,
)
from . import magnetic_orders
from ...utils.functions import introspect_model_defaults
from ...conversion_rules.codes import xsuite_conversion
from warnings import warn

type_conversion_rules_xsuite_reversed = xsuite_conversion.xsuite_conversion_rules_reverse


with open(
    os.path.dirname(os.path.abspath(__file__)) +
    "/../../conversion_rules/keywords/keyword_conversion_rules_Xsuite.yaml",
    "r",
) as infile:
    keyword_conversion_rules = yaml.safe_load(infile)

class XsuiteLatticeConverter(BaseModel):

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    name: str = "Lattice"

    machine_area: str = "Lattice"

    line: xt.Line
    """Xsuite line"""

    elements: Dict = {}
    """Dictionary containing converted element objects"""

    sections: Dict = {}

    layouts: Dict = {}

    def rotation_matrix_from_survey(self, row):
        """Builds rotation matrix (local→global) from survey row."""
        R = np.array([
            [row["ex"][0], row["ex"][1], row["ex"][2]],
            [row["ey"][0], row["ey"][1], row["ey"][2]],
            [row["ez"][0], row["ez"][1], row["ez"][2]],
        ])
        return R

    def Ry(self, angle):
        """Rotation matrix about local y axis."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, 0, s],
                         [0, 1, 0],
                         [-s, 0, c]])

    def compute_element_center(self, P0, R0, L, theta=0.0):
        """
        Given start position/orientation, return global center position and orientation.
        theta is total bending angle (radians); positive = bend right (horizontal plane).
        """
        # --- position of midpoint in local coordinates ---
        if abs(theta) < 1e-12:  # straight
            local_mid = np.array([0.0, 0.0, L / 2])
        else:
            Rbend = L / theta
            phi = theta / 2
            local_mid = np.array([
                Rbend * (1 - np.cos(phi)),  # x
                0.0,  # y
                Rbend * np.sin(phi)  # s
            ])

        # --- global midpoint ---
        Pcenter = P0 + R0 @ local_mid

        # --- global rotation at center ---
        if abs(theta) < 1e-12:
            Rcenter = R0
        else:
            Rcenter = R0 @ self.Ry(theta / 2)

        return Pcenter, Rcenter

    # Example for a batch of elements:
    def midpoints_for_line(self, element_and_survey,
                           local_axes_map=None):
        """
        Compute midpoints for many elements.

        Inputs
        - survey_positions: (N,3) array of start positions P0 for each element
        - survey_rotations: (N,3,3) array of rotations R0 for each element
          (R0 maps local->global)
        - elements: sequence of element-objects or dicts, each must provide:
            - length: float
            - angle: float   # bending angle in radians; if absent treated as 0
          Accepts any object where `getattr(el,'length')` and `getattr(el,'angle',0.0)` work,
          or dict-like with keys 'length' and 'angle'.
        - local_axes_map: see element_midpoint_global

        Returns
        - mids: (N,3) ndarray of midpoint positions
        """
        elem_pos = {}
        yhat = np.array([0, 1, 0])  # assuming horizontal bending plane

        for i, survey in enumerate(element_and_survey.values()):
            el = self.line.elements[i]
            # try several common attribute names for angle (xtrack names vary)
            L = getattr(el, 'length', getattr(el, 'L', 0.0))
            theta = getattr(el, 'angle', getattr(el, 'bending_angle', 0.0))
            P0 = np.array([survey["x"], survey["y"], survey["z"]])
            R0 = self.rotation_matrix_from_survey(survey)

            Pmid, Rmid = self.compute_element_center(P0, R0, L, theta)
            ex, ey, ez = Rmid[:, 0], Rmid[:, 1], Rmid[:, 2]

            elem_pos.update(
                {
                    list(element_and_survey.keys())[i]: {
                        "x": Pmid[0],
                        "y": Pmid[1],
                        "z": Pmid[2],
                        "phi": survey["phi"],
                        "psi": survey["psi"],
                        "theta": survey["theta"],
                    }
                }
            )
        return elem_pos

    def create_element_dictionary(self):
        s = self.line.survey()._data
        elems = {k: v for k, v in zip(s["name"], self.line.elements)}
        survey = {
            s["name"][i]: {
                "x": s["X"][i],
                "y": s["Y"][i],
                "z": s["Z"][i],
                "ex": s["ex"][i],
                "ey": s["ey"][i],
                "ez": s["ez"][i],
                "phi": (s["phi"][i] + np.pi) % (2*np.pi) - np.pi,
                "psi": (s["psi"][i] + np.pi) % (2*np.pi) - np.pi,
                "theta": (s["theta"][i] + np.pi) % (2*np.pi) - np.pi,
            } for i in range(len(s["X"][:-1]))
        }
        survey = self.midpoints_for_line(survey)
        for k, v in elems.items():
            machine_area = "IOTA_v8pt4_madx"
            length = 0
            if hasattr(v, "length"):
                length = v.length
            pos = [float(x) for x in [survey[k]["x"], survey[k]["y"], survey[k]["z"]]]
            rot = [float(x) for x in [survey[k]["phi"], survey[k]["psi"], survey[k]["theta"]]]
            phys = {"middle": pos, "global_rotation": rot, "length": length}

            if type(v) in type_conversion_rules_xsuite_reversed:
                p_obj = type_conversion_rules_xsuite_reversed[type(v)]
                model_fields = introspect_model_defaults(p_obj)
                hardware_class = p_obj.model_fields["hardware_class"].default
                if not type(p_obj.model_fields["hardware_type"].default) == PydanticUndefinedType:
                    hardware_type = p_obj.model_fields["hardware_type"].default
                else:
                    hardware_type = hardware_class
                if type(hardware_class) == PydanticUndefinedType:
                    hardware_class = hardware_type
                newobj = {
                    "name": k,
                    "hardware_type": hardware_type,
                    "hardware_class": hardware_class,
                    "machine_area": machine_area,
                    "physical": phys,
                }
                try:
                    merged = keyword_conversion_rules[hardware_type.lower()] | keyword_conversion_rules["general"]
                except KeyError:
                    merged = keyword_conversion_rules["general"]
                except TypeError:
                    merged = keyword_conversion_rules["general"]
                for subk in ["magnetic", "cavity", "simulation", "diagnostic"]:
                    if subk in model_fields:
                        newobj.update({subk: {}})
                kwele = {y: x for x, y in merged.items()}
                exclude = ["order"]
                for name in dir(v):
                    for subk in model_fields:
                        if isinstance(model_fields[subk], dict) and name not in exclude:
                            if name in ["k1", "k2", "k3", "angle"] and isinstance(v, _HasKnlKsl):
                                if "magnetic" not in newobj:
                                    newobj.update({"magnetic": {"length": length}})
                                try:
                                    newobj["magnetic"]["kl"] = getattr(
                                        v, f"k{magnetic_orders[newobj['hardware_type']]}"
                                    ) * v.length
                                except AttributeError as e:
                                    print(e)
                                    newobj["magnetic"]["kl"] = getattr(v, name)
                                newobj["magnetic"].update({name: getattr(v, name)})
                                if name == "angle":
                                    newobj["magnetic"]["kl"] = newobj["magnetic"]["kl"] * -1
                                newobj["hardware_class"] = "Magnet"
                            if name in ["ks"]:
                                newobj.update({"magnetic": {"ks": v.ks, "length": v.length}})
                            if name in model_fields[subk]:
                                newobj[subk].update({name: getattr(v, name)})
                            elif name in kwele:
                                if kwele[name] in model_fields[subk]:
                                    if not isinstance(model_fields[subk][kwele[name]], str) or model_fields[subk][
                                        kwele[name]]:
                                        try:
                                            newobj[subk].update({kwele[name]: getattr(v, name)})
                                        except KeyError as e:
                                            print(e)
                                        except AttributeError as e:
                                            print(e)
                if "angle" in newobj["physical"]:
                    print(newobj)
                    newobj["physical"].update({"angle": newobj["physical"]["angle"] * -1})
                    print(newobj)
                self.elements.update({k: p_obj(**newobj)})
            else:
                warn(f"Type conversion {type(v)} not implemented")

    def create_section(self, start: str, end: str, name: str) -> Dict[str, SectionLattice]:
        if not self.elements:
            self.create_element_dictionary()
        appending = False
        order = []
        elems = {}
        if any([start not in self.elements.keys(), end not in self.elements.keys()]):
            raise KeyError(f"Could not find {start} or {end} in lattice; please check names")
        for name, elem in self.elements.items():
            if name == start:
                appending = True
            if appending:
                order.append(name)
                elems.update({name: elem})
            if name == end:
                appending = False
        if not elems:
            raise ValueError(f"Could not create list of elements; check {start} is before {end}")
        seclat = SectionLattice(order=order, elements=ElementList(elements=elems), name=name)
        self.sections.update({name: seclat})
        return {name: seclat}

    def create_layout(self, name: str, sections: List[Dict]) -> MachineLayout:
        if not self.elements:
            self.create_element_dictionary()
        layout_sections = {}
        for sec in sections:
            assert "name" in sec and "start" in sec and "end" in sec
            layout_sections.update(
                self.create_section(
                    start=sec["start"],
                    end=sec["end"],
                    name=sec["name"],
                )
            )
        layout = MachineLayout(
            name=name,
            sections={k: v for k, v in zip(list(layout_sections.keys()), list(layout_sections.values()))}
        )
        self.layouts.update({name: layout})
        return layout