============
Installation
============

``GeoSpatialTools`` is not currently available on PyPI so must be installed either from source or directly from the
GitLab repository.

We recommend the installation of ``GeoSpatialTools`` using the uv_ package manager, however it can be installed using
pip_.

Via UV
======

You can install the library directly from the GitLab repository, adding the library to your current uv virtual
environment. This will add the library as a dependency in your current project.

.. code-block:: bash

   uv add git+ssh://git@git.noc.ac.uk/nocsurfaceprocesses/geospatialtools.git

Development mode
----------------

If you wish to contribute to ``GeoSpatialTools`` you can install the library in development mode. This will require
cloning the repository and creating a new uv environment.

.. code-block:: bash

   git clone git@git.noc.ac.uk/nocsurfaceprocesses/geospatialtools.git
   cd geospatialtools
   uv sync --all-extras --dev --python 3.12  # Install with all dependencies and create an environment with python 3.12
   source .venv/bin/activate                 # Load the environment

The recommended python version is python 3.12. By default, uv creates a virtual environment in ``.venv``.

Via Pip
=======

The library can be installed via pip with the following command:

.. code-block:: bash

   pip install git+ssh://git@git.noc.ac.uk/nocsurfaceprocesses/geospatialtools.git

From Source
-----------

Alternatively, you can clone the repository and install using pip (or conda if preferred). This installs in ``editable``
mode.

.. code-block:: bash

   git clone git@git.noc.ac.uk/nocsurfaceprocesses/geospatialtools.git
   cd geospatialtools
   python -m venv venv
   source venv/bin/activate
   pip install -e .

.. include:: hyperlinks.rst
