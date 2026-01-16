from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    experiments = relationship("Experiment", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"

class Experiment(Base):
    __tablename__ = 'experiments'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='Draft')  # Draft, Final, Archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    experiment_date = Column(DateTime)
    tags = Column(String(500))  # Comma-separated tags
    wavelength_range = Column(String(100))  # e.g., "760-820 nm"
    pulse_energy = Column(Float)
    pulse_energy_unit = Column(String(20), default='mJ')
    repetition_rate = Column(Float)  # Hz or kHz
    vacuum_level = Column(Float)  # mbar
    sample_temperature = Column(Float)  # Kelvin
    instrument_config = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="experiments")
    entries = relationship("Entry", back_populates="experiment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Experiment(id={self.id}, title='{self.title}', status='{self.status}')>"

class Entry(Base):
    __tablename__ = 'entries'
    
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text)  # Markdown content
    content_type = Column(String(20), default='markdown')  # markdown, plain
    entry_format = Column(String(50), default='standard')  # standard, felix
    felix_payload = Column(Text)  # JSON blob for FELIX-format entries
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Security and compliance
    is_locked = Column(Boolean, default=False)
    digital_signature = Column(String(200))  # User signature confirmation
    locked_at = Column(DateTime)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="entries")
    attachments = relationship("Attachment", back_populates="entry", cascade="all, delete-orphan")
    linked_materials = relationship("LinkedMaterial", back_populates="entry", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="entry", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Entry(id={self.id}, title='{self.title}', locked={self.is_locked})>"

class Attachment(Base):
    __tablename__ = 'attachments'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entry = relationship("Entry", back_populates="attachments")
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, filename='{self.filename}')>"

# Inventory System
class Material(Base):
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    material_type = Column(String(100))  # crystal, dye, gas, optic
    vendor = Column(String(200))
    part_number = Column(String(100))
    wavelength_range = Column(String(100))
    damage_threshold = Column(Float)
    unit = Column(String(20))  # mm, %, etc.
    storage_location = Column(String(100))
    handling_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    linked_materials = relationship("LinkedMaterial", back_populates="material")
    
    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.name}')>"

class Target(Base):
    __tablename__ = 'targets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    composition = Column(Text)
    target_type = Column(String(100))  # supersonic jet, molecular beam, thin film
    backing_gas = Column(String(100))
    stagnation_pressure = Column(Float)
    stagnation_pressure_unit = Column(String(20), default='bar')
    temperature = Column(Float)
    temperature_unit = Column(String(10), default='K')
    storage_location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Target(id={self.id}, name='{self.name}')>"

class Instrument(Base):
    __tablename__ = 'instruments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    model = Column(String(100))
    serial_number = Column(String(100))
    location = Column(String(100))
    status = Column(String(20), default='Available')  # Available, In Use, Maintenance
    last_maintenance = Column(DateTime)
    beamline_position = Column(String(100))
    control_software = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Instrument(id={self.id}, name='{self.name}', status='{self.status}')>"

class LinkedMaterial(Base):
    __tablename__ = 'linked_materials'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    usage_context = Column(Text)  # e.g., "Nonlinear crystal in OPO"
    quantity_used = Column(Float)
    unit = Column(String(20))
    notes = Column(Text)
    linked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entry = relationship("Entry", back_populates="linked_materials")
    material = relationship("Material", back_populates="linked_materials")
    
    def __repr__(self):
        return f"<LinkedMaterial(entry_id={self.entry_id}, material_id={self.material_id})>"


class Protocol(Base):
    __tablename__ = 'protocols'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    content = Column(Text)  # Markdown content
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(200))
    
    # Relationships
    parent_protocol_id = Column(Integer, ForeignKey('protocols.id'))
    child_protocols = relationship("Protocol", remote_side=[id])
    
    def __repr__(self):
        return f"<Protocol(id={self.id}, name='{self.name}', version={self.version})>"

# Audit Trail
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id'), nullable=False)
    action = Column(String(50), nullable=False)  # created, updated, locked, unlocked
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(200))  # Simple user identification
    details = Column(Text)  # Additional details about the action
    
    # Relationships
    entry = relationship("Entry", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(entry_id={self.entry_id}, action='{self.action}', timestamp='{self.timestamp}')>"

# Database setup
DATABASE_URL = "sqlite:///eln_database.db"

def get_engine():
    return create_engine(DATABASE_URL)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_database():
    """Create all database tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

if __name__ == "__main__":
    create_database()
    print("Database created successfully!")
