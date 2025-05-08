"""
Utils
=====
Utility functions. Including Error classes and Warnings.
"""


class LatitudeError(ValueError):
    """Error for invalid Latitude Value"""

    pass


class DateWarning(Warning):
    """Warning for Datetime Value"""

    pass
