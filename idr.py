import sys
import math

GEL_RESISTANCE = 0.000550  # Tuned to match real-world data


def calculate_energy(velocity, grains):
    """Return kinetic energy in ft-lbs."""
    return (velocity ** 2 * grains) / 450240


def get_terminal_conditions(v_start, initial_idr):
    """Return velocity floor, energy floor, and stop message based on projectile class."""
    if initial_idr <= 0.50:
        return 0, 30, "IDR threshold (small caliber floor)"
    if v_start < 1200 and initial_idr >= 2.0:
        return 25, 30, "Terminal condition met (heavy/subsonic)"
    if v_start <= 1400:
        return 5, 3, "Terminal condition met (handgun)"
    return 25, 30, "Terminal condition met (rifle)"


def get_expansion_const(impact_energy):
    """Return expansion constant based on impact energy (graduated scale)."""
    if impact_energy < 200:
        return 0.001   # Almost no expansion (low-energy rounds)
    elif impact_energy < 500:
        return 0.05    # Handgun / slow expansion
    elif impact_energy < 900:
        return 0.12    # Moderate expansion
    else:
        return 0.25    # Full rifle-speed expansion


def run_simulation(v_start, grains, caliber):
    # 1. Compute Initial Sectional Density
    initial_sd = grains / (7000 * (caliber ** 2))

    # Impact Density Rate using the computed SD
    initial_idr = (v_start * (grains / 7000) * initial_sd) * caliber

    vel_floor, nrg_floor, stop_msg = get_terminal_conditions(v_start, initial_idr)

    v = v_start
    dist = 0
    total_wound_volume = 0.0
    stop_reason = ""
    max_caliber = caliber * 1.75
    Step = 0.01

    # Expansion rate is determined by impact velocity/energy.
    # Moving this outside the loop prevents the "shrinking bullet" bug.
    impact_energy = calculate_energy(v_start, grains)
    expansion_const = get_expansion_const(impact_energy)

    while dist < 100:
        # Increment distance first so wound volume is measured after travel
        dist += Step

        # The bullet expands over distance, but stays expanded once it grows.
        expansion_progress = 1 - math.exp(-expansion_const * dist)
        expanded_cal = caliber + (max_caliber - caliber) * expansion_progress

        # Re-compute SD dynamically based on expansion (frontal area increases)
        current_sd = grains / (7000 * (expanded_cal ** 2))

        # IDR also shifts as the bullet flattens/expands
        current_idr = (v * (grains / 7000) * current_sd) * expanded_cal

        energy = calculate_energy(v, grains)
        if v <= vel_floor or energy <= nrg_floor:
            stop_reason = stop_msg
            break

        # Guard against division by zero if IDR drops to zero
        if current_idr <= 0:
            stop_reason = "Simulation halted (IDR reached zero)"
            break

        # Calculate area of the current expanded face
        area = math.pi * (expanded_cal / 2) ** 2
        total_wound_volume += (area * Step)

        # Calculate velocity loss based on drag and IDR momentum
        v_loss = (GEL_RESISTANCE * v ** 2 * area) / current_idr

        # Apply velocity loss
        v = max(0.0, v - (v_loss * Step))

        # Optional: Uncomment to see the expansion progression
        # print(f"Dist: {dist:1.2f}in | Cal: {expanded_cal:.3f} | Vel: {int(v)} fps | Eng: {int(energy)} ft-lbs")
        # print(f"{dist:1.2f},{energy:4.2f}")
        #print(f"{dist:1.2f},{total_wound_volume:3.2f}")

    if not stop_reason:
        stop_reason = "Full penetration (100in limit reached)"

    init_energy = calculate_energy(v_start, grains)
    print("-" * 40)
    print(f"Bullet Specs:       {grains}gr | .{int(caliber * 1000)} cal")
    print(f"Calculated SD:      {initial_sd:.4f}")
    print(f"Impact IDR:         {initial_idr:.4f}")
    print(f"Penetration Depth:  {dist:3.1f} in")
    print(f"Impact Energy:      {round(init_energy)} ft-lbs")
    print(f"Wound Volume:       {total_wound_volume:.4f} in³")
    print(f"Status:             {stop_reason}")
    print("-" * 40)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 idr.py <velocity> <weight_grains> <caliber_inch>")
        print("Example: python3 idr.py 2162 180 0.308")
        sys.exit(1)
    try:
        v_start = float(sys.argv[1])
        grains = float(sys.argv[2])
        caliber = float(sys.argv[3])
    except ValueError:
        print("Error: Inputs must be numeric.")
        sys.exit(1)

    if v_start <= 0 or grains <= 0 or caliber <= 0:
        print("Error: velocity, grains, and caliber must all be positive values.")
        sys.exit(1)

    run_simulation(v_start, grains, caliber)
