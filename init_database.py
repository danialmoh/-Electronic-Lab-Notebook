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
            name="Protein Expression Study",
            description="Study of recombinant protein expression in E. coli"
        )
        project2 = db.create_project(
            name="Drug Screening Assay",
            description="High-throughput screening of potential drug candidates"
        )
        
        # Create sample experiments
        exp1 = db.create_experiment(
            project_id=project1.id,
            title="Small-scale expression test",
            description="Test expression of target protein in BL21(DE3) cells",
            status="Final",
            experiment_date=datetime.now() - timedelta(days=5),
            tags="expression, BL21, IPTG"
        )
        
        exp2 = db.create_experiment(
            project_id=project1.id,
            title="Protein purification",
            description="Purify expressed protein using Ni-NTA chromatography",
            status="Draft",
            experiment_date=datetime.now() - timedelta(days=2),
            tags="purification, Ni-NTA"
        )
        
        exp3 = db.create_experiment(
            project_id=project2.id,
            title="Compound library screening",
            description="Screen 1000 compounds against target enzyme",
            status="Draft",
            experiment_date=datetime.now(),
            tags="screening, HTS, enzyme"
        )
        
        # Create sample entries
        entry1 = db.create_entry(
            experiment_id=exp1.id,
            title="Initial setup and culture preparation",
            content="""# Culture Preparation

## Materials
- LB broth
- Kanamycin (50 µg/mL)
- BL21(DE3) competent cells
- IPTG

## Procedure
1. Prepare 5 mL LB + Kanamycin
2. Inoculate with single colony
3. Grow overnight at 37°C, 200 rpm
4. Dilute 1:100 into fresh media
5. Grow to OD600 = 0.6
6. Induce with 1 mM IPTG
7. Express for 4 hours at 30°C

## Results
Final OD600: 2.1
Expression observed by SDS-PAGE

## Notes
- Temperature reduction to 30°C improved solubility
- Consider testing 0.5 mM IPTG in next trial"""
        )
        
        entry2 = db.create_entry(
            experiment_id=exp2.id,
            title="Chromatography setup",
            content="""# Ni-NTA Purification Protocol

## Buffer Preparation
- **Binding Buffer**: 50 mM Tris-HCl pH 8.0, 300 mM NaCl, 10 mM imidazole
- **Wash Buffer**: 50 mM Tris-HCl pH 8.0, 300 mM NaCl, 20 mM imidazole  
- **Elution Buffer**: 50 mM Tris-HCl pH 8.0, 300 mM NaCl, 250 mM imidazole

## Equipment
- ÄKTA FPLC system
- Ni-NTA Superflow column (5 mL)
- UV detector at 280 nm

## Procedure
1. Equilibrate column with 5 column volumes (CV) binding buffer
2. Load clarified lysate (filtered through 0.45 µm)
3. Wash with 10 CV wash buffer
4. Elute with linear gradient to 100% elution buffer over 20 CV
5. Collect 1 mL fractions

## Expected Results
- Target protein should elute at ~200 mM imidazole
- Monitor absorbance at 280 nm
- Analyze fractions by SDS-PAGE"""
        )
        
        # Create sample reagents
        reagent1 = db.create_reagent(
            name="IPTG",
            description="Isopropyl β-D-1-thiogalactopyranoside",
            catalog_number="I6758",
            supplier="Sigma-Aldrich",
            concentration=1.0,
            unit="M",
            storage_location="Freezer A, Shelf 2",
            safety_info="Handle with gloves. Avoid inhalation."
        )
        
        reagent2 = db.create_reagent(
            name="Kanamycin",
            description="Antibiotic for bacterial selection",
            catalog_number="K1600",
            supplier="Sigma-Aldrich",
            concentration=50,
            unit="mg/mL",
            storage_location="Fridge B, Door 1",
            safety_info="Antibiotic - handle with care"
        )
        
        reagent3 = db.create_reagent(
            name="Ni-NTA Agarose",
            description="Nickel-charged affinity chromatography resin",
            catalog_number="30210",
            supplier="Qiagen",
            concentration=None,
            unit="mL",
            storage_location="Cold Room, Shelf 3",
            safety_info="Contains nickel - avoid skin contact"
        )
        
        # Link reagents to entries
        db.link_reagent_to_entry(
            entry_id=entry1.id,
            reagent_id=reagent1.id,
            quantity_used=1.0,
            unit="mM",
            notes="Used for induction"
        )
        
        db.link_reagent_to_entry(
            entry_id=entry1.id,
            reagent_id=reagent2.id,
            quantity_used=50,
            unit="µg/mL",
            notes="Antibiotic selection"
        )
        
        db.link_reagent_to_entry(
            entry_id=entry2.id,
            reagent_id=reagent3.id,
            quantity_used=5,
            unit="mL",
            notes="Column packing"
        )
        
        # Create sample samples
        sample1 = db.create_sample(
            name="BL21(DE3) glycerol stock",
            description="Competent cells for protein expression",
            sample_type="Bacterial stock",
            storage_location="Freezer A, Box 1",
            quantity=100,
            unit="µL"
        )
        
        sample2 = db.create_sample(
            name="Target protein lysate",
            description="Clarified lysate from expression test",
            sample_type="Protein sample",
            storage_location="Freezer B, Shelf 1",
            quantity=50,
            unit="mL"
        )
        
        # Create sample equipment
        equipment1 = db.create_equipment(
            name="Thermal Cycler",
            model="T100",
            serial_number="TC12345",
            location="Lab Bench 1",
            status="Available",
            last_maintenance=datetime.now() - timedelta(days=30)
        )
        
        equipment2 = db.create_equipment(
            name="Centrifuge",
            model="5424 R",
            serial_number="CF67890",
            location="Equipment Room A",
            status="Available",
            last_maintenance=datetime.now() - timedelta(days=15)
        )
        
        equipment3 = db.create_equipment(
            name="FPLC System",
            model="ÄKTA pure",
            serial_number="AK11111",
            location="Cold Room",
            status="In Use",
            last_maintenance=datetime.now() - timedelta(days=7)
        )
        
        # Create sample protocols
        protocol1 = db.create_protocol(
            name="Bacterial Transformation Protocol",
            description="Standard protocol for transforming E. coli with plasmid DNA",
            content="""# Bacterial Transformation Protocol

## Materials
- Chemically competent E. coli cells
- Plasmid DNA (1-10 ng)
- SOC medium
- LB agar plates with appropriate antibiotic

## Equipment
- Water bath (42°C)
- Incubator (37°C)
- Shaking incubator

## Procedure
1. Thaw competent cells on ice (50 µL per transformation)
2. Add plasmid DNA to cells, mix gently
3. Incubate on ice for 30 minutes
4. Heat shock at 42°C for 45 seconds
5. Return to ice for 2 minutes
6. Add 450 µL SOC medium
7. Incubate at 37°C for 1 hour with shaking
8. Plate 100-200 µL on selective agar plates
9. Incubate overnight at 37°C

## Expected Results
- Transformation efficiency: 10^6 - 10^8 CFU/µg DNA
- Colonies should appear after 12-16 hours

## Troubleshooting
- Low efficiency: Check DNA quality, cell competency
- No colonies: Verify antibiotic concentration, cell viability""",
            created_by="Dr. Smith"
        )
        
        protocol2 = db.create_protocol(
            name="SDS-PAGE Protocol",
            description="Standard protocol for protein analysis by SDS-PAGE",
            content="""# SDS-PAGE Protocol

## Materials
- Acrylamide/Bis solution (30%)
- Tris-Glycine SDS running buffer
- Sample buffer (2X Laemmli)
- Molecular weight markers
- Coomassie Brilliant Blue stain

## Equipment
- Gel electrophoresis apparatus
- Power supply
- Gel casting system

## Procedure
### Gel Preparation
1. Prepare resolving gel (10-12% depending on protein size)
2. Prepare stacking gel (5%)
3. Assemble gel casting apparatus
4. Allow polymerization (30-45 minutes)

### Sample Preparation
1. Mix sample with 2X Laemmli buffer
2. Heat at 95°C for 5 minutes
3. Cool on ice

### Electrophoresis
1. Assemble gel in electrophoresis chamber
2. Fill chambers with running buffer
3. Load samples and molecular weight marker
4. Run at 120 V until dye front reaches bottom

### Staining
1. Remove gel and place in staining solution
2. Stain for 1-2 hours
3. Destain until clear background achieved

## Notes
- Use appropriate gel percentage for protein size range
- Include reducing agent (β-mercaptoethanol or DTT) for denaturing conditions""",
            created_by="Lab Manager"
        )
        
        print("Sample data created successfully!")
        
        # Print summary
        print(f"\nDatabase Summary:")
        print(f"- Projects: {len(db.get_projects())}")
        print(f"- Experiments: {len(db.get_experiments())}")
        print(f"- Entries: {len(db.get_entries())}")
        print(f"- Reagents: {len(db.get_reagents())}")
        print(f"- Samples: {len(db.get_samples())}")
        print(f"- Equipment: {len(db.get_equipment())}")
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
