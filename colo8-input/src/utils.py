"""
Utility functions for well notation and string manipulation
"""

import re


def strip_zeros(well):
    """
    Remove the zero before the well number.

    Parameters
    ----------
    well : str
        Well notation with zero padding (e.g., 'A01', 'B12')

    Returns
    -------
    str
        Well notation without zero padding (e.g., 'A1', 'B12')

    Examples
    --------
    >>> strip_zeros('A01')
    'A1'
    >>> strip_zeros('B12')
    'B12'
    """
    number = re.split('(\d+)', well)[1].lstrip('0')
    letter = re.split('(\d+)', well)[0]
    new_well = letter + number
    return new_well


def strip_spaces(a_str_with_spaces):
    """
    Remove extra white spaces from a string.

    Parameters
    ----------
    a_str_with_spaces : str
        String potentially containing spaces

    Returns
    -------
    str
        String with all spaces removed

    Examples
    --------
    >>> strip_spaces('A 01')
    'A01'
    >>> strip_spaces('colo - 002')
    'colo-002'
    """
    # https://stackoverflow.com/questions/43332057/pandas-strip-white-space
    return a_str_with_spaces.replace(' ', '')
