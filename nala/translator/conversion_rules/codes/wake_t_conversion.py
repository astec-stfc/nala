from wake_t import (
    PlasmaStage,
    ActivePlasmaLens,
    Dipole,
    Quadrupole,
    Sextupole,
    GaussianPulse,
)

wake_t_conversion_rules = {
    "Dipole": Dipole,
    "Quadrupole": Quadrupole,
    "Sextupole": Sextupole,
    "Laser": GaussianPulse,
    "Plasma": PlasmaStage,
    "Plasma_Lens": ActivePlasmaLens,
}
