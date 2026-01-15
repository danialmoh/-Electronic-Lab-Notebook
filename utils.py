import streamlit as st
import markdown
import re
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import os

def render_markdown_with_latex(content: str) -> str:
    """Render markdown content with LaTeX support"""
    if not content:
        return ""
    
    # Convert markdown to HTML
    html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # Simple LaTeX to HTML conversion (basic patterns)
    # Inline math: $...$
    html = re.sub(r'\$(.*?)\$', r'<span class="math-inline">\1</span>', html)
    
    # Display math: $$...$$
    html = re.sub(r'\$\$(.*?)\$\$', r'<div class="math-display">\1</div>', html)
    
    return html

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return ""

def format_date(dt: datetime) -> str:
    """Format date for display"""
    if dt:
        return dt.strftime("%Y-%m-%d")
    return ""

def get_status_color(status: str) -> str:
    """Get color for experiment status"""
    colors = {
        'Draft': 'orange',
        'Final': 'green',
        'Archived': 'gray'
    }
    return colors.get(status, 'blue')

def export_to_pdf(content: str, filename: str, title: str = ""):
    """Export content to PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
    if title:
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(10)
    
    # Add content
    pdf.set_font("Arial", size=12)
    # Simple text wrapping for PDF
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            # Handle long lines
            while len(line) > 80:
                pdf.cell(0, 10, line[:80], ln=True)
                line = line[80:]
            pdf.cell(0, 10, line, ln=True)
        else:
            pdf.ln(5)
    
    pdf.output(filename)
    return filename

def export_entries_to_csv(entries):
    """Export entries to CSV format"""
    data = []
    for entry in entries:
        data.append({
            'ID': entry.id,
            'Title': entry.title,
            'Content': entry.content,
            'Experiment ID': entry.experiment_id,
            'Created': format_datetime(entry.created_at),
            'Updated': format_datetime(entry.updated_at),
            'Locked': entry.is_locked,
            'Digital Signature': entry.digital_signature
        })
    
    df = pd.DataFrame(data)
    return df

def save_uploaded_file(uploaded_file, upload_folder='uploads'):
    """Save uploaded file to the upload folder"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(upload_folder, filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path, filename

def get_file_size_mb(file_path):
    """Get file size in MB"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    return 0

def validate_digital_signature(signature: str) -> bool:
    """Simple validation for digital signature"""
    return len(signature.strip()) >= 3

def parse_tags(tags_string: str) -> list:
    """Parse comma-separated tags into list"""
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(',') if tag.strip()]

def format_tags(tags_list: list) -> str:
    """Format list of tags into comma-separated string"""
    return ', '.join(tags_list) if tags_list else ""

def search_highlight(text: str, query: str) -> str:
    """Highlight search query in text"""
    if not query:
        return text
    
    # Simple highlighting using markdown
    highlighted = text.replace(query, f"**{query}**")
    return highlighted

def get_experiment_statistics():
    """Get statistics for dashboard"""
    from database import get_db_manager
    
    with get_db_manager() as db:
        projects_count = len(db.get_projects())
        experiments_count = len(db.get_experiments())
        entries_count = len(db.get_entries())
        materials_count = len(db.get_materials())
        targets_count = len(db.get_targets())
        instruments_count = len(db.get_instruments())
        protocols_count = len(db.get_current_protocols())
        
        # Recent activity
        recent_experiments = db.get_experiments()[:5]
        recent_entries = db.get_entries()[:5]
        
        return {
            'projects_count': projects_count,
            'experiments_count': experiments_count,
            'entries_count': entries_count,
            'materials_count': materials_count,
            'targets_count': targets_count,
            'instruments_count': instruments_count,
            'protocols_count': protocols_count,
            'recent_experiments': recent_experiments,
            'recent_entries': recent_entries
        }

def display_success(message: str):
    """Display success message"""
    st.success(message)

def display_error(message: str):
    """Display error message"""
    st.error(message)

def display_warning(message: str):
    """Display warning message"""
    st.warning(message)

def display_info(message: str):
    """Display info message"""
    st.info(message)
