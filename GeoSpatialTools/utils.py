"""
Utils
=====
Utility functions. Including Error classes and Warnings.
"""


class LatitudeError(ValueError):
    """Error for invalid Latitude Value"""

    pass


class DateWarning(Warning):
    """Warnning for Datetime Value"""

    pass
