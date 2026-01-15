#!/usr/bin/env python3
"""
Database initialization script for the Electronic Lab Notebook
Run this script to create the database and add sample data
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import create_database, get_session
from database import DatabaseManager
from utils import display_success, display_error

def create_sample_data():
    """Create sample data for testing"""
    print("Creating sample data...")
    
    with DatabaseManager() as db:
        # Create sample projects
        project1 = db.create_project(
            name="IR-UV Ion Dip Spectroscopy of Tryptophan",
            description="Two-color IR/UV experiments on jet-cooled tryptophan clusters"
        )
        project2 = db.create_project(
            name="Ultrafast Pump-Probe Beamline Commissioning",
            description="Setup and diagnostics for 400 nm pump / broadband probe experiments"
        )
        
        # Create sample experiments
        exp1 = db.create_experiment(
            project_id=project1.id,
            title="Jet-cooled tryptophan monomer scan",
            description="Record REMPI spectrum and IR ion-dip features of isolated tryptophan",
            status="Final",
            experiment_date=datetime.now() - timedelta(days=5),
            tags="REMPI, IR-UV, jet",
            wavelength_range="212-230 nm",
            pulse_energy=0.3,
            pulse_energy_unit="mJ",
            repetition_rate=10.0,
            vacuum_level=2e-6,
            sample_temperature=120.0,
            instrument_config="Nd:YAG pumped OPO for IR, frequency-doubled dye laser for UV"
        )
        
        exp2 = db.create_experiment(
            project_id=project1.id,
            title="Tryptophan dimer assignment",
            description="Two-color scans on dimer bands with IR depletion",
            status="Draft",
            experiment_date=datetime.now() - timedelta(days=2),
            tags="cluster, IR depletion",
            wavelength_range="2800-3600 cm-1",
            pulse_energy=0.4,
            pulse_energy_unit="mJ",
            repetition_rate=10.0,
            vacuum_level=1.5e-6,
            sample_temperature=110.0,
            instrument_config="Same as exp1 with delayed IR beam"
        )
        
        exp3 = db.create_experiment(
            project_id=project2.id,
            title="Pump-probe cross-correlation",
            description="400/800 nm cross-correlation and chirp characterization",
            status="Draft",
            experiment_date=datetime.now(),
            tags="pump-probe, diagnostics",
            wavelength_range="400-800 nm",
            pulse_energy=1.2,
            pulse_energy_unit="µJ",
            repetition_rate=250.0,
            vacuum_level=8e-7,
            sample_temperature=295.0,
            instrument_config="Ti:sapph amplifier, NOPA for visible probe"
        )
        
        # Create sample entries
        entry1 = db.create_entry(
            experiment_id=exp1.id,
            title="Beam alignment and REMPI scan",
            content="""# UV Beam Alignment

## Laser Settings
- Dye: Styryl 9, doubled to 218 nm
- UV pulse energy: 0.3 mJ
- IR OPO parked at 3.2 µm for depletion check

## Procedure
1. Align UV through skimmer apertures using fluorescent card
2. Optimize ion optics for tof peak at 8.2 µs
3. Record REMPI scan from 212-230 nm (0.05 nm steps)
4. Trigger IR 200 ns after UV to confirm depletion

## Observations
- Strong band at 217.4 nm (monomer S1 origin)
- IR depletion of 30% when tuned to 3520 cm-1

## Notes
- Need longer averaging for weak hot bands
- Consider lowering valve temperature to 115 K"""
        )
        
        entry2 = db.create_entry(
            experiment_id=exp2.id,
            title="IR ion-dip map of dimer band B",
            content="""# IR Ion-Dip Protocol

## Scan Plan
- UV fixed at 223.1 nm (band B)
- IR scan: 2800–3600 cm⁻¹ in 2 cm⁻¹ steps
- Averaging: 500 shots per point

## Procedure
1. Lock UV to band B using wavemeter feedback
2. Align IR focus at interaction region (use burn paper)
3. Scan IR while recording depletion and tof spectra

## Results
- Sharp depletion features at 3305, 3442, 3521 cm⁻¹
- Mode at 3521 cm⁻¹ matches monomer ν3, suggests shared chromophore

