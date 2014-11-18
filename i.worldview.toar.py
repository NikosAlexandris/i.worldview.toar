#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MODULE:         i.worldview.toar

AUTHOR:         Nikos Alexandris <nik@nikosalexandris.net>
                Converted from a bash shell script | Trikala, November 2014


PURPOSE:        Converting WorldView2 DN values to Spectral Radiance or
                    Reflectance

                From the document: ------------------------------------------
                Whether the final bit depth is 16 or 8 bits, the goal of the
                radiometric correction, other than minimize image artifacts,
                is to scale all image pixels to top-of-atmosphere spectral
                radiance so that one absolute calibration factor can be applied
                to all pixels in a given band.
                -------------------------------------------------------------
                The absolute radiometric calibration factor is dependent on the
                specific band, as well as the TDI exposure level, line rate,
                pixel aggregration, and bit depth of the product. Based on
                these parameters, the appropriate value is provided in the
                .IMD file. For this reason, care should be taken not to mix
                absolute radiometric calibration factors between products that
                might have different collection conditions.
                -------------------------------------------------------------

                Spectral Radiance -------------------------------------------

                L(λ|Pixel, Band) = K(Band) * q(Pixel, Band) / Δ(λ|Band)

                where:

                L(λ): Top-of-Atmosphere Spectral Radiance image pixels
                [W/sq.m./sr/μm]
                KBand: absolute radiometric calibration factor
                [W/sq.m./sr/count] for a given band
                q(Pixel,Band): radiometrically corrected image pixels
                [countsor  or  Digital Numbers]
                Δ(λ|Band): effective bandwidth [μm] for a given band.

                Planetary Reflectance ---------------------------------------

                    ρ(p) = π x L(λ) x d^2 / ESUN(λ) x cos(θ(S))

                where:
                - ρ: Unitless Planetary Reflectance
                - π: Mathematical constant
                - L(λ): Spectral Radiance from equation (1)
                - d: Earth-Sun distance in astronomical units [calculated using
                AcquisitionTime class]


                Sources -----------------------------------------------------

                Radiometric Use of WorldView-2 Imagery, Technical Note (2010),
                by Todd Updike & Chris Comp


 COPYRIGHT:    (C) 2014 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

#%Module
#%  description: Converting WorlView2 (radiometrically corrected) digital numbers to Top-of-Atmosphere Spectral Radiance or Reflectance  (Krause, 2005)
#%  keywords: imagery, radiometric conversion, radiance, reflectance, WorldView2
#%End

#%flag
#%  key: r
#%  description: Convert to at-sensor spectral radiance
#%end

#%flag
#%  key: k
#%  description: Keep current computational region settings
#%end

#%flag
#%  key: i
#%  description: Print out coversion formulas (Krause, 2005)
#%end

#%option G_OPT_R_INPUTS
#% key: band
#% key_desc: band name
#% type: string
#% label: WorldView2 band
#% description: WorldView2 acquired spectral band(s) (DN values)
#% multiple: yes
#% required: yes
#%end

#%option G_OPT_R_BASENAME_OUTPUT
#% key: outputsuffix
#% key_desc: suffix string
#% type: string
#% label: output file(s) suffix
#% description: Suffix for spectral radiance or reflectance output image(s)
#% required: yes
#% answer: toar
#%end

#%option
#% key: utc
#% key_desc: YYYY_MM_DDThh:mm:ss:ddddddZ; or YYYY-MM-DDThh:mm:ss:ddddddZ;
#% type: string
#% label: UTC
#% description: Coordinated Universal Time string as identified in the acquisition's metadata file (.IMD)
#% guisection: Metadata
#% required: no
#%end

#%option
#% key: doy
#% key_desc: day of year
#% type: integer
#% label: Day of Year
#% description: User defined aquisition's Day of Year (Julian Day) to calculate Earth-Sun distance. Will override UTC string input.
#% options: 1-365
#% guisection: Metadata
#% required: no
#%end

#%option
#% key: sea
#% key_desc: degrees
#% type: double
#% label: Sun Elevation Angle
#% description: Aquisition's mean sun elevation angle
#% options: 0.0 - 90.0
#% guisection: Metadata
#% required: yes
#%end

# required librairies -------------------------------------------------------
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]),
                                'etc', 'i.worldview.toar'))

import atexit
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.raster.abstract import Info

import math
from utc_to_esd import AcquisitionTime, jd_to_esd

