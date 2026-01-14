import streamlit as st
from datetime import datetime
from database import DatabaseManager
from utils import render_markdown_with_latex, display_success, display_error, display_warning, display_info

def render_protocol_manager():
    """Render the protocol management interface"""
    
    with DatabaseManager() as db:
        protocols = db.get_current_protocols()
        
        st.title("📋 Protocol Management")
        
        # Create new protocol
        with st.expander("➕ Create New Protocol"):
            render_protocol_form(db)
        
        st.markdown("---")
        
        # Protocol tabs
        current_tab, history_tab = st.tabs(["📋 Current Protocols", "📜 Version History"])
        
        with current_tab:
            render_current_protocols(db, protocols)
        
        with history_tab:
            render_protocol_history(db)

def render_protocol_form(db, protocol=None):
    """Render the protocol creation/editing form"""
    
    is_edit = protocol is not None
    
    with st.form("protocol_form"):
        name = st.text_input("Protocol Name*", value=protocol.name if protocol else "")
        description = st.text_area("Description", value=protocol.description if protocol else "")
        content = st.text_area(
            "Protocol Content (Markdown)*", 
            value=protocol.content if protocol else "",
            height=400,
            help="Use Markdown formatting. LaTeX math supported with $...$ for inline and $$...$$ for display."
        )
        created_by = st.text_input("Created By", value=protocol.created_by if protocol else "")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Protocol", type="primary"):
                if name.strip() and content.strip():
                    if is_edit:
                        # Create new version instead of editing
                        new_protocol = db.create_protocol_version(
                            parent_id=protocol.id,
                            content=content,
                            created_by=created_by
                        )
                        if new_protocol:
                            display_success(f"New version ({new_protocol.version}) created successfully!")
                            st.rerun()
                        else:
                            display_error("Failed to create new version")
                    else:
                        # Create new protocol
                        new_protocol = db.create_protocol(
                            name=name,
                            description=description,
                            content=content,
                            created_by=created_by
                        )
                        display_success(f"Protocol '{new_protocol.name}' created successfully!")
                        st.rerun()
                else:
                    display_error("Name and content are required")
        
        with col2:
            if st.form_submit_button("👁️ Preview"):
                if content.strip():
                    st.markdown("### Content Preview")
                    rendered_content = render_markdown_with_latex(content)
                    st.markdown(rendered_content, unsafe_allow_html=True)
                else:
                    display_warning("No content to preview")

def render_current_protocols(db, protocols):
    """Render current protocols list"""
    
    if protocols:
        st.subheader(f"Current Protocols ({len(protocols)})")
        
        for protocol in protocols:
            with st.expander(f"📋 {protocol.name} (v{protocol.version})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Description:** {protocol.description or 'No description'}")
                    st.markdown(f"**Version:** {protocol.version}")
                    st.markdown(f"**Created By:** {protocol.created_by or 'Unknown'}")
                    st.markdown(f"**Created:** {format_datetime(protocol.created_at)}")
                    st.markdown(f"**Updated:** {format_datetime(protocol.updated_at)}")
                    
                    # Show content preview
                    if protocol.content:
                        st.markdown("### Protocol Preview")
                        preview_content = protocol.content[:300] + "..." if len(protocol.content) > 300 else protocol.content
                        rendered_preview = render_markdown_with_latex(preview_content)
                        st.markdown(rendered_preview, unsafe_allow_html=True)
                
                with col2:
                    if st.button("👁️ View Full", key=f"view_protocol_{protocol.id}"):
                        st.session_state.view_protocol = protocol.id
                        st.rerun()
                    
                    if st.button("📝 New Version", key=f"new_version_{protocol.id}"):
                        st.session_state.edit_protocol = protocol.id
                        st.rerun()
                    
                    if st.button("📜 View History", key=f"history_{protocol.id}"):
                        st.session_state.protocol_history = protocol.id
                        st.rerun()
                    
                    if st.button("📄 Export", key=f"export_protocol_{protocol.id}"):
                        # Export protocol as text file
                        content = f"# {protocol.name} (v{protocol.version})\n\n"
                        content += f"**Description:** {protocol.description or 'N/A'}\n\n"
                        content += f"**Created By:** {protocol.created_by or 'Unknown'}\n\n"
                        content += f"**Created:** {format_datetime(protocol.created_at)}\n\n"
                        content += f"**Updated:** {format_datetime(protocol.updated_at)}\n\n"
                        content += "---\n\n"
                        content += protocol.content
                        
                        st.download_button(
                            label="⬇️ Download Protocol",
                            data=content,
                            file_name=f"protocol_{protocol.name.replace(' ', '_')}_v{protocol.version}.md",
                            mime="text/markdown"
                        )
    else:
        st.info("No protocols found. Create your first protocol above!")

