import numpy as np
from pydantic import field_validator, confloat, Field, AliasChoices
from typing import List, Type, Union, Dict

from ._functions import _rotation_matrix

from .baseModels import IgnoreExtra, NumpyVectorModel, T


class Position(NumpyVectorModel):
    """
    Position model. Cartesian co-ordinates are used.
    """

    x: float = 0.0
    """Horizontal position [m]."""

    y: float = 0.0
    """Vertical position [m]."""

    z: float = 0.0
    """Longitudinal position [m]."""

    def __add__(self, other: Type[T]) -> T:
        return Position(
            x=(self.x + other.x), y=(self.y + other.y), z=(self.z + other.z)
        )

    def __radd__(self, other: Type[T]) -> T:
        return self.__add__(other)

    def __sub__(self, other: Type[T]) -> T:
        return Position(
            x=(self.x - other.x), y=(self.y - other.y), z=(self.z - other.z)
        )

    def __rsub__(self, other: Type[T]) -> T:
        return Position(
            x=(other.x - self.x), y=(other.y - self.y), z=(other.z - self.z)
        )

    def dot(self, other: Union[List, Type[T]]) -> float:
        if isinstance(other, (set, tuple, list)):
            other = Position.from_list(other)
        return self.x * other.x + self.y * other.y + self.z * other.z

    def vector_angle(self, other: Union[List, Type[T]], direction: List) -> float:
        if isinstance(other, (set, tuple, list)):
            other = Position.from_list(other)
        return (self - other).dot(direction)

    def length(self) -> float:
        return np.sqrt([self.x * self.x + self.y * self.y + self.z * self.z])


class Rotation(NumpyVectorModel):
    """
    Rotation model.
    """

    phi: confloat(ge=-np.pi, le=np.pi) = 0.0  # type: ignore
    """Rotation about the horizontal axis [rad]."""

    psi: confloat(ge=-np.pi, le=np.pi) = 0.0  # type: ignore
    """Rotation about the vertical axis [rad]."""

    theta: confloat(ge=-np.pi, le=np.pi) = 0.0  # type: ignore
    """Rotation about the longitudinal axis [rad]."""

    def __add__(self, other: Type[T]) -> T:
        return Rotation(
            phi=(self.phi + other.phi),
            psi=(self.psi + other.psi),
            theta=(self.theta + other.theta),
        )

    def __radd__(self, other: Type[T]) -> T:
        return self.__add__(other)

    def __sub__(self, other: Type[T]) -> T:
        return Rotation(
            phi=(self.phi - other.phi),
            psi=(self.psi - other.psi),
            theta=(self.theta - other.theta),
        )

    def __rsub__(self, other: Type[T]) -> T:
        return Rotation(
            phi=(other.phi - self.phi),
            psi=(other.psi - self.psi),
            theta=(other.theta - self.theta),
        )

    def __abs__(self):
        return Rotation(phi=abs(self.phi), psi=abs(self.psi), theta=abs(self.theta))

    def __gt__(self, value: Union[int, float, List, Type[T]]):
        if isinstance(value, (int, float)):
            return any([self.phi > value, self.psi > value, self.theta > value])
        elif isinstance(value, (Union[list, set, tuple])):
            return [self.phi, self.psi, self.theta] > value
        elif isinstance(value, Rotation):
            return any(
                [self.phi > value.phi, self.psi > value.psi, self.theta > value.theta]
            )


