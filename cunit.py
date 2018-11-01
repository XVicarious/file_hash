""" Enums for SI and IEC memory units """
from enum import IntEnum


class SIUnit(IntEnum):
    """ Definitions for SI and IEC units """
    _si = 1000  # Multiplier for SI units
    B = 1  # A single byte
    # SI Units
    KB = B * _si
    MB = KB * _si
    GB = MB * _si
    TB = GB * _si
    PB = TB * _si


class IECUnit(IntEnum):
    """ Definitions for IEC units """
    _iec = 1024  # Multiplier for IEC units
    B = 1  # A single byte
    # IEC Units
    KiB = B * _iec
    MiB = KiB * _iec
    GiB = MiB * _iec
    TiB = GiB * _iec
    PiB = TiB * _iec
