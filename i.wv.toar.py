# -*- coding: utf-8 -*-
"""
@author: nik | Created on Sat Nov  8 00:18:22 2014
"""

#!/bin/bash

# Lλ_(Pixel, Band) = ( K_Band ⋅ q_(Pixel, Band) / ∆λ_Band )

  # where

  # LλPixel,Band:  Top-of-Atmosphere Spectral Radiance image pixels [W/sq.m./sr/μm]
  # KBand:  the absolute radiometric calibration factor [W/sq.m./sr/count] for a given band
  # qPixel,Band:  radiometrically corrected image pixels [counts  or  Digital Numbers]
  # ∆λ_Band:  the effective bandwidth [μm] for a given bandwidth


# π, first 11 decimals
PI=3.14159265358
#echo "Pi set to ${PI}"

# HardCoded MetaData!

  # Acquisition's Day of Year and estimated Earth-Sun Distance
  DOY=100; ESD=1.00184

  # Sun Zenith Angle based on the acquisition's Sun Elevation Angle
  SEA=53.8; SZA=$(echo "90 - ${SEA}" | bc )

  # some echo
  echo "Acquisition-specific parameters"
  echo "Day of Year: ${DOY}, Earth-Sun Distance: ${ESD}, Sun Zenith Angle: ${SZA}"
  echo -e "\n"

# 1st column: Absolute Calibration Factors
# 2nd column: Spectral Band Effective Bandwidth, Δλ
# 3rd column: Band-Averaged Solar Spectral Irradiance [W/sq.m./micro-m]

K_Pan=0.05678345		;	Pan_Width=0.2846000			;	Pan_Esun=1580.8140
K_Coastal=0.009295654	;	Coastal_Width=0.04730000	;	Coastal_Esun=1758.2229
K_Blue=0.01260825		;	Blue_Width=0.05430000		;	Blue_Esun=1974.2416
K_Green=0.009713071		;	Green_Width=0.06300000		;	Green_Esun=1856.4104
K_Yellow=0.005829815	;	Yellow_Width=0.03740000		;	Yellow_Esun=1738.4791
K_Red=0.01103623		;	Red_Width=0.05740000		;	Red_Esun=1559.4555
K_RedEdge=0.005188136	;	RedEdge_Width=0.03930000	;	RedEdge_Esun=1342.0695
K_NIR1=0.01224380		;	NIR1_Width=0.09890000		;	NIR1_Esun=1069.7302
K_NIR2=0.009042234		;	NIR2_Width=0.09960000		;	NIR2_Esun=861.2866



# Bands
Spectral_Bands="Pan Coastal Blue Green Yellow Red RedEdge NIR1 NIR2"

# loop over all bands
for BAND in ${Spectral_Bands}; do

  # some echo
  echo -e "Processing the \"${BAND}\" spectral band"

  # set band parameters as variables  -- using  K16  for 16-bit data!
  eval K_BAND="K_${BAND}"
  eval BAND_Width="${BAND}_Width"
  echo "* Band-specific radiometric parameters set to K=${!K_BAND}, Bandwidth=${!BAND_Width}"

  # set region
#   echo "* Region matching the ${BAND} spectral band."
  g.region rast=${BAND}_DNs

  # conversion to Radiance based on (1) -- attention: 32-bit calculations required
  echo "* Converting ${BAND} Digital Numebrs to Radiance..." | tr -d "\n"
  r.mapcalc "${BAND}_Radiance = ( double(${!K_BAND}) * ${BAND}_DNs ) / ${!BAND_Width}"
  

  # report range
  echo "* Reporting range of the ${BAND} spectral radiance: " | tr -d "\n"
  # r.info -r "${BAND}_Radiance"
  r.info -r "${BAND}_Radiance" | tr "\n" "," | cut -d"," -f1,2 | sed 's/,/,\ /'

  # add info
  r.support map=${BAND}_Radiance \
  title="" \
  units="W / sq.m. / μm / ster" \
  description="Top-of-Atmosphere `echo ${BAND}` band spectral Radiance [W/m^2/sr/μm]" \
  source1='"Radiometric Use of WorldView-2 Imagery, Technical Note (2010)", by Todd Updike & Chris Comp'

  # Esun
  eval BAND_Esun="${BAND}_Esun"

  # some echo
  echo "* Parameters required for the conversion: Esun= ${!BAND_Esun}, ESD= ${ESD}, ${SZA}"

  # calculate ToAR
  echo "* Converting ${BAND}_Radiance to Top of Atmosphere Reflectance..." | tr -d "\n"
  r.mapcalc "${BAND}_ToAR = \
	( ${PI} * ${BAND}_Radiance * ${ESD}^2 ) / ( ${!BAND_Esun} * cos(${SZA}) )"

  # report range
  echo "* Reporting range of the ${BAND} spectral radiance: " | tr -d "\n"
  r.info -r ${BAND}_ToAR | tr "\n" "," | cut -d"," -f1,2 | sed 's/,/,\ /'

  # add some metadata
  r.support map=${BAND}_ToAR \
  title="echo ${BAND} band (Top of Atmosphere Reflectance)" \
  units="Unitless planetary reflectance" \
  description="Top of Atmosphere `echo ${BAND}` band spectral Reflectance (unitless)" \
  source1='"Radiometric Use of WorldView-2 Imagery, Technical Note (2010)", by Todd Updike & Chris Comp, Digital Globe' \
  source2="Digital Globe" \
  history="PI=3.14159265358; K=${!K_BAND}; Bandwidth=${!BAND_Width}; ESD=${ESD}; Esun=${!BAND_Esun}; SZA=${SZA}"

  echo -e "\n"
done

# ###########################################################################
# From the metadata

# # Panchromatic
# absCalFactor = 0.05678345; effectiveBandwidth = 0.2846000
# 
# # Coastal Blue
# absCalFactor = 0.009295654; effectiveBandwidth = 0.04730000;
# 
# # Blue
# absCalFactor = 0.01260825; effectiveBandwidth = 0.05430000;
# 
# # Green
# absCalFactor = 0.009713071; effectiveBandwidth = 0.06300000
# 
# # Yellow
# absCalFactor = 0.005829815; effectiveBandwidth = 0.03740000
# 
# # Red
# absCalFactor = 0.01103623; effectiveBandwidth = 0.05740000
# 
# # Edge Red
# absCalFactor = 0.005188136; effectiveBandwidth = 0.03930000
# 
# # NIR
# absCalFactor = 0.01224380; effectiveBandwidth = 0.09890000
# 
# # NIR2
# absCalFactor = 0.009042234; effectiveBandwidth = 0.09960000
