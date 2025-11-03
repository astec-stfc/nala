# python
import pytest
import numpy as np
from nala.models.physical import (
    Position,
    Rotation,
    ElementError,
    PhysicalElement,
)


def test_position_operations():
    p1 = Position(x=1, y=2, z=3)
    p2 = Position(x=4, y=5, z=6)
    assert (p1 + p2) == Position(x=5, y=7, z=9)
    assert (p2 - p1) == Position(x=3, y=3, z=3)
    assert p1.dot(p2) == 32
    assert p1.length() == pytest.approx(3.7417, rel=1e-3)

def test_rotation_operations():
    r1 = Rotation(phi=0.1, psi=0.2, theta=0.3)
    r2 = Rotation(phi=0.4, psi=0.5, theta=0.6)
    assert all(
        [np.isclose(x, y) for x, y in zip((r1 + r2).model_dump(), Rotation(phi=0.5, psi=0.7, theta=0.9).model_dump())])
    assert all(
        [np.isclose(x, y) for x, y in zip((r2 - r1).model_dump(), Rotation(phi=0.3, psi=0.3, theta=0.3).model_dump())])
    assert abs(r1) == Rotation(phi=0.1, psi=0.2, theta=0.3)

def test_element_error_initialization():
    error = ElementError(position=[1, 2, 3], rotation=[0.1, 0.2, 0.3])
    assert error.position == Position(x=1, y=2, z=3)
    assert error.rotation == Rotation(theta=0.1, phi=0.2, psi=0.3)

def test_physical_element_properties():
    pe = PhysicalElement(middle=[1, 2, 3], length=10, global_rotation=[-0.1, -0.2, -0.3])
    assert pe.start.x < pe.middle.x
    assert pe.end.z > pe.middle.z
    assert pe.rotation_matrix is not None