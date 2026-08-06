#!/bin/bash
# Reference solution for m2_electromagnetism_0_003_gen14_20260728_105919

cat > /app/law.py << 'EOL'
import numpy as np


def Piecewise(*pairs):
    for value, condition in pairs:
        if bool(condition):
            return value
    return pairs[-1][0]


pi = np.pi
sin = np.sin
cos = np.cos
tan = np.tan
asin = np.arcsin
acos = np.arccos
atan = np.arctan
atan2 = np.arctan2
sinh = np.sinh
cosh = np.cosh
tanh = np.tanh
exp = np.exp
log = np.log
sqrt = np.sqrt
Abs = abs


def Max(*args):
    return max(args)


def Min(*args):
    return min(args)


sign = np.sign
floor = np.floor
ceiling = np.ceil


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    predictions = []
    epsilon_0 = 8.854e-12
    c = 299792458.0
    crossing_angle = 0.5236
    ellipticity_angle = 0.3927
    first_wave_ellipticity_angle = 0.3142
    sigma_phi = 0.1
    sigma_theta = 0.1
    sigma_ellipticity_angle = 0.05
    phase_orientation_correlation = 0.3
    normalized_aperture_rms_width = 1.0
    sigma_log_amplitude_1 = 0.1
    sigma_log_amplitude_2 = 0.1
    log_amplitude_correlation = 0.5
    aperture_to_beam_waist_ratio = 0.5
    normalized_differential_wavefront_curvature = 0.3
    normalized_second_beam_centroid_offset = 0.4
    second_to_first_beam_waist_ratio = 1.5

    for point in input_data:
        E_1 = point['E_1']
        E_2 = point['E_2']
        phi = point['phi']
        theta = point['theta']
        I_avg = epsilon_0*c*(E_1**2*exp(sigma_log_amplitude_1**2)/sqrt(1 + 4*aperture_to_beam_waist_ratio**2) + cos(crossing_angle)*E_2**2*exp(sigma_log_amplitude_2**2)*exp(-2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset**2/(second_to_first_beam_waist_ratio**2 + 4*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2))/sqrt(1 + 4*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2) + E_1*E_2*(1 + cos(crossing_angle))*exp(log_amplitude_correlation*sigma_log_amplitude_1*sigma_log_amplitude_2)*exp(-(sigma_phi**2 + sigma_theta**2 + sigma_ellipticity_angle**2)/2)*exp(-aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset**2/second_to_first_beam_waist_ratio**2 + ((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) - 2*normalized_differential_wavefront_curvature*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2)))*(cos(theta)*(cosh(phase_orientation_correlation*sigma_phi*sigma_theta)*cos(first_wave_ellipticity_angle - ellipticity_angle) + sinh(phase_orientation_correlation*sigma_phi*sigma_theta)*sin(first_wave_ellipticity_angle + ellipticity_angle))*cos(phi + atan(normalized_differential_wavefront_curvature/(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2)))/2 + (normalized_differential_wavefront_curvature*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) + 2*(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2))) + sin(theta)*(cosh(phase_orientation_correlation*sigma_phi*sigma_theta)*sin(first_wave_ellipticity_angle + ellipticity_angle) + sinh(phase_orientation_correlation*sigma_phi*sigma_theta)*cos(first_wave_ellipticity_angle - ellipticity_angle))*sin(phi + atan(normalized_differential_wavefront_curvature/(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2)))/2 + (normalized_differential_wavefront_curvature*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) + 2*(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2))))/sqrt(sqrt((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2)))/2
        predictions.append({'I_avg': float(I_avg)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_003_gen14_20260728_105919 Reference Law

Target: `I_avg`

Input variables: `E_1`, `E_2`, `phi`, `theta`

Reference expression:

```text
I_avg = epsilon_0*c*(E_1**2*exp(sigma_log_amplitude_1**2)/sqrt(1 + 4*aperture_to_beam_waist_ratio**2) + cos(crossing_angle)*E_2**2*exp(sigma_log_amplitude_2**2)*exp(-2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset**2/(second_to_first_beam_waist_ratio**2 + 4*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2))/sqrt(1 + 4*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2) + E_1*E_2*(1 + cos(crossing_angle))*exp(log_amplitude_correlation*sigma_log_amplitude_1*sigma_log_amplitude_2)*exp(-(sigma_phi**2 + sigma_theta**2 + sigma_ellipticity_angle**2)/2)*exp(-aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset**2/second_to_first_beam_waist_ratio**2 + ((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) - 2*normalized_differential_wavefront_curvature*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2)))*(cos(theta)*(cosh(phase_orientation_correlation*sigma_phi*sigma_theta)*cos(first_wave_ellipticity_angle - ellipticity_angle) + sinh(phase_orientation_correlation*sigma_phi*sigma_theta)*sin(first_wave_ellipticity_angle + ellipticity_angle))*cos(phi + atan(normalized_differential_wavefront_curvature/(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2)))/2 + (normalized_differential_wavefront_curvature*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) + 2*(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2))) + sin(theta)*(cosh(phase_orientation_correlation*sigma_phi*sigma_theta)*sin(first_wave_ellipticity_angle + ellipticity_angle) + sinh(phase_orientation_correlation*sigma_phi*sigma_theta)*cos(first_wave_ellipticity_angle - ellipticity_angle))*sin(phi + atan(normalized_differential_wavefront_curvature/(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2)))/2 + (normalized_differential_wavefront_curvature*((2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)**2 - (normalized_aperture_rms_width*sin(crossing_angle))**2) + 2*(1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))*(2*aperture_to_beam_waist_ratio**2*cos(crossing_angle)**2*normalized_second_beam_centroid_offset/second_to_first_beam_waist_ratio**2)*(normalized_aperture_rms_width*sin(crossing_angle)))/(2*((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2))))/sqrt(sqrt((1 + 2*aperture_to_beam_waist_ratio**2*(1 + cos(crossing_angle)**2/second_to_first_beam_waist_ratio**2))**2 + normalized_differential_wavefront_curvature**2)))/2
```

Fixed parameters: epsilon_0=8.854e-12, c=2.99792e+08, crossing_angle=0.5236, ellipticity_angle=0.3927, first_wave_ellipticity_angle=0.3142, sigma_phi=0.1, sigma_theta=0.1, sigma_ellipticity_angle=0.05, phase_orientation_correlation=0.3, normalized_aperture_rms_width=1, sigma_log_amplitude_1=0.1, sigma_log_amplitude_2=0.1, log_amplitude_correlation=0.5, aperture_to_beam_waist_ratio=0.5, normalized_differential_wavefront_curvature=0.3, normalized_second_beam_centroid_offset=0.4, second_to_first_beam_waist_ratio=1.5.
EOL
