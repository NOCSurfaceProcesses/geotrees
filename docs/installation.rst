============
Installation
============

``geotrees`` is available on PyPI. Versions of python between 3.9 and 3.13, inclusive, are supported,
however the recommended version of python is 3.12.

We recommend the installation of ``geotrees`` using the uv_ package manager, however it can be installed using
pip_.

The only required dependency of the project is NumPy_. Additional dependency polars_ is required to run the Jupyter_
notebooks.

Via UV
======

You can install the library directly from pip, adding the library to your current uv virtual
environment. This will add the library as a dependency in your current project.

.. code-block:: bash

   uv add geotrees

Development mode
----------------

If you wish to contribute to ``geotrees`` you can install the library in development mode. This will require
cloning the repository and creating a new uv environment.

.. code-block:: bash

   # Get the code
   git clone git@github.com/NOCSurfaceProcesses/geotrees
   cd geotrees

   # Install with all dependencies and create an environment with python 3.12
   uv sync --all-extras --dev --python 3.12

   # Load the environment
   source .venv/bin/activate

   # Run the unit tests
   uv run pytest test

.. note:: The recommended python version is python 3.12. By default, uv creates a virtual environment in ``.venv``.

Via Pip
=======

The library can be installed via pip with the following command:

.. code-block:: bash

   pip install geotrees

From Source
-----------

Alternatively, you can clone the repository and install using pip (or conda if preferred). This installs in ``editable``
mode.

.. code-block:: bash

   git clone git@github.com/NOCSurfaceProcesses/geotrees
   cd geotrees
   python -m venv venv
   source venv/bin/activate
   pip install -e .

.. include:: hyperlinks.rst
