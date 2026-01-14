# Electronic Lab Notebook (ELN)

A professional-grade Electronic Lab Notebook built with Streamlit and SQLAlchemy.

## Features

### Core Functionality
- **Hierarchical Data Structure**: Projects > Experiments > Entries
- **Advanced Entry Editor**: Markdown support with LaTeX rendering
- **Relational Inventory System**: Track reagents, samples, and equipment with linking
- **Protocol Versioning**: SOP management with version control
- **Security & Compliance**: Digital signatures and audit trails
- **Search & Export**: Full-text search and PDF/CSV export

### Database Schema
- **Projects**: Top-level organization
- **Experiments**: Individual experiments with metadata (status, tags, dates)
- **Entries**: Detailed experiment notes with Markdown/LaTeX support
- **Inventory**: Reagents, samples, and equipment tracking
- **Protocols**: Version-controlled standard operating procedures
- **Audit Trail**: Complete log of all changes and signatures

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Or if using Python 3:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python3 init_database.py
   ```
   This will create the SQLite database and optionally add sample data.

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
eln/
├── app.py              # Main Streamlit application
├── models.py           # SQLAlchemy database models
├── database.py         # Database operations and management
├── utils.py            # Utility functions and helpers
├── init_database.py    # Database initialization script
├── requirements.txt    # Python dependencies
├── uploads/            # File upload directory
├── eln_database.db     # SQLite database (created after init)
└── README.md           # This file
```

## Usage Guide

### Dashboard
- Overview of all projects, experiments, and inventory
- Recent activity and statistics
- Quick access to all sections

### Projects
- Create and manage research projects
- View all experiments within a project
- Project-level metadata and organization

### Experiments
- Create experiments with rich metadata
- Status tracking (Draft, Final, Archived)
- Tag-based organization
- Date and timestamp management

### Entries
- **Rich Text Editor**: Markdown with LaTeX support
- **Preview Mode**: Rendered view of content
- **File Attachments**: Upload images and documents
- **Reagent Linking**: Connect inventory items to experiments
- **Digital Signatures**: Lock entries with confirmation
- **Audit Trail**: Complete change history

### Inventory
- **Reagents**: Chemical inventory with supplier info
- **Samples**: Sample tracking and storage
- **Equipment**: Equipment status and maintenance logs
- **Smart Linking**: Dropdown selection in experiment entries

### Protocols
- **Version Control**: Automatic versioning on updates
- **Archive Access**: View all historical versions
- **Rich Content**: Markdown with LaTeX support
- **Search**: Find protocols by content or title

### Security Features
- **Digital Signatures**: Checkbox confirmation to lock entries
- **Audit Logging**: Automatic tracking of all changes
- **Entry Locking**: Prevent further edits after signing
- **User Attribution**: Track who made changes

## Technical Details

### Database
- **Engine**: SQLite with SQLAlchemy ORM
- **Models**: Relational schema with proper foreign keys
- **Migrations**: Manual schema updates via init script

### Frontend
- **Framework**: Streamlit 1.29+
- **UI Components**: Built-in Streamlit widgets
- **Markdown**: Python-Markdown with math extensions
- **File Handling**: Upload and attachment management

### Export Features
- **PDF**: FPDF-based document generation
- **CSV**: Pandas DataFrame export
- **Markdown**: Native format preservation

## Dependencies

- `streamlit==1.29.0` - Web application framework
- `sqlalchemy==2.0.23` - Database ORM
- `pandas==2.1.4` - Data manipulation and export
- `fpdf2==2.7.6` - PDF generation
- `markdown==3.5.1` - Markdown processing
- `python-markdown-math==0.8.0` - LaTeX math support
- `pillow==10.1.0` - Image processing
- `python-dateutil==2.8.2` - Date utilities

## Development

### Adding New Features
1. Update `models.py` for database changes
2. Add operations to `database.py`
3. Create UI components in `app.py`
4. Add utilities to `utils.py`

### Database Schema Changes
1. Update models in `models.py`
2. Create migration script or update `init_database.py`
3. Test with fresh database

### Styling
- Uses Streamlit's built-in theming
- Custom CSS can be added via Streamlit's markdown injection

## Troubleshooting

### Common Issues

**Database not found**: Run `python3 init_database.py` first

**Dependencies missing**: Install with `pip install -r requirements.txt`

**File uploads not working**: Ensure `uploads/` directory exists and is writable

**LaTeX not rendering**: Check `python-markdown-math` is installed

**Port already in use**: Streamlit will automatically find an available port

### Performance Tips
- Use SQLite for small to medium labs
- Consider PostgreSQL for large-scale deployments
- Regular database maintenance via SQLite tools

## License

This project is provided as-is for educational and research use.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Test with sample data first