class ElementError(IgnoreExtra):
    """
    Position/Rotation error model.
    """

    position: Union[Position, List[Union[float, int]]] = Position(x=0, y=0, z=0)
    """Errors in position."""

    rotation: Union[Rotation, List[Union[float, int]]] = Rotation(theta=0, phi=0, psi=0)
    """Errors in rotation."""

    @field_validator("position", mode="before")
    @classmethod
    def validate_position(cls, v: Union[Position, Dict, List, np.ndarray]) -> Position:
        if isinstance(v, (list, tuple, np.ndarray)) and len(v) == 3:
            return Position(x=v[0], y=v[1], z=v[2])
        elif isinstance(v, Position):
            return v
        elif isinstance(v, dict):
            keys = list(v.keys())
            values = list(v.values())
            if all([x in keys for x in ["x", "y", "z"]]) and all([type(val) == float for val in values]) and len(
                    keys) == 3:
                return Position(**v)
            else:
                raise ValueError("setting middle as dictionary must include x, y, z as floats")

        else:
            raise ValueError("position should be a number or a list of floats")

    @field_validator("rotation", mode="before")
    @classmethod
    def validate_rotation(cls, v: Union[Rotation, Dict, List, np.ndarray]) -> Rotation:
        if isinstance(v, (list, tuple, np.ndarray)) and len(v) == 3:
            return Rotation(theta=v[0], phi=v[1], psi=v[2])
        elif isinstance(v, Rotation):
            return v
        elif isinstance(v, dict):
            keys = list(v.keys())
            values = list(v.values())
            if all([x in keys for x in ["phi", "psi", "theta"]]) and all(
                    [type(val) == float for val in values]) and len(keys) == 3:
                return Rotation(**v)
            else:
                raise ValueError("setting rotation as dictionary must include x, y, z as floats")

        else:
            raise ValueError("rotation should be a number or a list of floats")

    def __str__(self):
        cls = self.__class__
        if any([getattr(self, k) != 0 for k in cls.model_fields]):
            return " ".join(
                [
                    getattr(self, k).__repr__()
                    for k in cls.model_fields
                    if getattr(self, k) != 0
                ]
            )
        else:
            return str(None)

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.__str__() + ")"

    def __eq__(self, other):
        cls = self.__class__
        if other == 0:
            return all([getattr(self, k) == 0 for k in cls.model_fields.keys()])
        else:
            return super().__eq__(other)


class ElementSurvey(ElementError):
    pass