def render_protocol_history(db):
    """Render protocol version history"""
    
    st.subheader("📜 Protocol Version History")
    
    all_protocols = db.get_protocols()
    
    if all_protocols:
        # Group protocols by name
        protocol_groups = {}
        for protocol in all_protocols:
            if protocol.name not in protocol_groups:
                protocol_groups[protocol.name] = []
            protocol_groups[protocol.name].append(protocol)
        
        # Sort each group by version (descending)
        for name in protocol_groups:
            protocol_groups[name].sort(key=lambda x: x.version, reverse=True)
        
        # Display each protocol group
        for protocol_name, versions in protocol_groups.items():
            with st.expander(f"📋 {protocol_name} ({len(versions)} versions)"):
                for version in versions:
                    status_icon = "✅" if version.is_current else "📜"
                    
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"{status_icon} **Version {version.version}**")
                            st.markdown(f"Created: {format_datetime(version.created_at)}")
                            st.markdown(f"By: {version.created_by or 'Unknown'}")
                            if not version.is_current:
                                st.markdown(f"*Archived version*")
                        
                        with col2:
                            if st.button("👁️ View", key=f"view_version_{version.id}"):
                                st.session_state.view_protocol = version.id
                                st.rerun()
                        
                        with col3:
                            if version.is_current:
                                st.markdown("**Current**")
                            else:
                                if st.button("🔄 Restore", key=f"restore_{version.id}"):
                                    # Restore this version as current
                                    with DatabaseManager() as restore_db:
                                        # Mark all versions as not current
                                        for v in versions:
                                            v.is_current = False
                                        
                                        # Mark this version as current
                                        version.is_current = True
                                        restore_db.session.commit()
                                        
                                        display_success(f"Version {version.version} restored as current!")
                                        st.rerun()
                        
                        st.markdown("---")
    else:
        st.info("No protocol history found")

def render_protocol_view(protocol_id):
    """Render a detailed view of a protocol"""
    
    with DatabaseManager() as db:
        protocol = db.get_protocol(protocol_id)
        
        if not protocol:
            display_error("Protocol not found")
            return
        
        st.title(f"📋 {protocol.name}")
        
        # Version info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Version", protocol.version)
        
        with col2:
            status = "✅ Current" if protocol.is_current else "📜 Archived"
            st.metric("Status", status)
        
        with col3:
            st.metric("Created", protocol.created_at.strftime('%Y-%m-%d'))
        
        with col4:
            st.metric("Updated", protocol.updated_at.strftime('%Y-%m-%d'))
        
        st.markdown("---")
        
        # Protocol details
        if protocol.description:
            st.markdown("### Description")
            st.markdown(protocol.description)
        
        if protocol.created_by:
            st.markdown(f"**Created By:** {protocol.created_by}")
        
        # Content tabs
        content_tab, compare_tab = st.tabs(["📄 Content", "🔄 Compare Versions"])
        
        with content_tab:
            if protocol.content:
                rendered_content = render_markdown_with_latex(protocol.content)
                st.markdown(rendered_content, unsafe_allow_html=True)
            else:
                st.info("No content")
        
        with compare_tab:
            render_version_comparison(db, protocol)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Create New Version", type="primary"):
                st.session_state.edit_protocol = protocol.id
                st.rerun()
        
        with col2:
            if st.button("📄 Export Protocol"):
                content = f"# {protocol.name} (v{protocol.version})\n\n"
                content += f"**Description:** {protocol.description or 'N/A'}\n\n"
                content += f"**Created By:** {protocol.created_by or 'Unknown'}\n\n"
                content += f"**Created:** {format_datetime(protocol.created_at)}\n\n"
                content += f"**Updated:** {format_datetime(protocol.updated_at)}\n\n"
                content += "---\n\n"
                content += protocol.content
                
                st.download_button(
                    label="⬇️ Download Protocol",
                    data=content,
                    file_name=f"protocol_{protocol.name.replace(' ', '_')}_v{protocol.version}.md",
                    mime="text/markdown"
                )
        
        with col3:
            if st.button("🔍 Back to Protocols"):
                st.session_state.page = "Protocols"
                st.rerun()

