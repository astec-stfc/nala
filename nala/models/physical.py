import numpy as np
from pydantic import field_validator, confloat, Field, AliasChoices
from typing import List, Type, Union

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
    def validate_position(cls, v: Union[Position, List, np.ndarray]) -> Position:
        if isinstance(v, (list, tuple, np.ndarray)) and len(v) == 3:
            return Position(x=v[0], y=v[1], z=v[2])
        elif isinstance(v, Position):
            return v
        else:
            raise ValueError("position should be a number or a list of floats")

    @field_validator("rotation", mode="before")
    @classmethod
    def validate_rotation(cls, v: Union[Rotation, List, np.ndarray]) -> Rotation:
        if isinstance(v, (list, tuple, np.ndarray)) and len(v) == 3:
            return Rotation(theta=v[0], phi=v[1], psi=v[2])
        elif isinstance(v, Rotation):
            return v
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

    angle: float = 0.0

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

    # def __add__(self, other: PhysicalElement) -> [Position, Rotation]:
    #     pass
    #
    # def __radd__(self, other: PhysicalElement) ->  -> [Position, Rotation]:
    #     pass
    #
    # def __sub__ (self, other: PhysicalElement) ->  -> [Position, Rotation]:
    #     pass

    @field_validator("middle", "datum", mode="before")
    @classmethod
    def validate_middle(cls, v: Union[float, int, List, np.ndarray]) -> Position:
        if isinstance(v, (float, int)):
            return Position(z=v)
        elif isinstance(v, (list, tuple, np.ndarray)):
            if len(v) == 3:
                return Position(x=v[0], y=v[1], z=v[2])
            elif len(v) == 2:
                return Position(x=v[0], y=0, z=v[1])
        elif isinstance(v, (Position)):
            return v
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
        elif isinstance(v, (Rotation)):
            return v
        else:
            raise ValueError("middle should be a number or a list of floats")

    @property
    def rotation_matrix(self) -> np.ndarray:
        """
        Get the rotation matrix of the element based on `rotation.theta` + `global_rotation.theta`.

        Returns
        -------
        np.ndarray
            Rotation matrix
        """
        return _rotation_matrix(self.rotation.theta + self.global_rotation.theta)

    def rotated_position(
        self, vec: List[Union[int, float]] = [0, 0, 0]
    ) -> List[Union[int, float]]:
        """
        Get the rotated position of the element  based on the dot product of `vec` with its :attr:`~rotation_matrix`.

        Parameters
        ----------
        vec: List[float]
            Vector by which to rotate the element

        Returns
        -------
        List[float]
            Dot product of `vec` with :attr:`~rotation_matrix`.
        """
        return np.dot(np.array(vec), self.rotation_matrix)

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
        sx = 0
        sy = 0
        sz = (
            1.0 * self.length * np.tan(0.5 * self.angle) / self.angle
            if hasattr(self, "angle") and abs(self.angle) > 1e-9
            else 1.0 * self.length / 2.0
        )
        vec = [sx, sy, sz]
        start = middle - self.rotated_position(vec)
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
        ex = (
            (self.length * (1 - np.cos(self.angle))) / self.angle
            if hasattr(self, "angle") and abs(self.angle) > 1e-9
            else 0
        )
        ey = 0
        ez = (
            (self.length * (np.sin(self.angle))) / self.angle
            if hasattr(self, "angle") and abs(self.angle) > 1e-9
            else self.length
        )
        vec = [ex, ey, ez]
        end = self.start.array + self.rotated_position(vec)
        return Position.from_list(end)