class PhysicalElement(IgnoreExtra):
    """
    Physical info model.
    """

    middle: Position = Field(default=Position(), alias=AliasChoices("position", "centre"))
    """Middle position of the element."""

    datum: Position = Field(default=0)
    """Datum."""

    rotation: Rotation = Rotation(theta=0, phi=0, psi=0)
    """Local rotation of the element."""

    global_rotation: Rotation = Rotation(theta=0, phi=0, psi=0)
    """Global rotation of the element."""

    error: ElementError = ElementError()
    """Position errors in the element."""

    survey: ElementSurvey = ElementSurvey()
    """Survey positions of the element."""

    length: float = 0.0
    """Length of the element."""

    physical_angle: float = 0.0
    """Physical angle"""

    def __str__(self):
        cls = self.__class__
        if any([getattr(self, k) != 0 for k in cls.model_fields.keys()]):
            return " ".join(
                [
                    str(k) + "=" + getattr(self, k).__repr__()
                    for k in cls.model_fields.keys()
                    if getattr(self, k) != 0
                ]
            )
        else:
            return str()

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.__str__() + ")"

    @field_validator("middle", "datum", mode="before")
    @classmethod
    def validate_middle(cls, v: Union[float, int, Dict, List, np.ndarray]) -> Position:
        if isinstance(v, (float, int)):
            return Position(z=v)
        elif isinstance(v, (list, tuple, np.ndarray)):
            if len(v) == 3:
                return Position(x=v[0], y=v[1], z=v[2])
            elif len(v) == 2:
                return Position(x=v[0], y=0, z=v[1])
        elif isinstance(v, Position):
            return v
        elif isinstance(v, dict):
            keys = list(v.keys())
            values = list(v.values())
            if all([x in keys for x in ["x", "y", "z"]]) and all([type(val) == float for val in values]) and len(
                    keys) == 3:
                return Position(**v)
            else:
                raise ValueError("setting middle as dictionary must include x, y, z as floats")

        else:
            raise ValueError("middle should be a number or a list of floats")

    @field_validator("rotation", "global_rotation", mode="before")
    @classmethod
    def validate_rotation(cls, v: Union[float, int, List, np.ndarray]) -> Rotation:
        if isinstance(v, (float, int)):
            return Rotation(theta=v)
        elif isinstance(v, (list, tuple, np.ndarray)):
            if len(v) == 3:
                return Rotation(phi=v[0], psi=v[1], theta=v[2])
        elif isinstance(v, Rotation):
            return v
        elif isinstance(v, dict):
            keys = list(v.keys())
            values = list(v.values())
            if all([x in keys for x in ["phi", "psi", "theta"]]) and all(
                    [type(val) == float for val in values]) and len(keys) == 3:
                return Rotation(**v)
            else:
                raise ValueError("setting rotation as dictionary must include x, y, z as floats")

        else:
            raise ValueError("rotation should be a number or a list of floats")

    @property
    def rotation_matrix(self) -> np.ndarray:
        """
        Get the 3D rotation matrix of the element based on combined rotations.
        Convention: [pitch, roll, yaw] = [rotation around X, rotation around Z, rotation around Y]

        Returns
        -------
        np.ndarray
            3x3 Rotation matrix
        """
        # Get the combined rotation angles
        pitch = self.rotation.phi + self.global_rotation.phi  # X rotation (pitch) - affects Y,Z
        roll = self.rotation.psi + self.global_rotation.psi  # Z rotation (roll) - affects X,Y
        yaw = self.rotation.theta + self.global_rotation.theta  # Y rotation (yaw) - affects X,Z

        # Rotation matrix around X axis (pitch)
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(pitch), -np.sin(pitch)],
            [0, np.sin(pitch), np.cos(pitch)]
        ])

        # Rotation matrix around Z axis (roll)
        Rz = np.array([
            [np.cos(roll), -np.sin(roll), 0],
            [np.sin(roll), np.cos(roll), 0],
            [0, 0, 1]
        ])

        # Rotation matrix around Y axis (yaw) - this is the horizontal bending
        Ry = np.array([
            [np.cos(yaw), 0, np.sin(yaw)],
            [0, 1, 0],
            [-np.sin(yaw), 0, np.cos(yaw)]
        ])

        # Combined rotation matrix - apply yaw first (most common), then pitch, then roll
        return Rx @ Rz @ Ry

    def rotated_position(
            self, vec: List[Union[int, float]] = [0, 0, 0]
    ) -> np.ndarray:
        """
        Get the rotated position of the element based on matrix multiplication with rotation_matrix.

        Parameters
        ----------
        vec: List[float]
            Vector by which to rotate the element

        Returns
        -------
        np.ndarray
            Rotated vector.
        """
        return self.rotation_matrix @ np.array(vec)

    @property
    def start(self) -> Position:
        """
        Start position of the element.

        Returns
        -------
        :class:`~nala.models.physical.Position
            Start position of the element.
        """
        middle = np.array(self.middle.array)

        # Calculate local offset from middle to start
        if abs(self.physical_angle) > 1e-9:
            # Bent element - correct arc geometry
            # The start is offset from middle by half the chord deviation
            sx = -self.length * (1 - np.cos(self.physical_angle)) / (2 * self.physical_angle)
            sy = 0
            sz = -self.length * np.sin(self.physical_angle) / (2 * self.physical_angle)
        else:
            # Straight element
            sx = 0
            sy = 0
            sz = -self.length / 2.0

        # Local offset vector
        vec = [sx, sy, sz]

        # Rotate to global coordinates and add to middle
        start = middle + self.rotated_position(vec)
        return Position.from_list(start)

    @property
    def end(self) -> Position:
        """
        End position of the element.

        Returns
        -------
        :class:`~nala.models.physical.Position
            End position of the element.
        """
        middle = np.array(self.middle.array)

        # Calculate local offset from middle to end
        if abs(self.physical_angle) > 1e-9:
            # Bent element - arc geometry (symmetric to start)
            ex = self.length * (1 - np.cos(self.physical_angle)) / (2 * self.physical_angle)
            ey = 0
            ez = self.length * np.sin(self.physical_angle) / (2 * self.physical_angle)
        else:
            # Straight element
            ex = 0
            ey = 0
            ez = self.length / 2.0

        # Local offset vector
        vec = [ex, ey, ez]

        # Rotate to global coordinates and add to middle
        end = middle + self.rotated_position(vec)
        return Position.from_list(end)