# globals -------------------------------------------------------------------
acq_tim = ''
tmp = ''
tmp_rad = ''
tmp_toar = ''


# constants ----------------------------------------------------------------
"""
Factors for Conversion to Top-of-Atmosphere Spectral Radiance
    (absolute radiometric calibration factors)

Structure of the dictionary:
- Key: Name of band
- Items in tupple(s):
    - 1st: Absolute Calibration Factors
    - 2nd: Spectral Band's Effective Bandwidth, Δλ
    - 3rd: Band-Averaged Solar Spectral Irradiance [W/sq.m./micro-m]

Retrieving values:
    band = <Name of Band>
    K[band][0]  # for Effective Bandwidth
    K[band][1]  # for Esun
    K[band][2]  # for Absolute Conversion Factor
"""

CF_BW_ESUN = {
    'Pan':     (0.28460000, 1580.8140, 0.056783450),
    'Coastal': (0.04730000, 1758.2229, 0.009295654),
    'Blue':    (0.05430000, 1974.2416, 0.012608250),
    'Green':   (0.06300000, 1856.4104, 0.009713071),
    'Yellow':  (0.03740000, 1738.4791, 0.005829815),
    'Red':     (0.05740000, 1559.4555, 0.011036230),
    'RedEdge': (0.03930000, 1342.0695, 0.005188136),
    'NIR1':    (0.09890000, 1069.7302, 0.012243800),
    'NIR2':    (0.09960000,  861.2866, 0.009042234)}

spectral_bands = CF_BW_ESUN.keys()

# string for metadata
source1_rad = source1_toar = '''"Radiometric Use of WorldView-2 Imagery,
                                 Technical Note (2010)", by Todd Updike &
                                 Chris Comp'''

source2_rad = source2_toar = ""


# helper functions ----------------------------------------------------------
def cleanup():
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.%s*' % os.getpid(), quiet=True)


def run(cmd, **kwargs):
    """ """
    grass.run_command(cmd, quiet=True, **kwargs)


def main():

    global acq_time, esd

    """1st, get input, output, options and flags"""

    spectral_bands = options['band'].split(',')
    outputsuffix = options['outputsuffix']
    utc = options['utc']
    doy = options['doy']
    sea = options['sea']

    radiance = flags['r']
    if radiance and outputsuffix == 'toar':
        outputsuffix = 'rad'
        g.message("Output-suffix set to %s" % outputsuffix)

    keep_region = flags['k']
    info = flags['i']

    # -----------------------------------------------------------------------
    # Equations
    # -----------------------------------------------------------------------

    if info:
        # conversion to Radiance based on (1)
        msg = "|i Spectral Radiance = K * DN / Effective Bandwidth | " \
              "Reflectance = ( Pi * Radiance * ESD^2 ) / BAND_Esun * cos(SZA)"
        g.message(msg)

    # -----------------------------------------------------------------------
    # List images and their properties
    # -----------------------------------------------------------------------

    mapset = grass.gisenv()['MAPSET']  # Current Mapset?

#    imglst = [pan]
#    imglst.extend(msxlst)  # List of input imagery

    images = {}
    for img in spectral_bands:  # Retrieving Image Info
        images[img] = Info(img, mapset)
        images[img].read()

    # -----------------------------------------------------------------------
    # Temporary Region and Files
    # -----------------------------------------------------------------------

    if not keep_region:
        grass.use_temp_region()  # to safely modify the region
    tmpfile = grass.tempfile()  # Temporary file - replace with os.getpid?
    tmp = "tmp." + grass.basename(tmpfile)  # use its basename

    # -----------------------------------------------------------------------
    # Global Metadata: Earth-Sun distance, Sun Zenith Angle
    # -----------------------------------------------------------------------

    # Earth-Sun distance
    if doy:
        g.message("|! Using Day of Year to calculate Earth-Sun distance.")
        esd = jd_to_esd(int(doy))

    elif (not doy) and utc:
        acq_utc = AcquisitionTime(utc)  # will hold esd (earth-sun distance)
        esd = acq_utc.esd

    else:
        grass.fatal(_("Either the UTC string or "
                      "the Day-of-Year (doy) are required!"))

    sza = 90 - float(sea)  # Sun Zenith Angle based on Sun Elevation Angle

    # -----------------------------------------------------------------------
    # Loop processing over all bands
    # -----------------------------------------------------------------------
    for band in spectral_bands:

        global tmp_rad

        # -------------------------------------------------------------------
        # Match bands region if... ?
        # -------------------------------------------------------------------

        if not keep_region:
            run('g.region', rast=band)   # ## FixMe?
            msg = "\n|! Region matching the %s spectral band" % band
            g.message(msg)

        elif keep_region:
            msg = "|! Operating on current region"
            g.message(msg)

        # -------------------------------------------------------------------
        # Band dependent metadata for Spectral Radiance
        # -------------------------------------------------------------------

