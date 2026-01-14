import streamlit as st
import os
from datetime import datetime
from database import DatabaseManager
from models import Attachment
from utils import render_markdown_with_latex, save_uploaded_file, display_success, display_error, display_warning

def render_entry_editor(entry_id=None, experiment_id=None):
    """Render the advanced entry editor with Markdown/LaTeX support and reagent linking"""
    
    with DatabaseManager() as db:
        # Get entry data if editing
        entry = None
        if entry_id:
            entry = db.get_entry(entry_id)
            if not entry:
                display_error("Entry not found")
                return
        
        # Check if entry is locked
        if entry and entry.is_locked:
            display_warning("This entry is locked and cannot be edited")
            return
        
        # Get experiment info
        experiment = None
        if entry:
            experiment = db.get_experiment(entry.experiment_id)
        elif experiment_id:
            experiment = db.get_experiment(experiment_id)
        
        if not experiment:
            display_error("No experiment associated with this entry")
            return
        
        st.subheader(f"📝 {'Edit' if entry else 'Create'} Entry")
        st.markdown(f"**Experiment:** {experiment.title}")
        
        # Editor tabs
        editor_tab, preview_tab, attachments_tab, reagents_tab = st.tabs(["✏️ Edit", "👁️ Preview", "📎 Attachments", "🧪 Linked Reagents"])
        
        with editor_tab:
            render_edit_form(entry, experiment, db)
        
        with preview_tab:
            render_preview(entry, db)
        
        with attachments_tab:
            render_attachments(entry, db)
        
        with reagents_tab:
            render_linked_reagents(entry, experiment, db)

