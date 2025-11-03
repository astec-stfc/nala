# python
from nala.models.magnetic import (
    Multipole,
    Multipoles,
    FieldIntegral,
    LinearSaturationFit,
    MagneticElement,
    Dipole_Magnet,
    Quadrupole_Magnet,
    Sextupole_Magnet,
    Octupole_Magnet,
    Solenoid_Magnet,
    SolenoidFields,
    NonLinearLens_Magnet,
    Wiggler_Magnet,
)

def test_multipole_initialization():
    m = Multipole(order=1, normal=0.5, skew=0.2)
    assert m.order == 1
    assert m.normal == 0.5
    assert m.skew == 0.2

def test_multipoles_operations():
    multipoles = Multipoles(K1L={"order": 1, "normal": 0.5})
    assert multipoles.normal(1) == 0.5
    assert multipoles.K1L.order == 1

def test_field_integral_current_to_k():
    fi = FieldIntegral(coefficients=[1, 2, 3])
    k = fi.currentToK(current=10, energy=100)
    assert k > 0

def test_linear_saturation_fit_current_to_k():
    lsf = LinearSaturationFit(m=1, I_max=10, f=0.1, a=0.2, I0=5, d=0.3, L=1)
    result = lsf.currentToK(current=5, momentum=100)
    assert "K" in result
    assert result["K"] > 0

def test_magnetic_element_properties():
    me = MagneticElement(order=1, length=2.0, multipoles={"K1L": {"order": 1, "normal": 0.5}})
    assert me.KnL(1) == 0.5
    assert me.gradient(momentum=100) > 0

def test_dipole_magnet_properties():
    dipole = Dipole_Magnet(length=2.0)
    dipole.angle = 0.1
    assert dipole.rho > 0
    assert dipole.field_strength(momentum=100) > 0

def test_quadrupole_magnet_properties():
    quad = Quadrupole_Magnet(length=1.0, k1l=0.2)
    assert quad.k1l == 0.2

def test_sextupole_magnet_properties():
    sext = Sextupole_Magnet(length=1.0, k2l=0.2)
    assert sext.k2l == 0.2

def test_octupole_magnet_properties():
    sext = Octupole_Magnet(length=1.0, k3l=0.2)
    assert sext.k3l == 0.2

def test_solenoid_magnet_properties():
    solenoid = Solenoid_Magnet(length=1.0, ks=0.3)
    assert solenoid.ks == 0.3

def test_nonlinear_lens_magnet():
    lens = NonLinearLens_Magnet(length=1.0, integrated_strength=0.5)
    assert lens.integrated_strength == 0.5

def test_wiggler_magnet_properties():
    wiggler = Wiggler_Magnet(length=2.0, strength=1.0, period=0.1, num_periods=10)
    assert wiggler.normalized_strength > 0
    assert wiggler.poles == 20

def test_solenoid_fields():
    fields = SolenoidFields(S0L=0.5, S1L=0.3)
    assert fields.S0L == 0.5
    assert fields.S1L == 0.3