#        # which Pan TDI level?
#        if band == 'Pan':
#            band_key = band + tdi
#            g.message("\n|* Processing the Panchromatic band (TDI level: %s)"
#                      % tdi, flags='i')
#        else:
#            band_key = band
#            # some echo...
        g.message("\n|* Processing the %s band"
                      % band, flags='i')

        # Why is this necessary?  Any function to remove the mapsets name?
        if '@' in band:
            band = (band.split('@')[0])

        # get absolute calibration factor
        acf = float(CF_BW_ESUN[band][2])
        acf_msg = "K=" + str(acf)

        # effective bandwidth
        bw = float(CF_BW_ESUN[band][0])

        # -------------------------------------------------------------------
        # Converting to Spectral Radiance
        # -------------------------------------------------------------------

        msg = "\n|> Converting to Spectral Radiance " \
              "| Conversion Factor %s, Bandwidth=%.3f" % (acf_msg, bw)
        g.message(msg)

        # convert
        tmp_rad = "%s.Radiance" % tmp  # Temporary Map
        rad = "%s = %f * %s / %f" \
            % (tmp_rad, acf, band, bw)  # Attention: 32-bit calculations requ.
        grass.mapcalc(rad, overwrite=True)

        # strings for metadata
        history_rad = rad
        history_rad += "Conversion Factor=%f; Effective Bandwidth=%.3f" \
            % (acf, bw)
        title_rad = ""
        description_rad = "Top-of-Atmosphere %s band spectral Radiance " \
                          "[W/m^2/sr/μm]" % band
        units_rad = "W / sq.m. / μm / ster"

        if not radiance:

            # ---------------------------------------------------------------
            # Converting to Top-of-Atmosphere Reflectance
            # ---------------------------------------------------------------

            global tmp_toar

            msg = "\n|> Converting to Top-of-Atmosphere Reflectance"
            g.message(msg)

            esun = float(CF_BW_ESUN[band][1])
            msg = "   %s band mean solar exoatmospheric irradiance=%.2f" \
                % (band, esun)
            g.message(msg)

            # convert
            tmp_toar = "%s.Reflectance" % tmp  # Spectral Reflectance
            toar = "%s = %f * %s * %f^2 / %f * cos(%f)" \
                % (tmp_toar, math.pi, tmp_rad, esd, esun, sza)
            grass.mapcalc(toar, overwrite=True)

            # report range? Using a flag and skip actual conversion?
            # todo?

            # strings for metadata
            title_toar = "%s band (Top of Atmosphere Reflectance)" % band
            description_toar = "Top of Atmosphere %s band spectral Reflectance" \
                % band
            units_toar = "Unitless planetary reflectance"
            history_toar = "K=%f; Bandwidth=%.1f; ESD=%f; Esun=%.2f; SZA=%.1f" \
                % (acf, bw, esd, esun, sza)

        if tmp_toar:

            # history entry
            run("r.support", map=tmp_toar, title=title_toar,
                units=units_toar, description=description_toar,
                source1=source1_toar, source2=source2_toar,
                history=history_toar)

            # add suffix to basename & rename end product
            toar_name = ("%s.%s" % (band.split('@')[0], outputsuffix))
            run("g.rename", rast=(tmp_toar, toar_name))

        elif tmp_rad:

            # history entry
            run("r.support", map=tmp_rad,
                title=title_rad, units=units_rad, description=description_rad,
                source1=source1_rad, source2=source2_rad, history=history_rad)

            # add suffix to basename & rename end product
            rad_name = ("%s.%s" % (band.split('@')[0], outputsuffix))
            run("g.rename", rast=(tmp_rad, rad_name))

    # visualising-related information
    if not keep_region:
        grass.del_temp_region()  # restoring previous region settings
    g.message("\n|! Region's resolution restored!")
    g.message("\n>>> Hint: rebalancing colors "
              "(i.colors.enhance) may improve appearance of RGB composites!",
              flags='i')

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
