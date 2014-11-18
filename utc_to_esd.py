# -*- coding: utf-8 -*-
"""
@author: Nikos Alexandris | Trikala, Wed Nov 12 16:22:18 2014
"""

"""
Code for the creation of an AcquisitionTime (python Class) object.
The Earth - Sun Distance is calculated and stored as an attribute of
the AcquisitionTime (python Class) object.

Source of Equations: "Radiometric Use of QuickBird Imagery. Technical Note".
2005-11-07, Keith Krause.
"""

import math


"""
The acquisition time in .IMD files, uses the UTC time format:
    YYYY_MM_DDThh:mm:ss:ddddddZ;
"""


# helper functions ----------------------------------------------------------


def extract_time_elements(utc):
    """Extracting Year, Month, Day, Hours, Minutes, Seconds from a
    UTC formatted time string in a new dictionary, named 'acq_utc'
    (as in 'acquisition time')"""
    acq_utc = {}
    acq_utc['year'] = int(utc[:4])
    # Modify for Jan, Feb ---------------------------------------------------
    acq_utc['month'] = int(utc[5:7])
    if acq_utc['month'] in (1, 2):
        acq_utc['year'] -= 1
        acq_utc['month'] += 12
        print "* Modification applied for January or February"
    # -----------------------------------------------------------------------
    acq_utc['day'] = int(utc[8:10])
    acq_utc['hours'] = int(utc[11:13])
    acq_utc['minutes'] = int(utc[14:16])
    acq_utc['seconds'] = float(utc[17:26])
    return acq_utc


def universal_time(hh, mm, ss):
    """Function converting hh:mm:ss to Universal Time"""
    ut = int(hh) + (int(mm) / 60.) + (float(ss) / 3600.)
    return ut


def julian_day(year, month, day, ut):
    """Function converting YYYY, MM, DD, UT to Julian Day"""

    # get B for Julian Day equation
    A = int(year / 100)
    B = 2 - A + int(A / 4)

    # calculate Julian Day
    jd = int(365.25 * (year + 4716)) + \
        int(30.6001 * (month + 1)) + \
        day + ut/24.0 + \
        B - 1525.5
    return float(jd)


def jd_to_esd(jd):
    """Function converting Julian Day to Earth-Sun distance
    (U.S. Naval Observatory)"""
    D = jd - 2451545.0
    g = 357.529 + 0.98560028 * D
    gr = math.radians(g)
    dES = 1.00014 - 0.01671 * math.cos(gr) - 0.00014 * math.cos(2 * gr)

    if 0.983 <= dES <= 1.017:  # check validity - not really necessary!
        return dES
    else:
        msg = "The result is an invalid Earth-Sun distance. " \
            "Please review input values!"
        raise ValueError(msg)


def utc_to_esd(utc):
    """Function converting UTC to Earth-Sun distance"""
    acqtim = extract_time_elements(utc)
    ut = universal_time(acqtim['hours'], acqtim['minutes'], acqtim['seconds'])
    jd = julian_day(acqtim['year'], acqtim['month'], acqtim['day'], ut)
    dES = jd_to_esd(jd)
    return dES


class AcquisitionTime:
    """Create an Acquisition Time object from a UTC string
    (of the form: YYYY_MM_DDThh:mm:ss:ddddddZ;).
    Meant to be used for... i.X.toar grass-gis python scripts"""
    def __init__(self, utc):
        self.utc = utc
        self.acq_utc = extract_time_elements(self.utc)
        self.year = self.acq_utc['year']
        self.month = self.acq_utc['month']
        self.day = self.acq_utc['day']
        self.hours = self.acq_utc['hours']
        self.minutes = self.acq_utc['minutes']
        self.seconds = self.acq_utc['seconds']

        self.ut = universal_time(self.hours, self.minutes, self.seconds)
        self.jd = julian_day(self.year, self.month, self.day, self.ut)
        self.esd = utc_to_esd(self.utc)

    def __str__(self):
        return "Acquisition time (UTC format): " + self.utc

#    def __str__(self):
#        return "Acquisition time (UTC format): " + self.utc + '\n' + \
#        "Julian Day: " + str(self.jd) + '\n' + \
#        "Earth-Sun Distance: " + str(self.esd)


"""Exemplifying"""

"""
utc = '2014_11_12T16:47:08.000000Z;'
utc_to_esd(utc)
utcstamp = utc_to_esd(utc) ; print "UTC Stamp: ", utcstamp
print utc_to_esd('2014_11_12T16:47:08.000000Z;')
"""

"""Example (from Krause, 2005), the QuickBird launch date of:
 October 18, 2001 at 18:51:26 GMT corresponds to the
 Julian Day 2452201.286."""

"""
utc_to_esd('2001_10_18T18:51:26.000000Z;')
print "Conversion: ", utc_to_esd('2001_10_18T18:51:26.000000Z;')
"""
