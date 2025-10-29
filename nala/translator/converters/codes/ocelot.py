import os
import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict
from typing import Dict
from scipy.spatial.transform import Rotation
from ocelot.cpbd.magnetic_lattice import MagneticLattice
import nala.models.element as NALA_elements
from . import magnetic_orders
from ...utils.functions import introspect_model_defaults
from ...conversion_rules.codes import ocelot_conversion
from warnings import warn

type_conversion_rules_Ocelot = ocelot_conversion.ocelot_conversion_rules


with open(
    os.path.dirname(os.path.abspath(__file__)) +
    "/../../conversion_rules/keywords/keyword_conversion_rules_ocelot.yaml",
    "r",
) as infile:
    keyword_conversion_rules = yaml.safe_load(infile)

class OcelotLatticeImporter(BaseModel):

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    name: str = "Lattice"

    machine_area: str = "Lattice"

    magnetic_lattice: MagneticLattice
    """Name of ELEGANT parameters file"""

    nala_elements: Dict = {}
    """Dictionary containing converted element objects"""

    def magnetic_lattice_to_elements(self):
        return self.lattice_to_cartesian_with_rotation(self.magnetic_lattice.sequence)

    def create_element_dictionary(self):
        elements = self.magnetic_lattice_to_elements()
        self.nala_elements = {}
        switch_dict = {f"{str(y).lower().split('.')[-1].strip("\'>")}_{x}": x for x, y in
                       type_conversion_rules_Ocelot.items()}

        for elem, pos_and_rot in elements.items():
            # if type(elem) not in switch_dict:
            #     warn(f"Ocelot element type {type(elem)} not convertible")
            typeconv = str(type(elem)).lower().split('.')[-1].strip("\'>")
            key = None
            for k, v in switch_dict.items():
                if v == k.split('_')[-1] and typeconv in k:
                    key = k
            if not key:
                warn(f"Could not find element type {type(elem)} for {elem.id}; "
                     f"setting as drift")
                key = "drift_drift"
            newobj = {
                "name": elem.id,
                "hardware_type": switch_dict[key],
                "hardware_class": switch_dict[key],
                "machine_area": self.machine_area}
            try:
                merged = keyword_conversion_rules[switch_dict[key].lower()] | keyword_conversion_rules["general"]
            except KeyError:
                merged = keyword_conversion_rules["general"]
            for sfparam, oceparam in merged.items():
                if hasattr(elem, oceparam):
                    newobj.update({sfparam: getattr(elem, oceparam)})
            sftype = switch_dict[key]
            try:
                if sftype == "Kicker":
                    model_fields = introspect_model_defaults(getattr(NALA_elements, "Combined_Corrector"))
                    newobj["hardware_type"] = "Combined_Corrector"
                elif "Cavity" not in sftype:
                    model_fields = introspect_model_defaults(getattr(NALA_elements, sftype.capitalize()))
                    newobj["hardware_type"] = sftype.capitalize()
                else:
                    model_fields = introspect_model_defaults(getattr(NALA_elements, sftype))
            except AttributeError:
                print(f"type {sftype} not recognized")
                newobj.update(
                    {
                        k: {
                            "hardware_type": "Drift",
                            "name": k,
                            "hardware_class": "Drift",
                            "machine_area": self.machine_area
                        }
                    }
                )
                continue
            for subk in ["magnetic", "cavity", "simulation", "diagnostic", "physical"]:
                if subk in model_fields:
                    newobj.update({subk: {}})
            for oceparam, value in elem.element.__dict__.items():
                oceparam = oceparam.lower()
                kwele = {y: x for x, y in merged.items()}
                for subk in model_fields:
                    if isinstance(model_fields[subk], dict):
                        if oceparam in ["k1", "k2", "k3", "angle"] and newobj['hardware_type'] in magnetic_orders:
                            if "magnetic" not in newobj:
                                newobj.update({"magnetic": {}})
                            try:
                                newobj["magnetic"]["kl"] = getattr(
                                    elem.element, f"k{magnetic_orders[newobj['hardware_type']]}"
                                ) * elem.l
                            except AttributeError:
                                newobj["magnetic"]["kl"] = elem.element.angle
                            newobj["magnetic"].update({oceparam: value})
                            newobj["hardware_class"] = "Magnet"
                        if oceparam in model_fields[subk] and hasattr(elem, oceparam):
                            newobj[subk].update({oceparam: getattr(elem, oceparam)})
                        elif oceparam in kwele:
                            if kwele[oceparam] in model_fields[subk]:
                                if not isinstance(model_fields[subk][kwele[oceparam]], str) or model_fields[subk][
                                    kwele[oceparam]]:
                                    try:
                                        if oceparam == "v" and "Cavity" in newobj["hardware_type"]:
                                            newobj["hardware_class"] = "RF"
                                            newobj[subk].update({kwele[oceparam]: getattr(elem, oceparam) * 1e9})
                                        else:
                                            newobj[subk].update({kwele[oceparam]: getattr(elem, oceparam)})
                                    except KeyError:
                                        pass
                                    except AttributeError:
                                        pass
            pos = pos_and_rot[0][::-1]
            rot = [float(pos_and_rot[1][0]), float(pos_and_rot[1][2]), float(pos_and_rot[1][1])]
            newobj["physical"]["position"] = pos
            newobj["physical"]["global_rotation"] = rot
            self.nala_elements.update({elem.id: getattr(NALA_elements, newobj["hardware_type"])(**newobj)})

    def save_lattice_file(self, filename: str, directory: str):
        if not self.nala_elements:
            self.create_framework_element_dictionary()
        save_lattice_file(self.nala_elements, filename, directory)

    @staticmethod
    def lattice_to_cartesian_with_rotation(elements) -> Dict:
        """
        Compute Cartesian coordinates [x, y, z] of accelerator lattice elements
        and the global rotation (Euler angles) at the MIDPOINT of each element.
        """

        x, y, z = 0.0, 0.0, 0.0
        theta_h = 0.0
        theta_v = 0.0
        elems, positions, rotations = [], [], []
        cumulative_R = np.eye(3)

        for elem in elements:
            if "bend" not in str(type(elem)).lower() or abs(getattr(elem, "angle", 0.0)) < 1e-9:
                # --- Drift ---
                L = elem.l
                # Direction vector
                dx = L * np.cos(theta_v) * np.cos(theta_h)
                dy = L * np.sin(theta_v)
                dz = L * np.cos(theta_v) * np.sin(theta_h)

                # Midpoint is halfway along the segment
                mid_x = x + dx / 2
                mid_y = y + dy / 2
                mid_z = z + dz / 2

                # Store midpoint
                euler_angles = Rotation.from_matrix(cumulative_R).as_euler('zyx', degrees=False)
                elems.append(elem)
                positions.append(np.array([mid_x, mid_y, mid_z]))
                rotations.append(euler_angles)

                # Move to exit for next element
                x += dx
                y += dy
                z += dz

            else:
                # --- Dipole Bend ---
                L, phi, tilt = elem.l, elem.angle, elem.tilt

                if np.isclose(tilt, 0):  # Horizontal bend (x-z plane)
                    R_bend = Rotation.from_euler('y', phi).as_matrix()
                    R_half = Rotation.from_euler('y', phi / 2).as_matrix()

                    R_geom = L / phi  # bending radius

                    # Center of curvature
                    cx = x - R_geom * np.sin(theta_h)
                    cz = z + R_geom * np.cos(theta_h)

                    # Midpoint (half of bend angle)
                    theta_mid = theta_h + phi / 2
                    mid_x = cx + R_geom * np.sin(theta_mid)
                    mid_y = y
                    mid_z = cz - R_geom * np.cos(theta_mid)

                    # Rotation halfway through bend
                    R_mid = cumulative_R @ R_half

                    euler_angles = Rotation.from_matrix(R_mid).as_euler('zyx', degrees=False)
                    elems.append(elem)
                    positions.append(np.array([mid_x, mid_y, mid_z]))
                    rotations.append(euler_angles)

                    # Update to exit of element
                    theta_h += phi
                    x = cx + R_geom * np.sin(theta_h)
                    z = cz - R_geom * np.cos(theta_h)
                    cumulative_R = cumulative_R @ R_bend

                elif np.isclose(tilt, np.pi / 2):  # Vertical bend (x-y plane)
                    R_bend = Rotation.from_euler('x', -phi).as_matrix()
                    R_half = Rotation.from_euler('x', -phi / 2).as_matrix()
                    R_geom = L / phi

                    cy = y - R_geom * np.cos(theta_v)

                    # Midpoint
                    theta_mid = theta_v + phi / 2
                    mid_y = cy + R_geom * np.cos(theta_mid)
                    mid_x = x
                    mid_z = z
                    R_mid = cumulative_R @ R_half

                    euler_angles = Rotation.from_matrix(R_mid).as_euler('zyx', degrees=False)
                    elems.append(elem)
                    positions.append(np.array([mid_x, mid_y, mid_z]))
                    rotations.append(euler_angles)

                    # Exit of element
                    theta_v += phi
                    y = cy + R_geom * np.cos(theta_v)
                    cumulative_R = cumulative_R @ R_bend

                else:
                    raise ValueError(f"Unrecognized tilt angle {tilt} for {elem.id}")

        positions_and_rotations = [(p, r) for p, r in zip(np.array(positions), np.array(rotations))]
        return {e: pr for e, pr in zip(elems, positions_and_rotations)}

    @staticmethod
    def _convert_k_to_kl(v) -> dict:
        newk = {}
        for n in range(1, 9):
            if hasattr(v, f"k{n}") and hasattr(v, "l"):
                newk.update({f"k{n}l": getattr(v, f"k{n}") * getattr(v, "l")})
        return newk