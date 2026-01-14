import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import create_database
from database import DatabaseManager
from utils import (
    render_markdown_with_latex, format_datetime, format_date, get_status_color,
    export_to_pdf, export_entries_to_csv, save_uploaded_file, get_file_size_mb,
    validate_digital_signature, parse_tags, format_tags, search_highlight,
    get_experiment_statistics, display_success, display_error, display_warning, display_info
)
from editor import render_entry_editor, render_entry_view
from protocols import render_protocol_manager, handle_protocol_modals

# Initialize database
create_database()

# Page configuration
st.set_page_config(
    page_title="Electronic Lab Notebook",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.status-draft { color: #ff9500; }
.status-final { color: #34c759; }
.status-archived { color: #8e8e93; }
.entry-locked { background-color: #fff2f2; border-left: 4px solid #ff3b30; }
.math-inline { font-style: italic; color: #007aff; }
.math-display { background-color: #f8f9fa; padding: 1rem; border-radius: 0.25rem; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🔬 Electronic Lab Notebook")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate",
    [
        "🏠 Dashboard",
        "📁 Projects", 
        "🧪 Experiments",
        "📝 Entries",
        "🧫 Lab Inventory",
        "📋 Protocols",
        "🔍 Search",
        "⚙️ Settings"
    ]
)

# Helper functions for pages
def render_dashboard():
    st.title("🏠 Dashboard")
    
    stats = get_experiment_statistics()
    
    # Statistics cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Projects", stats['projects_count'])
    
    with col2:
        st.metric("Experiments", stats['experiments_count'])
    
    with col3:
        st.metric("Entries", stats['entries_count'])
    
    with col4:
        st.metric("Reagents", stats['reagents_count'])
    
    with col5:
        st.metric("Protocols", stats['protocols_count'])
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Recent Experiments")
        if stats['recent_experiments']:
            for exp in stats['recent_experiments'][:5]:
                status_color = get_status_color(exp.status)
                st.markdown(f"**{exp.title}**")
                st.markdown(f"<span class='status-{exp.status.lower()}'>{exp.status}</span> • {format_datetime(exp.updated_at)}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No experiments yet")
    
    with col2:
        st.subheader("📝 Recent Entries")
        if stats['recent_entries']:
            for entry in stats['recent_entries'][:5]:
                lock_status = "🔒" if entry.is_locked else "📝"
                st.markdown(f"{lock_status} **{entry.title}**")
                st.markdown(f"{format_datetime(entry.updated_at)}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No entries yet")

def render_projects():
    st.title("📁 Projects")
    
    with DatabaseManager() as db:
        projects = db.get_projects()
        
        # Create new project
        with st.expander("➕ Create New Project"):
            with st.form("new_project"):
                name = st.text_input("Project Name*")
                description = st.text_area("Description")
                
                if st.form_submit_button("Create Project"):
                    if name:
                        project = db.create_project(name, description)
                        display_success(f"Project '{project.name}' created successfully!")
                        st.rerun()
        
        # Display projects
        if projects:
            st.subheader(f"Projects ({len(projects)})")
            
            for project in projects:
                with st.expander(f"📁 {project.name}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {project.description or 'No description'}")
                        st.markdown(f"**Created:** {format_datetime(project.created_at)}")
                        st.markdown(f"**Updated:** {format_datetime(project.updated_at)}")
                        
                        # Show experiments count
                        experiments = db.get_experiments(project.id)
                        st.markdown(f"**Experiments:** {len(experiments)}")
                    
                    with col2:
                        if st.button("📝 View Experiments", key=f"view_exp_{project.id}"):
                            st.session_state.selected_project = project.id
                            st.session_state.page = "Experiments"
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_proj_{project.id}"):
                            if db.delete_project(project.id):
                                display_success("Project deleted successfully!")
                                st.rerun()
        else:
            st.info("No projects found. Create your first project above!")

def render_experiments():
    st.title("🧪 Experiments")
    
    # Handle project selection from projects page
    if 'selected_project' in st.session_state and st.session_state.selected_project:
        project_filter = st.session_state.selected_project
    else:
        project_filter = None
    
    with DatabaseManager() as db:
        projects = db.get_projects()
        experiments = db.get_experiments(project_filter)
        
        # Project filter
        if projects:
            project_options = {p.name: p.id for p in projects}
            project_options["All Projects"] = None
            
            selected_project_name = st.selectbox(
                "Filter by Project",
                options=list(project_options.keys()),
                index=list(project_options.keys()).index("All Projects") if not project_filter else 0
            )
            
            project_filter = project_options[selected_project_name]
            experiments = db.get_experiments(project_filter)
        
        # Create new experiment
        with st.expander("➕ Create New Experiment"):
            with st.form("new_experiment"):
                name = st.text_input("Experiment Title*")
                description = st.text_area("Description")
                
                if projects:
                    project_options = {f"{p.name} (ID: {p.id})": p.id for p in projects}
                    selected_project = st.selectbox("Project*", options=list(project_options.keys()))
                    project_id = project_options[selected_project]
                else:
                    st.warning("Please create a project first!")
                    project_id = None
                
                status = st.selectbox("Status", ["Draft", "Final", "Archived"])
                experiment_date = st.date_input("Experiment Date", datetime.now())
                tags = st.text_input("Tags (comma-separated)", help="e.g., PCR, DNA, cloning")
                
                if st.form_submit_button("Create Experiment") and project_id:
                    experiment = db.create_experiment(
                        project_id=project_id,
                        title=name,
                        description=description,
                        status=status,
                        experiment_date=datetime.combine(experiment_date, datetime.min.time()),
                        tags=tags
                    )
                    display_success(f"Experiment '{experiment.title}' created successfully!")
                    st.rerun()
        
        # Display experiments
        if experiments:
            st.subheader(f"Experiments ({len(experiments)})")
            
            for experiment in experiments:
                status_color = get_status_color(experiment.status)
                
                with st.expander(f"🧪 {experiment.title}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Status:** <span class='status-{experiment.status.lower()}'>{experiment.status}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Description:** {experiment.description or 'No description'}")
                        st.markdown(f"**Date:** {format_date(experiment.experiment_date)}")
                        st.markdown(f"**Created:** {format_datetime(experiment.created_at)}")
                        
                        if experiment.tags:
                            tags_list = parse_tags(experiment.tags)
                            st.markdown(f"**Tags:** {', '.join([f'`{tag}`' for tag in tags_list])}")
                        
                        # Show entries count
                        entries = db.get_entries(experiment.id)
                        st.markdown(f"**Entries:** {len(entries)}")
                    
                    with col2:
                        if st.button("📝 View Entries", key=f"view_entries_{experiment.id}"):
                            st.session_state.selected_experiment = experiment.id
                            st.session_state.page = "Entries"
                            st.rerun()
                        
                        if st.button("✏️ Edit", key=f"edit_exp_{experiment.id}"):
                            st.session_state.edit_experiment = experiment.id
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_exp_{experiment.id}"):
                            if db.delete_experiment(experiment.id):
                                display_success("Experiment deleted successfully!")
                                st.rerun()
        else:
            st.info("No experiments found. Create your first experiment above!")

def render_entries():
    st.title("📝 Entries")
    
    # Handle experiment selection from experiments page
    if 'selected_experiment' in st.session_state and st.session_state.selected_experiment:
        experiment_filter = st.session_state.selected_experiment
    else:
        experiment_filter = None
    
    with DatabaseManager() as db:
        experiments = db.get_experiments()
        entries = db.get_entries(experiment_filter)
        
        # Experiment filter
        if experiments:
            exp_options = {f"{exp.title} (ID: {exp.id})": exp.id for exp in experiments}
            exp_options["All Experiments"] = None
            
            selected_exp_name = st.selectbox(
                "Filter by Experiment",
                options=list(exp_options.keys()),
                index=list(exp_options.keys()).index("All Experiments") if not experiment_filter else 0
            )
            
            experiment_filter = exp_options[selected_exp_name]
            entries = db.get_entries(experiment_filter)
        
        # Create new entry
        with st.expander("➕ Create New Entry"):
            with st.form("new_entry_form"):
                title = st.text_input("Entry Title*")
                
                if experiments:
                    exp_options = {f"{exp.title} (ID: {exp.id})": exp.id for exp in experiments}
                    selected_experiment = st.selectbox("Experiment*", options=list(exp_options.keys()))
                    experiment_id = exp_options[selected_experiment]
                else:
                    st.warning("Please create an experiment first!")
                    experiment_id = None
                
                content_type = st.selectbox("Content Type", ["markdown", "plain"])
                
                if st.form_submit_button("📝 Create Entry with Advanced Editor") and experiment_id:
                    st.session_state.new_entry = experiment_id
                    st.rerun()
                
                if st.form_submit_button("Create Simple Entry") and experiment_id:
                    entry = db.create_entry(
                        experiment_id=experiment_id,
                        title=title,
                        content_type=content_type
                    )
                    display_success(f"Entry '{entry.title}' created successfully!")
                    st.rerun()
        
        # Display entries
        if entries:
            st.subheader(f"Entries ({len(entries)})")
            
            for entry in entries:
                lock_icon = "🔒" if entry.is_locked else "📝"
                
                with st.expander(f"{lock_icon} {entry.title}"):
                    if entry.is_locked:
                        st.warning("🔒 This entry is locked and cannot be edited")
                        st.markdown(f"**Digital Signature:** {entry.digital_signature}")
                        st.markdown(f"**Locked on:** {format_datetime(entry.locked_at)}")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Created:** {format_datetime(entry.created_at)}")
                        st.markdown(f"**Updated:** {format_datetime(entry.updated_at)}")
                        
                        # Show content
                        if entry.content:
                            if entry.content_type == "markdown":
                                st.markdown("### Content Preview")
                                st.markdown(render_markdown_with_latex(entry.content), unsafe_allow_html=True)
                            else:
                                st.markdown("### Content")
                                st.text(entry.content)
                        
                        # Show linked reagents
                        linked_reagents = db.get_linked_reagents(entry.id)
                        if linked_reagents:
                            st.markdown("### Linked Reagents")
                            for link in linked_reagents:
                                reagent = db.get_reagent(link.reagent_id)
                                if reagent:
                                    quantity_info = f" ({link.quantity_used} {link.unit})" if link.quantity_used else ""
                                    st.markdown(f"- **{reagent.name}**{quantity_info}")
                                    if link.notes:
                                        st.markdown(f"  *Note: {link.notes}*")
                    
                    with col2:
                        if st.button("👁️ View", key=f"view_entry_{entry.id}"):
                            st.session_state.view_entry = entry.id
                            st.rerun()
                        
                        if not entry.is_locked:
                            if st.button("✏️ Edit", key=f"edit_entry_{entry.id}"):
                                st.session_state.edit_entry = entry.id
                                st.rerun()
                            
                            if st.button("🔒 Lock Entry", key=f"lock_entry_{entry.id}"):
                                st.session_state.lock_entry = entry.id
                                st.rerun()
                        else:
                            if st.button("🔓 Unlock Entry", key=f"unlock_entry_{entry.id}"):
                                st.session_state.unlock_entry = entry.id
                                st.rerun()
                        
                        if st.button("📄 Export PDF", key=f"export_pdf_{entry.id}"):
                            if entry.content:
                                filename = f"entry_{entry.id}_{entry.title.replace(' ', '_')}.pdf"
                                export_to_pdf(entry.content, filename, entry.title)
                                display_success(f"PDF exported as {filename}")
                        
                        if st.button("🗑️ Delete", key=f"del_entry_{entry.id}"):
                            if not entry.is_locked:
                                # Delete entry (cascade will handle related records)
                                db.session.delete(entry)
                                db.session.commit()
                                display_success("Entry deleted successfully!")
                                st.rerun()
                            else:
                                display_error("Cannot delete locked entry!")
        else:
            st.info("No entries found. Create your first entry above!")

def render_inventory():
    st.title("🧫 Lab Inventory")
    
    inventory_type = st.tabs(["🧪 Reagents", "🧬 Samples", "🔧 Equipment"])
    
    with inventory_type[0]:  # Reagents
        render_reagents()
    
    with inventory_type[1]:  # Samples
        render_samples()
    
    with inventory_type[2]:  # Equipment
        render_equipment()

def render_reagents():
    with DatabaseManager() as db:
        reagents = db.get_reagents()
        
        # Create new reagent
        with st.expander("➕ Add New Reagent"):
            with st.form("new_reagent"):
                name = st.text_input("Reagent Name*")
                description = st.text_area("Description")
                catalog_number = st.text_input("Catalog Number")
                supplier = st.text_input("Supplier")
                concentration = st.number_input("Concentration", min_value=0.0, format="%.2f")
                unit = st.selectbox("Unit", ["M", "mM", "µM", "mg/mL", "µg/mL", "g/L", "mg", "g", "mL", "L"])
                storage_location = st.text_input("Storage Location")
                safety_info = st.text_area("Safety Information")
                
                if st.form_submit_button("Add Reagent"):
                    reagent = db.create_reagent(
                        name=name,
                        description=description,
                        catalog_number=catalog_number,
                        supplier=supplier,
                        concentration=concentration if concentration > 0 else None,
                        unit=unit,
                        storage_location=storage_location,
                        safety_info=safety_info
                    )
                    display_success(f"Reagent '{reagent.name}' added successfully!")
                    st.rerun()
        
        # Display reagents
        if reagents:
            st.subheader(f"Reagents ({len(reagents)})")
            
            for reagent in reagents:
                with st.expander(f"🧪 {reagent.name}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {reagent.description or 'No description'}")
                        if reagent.catalog_number:
                            st.markdown(f"**Catalog #:** {reagent.catalog_number}")
                        if reagent.supplier:
                            st.markdown(f"**Supplier:** {reagent.supplier}")
                        if reagent.concentration:
                            st.markdown(f"**Concentration:** {reagent.concentration} {reagent.unit}")
                        if reagent.storage_location:
                            st.markdown(f"**Storage:** {reagent.storage_location}")
                        if reagent.safety_info:
                            st.markdown(f"**Safety:** {reagent.safety_info}")
                        st.markdown(f"**Updated:** {format_datetime(reagent.updated_at)}")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_reagent_{reagent.id}"):
                            st.session_state.edit_reagent = reagent.id
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_reagent_{reagent.id}"):
                            if db.delete_reagent(reagent.id):
                                display_success("Reagent deleted successfully!")
                                st.rerun()
        else:
            st.info("No reagents found. Add your first reagent above!")

def render_samples():
    with DatabaseManager() as db:
        samples = db.get_samples()
        
        # Create new sample
        with st.expander("➕ Add New Sample"):
            with st.form("new_sample"):
                name = st.text_input("Sample Name*")
                description = st.text_area("Description")
                sample_type = st.text_input("Sample Type")
                storage_location = st.text_input("Storage Location")
                quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
                unit = st.selectbox("Unit", ["mg", "g", "µg", "mL", "L", "µL", "units"])
                
                if st.form_submit_button("Add Sample"):
                    sample = db.create_sample(
                        name=name,
                        description=description,
                        sample_type=sample_type,
                        storage_location=storage_location,
                        quantity=quantity if quantity > 0 else None,
                        unit=unit
                    )
                    display_success(f"Sample '{sample.name}' added successfully!")
                    st.rerun()
        
        # Display samples
        if samples:
            st.subheader(f"Samples ({len(samples)})")
            
            for sample in samples:
                with st.expander(f"🧬 {sample.name}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {sample.description or 'No description'}")
                        if sample.sample_type:
                            st.markdown(f"**Type:** {sample.sample_type}")
                        if sample.storage_location:
                            st.markdown(f"**Storage:** {sample.storage_location}")
                        if sample.quantity:
                            st.markdown(f"**Quantity:** {sample.quantity} {sample.unit}")
                        st.markdown(f"**Updated:** {format_datetime(sample.updated_at)}")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_sample_{sample.id}"):
                            st.session_state.edit_sample = sample.id
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_sample_{sample.id}"):
                            db.session.delete(sample)
                            db.session.commit()
                            display_success("Sample deleted successfully!")
                            st.rerun()
        else:
            st.info("No samples found. Add your first sample above!")

def render_equipment():
    with DatabaseManager() as db:
        equipment_list = db.get_equipment()
        
        # Create new equipment
        with st.expander("➕ Add New Equipment"):
            with st.form("new_equipment"):
                name = st.text_input("Equipment Name*")
                model = st.text_input("Model")
                serial_number = st.text_input("Serial Number")
                location = st.text_input("Location")
                status = st.selectbox("Status", ["Available", "In Use", "Maintenance"])
                last_maintenance = st.date_input("Last Maintenance", datetime.now() - timedelta(days=30))
                
                if st.form_submit_button("Add Equipment"):
                    equipment = db.create_equipment(
                        name=name,
                        model=model,
                        serial_number=serial_number,
                        location=location,
                        status=status,
                        last_maintenance=datetime.combine(last_maintenance, datetime.min.time())
                    )
                    display_success(f"Equipment '{equipment.name}' added successfully!")
                    st.rerun()
        
        # Display equipment
        if equipment_list:
            st.subheader(f"Equipment ({len(equipment_list)})")
            
            for equipment in equipment_list:
                status_color = {
                    'Available': 'green',
                    'In Use': 'orange', 
                    'Maintenance': 'red'
                }.get(equipment.status, 'gray')
                
                with st.expander(f"🔧 {equipment.name}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Status:** <span style='color: {status_color}'>{equipment.status}</span>", unsafe_allow_html=True)
                        if equipment.model:
                            st.markdown(f"**Model:** {equipment.model}")
                        if equipment.serial_number:
                            st.markdown(f"**Serial #:** {equipment.serial_number}")
                        if equipment.location:
                            st.markdown(f"**Location:** {equipment.location}")
                        if equipment.last_maintenance:
                            st.markdown(f"**Last Maintenance:** {format_date(equipment.last_maintenance)}")
                        st.markdown(f"**Updated:** {format_datetime(equipment.updated_at)}")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_equipment_{equipment.id}"):
                            st.session_state.edit_equipment = equipment.id
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_equipment_{equipment.id}"):
                            db.session.delete(equipment)
                            db.session.commit()
                            display_success("Equipment deleted successfully!")
                            st.rerun()
        else:
            st.info("No equipment found. Add your first equipment above!")

def render_protocols():
    render_protocol_manager()

def render_search():
    st.title("🔍 Search")
    
    search_type = st.selectbox("Search in", ["All", "Projects", "Experiments", "Entries", "Protocols"])
    query = st.text_input("Search query", placeholder="Enter your search terms...")
    
    if query:
        with DatabaseManager() as db:
            results = []
            
            if search_type in ["All", "Projects"]:
                project_results = db.search_projects(query)
                for project in project_results:
                    results.append({
                        'type': 'Project',
                        'title': project.name,
                        'description': project.description or '',
                        'id': project.id,
                        'updated': project.updated_at
                    })
            
            if search_type in ["All", "Experiments"]:
                experiment_results = db.search_experiments(query)
                for exp in experiment_results:
                    results.append({
                        'type': 'Experiment',
                        'title': exp.title,
                        'description': exp.description or '',
                        'id': exp.id,
                        'updated': exp.updated_at
                    })
            
            if search_type in ["All", "Entries"]:
                entry_results = db.search_entries(query)
                for entry in entry_results:
                    results.append({
                        'type': 'Entry',
                        'title': entry.title,
                        'description': entry.content[:200] + "..." if entry.content and len(entry.content) > 200 else (entry.content or ''),
                        'id': entry.id,
                        'updated': entry.updated_at
                    })
            
            if search_type in ["All", "Protocols"]:
                protocol_results = db.get_protocols()  # Simple search for now
                for protocol in protocol_results:
                    if query.lower() in protocol.name.lower() or (protocol.description and query.lower() in protocol.description.lower()):
                        results.append({
                            'type': 'Protocol',
                            'title': protocol.name,
                            'description': protocol.description or '',
                            'id': protocol.id,
                            'updated': protocol.updated_at
                        })
            
            # Sort by updated date
            results.sort(key=lambda x: x['updated'], reverse=True)
            
            if results:
                st.subheader(f"Results ({len(results)})")
                
                for result in results:
                    icon = {
                        'Project': '📁',
                        'Experiment': '🧪',
                        'Entry': '📝',
                        'Protocol': '📋'
                    }.get(result['type'], '📄')
                    
                    with st.expander(f"{icon} {result['title']} ({result['type']})"):
                        st.markdown(f"**Type:** {result['type']}")
                        st.markdown(f"**Description:** {search_highlight(result['description'], query)}")
                        st.markdown(f"**Last Updated:** {format_datetime(result['updated'])}")
                        
                        # Action buttons based on type
                        if result['type'] == 'Project':
                            if st.button("View Project", key=f"search_proj_{result['id']}"):
                                st.session_state.selected_project = result['id']
                                st.session_state.page = "Experiments"
                                st.rerun()
                        elif result['type'] == 'Experiment':
                            if st.button("View Experiment", key=f"search_exp_{result['id']}"):
                                st.session_state.selected_experiment = result['id']
                                st.session_state.page = "Entries"
                                st.rerun()
                        elif result['type'] == 'Entry':
                            if st.button("View Entry", key=f"search_entry_{result['id']}"):
                                st.session_state.view_entry = result['id']
                                st.session_state.page = "Entries"
                                st.rerun()
                        elif result['type'] == 'Protocol':
                            if st.button("View Protocol", key=f"search_protocol_{result['id']}"):
                                st.session_state.view_protocol = result['id']
                                st.session_state.page = "Protocols"
                                st.rerun()
            else:
                st.info("No results found for your search query.")
    else:
        st.info("Enter a search query to find items across your ELN.")

def render_settings():
    st.title("⚙️ Settings")
    
    st.subheader("Database Information")
    
    with DatabaseManager() as db:
        projects_count = len(db.get_projects())
        experiments_count = len(db.get_experiments())
        entries_count = len(db.get_entries())
        reagents_count = len(db.get_reagents())
        samples_count = len(db.get_samples())
        equipment_count = len(db.get_equipment())
        protocols_count = len(db.get_protocols())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Projects", projects_count)
            st.metric("Experiments", experiments_count)
            st.metric("Entries", entries_count)
            st.metric("Reagents", reagents_count)
        
        with col2:
            st.metric("Samples", samples_count)
            st.metric("Equipment", equipment_count)
            st.metric("Protocols", protocols_count)
            st.metric("Total Items", projects_count + experiments_count + entries_count + reagents_count + samples_count + equipment_count + protocols_count)
    
    st.markdown("---")
    
    st.subheader("Export Data")
    
    export_type = st.selectbox("Export Type", ["Entries as CSV", "All Data (Coming Soon)"])
    
    if export_type == "Entries as CSV":
        if st.button("📊 Export Entries to CSV"):
            with DatabaseManager() as db:
                entries = db.get_entries()
                if entries:
                    df = export_entries_to_csv(entries)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"eln_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No entries to export")
    
    st.markdown("---")
    
    st.subheader("About")
    st.markdown("""
    **Electronic Lab Notebook v1.0**
    
    A professional-grade ELN built with:
    - Streamlit for the web interface
    - SQLAlchemy for database management
    - SQLite for data storage
    - Markdown and LaTeX for rich content
    
    **Features:**
    - Hierarchical organization (Projects > Experiments > Entries)
    - Rich text editing with Markdown and LaTeX support
    - Inventory management with reagent linking
    - Protocol versioning
    - Digital signatures and audit trails
    - Search and export functionality
    """)
    
    st.markdown("---")
    
    st.subheader("Database Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Database", help="Refresh database connection"):
            st.rerun()
    
    with col2:
        if st.button("📊 Database Stats", help="Show detailed database statistics"):
            with DatabaseManager() as db:
                st.info("Database statistics refreshed")

# Main app logic
def main():
    # Initialize session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = page
    else:
        # Update session state when user picks a different page from sidebar
        if page != st.session_state.page:
            st.session_state.page = page
    
    current_page = st.session_state.page
    
    # Render the selected page
    if current_page == "🏠 Dashboard":
        render_dashboard()
    elif current_page == "📁 Projects":
        render_projects()
    elif current_page == "🧪 Experiments":
        render_experiments()
    elif current_page == "📝 Entries":
        render_entries()
    elif current_page == "🧫 Lab Inventory":
        render_inventory()
    elif current_page == "📋 Protocols":
        render_protocols()
    elif current_page == "🔍 Search":
        render_search()
    elif current_page == "⚙️ Settings":
        render_settings()
    
    # Handle modal dialogs (edit forms, etc.)
    handle_modals()
    handle_protocol_modals()

def handle_modals():
    """Handle modal dialogs for editing, locking, etc."""
    
    # Entry editor modal
    if 'edit_entry' in st.session_state and st.session_state.edit_entry:
        with st.modal("✏️ Edit Entry"):
            render_entry_editor(entry_id=st.session_state.edit_entry)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    st.session_state.edit_entry = None
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.edit_entry
                    st.rerun()
    
    # New entry editor modal
    if 'new_entry' in st.session_state and st.session_state.new_entry:
        with st.modal("📝 Create New Entry"):
            render_entry_editor(experiment_id=st.session_state.new_entry)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Create Entry", type="primary"):
                    st.session_state.new_entry = None
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.new_entry
                    st.rerun()
    
    # Entry view modal
    if 'view_entry' in st.session_state and st.session_state.view_entry:
        with st.modal("📄 View Entry"):
            render_entry_view(st.session_state.view_entry)
            
            if st.button("❌ Close"):
                del st.session_state.view_entry
                st.rerun()
    
    # Entry locking modal
    if 'lock_entry' in st.session_state and st.session_state.lock_entry:
        with st.modal("🔒 Lock Entry"):
            st.warning("Locking an entry will prevent further edits. This action requires a digital signature.")
            
            with DatabaseManager() as db:
                entry = db.get_entry(st.session_state.lock_entry)
                
                if entry:
                    st.markdown(f"**Entry:** {entry.title}")
                    st.markdown(f"**Experiment ID:** {entry.experiment_id}")
                    
                    signature = st.text_input("Digital Signature*", placeholder="Enter your name or initials", help="This serves as your digital signature")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔒 Lock Entry", type="primary"):
                            if signature and validate_digital_signature(signature):
                                if db.lock_entry(entry.id, signature):
                                    display_success("Entry locked successfully!")
                                    del st.session_state.lock_entry
                                    st.rerun()
                                else:
                                    display_error("Failed to lock entry")
                            else:
                                display_error("Please enter a valid signature")
                    
                    with col2:
                        if st.button("❌ Cancel"):
                            del st.session_state.lock_entry
                            st.rerun()
    
    # Entry unlocking modal
    if 'unlock_entry' in st.session_state and st.session_state.unlock_entry:
        with st.modal("🔓 Unlock Entry"):
            st.warning("Unlocking an entry requires the same digital signature used to lock it.")
            
            with DatabaseManager() as db:
                entry = db.get_entry(st.session_state.unlock_entry)
                
                if entry:
                    st.markdown(f"**Entry:** {entry.title}")
                    st.markdown(f"**Locked with signature:** {entry.digital_signature}")
                    
                    signature = st.text_input("Digital Signature*", placeholder="Enter the signature used to lock this entry")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔓 Unlock Entry", type="primary"):
                            if signature:
                                if db.unlock_entry(entry.id, signature):
                                    display_success("Entry unlocked successfully!")
                                    del st.session_state.unlock_entry
                                    st.rerun()
                                else:
                                    display_error("Invalid signature or entry is not locked")
                            else:
                                display_error("Please enter the signature")
                    
                    with col2:
                        if st.button("❌ Cancel"):
                            del st.session_state.unlock_entry
                            st.rerun()

if __name__ == "__main__":
    main()
