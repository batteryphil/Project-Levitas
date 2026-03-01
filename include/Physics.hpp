#ifndef LEVITAS_PHYSICS_HPP
#define LEVITAS_PHYSICS_HPP

#include <cstdint>

namespace levitas {

/**
 * @brief Physics IDs for telemetry mapping (1-127).
 * IDs 0-31: Gravitational Gradient Baseline (G)
 * IDs 32-63: Electromagnetic Flux Densities
 * IDs 64-95: Angular Momentum / Rotational Frequency
 * IDs 96-127: Thermal Vacuum Density
 */
enum class TelemetryID : uint8_t {
    G_MIN = 0,
    G_MAX = 31,
    EM_MIN = 32,
    EM_MAX = 63,
    ROT_MIN = 64,
    ROT_MAX = 95,
    VAC_MIN = 96,
    VAC_MAX = 127
};

struct TelemetryPoint {
    float gravitational_gradient;
    float em_flux;
    float angular_momentum;
    float thermal_vacuum;
};

} // namespace levitas

#endif // LEVITAS_PHYSICS_HPP
