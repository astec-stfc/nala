.. _magnet:

Magnet Class
============

Magnet elements in :mod:`NALA` contain, in addition to the auxiliary information associated with the :ref:`element-class` (see :ref:`auxiliary`), detailed descriptions of the object's magnetic fields. Various magnet types are currently supported, including :ref:`multipole`, :ref:`solenoid`, :ref:`wiggler`, and :ref:`non-linear-lens`.
Every :py:class:`Magnet <nala.models.element.Magnet>` object has a ``magnetic`` attribute, described by a :py:class:`MagneticElement <nala.models.magnetic.MagneticElement>` instance, with various examples given below. 

.. _multipole:

Multipole Magnet
----------------

This class covers the majority of magnetic elements in many standard accelerator lattices, with various child classes such as :py:class:`Dipole_Magnet <nala.models.magnetic.Dipole_Magnet>` and :py:class:`Quadrupole_Magnet <nala.models.magnetic.Quadrupole_Magnet>` deriving from :py:class:`MagneticElement <nala.models.magnetic.MagneticElement>`, which has the following properties:

* ``order: int`` -- magnetic order, with ``dipole=0``, ``quadrupole=1``, and so on.
* ``skew: bool`` -- indicates whether the magnetic field is skewed with respect to the nominal axis.
* ``length: float`` -- magnetic length (does not need to be the same as the physical length defined in :ref:`physical-element`).
* ``multipoles: Multipoles`` -- magnetic multipoles; see :ref:`multipoles-class`.
* ``systematic_multipoles: Multipoles`` -- systematic additional multipoles.
* ``random_multipoles: Multipoles`` -- random additional multipoles.
* ``field_integral_coefficients: FieldIntegral`` -- coefficients for calculating magnetic field integrals.
* ``linear_saturation_coefficients: LinearSaturationFit`` -- coefficients used for converting between current and magnetic field strength.
* ``entrance_edge_angle: float`` -- angle made between the nominal beam path and the magnet entrance pole face.
* ``exit_edge_angle: float`` -- angle made between the nominal beam path and the magnet exit pole face.
* ``gap: float`` -- magnetic gap (default is 3.2 cm).
* ``bore: float`` -- magnet bore size (default is 3.7 cm).
* ``width: float`` -- width of magnet (default is 20 cm).
* ``tilt: float`` -- tilt angle with respect to the X-Z plane.

.. _multipoles-class:

Multipoles Class
~~~~~~~~~~~~~~~~

Each :py:class:`MagneticElement <nala.models.magnetic.MagneticElement>` class has a ``multipoles`` field, which consists of a dictionary of :py:class:`Multipole <nala.models.magnetic.Multipole>` items, up to 9th order, with each order defined as follows:

* ``order: int`` -- magnetic order.
* ``normal: float`` -- normalized magnetic strength in the nominal plane.
* ``skew: float`` -- skew component of normalized magnetic strength.
* ``radius: float`` -- magnetic radius.

The values in the ``multipoles`` attribute of the :py:class:`MagneticElement <nala.models.magnetic.MagneticElement>` class can be accessed via the ``KnL`` term, with ``n`` representing the magnetic order. So, to retrieve the normalized field strength of a :py:class:`Quadrupole_Magnet <nala.models.magnetic.Quadrupole_Magnet>`, one can call ``quad.KnL(1)``. Alternatively, one can call the ``quad.kl`` property which will retrieve the normalized field strength of the nominal order for that magnet. 

.. _solenoid:

Solenoid Magnet
----------------

Solenoid magnets comprise a different class of magnets, although their implementation is similar to that of :ref:`multipole`. The important difference with respect to standard multipoles is that, rather than the ``multipoles`` attribute, solenoids define ``fields``. This is an instance of :py:class:`SolenoidFields <nala.models.magnetic.SolenoidFields>` which has a similar structure to :py:class:`Multipoles <nala.models.magnetic.Multipoles>`, although with keys defined as ``SnL``. Furthermore, the solenoid strength can be set or retrieved as ``ks`` or ``field_amplitude``, with the former defined as :math:`K_s = \frac{ \partial B_s }{ \partial s }`, and the latter defining the peak solenoid field strength in Tesla. 

.. _wiggler:

Wiggler Magnet
--------------

Wigglers (or undulators) are defined using the following properties:

* ``length: float`` -- total length of wiggler
* ``strength: float`` -- wiggler strength K
* ``peak_magnetic_field: float``
* ``period: float``
* ``num_periods: int``
* ``helical: bool`` -- if this is ``False``, the wiggler is planar
* ``quadratic_roll_off_x: float``
* ``quadratic_roll_off_y: float``
* ``transverse_gradient_x: float``
* ``transverse_gradient_y: float``

.. _non-linear-lens:

NonLinearLens Magnet
--------------------

A non-linear lens is a thin lens with an elliptic magnetic potential :cite:`NonLinearLens` which can be used to create a fully integrable nonlinear lattice with large tune spread. Here, the MAD-X :cite:`MADX` convention is followed, and only the quadrupole component is included:

* ``integrated_strength: float`` -- the :math:`knll` term.
* ``dimensional_parameter: float`` -- the :math:`cnll` term.
