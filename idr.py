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
    
    # Expansion rate is determined by impact velocity/energy.
    # Moving this outside the loop prevents the "shrinking bullet" bug.
    impact_energy = calculate_energy(v_start, grains)
    if impact_energy < 200: # Typical threshold for expansion in lead
      expansion_const = 0.001 # Almost no expansion
    else:
      expansion_const = 0.25 # Rifle-speed expansion

    while dist < 100:
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

        # Calculate area of the current expanded face
        area = math.pi * (expanded_cal / 2) ** 2
        total_wound_volume += area

        # Calculate velocity loss based on drag and IDR momentum
        v_loss = (GEL_RESISTANCE * v ** 2 * area) / current_idr
        
        # Apply velocity loss
        v = max(0.0, v - v_loss)
        dist += 1
        
        # Optional: Uncomment to see the expansion progression
        #print(f"Dist: {dist}in | Cal: {expanded_cal:.3f} | Vel: {int(v)} fps")

    init_energy = calculate_energy(v_start, grains)
    print("-" * 40)
    print(f"Bullet Specs:       {grains}gr | .{int(caliber*1000)} cal")
    print(f"Calculated SD:      {initial_sd:.4f}")
    print(f"Impact IDR:         {initial_idr:.4f}")
    print(f"Penetration Depth:  {dist} in")
    print(f"Impact Energy:      {round(init_energy)} ft-lbs")
    print(f"Wound Volume:       {total_wound_volume:.4f} in³")
    if stop_reason:
        print(f"Status:             {stop_reason}")
    print("-" * 40)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 idr.py <velocity> <weight_grains> <caliber_inch>")
        print("Example: python3 idr.py 2162 180 .308")
        sys.exit(1)
    try:
        run_simulation(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]))
    except ValueError:
        print("Error: Inputs must be numeric.")
        sys.exit(1)