def render_version_comparison(db, current_protocol):
    """Render version comparison interface"""
    
    st.markdown("### Version Comparison")
    
    # Get all versions of this protocol
    all_protocols = db.get_protocols()
    same_name_protocols = [p for p in all_protocols if p.name == current_protocol.name]
    same_name_protocols.sort(key=lambda x: x.version, reverse=True)
    
    if len(same_name_protocols) < 2:
        st.info("No other versions to compare with")
        return
    
    # Select versions to compare
    version_options = {f"Version {p.version} ({p.created_at.strftime('%Y-%m-%d')})": p.id for p in same_name_protocols}
    
    col1, col2 = st.columns(2)
    
    with col1:
        version1_id = st.selectbox("Select Version 1", options=list(version_options.keys()), index=0)
        version1_id = version_options[version1_id]
    
    with col2:
        version2_options = [k for k in version_options.keys() if version_options[k] != version1_id]
        if version2_options:
            version2_id = st.selectbox("Select Version 2", options=version2_options, index=0)
            version2_id = version_options[version2_id]
        else:
            version2_id = None
    
    if version2_id and st.button("🔄 Compare Versions"):
        version1 = db.get_protocol(version1_id)
        version2 = db.get_protocol(version2_id)
        
        if version1 and version2:
            st.markdown(f"### Comparing Version {version1.version} vs Version {version2.version}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Version {version1.version}")
                st.markdown(f"**Created:** {format_datetime(version1.created_at)}")
                st.markdown(f"**By:** {version1.created_by or 'Unknown'}")
                st.markdown(f"**Current:** {'Yes' if version1.is_current else 'No'}")
                st.markdown("---")
                if version1.content:
                    rendered_content = render_markdown_with_latex(version1.content[:500] + "..." if len(version1.content) > 500 else version1.content)
                    st.markdown(rendered_content, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"#### Version {version2.version}")
                st.markdown(f"**Created:** {format_datetime(version2.created_at)}")
                st.markdown(f"**By:** {version2.created_by or 'Unknown'}")
                st.markdown(f"**Current:** {'Yes' if version2.is_current else 'No'}")
                st.markdown("---")
                if version2.content:
                    rendered_content = render_markdown_with_latex(version2.content[:500] + "..." if len(version2.content) > 500 else version2.content)
                    st.markdown(rendered_content, unsafe_allow_html=True)

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return ""

# Protocol editor modal
def render_protocol_editor(protocol_id=None):
    """Render protocol editor in a modal"""
    
    with DatabaseManager() as db:
        protocol = None
        if protocol_id:
            protocol = db.get_protocol(protocol_id)
        
        st.subheader(f"📝 {'Edit Protocol' if protocol else 'Create Protocol'}")
        render_protocol_form(db, protocol)

def handle_protocol_modals():
    """Handle protocol-related modals"""
    
    # Protocol editor modal
    if 'edit_protocol' in st.session_state and st.session_state.edit_protocol:
        with st.modal("📝 Protocol Editor"):
            render_protocol_editor(st.session_state.edit_protocol)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", type="primary"):
                    del st.session_state.edit_protocol
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.edit_protocol
                    st.rerun()
    
    # Protocol view modal
    if 'view_protocol' in st.session_state and st.session_state.view_protocol:
        with st.modal("📋 View Protocol"):
            render_protocol_view(st.session_state.view_protocol)
            
            if st.button("❌ Close"):
                del st.session_state.view_protocol
                st.rerun()
    
    # Protocol history modal
    if 'protocol_history' in st.session_state and st.session_state.protocol_history:
        with st.modal("📜 Protocol History"):
            with DatabaseManager() as db:
                protocol = db.get_protocol(st.session_state.protocol_history)
                if protocol:
                    st.markdown(f"### Version History: {protocol.name}")
                    
                    # Get all versions
                    all_protocols = db.get_protocols()
                    versions = [p for p in all_protocols if p.name == protocol.name]
                    versions.sort(key=lambda x: x.version, reverse=True)
                    
                    for version in versions:
                        status_icon = "✅" if version.is_current else "📜"
                        
                        with st.expander(f"{status_icon} Version {version.version}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Created:** {format_datetime(version.created_at)}")
                                st.markdown(f"**By:** {version.created_by or 'Unknown'}")
                                if version.description:
                                    st.markdown(f"**Description:** {version.description}")
                            
                            with col2:
                                if st.button("👁️ View", key=f"hist_view_{version.id}"):
                                    st.session_state.view_protocol = version.id
                                    del st.session_state.protocol_history
                                    st.rerun()
                                
                                if not version.is_current:
                                    if st.button("🔄 Restore", key=f"hist_restore_{version.id}"):
                                        # Restore this version
                                        for v in versions:
                                            v.is_current = False
                                        version.is_current = True
                                        db.session.commit()
                                        display_success(f"Version {version.version} restored!")
                                        st.rerun()
            
            if st.button("❌ Close"):
                del st.session_state.protocol_history
                st.rerun()
