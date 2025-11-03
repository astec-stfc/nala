import re
import os
import numpy as np
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from nala.models.element import Magnet
from typing import Any, Dict, Type, get_args, get_origin, Union, Literal

class Counter(dict):
    def __init__(self, sub={}):
        super().__init__()
        self.sub = sub

    def counter(self, type):
        type = self.sub[type] if type in self.sub else type
        if type not in self:
            return 1
        return self[type] + 1

    def value(self, type):
        type = self.sub[type] if type in self.sub else type
        if type not in self:
            return 1
        return self[type]

    def add(self, type, n=1):
        type = self.sub[type] if type in self.sub else type
        if type not in self:
            self[type] = n
        else:
            self[type] += n
        return self[type]

def convert_numpy_types(v):
    if isinstance(v, dict):
        return {key: convert_numpy_types(item) for key, item in v.items()}
    elif isinstance(v, (np.ndarray, list, tuple)):
        try:
            return [convert_numpy_types(li) for li in v]
        except TypeError:
            return float(v)
    elif isinstance(v, (np.float64, np.float32, np.float16)):
        return float(v)
    elif isinstance(
        v,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        return int(v)
    elif isinstance(v, field):
        return convert_numpy_types(v.model_dump())
    else:
        return v

def _rotation_matrix(theta):
    return np.array(
        [
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-1 * np.sin(theta), 0, np.cos(theta)],
        ]
    )

def chop(expr, delta=1e-8):
    """Performs a chop on small numbers"""
    if isinstance(expr, (int, float, complex)):
        return 0 if -delta <= expr <= delta else expr
    else:
        return [chop(x, delta) for x in expr]

def lattice_to_cartesian(elements):
    """
    Compute Cartesian coordinates [x, y, z] of accelerator lattice elements
    from a sequence of drifts and dipoles in 3D.

    Parameters
    ----------
    elements : list of tuples
        Each element is defined as:
          ("drift", L)
          ("dipole_h", L, phi)   # horizontal bend (x-z plane)
          ("dipole_v", L, phi)   # vertical bend (x-y plane)
        where L = length, phi = bending angle in radians.

    Returns
    -------
    positions : list of tuples
        Cartesian coordinates (x, y, z) for element ends.
    """

    x, y, z = 0.0, 0.0, 0.0  # starting point
    theta_h = 0.0  # azimuth angle in horizontal (x-z)
    theta_v = 0.0  # elevation angle in vertical (x-y)
    positions = [(x, y, z)]

    for elem in elements:
        cond1 = elem.hardware_type.lower() != "dipole"
        cond2 = False
        if isinstance(elem, Magnet):
            if abs(elem.magnetic.angle) > 1e-9:
                cond2 = True
        if cond1 and cond2:
            L = elem.physical.length
            dx = L * np.cos(theta_v) * np.cos(theta_h)
            dy = L * np.sin(theta_v)
            dz = L * np.cos(theta_v) * np.sin(theta_h)
            x, y, z = x + dx, y + dy, z + dz
            positions.append((x, y, z))
        else:  # horizontal bend in x-z plane
            L, phi, tilt = elem.physical.length, elem.magnetic.angle, elem.magnetic.tilt
            if np.isclose(tilt, 0):
                R = L / phi
                cx = x - R * np.sin(theta_h)
                cz = z + R * np.cos(theta_h)
                theta_h_new = theta_h + phi
                x = cx + R * np.sin(theta_h_new)
                z = cz - R * np.cos(theta_h_new)
                theta_h = theta_h_new
            elif np.isclose(tilt, np.pi/2):
                R = L / phi
                cy = y - R * np.sin(theta_v)
                cz = z + R * np.cos(theta_v)
                theta_v_new = theta_v + phi
                y = cy + R * np.sin(theta_v_new)
                z = cz - R * np.cos(theta_v_new)
                theta_v = theta_v_new
            else:
                raise ValueError(f"Unrecognised tilt angle {tilt} for {elem.name}")
            positions.append((x, y, z))
    return positions

def sanitize_kwargs(model_cls: type[BaseModel], data: dict[str, Any]) -> dict[str, Any]:
    sanitized = {}
    for field_name, field in model_cls.model_fields.items():
        value = data.get(field_name, None)
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        if value is None:
            # Allow None if explicitly part of the annotation
            if origin is Union and type(None) in args:
                sanitized[field_name] = None
            continue

        if origin is Union:
            # Handle Union of types (including Optional)
            non_none_args = [arg for arg in args if arg is not type(None)]
            if any(_is_valid_type(value, arg) for arg in non_none_args):
                sanitized[field_name] = value
        elif origin is Literal:
            # Handle Literal values
            if value in args:
                sanitized[field_name] = value
        elif _is_valid_type(value, annotation):
            # Simple direct type match
            sanitized[field_name] = value

    return sanitized

