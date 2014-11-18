`i.worldview.toar` is a GRASS-GIS add-on module converting WorldView2 DN values 
(Digital Numbers, that is relatively readiometrically corrected detector data) 
to Spectral Radiance or Reflectance.

_Conversion to top-of-atmosphere spectral radiance is a simple two step process 
that involves multiplying
radiometrically corrected image pixels by the appropriate absolute radiometric 
calibration factor (also referred to as a K factor) to get band-integrated 
radiance [W-m-2-sr-1] and then dividing the result by the appropriate effective 
bandwidth to get spectral radiance [W-m-2-sr-1-μm-1]_ (Updike, 2010).

For the moment, the module requires as an input the acquisition's date and time 
formatted as a UTC string OR the Day-of-Year (Julian Day), the (mean) Sun 
Elevation Angle. These are required to calculate the Earth-Sun distance 
parameter for the modules' internal computations and can be retrieved from the 
imagery's metadata files. The UTC string can be overriden by using the optional 
parameter `doy`, given the day of year (Julian Day) has been correctly estimated 
for the acquisition that is to be processed.

Optionally, the module may operate on the current computational region, instead 
of a bands whole extent.

*ToAdd: More details about retrieving the acquisition's metada.*

Source: Updike and Comp, 2010


## Spectral Radiance

L(λ|Pixel, Band) = K(Band) * q(Pixel, Band) / Δ(λ|Band)

where:
- L(λ): Top-of-Atmosphere Spectral Radiance image pixels [W/sq.m./sr/μm]
- KBand: absolute radiometric calibration factor [W/sq.m./sr/count] for a given 
band
- q(Pixel,Band): radiometrically corrected image pixels [countsor or Digital 
Numbers]
- Δ(λ|Band): effective bandwidth [μm] for a given band.

## Planetary Reflectance

ρ(p) = π x L(λ) x d^2 / ESUN(λ) x cos(θ(S))

where:
- ρ: Unitless Planetary Reflectance
- π: Mathematical constant
- L(λ): Spectral Radiance from equation (1)
- d: Earth-Sun distance in astronomical units [calculated using
AcquisitionTime class]

# Sources

- Radiometric Use of WorldView-2 Imagery, Technical Note (2010), by Todd Updike
  & Chris Comp
- <http://landsat.usgs.gov/how_is_radiance_calculated.php>