def render_edit_form(entry, experiment, db):
    """Render the entry editing form"""
    
    with st.form("entry_form"):
        title = st.text_input("Entry Title*", value=entry.title if entry else "")
        
        # Content editor
        st.markdown("### Content (Markdown with LaTeX support)")
        st.markdown("""
        **Formatting Guide:**
        - Use Markdown for formatting (headers, lists, tables, etc.)
        - Inline LaTeX math: `$E = mc^2$`
        - Display LaTeX math: `$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$`
        - Code blocks: Use triple backticks for code
        """)
        
        content = st.text_area(
            "Content",
            value=entry.content if entry else "",
            height=400,
            help="Enter your experiment notes using Markdown formatting. LaTeX math is supported."
        )
        
        content_type = st.selectbox(
            "Content Type",
            ["markdown", "plain"],
            index=0 if (entry and entry.content_type == "markdown") else 1
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Entry", type="primary"):
                if title.strip():
                    if entry:
                        # Update existing entry
                        updated_entry = db.update_entry(
                            entry.id,
                            title=title,
                            content=content,
                            content_type=content_type
                        )
                        if updated_entry:
                            display_success("Entry updated successfully!")
                            st.rerun()
                        else:
                            display_error("Failed to update entry")
                    else:
                        # Create new entry
                        new_entry = db.create_entry(
                            experiment_id=experiment.id,
                            title=title,
                            content=content,
                            content_type=content_type
                        )
                        display_success(f"Entry '{new_entry.title}' created successfully!")
                        st.rerun()
                else:
                    display_error("Title is required")
        
        with col2:
            if st.form_submit_button("🔒 Save & Lock"):
                if title.strip():
                    # First save the entry
                    if entry:
                        updated_entry = db.update_entry(
                            entry.id,
                            title=title,
                            content=content,
                            content_type=content_type
                        )
                        entry_id = updated_entry.id
                    else:
                        new_entry = db.create_entry(
                            experiment_id=experiment.id,
                            title=title,
                            content=content,
                            content_type=content_type
                        )
                        entry_id = new_entry.id
                    
                    # Then trigger lock modal
                    st.session_state.lock_entry = entry_id
                    st.rerun()
                else:
                    display_error("Title is required")

def render_preview(entry, db):
    """Render the preview of the entry content"""
    
    if entry and entry.content:
        st.markdown(f"### {entry.title}")
        
        if entry.content_type == "markdown":
            # Render markdown with LaTeX
            rendered_content = render_markdown_with_latex(entry.content)
            st.markdown(rendered_content, unsafe_allow_html=True)
        else:
            # Render plain text
            st.text(entry.content)
        
        # Show metadata
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Created:** {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            st.markdown(f"**Updated:** {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        with col3:
            lock_status = "🔒 Locked" if entry.is_locked else "📝 Editable"
            st.markdown(f"**Status:** {lock_status}")
    else:
        st.info("No content to preview. Add content in the Edit tab.")

def render_attachments(entry, db):
    """Render file attachment management"""
    
    st.markdown("### File Attachments")
    
    if entry:
        # Show existing attachments
        attachments = db.session.query(Attachment).filter(Attachment.entry_id == entry.id).all()
        
        if attachments:
            st.markdown(f"**Current Attachments ({len(attachments)}):**")
            
            for attachment in attachments:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"📄 {attachment.original_filename}")
                    st.markdown(f"Size: {attachment.file_size / 1024:.1f} KB | Uploaded: {attachment.uploaded_at.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    if os.path.exists(attachment.file_path):
                        with open(attachment.file_path, 'rb') as f:
                            st.download_button(
                                label="⬇️",
                                data=f.read(),
                                file_name=attachment.original_filename,
                                key=f"download_{attachment.id}"
                            )
                
                with col3:
                    if st.button("🗑️", key=f"del_attachment_{attachment.id}"):
                        db.session.delete(attachment)
                        db.session.commit()
                        display_success("Attachment deleted")
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("No attachments yet")
        
        # Add new attachment
        st.markdown("### Add New Attachment")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'csv', 'xlsx', 'docx'],
            help="Supported formats: Images, PDF, Text, CSV, Excel, Word"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                display_error("File size exceeds 10MB limit")
            else:
                if st.button("📎 Upload File"):
                    try:
                        file_path, filename = save_uploaded_file(uploaded_file)
                        
                        # Create attachment record
                        attachment = Attachment(
                            entry_id=entry.id,
                            filename=filename,
                            original_filename=uploaded_file.name,
                            file_path=file_path,
                            file_size=file_size,
                            mime_type=uploaded_file.type
                        )
                        db.session.add(attachment)
                        db.session.commit()
                        
                        display_success(f"File '{uploaded_file.name}' uploaded successfully!")
                        st.rerun()
                    except Exception as e:
                        display_error(f"Failed to upload file: {str(e)}")
    else:
        st.info("Please save the entry first before adding attachments")

def render_linked_reagents(entry, experiment, db):
    """Render reagent linking functionality"""
    
    st.markdown("### Linked Reagents")
    
    if entry:
        # Show existing linked reagents
        linked_reagents = db.get_linked_reagents(entry.id)
        
        if linked_reagents:
            st.markdown(f"**Currently Linked ({len(linked_reagents)}):**")
            
            for link in linked_reagents:
                reagent = db.get_reagent(link.reagent_id)
                if reagent:
                    with st.expander(f"🧪 {reagent.name}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Reagent:** {reagent.name}")
                            if reagent.supplier:
                                st.markdown(f"**Supplier:** {reagent.supplier}")
                            if reagent.catalog_number:
                                st.markdown(f"**Catalog #:** {reagent.catalog_number}")
                            if link.quantity_used:
                                st.markdown(f"**Quantity Used:** {link.quantity_used} {link.unit or 'units'}")
                            if link.notes:
                                st.markdown(f"**Notes:** {link.notes}")
                            st.markdown(f"**Linked:** {link.linked_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        with col2:
                            if st.button("🗑️ Remove", key=f"remove_reagent_{link.id}"):
                                if db.remove_linked_reagent(link.id):
                                    display_success("Reagent link removed")
                                    st.rerun()
                                else:
                                    display_error("Failed to remove reagent link")
                
                st.markdown("---")
        else:
            st.info("No reagents linked to this entry")
        
        # Add new reagent link
        st.markdown("### Link New Reagent")
        
        # Get available reagents
        reagents = db.get_reagents()
        
        if reagents:
            reagent_options = {f"{r.name} ({r.supplier or 'Unknown supplier'})": r.id for r in reagents}
            
            with st.form("link_reagent_form"):
                selected_reagent = st.selectbox("Select Reagent*", options=list(reagent_options.keys()))
                reagent_id = reagent_options[selected_reagent]
                
                quantity_used = st.number_input("Quantity Used", min_value=0.0, format="%.4f")
                unit = st.selectbox("Unit", ["mL", "µL", "L", "g", "mg", "µg", "mol", "mmol", "µmol", "units", ""])
                notes = st.text_area("Notes (optional)")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("🔗 Link Reagent", type="primary"):
                        if quantity_used > 0 or unit or notes:
                            linked_reagent = db.link_reagent_to_entry(
                                entry_id=entry.id,
                                reagent_id=reagent_id,
                                quantity_used=quantity_used if quantity_used > 0 else None,
                                unit=unit if unit else None,
                                notes=notes if notes else None
                            )
                            display_success(f"Reagent linked successfully!")
                            st.rerun()
                        else:
                            display_error("Please provide at least quantity, unit, or notes")
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.rerun()
        else:
            st.warning("No reagents available in inventory. Add reagents in the Lab Inventory section first.")
    else:
        st.info("Please save the entry first before linking reagents")

def render_entry_view(entry_id):
    """Render a read-only view of an entry"""
    
    with DatabaseManager() as db:
        entry = db.get_entry(entry_id)
        
        if not entry:
            display_error("Entry not found")
            return
        
        experiment = db.get_experiment(entry.experiment_id)
        project = db.get_project(experiment.project_id) if experiment else None
        
        # Header
        st.title(f"📝 {entry.title}")
        
        # Breadcrumb navigation
        if project and experiment:
            st.markdown(f"📁 {project.name} > 🧪 {experiment.title}")
        
        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Created", entry.created_at.strftime('%Y-%m-%d'))
        
        with col2:
            st.metric("Updated", entry.updated_at.strftime('%Y-%m-%d'))
        
        with col3:
            status = "🔒 Locked" if entry.is_locked else "📝 Editable"
            st.metric("Status", status)
        
        with col4:
            st.metric("Content Type", entry.content_type.capitalize())
        
        st.markdown("---")
        
        # Content tabs
        content_tab, attachments_tab, reagents_tab, audit_tab = st.tabs(["📄 Content", "📎 Attachments", "🧪 Reagents", "📋 Audit Trail"])
        
        with content_tab:
            if entry.content:
                if entry.content_type == "markdown":
                    rendered_content = render_markdown_with_latex(entry.content)
                    st.markdown(rendered_content, unsafe_allow_html=True)
                else:
                    st.text(entry.content)
            else:
                st.info("No content")
        
        with attachments_tab:
            render_attachments(entry, db)
        
        with reagents_tab:
            render_linked_reagents(entry, experiment, db)
        
        with audit_tab:
            render_audit_trail(entry, db)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not entry.is_locked:
                if st.button("✏️ Edit Entry", type="primary"):
                    st.session_state.edit_entry = entry.id
                    st.rerun()
            else:
                if st.button("🔓 Unlock Entry"):
                    st.session_state.unlock_entry = entry.id
                    st.rerun()
        
        with col2:
            if st.button("📄 Export PDF"):
                if entry.content:
                    filename = f"entry_{entry.id}_{entry.title.replace(' ', '_')}.pdf"
                    from utils import export_to_pdf
                    export_to_pdf(entry.content, filename, entry.title)
                    display_success(f"PDF exported as {filename}")
        
        with col3:
            if st.button("🔍 Back to Entries"):
                st.session_state.selected_experiment = entry.experiment_id
                st.rerun()

def render_audit_trail(entry, db):
    """Render the audit trail for an entry"""
    
    st.markdown("### Audit Trail")
    
    audit_logs = db.get_audit_logs(entry.id)
    
    if audit_logs:
        for log in audit_logs:
            with st.expander(f"📋 {log.action.title()} - {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Action:** {log.action}")
                    st.markdown(f"**User:** {log.user_id or 'System'}")
                    st.markdown(f"**Timestamp:** {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    if log.details:
                        st.markdown(f"**Details:** {log.details}")
                
                st.markdown("---")
    else:
        st.info("No audit logs available for this entry")