def _is_valid_type(value: Any, annotation: Any) -> bool:
    """
    Helper to check if a value matches a type annotation.
    Handles edge cases like Literal at the leaf level.
    """
    origin = get_origin(annotation)
    if origin is Literal:
        return value in get_args(annotation)
    return isinstance(value, annotation)

def get_field_default(field: FieldInfo) -> Any:
    """Get the default value or instance from a field definition."""
    if callable(field.default_factory):
        try:
            return field.default_factory()
        except Exception:
            return "FACTORY_ERROR"
    if field.default is not None:
        return field.default
    return None

def introspect_model_defaults(
    model_cls: Type[BaseModel],
    flatten: bool = False,
    parent_key: str = "",
    separator: str = "_",
) -> Dict[str, Any]:
    """Recursively introspect a Pydantic model class, extracting default values (including nested)."""
    result = {}

    for field_name, field in model_cls.model_fields.items():
        default_value = get_field_default(field)

        # If the default value is a BaseModel (e.g., from default_factory), recurse
        if isinstance(default_value, BaseModel):
            nested = introspect_model_defaults(
                default_value.__class__,
                flatten=flatten,
                parent_key=f"{parent_key}{separator}{field_name}" if parent_key else field_name,
                separator=separator,
            )
            if flatten:
                result.update(nested)
            else:
                result[field_name] = nested
        else:
            key = f"{parent_key}{separator}{field_name}" if (flatten and parent_key) else field_name
            result[key] = default_value

    return result

def isevaluable(self, s):
    try:
        eval(s)
        return True
    except Exception:
        return False

def path_function(a):
    # a_drive, a_tail = os.path.splitdrive(os.path.abspath(a))
    # b_drive, b_tail = os.path.splitdrive(os.path.abspath(b))
    # if (a_drive == b_drive):
    #     return os.path.relpath(a, b)
    # else:
    if a:
        return os.path.abspath(a)
    return './'


def expand_substitution(self, param, subs={}, elements={}, absolute=False):
    if isinstance(param, str):
        subs["master_lattice_location"] = (
            path_function(self.master_lattice_location)+ "/"
        )
        regex = re.compile(r"\$(.*)\$")
        s = re.search(regex, param)
        if s:
            if isevaluable(self, s.group(1)) is True:
                replaced_str = str(eval(re.sub(regex, str(eval(s.group(1))), param)))
            else:
                replaced_str = re.sub(regex, s.group(1), param)
            for key in subs:
                replaced_str = replaced_str.replace(key, subs[key])
            if os.path.exists(replaced_str):
                replaced_str = path_function(replaced_str).replace("\\", "/")
                # print('\tpath exists', replaced_str)
            for e in elements.keys():
                if e in replaced_str:
                    print("Element is in string!", e, replaced_str)
            return replaced_str
        else:
            return param
    else:
        return param

def checkValue(self, d, default=None):
    if isinstance(d, dict):
        if "type" in d and d["type"] == "list":
            if "default" in d:
                return [
                    a if a is not None else b for a, b in zip(d["value"], d["default"])
                ]
            else:
                if isinstance(d["value"], list):
                    return [val if val is not None else default for val in d["value"]]
                else:
                    return None
        else:
            d["value"] = expand_substitution(self, d["value"])
            return (
                d["value"]
                if d["value"] is not None
                else d["default"] if "default" in d else default
            )
    elif isinstance(d, str):
        return (
            getattr(self, d)
            if hasattr(self, d) and getattr(self, d) is not None
            else default
        )

def tw_cavity_energy_gain(cavity):
    """
    Estimate energy gain in a travelling-wave RF cavity.

    Parameters:
        cavity (nala.models.element.RFCavity): RFCavity element

    Returns:
        float: Estimated energy gain [eV]
    """

    # Approximate effective accelerating gradient
    E_acc = cavity.field_amplitude * np.sin(np.pi * cavity.mode_numerator * 2 / cavity.mode_denominator / 2)

    # Total cavity length
    L_total = cavity.n_cells * cavity.cell_length

    # Energy gain in MeV (since 1 MV/m * 1 m = 1 MeV for charge = e)
    delta_W = E_acc * L_total * np.cos(np.pi * cavity.phase / 180)

    return delta_W
