# Conda Installation Guide for Electronic Lab Notebook

## Quick Setup with Conda

### Step 1: Create Conda Environment

```bash
# Navigate to the project directory
cd /Users/danialmoh/CascadeProjects/windsurf-project-2

# Create the conda environment from the environment.yml file
conda env create -f environment.yml
```

### Step 2: Activate the Environment

```bash
conda activate eln
```

### Step 3: Initialize the Database

```bash
python init_database.py
```

When prompted, type `y` to create sample data (recommended for first-time setup).

### Step 4: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Alternative: Manual Conda Setup

If you prefer to install packages manually:

```bash
# Create a new conda environment
conda create -n eln python=3.10

# Activate the environment
conda activate eln

# Install dependencies using pip
pip install -r requirements.txt

# Initialize database
python init_database.py

# Run the app
streamlit run app.py
```

## Managing the Environment

### Activate the environment
```bash
conda activate eln
```

### Deactivate the environment
```bash
conda deactivate
```

### Update dependencies
```bash
conda activate eln
pip install -r requirements.txt --upgrade
```

### Remove the environment (if needed)
```bash
conda deactivate
conda env remove -n eln
```

## Verifying Installation

After activating the environment, verify the installation:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Verify Streamlit
streamlit --version
```

## Troubleshooting

### Issue: "conda: command not found"
- Make sure Conda is installed and added to your PATH
- Try using the full path to conda, e.g., `~/anaconda3/bin/conda`

### Issue: Package conflicts
- Try creating a fresh environment:
  ```bash
  conda deactivate
  conda env remove -n eln
  conda env create -f environment.yml
  ```

### Issue: Database errors
- Delete the database file and reinitialize:
  ```bash
  rm eln_database.db
  python init_database.py
  ```

### Issue: Port already in use
- Streamlit will automatically find an available port
- Or specify a custom port:
  ```bash
  streamlit run app.py --server.port 8502
  ```

## Next Steps

Once the application is running:

1. **Explore the Dashboard** - View statistics and recent activity
2. **Create a Project** - Start organizing your research
3. **Add Experiments** - Create experiments within projects
4. **Write Entries** - Use the advanced editor with Markdown/LaTeX
5. **Manage Inventory** - Add materials, targets, and instruments
6. **Create Protocols** - Document your SOPs with versioning

## Environment Details

The Conda environment includes:
- **Python 3.10** - Base interpreter
- **Streamlit 1.29.0** - Web framework
- **SQLAlchemy 2.0.23** - Database ORM
- **Pandas 2.1.4** - Data manipulation
- **FPDF2 2.7.6** - PDF generation
- **Markdown 3.5.1** - Markdown processing
- **Python-Markdown-Math 0.8.0** - LaTeX support
- **Pillow 10.1.0** - Image processing
- **Python-Dateutil 2.8.2** - Date utilities

## Support

For issues or questions:
1. Check the main README.md file
2. Review the PROJECT_SUMMARY.md for feature details
3. Examine the sample data created during initialization
