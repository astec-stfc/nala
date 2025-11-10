.. NALA documentation master file, created by
   sphinx-quickstart on Tue Sep 24 10:00:24 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

NALA: Not Another Lattice Architecture
======================================

**NALA** (Not Another Lattice Architecture) is a ``python`` package for handling particle accelerator lattice data.

This package provides a standardized interface for interacting with objects representing elements in an accelerator lattice. The intention is to collate as much information as possible about each element, in order to achieve the following goals:

* Representing a ground source of truth about a given particle accelerator lattice.
* Providing a basis for producing configurable simulation lattice files for a range of codes.
* Store auxiliary data -- mechanical, survey, electrical, for example.
* Provide a basic interface to the controls system for each element.

.. warning::
   | This site is currently **under construction**.
   | Some pages may have missing or incomplete reference documentation.

Architecture
------------

.. toctree::
   :maxdepth: 2

   Architecture/index
   Translator
   Examples

   
Participation
-------------

We welcome contributions and suggestions from the community! :mod:`NALA` is currently under active development,
and as such certain features may be missing or not working as expected. If you find any issues, please
raise it `here <https://github.com/astec-stfc/nala/issues>`_.

We are also happy to help with installation and setting up your accelerator lattice. 
   

.. API
   ---

.. toctree::
   :maxdepth: 2
   :caption: API
   
   nala.models

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


References
----------

.. bibliography::
   :style: unsrt
