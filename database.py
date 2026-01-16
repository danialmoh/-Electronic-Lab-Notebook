from sqlalchemy.orm import Session
from models import (
    get_session,
    Project,
    Experiment,
    Entry,
    Material,
    Target,
    Instrument,
    Protocol,
    LinkedMaterial,
    Attachment,
    AuditLog,
)
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

class DatabaseManager:
    """Centralized database operations for the ELN"""
    
    def __init__(self):
        self.session = get_session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    # Project operations
    def create_project(self, name: str, description: str = None) -> Project:
        project = Project(name=name, description=description)
        self.session.add(project)
        self.session.commit()
        return project
    
    def get_projects(self) -> List[Project]:
        return self.session.query(Project).order_by(Project.updated_at.desc()).all()
    
    def get_project(self, project_id: int) -> Optional[Project]:
        return self.session.query(Project).filter(Project.id == project_id).first()
    
    def update_project(self, project_id: int, name: str = None, description: str = None) -> Optional[Project]:
        project = self.get_project(project_id)
        if project:
            if name:
                project.name = name
            if description is not None:
                project.description = description
            project.updated_at = datetime.utcnow()
            self.session.commit()
        return project
    
    def delete_project(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        if project:
            self.session.delete(project)
            self.session.commit()
            return True
        return False
    
    # Experiment operations
    def create_experiment(
        self,
        project_id: int,
        title: str,
        description: str = None,
        status: str = 'Draft',
        experiment_date: datetime = None,
        tags: str = None,
        wavelength_range: str = None,
        pulse_energy: float = None,
        pulse_energy_unit: str = None,
        repetition_rate: float = None,
        vacuum_level: float = None,
        sample_temperature: float = None,
        instrument_config: str = None,
    ) -> Experiment:
        experiment = Experiment(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            experiment_date=experiment_date or datetime.utcnow(),
            tags=tags,
            wavelength_range=wavelength_range,
            pulse_energy=pulse_energy,
            pulse_energy_unit=pulse_energy_unit,
            repetition_rate=repetition_rate,
            vacuum_level=vacuum_level,
            sample_temperature=sample_temperature,
            instrument_config=instrument_config,
        )
        self.session.add(experiment)
        self.session.commit()
        return experiment
    
    def get_experiments(self, project_id: int = None) -> List[Experiment]:
        query = self.session.query(Experiment)
        if project_id:
            query = query.filter(Experiment.project_id == project_id)
        return query.order_by(Experiment.updated_at.desc()).all()
    
    def get_experiment(self, experiment_id: int) -> Optional[Experiment]:
        return self.session.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    def update_experiment(self, experiment_id: int, **kwargs) -> Optional[Experiment]:
        experiment = self.get_experiment(experiment_id)
        if experiment:
            for key, value in kwargs.items():
                if hasattr(experiment, key):
                    setattr(experiment, key, value)
            experiment.updated_at = datetime.utcnow()
            self.session.commit()
        return experiment
    
    def delete_experiment(self, experiment_id: int) -> bool:
        experiment = self.get_experiment(experiment_id)
        if experiment:
            self.session.delete(experiment)
            self.session.commit()
            return True
        return False
    
    # Entry operations
    def create_entry(
        self,
        experiment_id: int,
        title: str,
        content: str = None,
        content_type: str = 'markdown',
        entry_format: str = 'standard',
        felix_payload: Optional[Dict[str, Any]] = None,
    ) -> Entry:
        entry = Entry(
            experiment_id=experiment_id,
            title=title,
            content=content,
            content_type=content_type,
            entry_format=entry_format or 'standard',
            felix_payload=json.dumps(felix_payload, ensure_ascii=False) if felix_payload else None,
        )
        self.session.add(entry)
        self.session.commit()
        
        # Create audit log
        self._create_audit_log(entry.id, 'created', 'System', 'Entry created')
        
        return entry
    
    def get_entries(self, experiment_id: int = None) -> List[Entry]:
        query = self.session.query(Entry)
        if experiment_id:
            query = query.filter(Entry.experiment_id == experiment_id)
        return query.order_by(Entry.updated_at.desc()).all()
    
    def get_entry(self, entry_id: int) -> Optional[Entry]:
        return self.session.query(Entry).filter(Entry.id == entry_id).first()
    
    def update_entry(self, entry_id: int, **kwargs) -> Optional[Entry]:
        entry = self.get_entry(entry_id)
        if entry and not entry.is_locked:
            felix_payload = kwargs.pop('felix_payload', None) if 'felix_payload' in kwargs else None
            for key, value in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            if felix_payload is not None:
                entry.felix_payload = json.dumps(felix_payload, ensure_ascii=False) if felix_payload else None
            entry.updated_at = datetime.utcnow()
            self.session.commit()
            
            # Create audit log
            self._create_audit_log(entry.id, 'updated', 'System', 'Entry updated')
            
        return entry
    
    def lock_entry(self, entry_id: int, digital_signature: str) -> bool:
        entry = self.get_entry(entry_id)
        if entry and not entry.is_locked:
            entry.is_locked = True
            entry.digital_signature = digital_signature
            entry.locked_at = datetime.utcnow()
            self.session.commit()
            
            # Create audit log
            self._create_audit_log(entry.id, 'locked', digital_signature, 'Entry locked with digital signature')
            
            return True
        return False
    
    def unlock_entry(self, entry_id: int, digital_signature: str) -> bool:
        entry = self.get_entry(entry_id)
        if entry and entry.is_locked and entry.digital_signature == digital_signature:
            entry.is_locked = False
            entry.digital_signature = None
            entry.locked_at = None
            self.session.commit()
            
            # Create audit log
            self._create_audit_log(entry.id, 'unlocked', digital_signature, 'Entry unlocked')
            
            return True
        return False
    
    # Inventory operations
    def create_material(self, name: str, **kwargs) -> Material:
        material = Material(name=name, **kwargs)
        self.session.add(material)
        self.session.commit()
        return material
    
    def get_materials(self) -> List[Material]:
        return self.session.query(Material).order_by(Material.name).all()
    
    def get_material(self, material_id: int) -> Optional[Material]:
        return self.session.query(Material).filter(Material.id == material_id).first()
    
    def update_material(self, material_id: int, **kwargs) -> Optional[Material]:
        material = self.get_material(material_id)
        if material:
            for key, value in kwargs.items():
                if hasattr(material, key):
                    setattr(material, key, value)
            material.updated_at = datetime.utcnow()
            self.session.commit()
        return material
    
    def delete_material(self, material_id: int) -> bool:
        material = self.get_material(material_id)
        if material:
            self.session.delete(material)
            self.session.commit()
            return True
        return False
    
    def create_target(self, name: str, **kwargs) -> Target:
        target = Target(name=name, **kwargs)
        self.session.add(target)
        self.session.commit()
        return target
    
    def get_targets(self) -> List[Target]:
        return self.session.query(Target).order_by(Target.name).all()
    
    def create_instrument(self, name: str, **kwargs) -> Instrument:
        instrument = Instrument(name=name, **kwargs)
        self.session.add(instrument)
        self.session.commit()
        return instrument
    
    def get_instruments(self) -> List[Instrument]:
        return self.session.query(Instrument).order_by(Instrument.name).all()
    
    # Protocol operations
    def create_protocol(self, name: str, content: str, description: str = None, 
                       created_by: str = None) -> Protocol:
        protocol = Protocol(
            name=name,
            content=content,
            description=description,
            created_by=created_by
        )
        self.session.add(protocol)
        self.session.commit()
        return protocol
    
    def get_protocols(self) -> List[Protocol]:
        return self.session.query(Protocol).order_by(Protocol.name, Protocol.version.desc()).all()
    
    def get_current_protocols(self) -> List[Protocol]:
        return self.session.query(Protocol).filter(Protocol.is_current == True).order_by(Protocol.name).all()
    
    def create_protocol_version(self, parent_id: int, content: str, created_by: str = None) -> Protocol:
        parent = self.session.query(Protocol).filter(Protocol.id == parent_id).first()
        if parent:
            # Mark old version as not current
            parent.is_current = False
            
            # Create new version
            new_version = Protocol(
                name=parent.name,
                description=parent.description,
                content=content,
                version=parent.version + 1,
                is_current=True,
                created_by=created_by,
                parent_protocol_id=parent_id
            )
            self.session.add(new_version)
            self.session.commit()
            return new_version
        return None
    
    # Linked materials operations
    def link_material_to_entry(self, entry_id: int, material_id: int, quantity_used: float = None, 
                              unit: str = None, usage_context: str = None, notes: str = None) -> LinkedMaterial:
        linked_material = LinkedMaterial(
            entry_id=entry_id,
            material_id=material_id,
            quantity_used=quantity_used,
            unit=unit,
            usage_context=usage_context,
            notes=notes
        )
        self.session.add(linked_material)
        self.session.commit()
        return linked_material
    
    def get_linked_materials(self, entry_id: int) -> List[LinkedMaterial]:
        return self.session.query(LinkedMaterial).filter(LinkedMaterial.entry_id == entry_id).all()
    
    def remove_linked_material(self, linked_material_id: int) -> bool:
        linked_material = self.session.query(LinkedMaterial).filter(LinkedMaterial.id == linked_material_id).first()
        if linked_material:
            self.session.delete(linked_material)
            self.session.commit()
            return True
        return False

    # Audit log operations
    def _create_audit_log(self, entry_id: int, action: str, user_id: str, details: str = None):
        audit_log = AuditLog(
            entry_id=entry_id,
            action=action,
            user_id=user_id,
            details=details
        )
        self.session.add(audit_log)
        self.session.commit()
    
    def get_audit_logs(self, entry_id: int) -> List[AuditLog]:
        return self.session.query(AuditLog).filter(AuditLog.entry_id == entry_id).order_by(AuditLog.timestamp.desc()).all()
    
    # Search functionality
    def search_entries(self, query: str) -> List[Entry]:
        return self.session.query(Entry).filter(
            Entry.title.contains(query) | Entry.content.contains(query)
        ).order_by(Entry.updated_at.desc()).all()
    
    def search_experiments(self, query: str) -> List[Experiment]:
        return self.session.query(Experiment).filter(
            Experiment.title.contains(query) | 
            Experiment.description.contains(query) |
            Experiment.tags.contains(query)
        ).order_by(Experiment.updated_at.desc()).all()
    
    def search_projects(self, query: str) -> List[Project]:
        return self.session.query(Project).filter(
            Project.name.contains(query) | Project.description.contains(query)
        ).order_by(Project.updated_at.desc()).all()

# Convenience functions
def get_db_manager():
    return DatabaseManager()