## Next Steps
- Run isotopic substitution with deuterated backing gas
- Simulate spectrum with anharmonic calculations"""
        )
        
        # Create sample reagents
        material1 = db.create_material(
            name="KDP Doubling Crystal",
            description="Type-I 5x5x10 mm KDP for 532 nm generation",
            material_type="Crystal",
            vendor="EKSMA Optics",
            part_number="KDP-0510",
            wavelength_range="350-1100 nm",
            damage_threshold=0.5,
            unit="GW/cm^2",
            storage_location="Optics cabinet A1",
            handling_notes="Hygroscopic, keep in desiccator"
        )
        
        material2 = db.create_material(
            name="MgF2 Window",
            description="2 mm thick MgF2 for VUV beamline",
            material_type="Optic",
            vendor="Thorlabs",
            part_number="WG41010",
            wavelength_range="120-7000 nm",
            damage_threshold=5.0,
            unit="J/cm^2",
            storage_location="Optics drawer B3",
            handling_notes="Clean with dry nitrogen, avoid fingerprints"
        )
        
        material3 = db.create_material(
            name="IR Hollow-core Fiber",
            description="1 m Kagome fiber for pulse delivery",
            material_type="Fiber",
            vendor="GLOphotonics",
            part_number="HC-1200",
            wavelength_range="1.2-2.0 µm",
            damage_threshold=2.0,
            unit="GW/cm^2",
            storage_location="Fiber spool rack",
            handling_notes="Minimum bend radius 30 cm"
        )
        
        # Link materials to entries
        db.link_material_to_entry(
            entry_id=entry1.id,
            material_id=material1.id,
            usage_context="Frequency doubling dye output",
            quantity_used=1,
            unit="unit",
            notes="Realigned, confirmed phase matching"
        )
        
        db.link_material_to_entry(
            entry_id=entry1.id,
            material_id=material2.id,
            usage_context="Window between source and TOF",
            quantity_used=None,
            notes="Cleaned with acetone, no scratches"
        )
        
        db.link_material_to_entry(
            entry_id=entry2.id,
            material_id=material3.id,
            usage_context="Deliver IR beam to chamber",
            quantity_used=1.0,
            unit="m",
            notes="Transmission 65%, acceptable"
        )
        
        # Create sample targets
        target1 = db.create_target(
            name="Tryptophan seeded jet",
            composition="1% tryptophan in heptane, seeded in He",
            target_type="Supersonic jet",
            backing_gas="Helium",
            stagnation_pressure=2.0,
            temperature=130.0,
            storage_location="Valve box"
        )
        
        target2 = db.create_target(
            name="NO/Argon probe mix",
            composition="500 ppm NO in argon",
            target_type="Gas cell",
            backing_gas="Argon",
            stagnation_pressure=1.0,
            temperature=295.0,
            storage_location="Gas manifold"
        )
        
        # Create sample instruments
        instrument1 = db.create_instrument(
            name="OPA Pump Laser",
            model="Spectra-Physics Spitfire",
            serial_number="SP-OPA-3321",
            location="Laser Room Bay 2",
            status="Available",
            last_maintenance=datetime.now() - timedelta(days=30),
            beamline_position="Pump table",
            control_software="LabVIEW OPC"
        )
        
        instrument2 = db.create_instrument(
            name="Time-of-Flight Spectrometer",
            model="Jordan TOF-2",
            serial_number="JORDAN-221",
            location="Beamline vacuum chamber",
            status="In Use",
            last_maintenance=datetime.now() - timedelta(days=15),
            beamline_position="Interaction region",
            control_software="TOFDAQ"
        )
        
        instrument3 = db.create_instrument(
            name="Delay Stage",
            model="Newport XPS",
            serial_number="NPT-8891",
            location="Probe table",
            status="Maintenance",
            last_maintenance=datetime.now() - timedelta(days=7),
            beamline_position="Probe arm",
            control_software="Newport XPS"
        )
        
        # Create sample protocols
        protocol1 = db.create_protocol(
            name="Supersonic Jet Alignment SOP",
            description="Standard procedure for aligning laser beams through the skimmed molecular beam",
            content="""# Supersonic Jet Alignment SOP

## Prerequisites
- Chamber at < 5 × 10⁻⁶ mbar
- Valve warmed to operating temperature
- IR and UV lasers warmed up

## Steps
1. **Mechanical Alignment**
   - Insert alignment rod through skimmer, ensure < 0.2 mm offset.
   - Use theodolite to match beam height (95 cm from floor).
2. **UV Alignment**
   - Set dye laser to 230 nm, low power (<0.1 mJ).
   - Use fluorescing card to trace through skimmer and ion optics.
3. **IR Alignment**
   - Switch to HeNe pilot beam, overlap with UV using dichroic.
   - Verify focus at interaction region with burn paper.
4. **Diagnostics**
   - Record TOF background, ensure no stray ions.
   - Run REMPI scan of benzene as reference.

## Safety
- Wear goggles appropriate for both UV and IR wavelengths.
- Close beam shutters when adjusting optics.""",
            created_by="Beamline Lead"
        )
        
        protocol2 = db.create_protocol(
            name="Pump-Probe Delay Calibration",
            description="Procedure to calibrate temporal overlap using cross-correlation",
            content="""# Pump-Probe Delay Calibration

## Equipment
- Autocorrelator or thin BBO crystal
- Fast photodiodes for pump and probe
- Digitizer/oscilloscope

## Procedure
1. **Initial Coarse Overlap**
   - Set delay stage to nominal zero.
   - Place fast detector, observe pump and probe arrival times.
2. **Cross-Correlation**
   - Insert BBO in beam path, monitor sum-frequency signal.
   - Scan delay ±2 ps, record intensity.
3. **Fit & Record**
   - Fit to Gaussian to extract FWHM and zero delay.
   - Store calibration curve in logbook.
4. **Update Stage**
   - Zero the controller at fitted position.
   - Note thermal drift if >50 fs/hour.

## Notes
- Repeat weekly or after realignment.
- For broadband probe, use transient absorption signal instead.""",
            created_by="Ultrafast Team"
        )
        
        print("Sample data created successfully!")
        
        # Print summary
        print(f"\nDatabase Summary:")
        print(f"- Projects: {len(db.get_projects())}")
        print(f"- Experiments: {len(db.get_experiments())}")
        print(f"- Entries: {len(db.get_entries())}")
        print(f"- Materials: {len(db.get_materials())}")
        print(f"- Targets: {len(db.get_targets())}")
        print(f"- Instruments: {len(db.get_instruments())}")
        print(f"- Protocols: {len(db.get_protocols())}")

def main():
    """Main initialization function"""
    print("Electronic Lab Notebook - Database Initialization")
    print("=" * 50)
    
    try:
        # Create database tables
        print("Creating database tables...")
        create_database()
        print("Database tables created successfully!")
        
        # Ask user if they want sample data
        response = input("\nDo you want to create sample data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_data()
        else:
            print("Skipping sample data creation.")
        
        print("\nDatabase initialization complete!")
        print("You can now run the Streamlit app with: streamlit run app.py")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
