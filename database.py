from sqlalchemy.orm import Session
from models import get_session, Project, Experiment, Entry, Reagent, Sample, Equipment, Protocol, LinkedReagent, Attachment, AuditLog
from datetime import datetime
from typing import List, Optional

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
    def create_experiment(self, project_id: int, title: str, description: str = None, 
                         status: str = 'Draft', experiment_date: datetime = None, tags: str = None) -> Experiment:
        experiment = Experiment(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            experiment_date=experiment_date or datetime.utcnow(),
            tags=tags
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
    def create_entry(self, experiment_id: int, title: str, content: str = None, 
                    content_type: str = 'markdown') -> Entry:
        entry = Entry(
            experiment_id=experiment_id,
            title=title,
            content=content,
            content_type=content_type
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
            for key, value in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
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
    def create_reagent(self, name: str, **kwargs) -> Reagent:
        reagent = Reagent(name=name, **kwargs)
        self.session.add(reagent)
        self.session.commit()
        return reagent
    
    def get_reagents(self) -> List[Reagent]:
        return self.session.query(Reagent).order_by(Reagent.name).all()
    
    def get_reagent(self, reagent_id: int) -> Optional[Reagent]:
        return self.session.query(Reagent).filter(Reagent.id == reagent_id).first()
    
    def update_reagent(self, reagent_id: int, **kwargs) -> Optional[Reagent]:
        reagent = self.get_reagent(reagent_id)
        if reagent:
            for key, value in kwargs.items():
                if hasattr(reagent, key):
                    setattr(reagent, key, value)
            reagent.updated_at = datetime.utcnow()
            self.session.commit()
        return reagent
    
    def delete_reagent(self, reagent_id: int) -> bool:
        reagent = self.get_reagent(reagent_id)
        if reagent:
            self.session.delete(reagent)
            self.session.commit()
            return True
        return False
    
    def create_sample(self, name: str, **kwargs) -> Sample:
        sample = Sample(name=name, **kwargs)
        self.session.add(sample)
        self.session.commit()
        return sample
    
    def get_samples(self) -> List[Sample]:
        return self.session.query(Sample).order_by(Sample.name).all()
    
    def create_equipment(self, name: str, **kwargs) -> Equipment:
        equipment = Equipment(name=name, **kwargs)
        self.session.add(equipment)
        self.session.commit()
        return equipment
    
    def get_equipment(self) -> List[Equipment]:
        return self.session.query(Equipment).order_by(Equipment.name).all()
    
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
    
    # Linked reagents operations
    def link_reagent_to_entry(self, entry_id: int, reagent_id: int, quantity_used: float = None, 
                             unit: str = None, notes: str = None) -> LinkedReagent:
        linked_reagent = LinkedReagent(
            entry_id=entry_id,
            reagent_id=reagent_id,
            quantity_used=quantity_used,
            unit=unit,
            notes=notes
        )
        self.session.add(linked_reagent)
        self.session.commit()
        return linked_reagent
    
    def get_linked_reagents(self, entry_id: int) -> List[LinkedReagent]:
        return self.session.query(LinkedReagent).filter(LinkedReagent.entry_id == entry_id).all()
    
    def remove_linked_reagent(self, linked_reagent_id: int) -> bool:
        linked_reagent = self.session.query(LinkedReagent).filter(LinkedReagent.id == linked_reagent_id).first()
        if linked_reagent:
            self.session.delete(linked_reagent)
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
