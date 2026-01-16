import streamlit as st
import os
import json
from datetime import datetime, date
from database import DatabaseManager
from models import Attachment
from utils import (
    render_markdown_with_latex,
    save_uploaded_file,
    display_success,
    display_error,
    display_warning,
)

FELIX_FORMAT_KEY = "felix"
FORMAT_LABELS = {
    "standard": "Standard (Markdown)",
    FELIX_FORMAT_KEY: "FELIX IR-UV Logbook",
}


def load_felix_payload(entry):
    if entry and entry.felix_payload:
        try:
            return json.loads(entry.felix_payload)
        except json.JSONDecodeError:
            return {}
    return {}


def parse_saved_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def multiline_to_list(text_value: str):
    if not text_value:
        return []
    return [line.strip() for line in text_value.splitlines() if line.strip()]


def default_felix_payload():
    return {
        "run_date": None,
        "start_time": "",
        "end_time": "",
        "operators": [],
        "beamtime_campaign": "",
        "instrument_location": "",
        "goal_text": "",
        "experiment_type": "",
        "precursor_molecules": [],
        "discharge_enabled": False,
        "discharge_voltage": None,
        "discharge_current": None,
        "discharge_timing_offset": None,
        "expected_products": "",
        "target_mass_channels": [],
        "carrier_gas": "",
        "backing_pressure": None,
        "backing_pressure_unit": "bar",
        "valve_type": "",
        "valve_timing": "",
        "skimmer_in_place": False,
        "ir_source": "FELIX",
        "wavelength_start": None,
        "wavelength_end": None,
        "step_size": None,
        "pulse_energy": None,
        "pulse_energy_unit": "mJ",
        "repetition_rate": None,
        "uv_wavelength": None,
        "uv_pulse_energy": None,
        "ionization_scheme": "",
        "alignment_status": "Good",
        "signal_stability": "Stable",
        "background_level": "Low",
        "actions": [],
        "observations": {
            "ir_depletion_observed": False,
            "depletion_positions": [],
            "signal_trend": "",
            "noise_level": "",
            "unexpected_tags": [],
            "notes": "",
        },
        "interpretation_notes": "",
        "reference_comparison": "",
        "confidence_level": "Medium",
        "data_folder_path": "",
        "mass_spectra_files": [],
        "ir_depletion_files": [],
        "data_quality_notes": "",
        "goal_outcome": "Partial",
        "key_result": "",
        "main_limitation": "",
        "next_steps": [],
        "flags": {
            "reproducible_run": False,
            "calibration_valid": True,
            "alignment_issues": False,
            "data_questionable": False,
        },
        "summary_notes": "",
    }


def hydrate_felix_payload(entry):
    data = default_felix_payload()
    saved = load_felix_payload(entry)
    if saved:
        for key, value in saved.items():
            if key in ["observations", "flags"] and isinstance(value, dict):
                data[key].update(value)
            else:
                data[key] = value
    return data


def csv_to_list(value: str):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def list_to_csv(items):
    return ", ".join(items) if items else ""


def ensure_table_records(value, columns):
    rows = []
    if value is None:
        return rows
    if hasattr(value, "to_dict"):
        try:
            rows = value.to_dict("records")
        except Exception:
            rows = []
    elif isinstance(value, list):
        rows = value
    cleaned = []
    for row in rows:
        record = {}
        for col in columns:
            record[col] = (row.get(col) if isinstance(row, dict) else "") or ""
        if any(str(record[col]).strip() for col in columns):
            cleaned.append(record)
    return cleaned


ACTION_COLUMNS = ["timestamp", "parameter", "old_value", "new_value", "reason"]


def clean_editor_rows(rows, columns):
    if rows is None:
        return []
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    cleaned = []
    for row in rows:
        record = {}
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, str):
                value = value.strip()
            record[col] = value
        if any(str(record[col]).strip() for col in columns):
            cleaned.append(record)
    return cleaned


def parse_float_or_none(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def list_to_multiline(items):
    return "\n".join(items) if items else ""


def format_list(items, default="—"):
    if not items:
        return default
    if isinstance(items, str):
        return items
    return ", ".join(items)


def safe_option_index(options, value, fallback=0):
    """Return a valid index for Streamlit selectboxes without raising."""
    if value in options:
        return options.index(value)
    return fallback


FELIX_EXPERIMENT_TYPES = [
    "Alignment",
    "IR scan",
    "Wavelength optimization",
    "Discharge comparison",
    "Reference measurement",
    "Troubleshooting",
]

RUN_STATUS_OPTIONS = ["Good", "Acceptable", "Poor"]
STABILITY_OPTIONS = ["Stable", "Fluctuating", "Low"]
BACKGROUND_OPTIONS = ["Low", "Medium", "High"]
CONFIDENCE_OPTIONS = ["Low", "Medium", "High"]
GOAL_OUTCOMES = ["Yes", "Partially", "No"]
OBSERVATION_TAGS = ["No signal", "Strong depletion", "Beam unstable", "Saturation", "Drifting baseline"]


def render_entry_editor(entry_id=None, experiment_id=None, form_key="entry_form"):
    """Render the advanced entry editor with Markdown/LaTeX support and material linking"""
    
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
        
        format_keys = list(FORMAT_LABELS.keys())
        if entry and entry.entry_format in format_keys:
            default_format = entry.entry_format
        else:
            default_format = st.session_state.get('new_entry_format', 'standard')
        default_index = format_keys.index(default_format) if default_format in format_keys else 0
        
        selected_format = st.selectbox(
            "Entry Format",
            format_keys,
            index=default_index,
            format_func=lambda key: FORMAT_LABELS.get(key, key.title()),
            key=f"{form_key}_format_select"
        )
        
        if not entry:
            st.session_state['new_entry_format'] = selected_format
        
        # Editor tabs
        editor_tab, preview_tab, attachments_tab, materials_tab = st.tabs(
            ["✏️ Edit", "👁️ Preview", "📎 Attachments", "🧱 Linked Materials"]
        )
        
        with editor_tab:
            if selected_format == FELIX_FORMAT_KEY:
                render_felix_editor(entry, experiment, db, form_key=form_key)
            else:
                render_standard_editor(entry, experiment, db, form_key=form_key, entry_format=selected_format)
        
        with preview_tab:
            render_preview(entry, db)
        
        with attachments_tab:
            render_attachments(entry, db)
        
        with materials_tab:
            render_linked_materials(entry, experiment, db)

def render_standard_editor(entry, experiment, db, form_key, entry_format="standard"):
    """Render the classic Markdown/LaTeX editor"""
    
    form_id = f"{form_key}_standard_form"
    with st.form(form_id):
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
        
        content_type_options = ["markdown", "plain"]
        if entry and entry.content_type in content_type_options:
            default_index = content_type_options.index(entry.content_type)
        else:
            default_index = 0
        content_type = st.selectbox(
            "Content Type",
            content_type_options,
            index=default_index
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Entry", type="primary"):
                if title.strip():
                    if entry:
                        updated_entry = db.update_entry(
                            entry.id,
                            title=title,
                            content=content,
                            content_type=content_type,
                            entry_format=entry_format,
                            felix_payload=None,
                        )
                        if updated_entry:
                            display_success("Entry updated successfully!")
                            st.rerun()
                        else:
                            display_error("Failed to update entry")
                    else:
                        new_entry = db.create_entry(
                            experiment_id=experiment.id,
                            title=title,
                            content=content,
                            content_type=content_type,
                            entry_format=entry_format,
                            felix_payload=None,
                        )
                        display_success(f"Entry '{new_entry.title}' created successfully!")
                        st.rerun()
                else:
                    display_error("Title is required")


def render_felix_editor(entry, experiment, db, form_key):
    """Render FELIX-specific structured editor"""
    payload = hydrate_felix_payload(entry)
    observations = payload.get("observations", {})
    flags = payload.get("flags", {})
    summary_default = payload.get("summary_notes") or (entry.content if entry else "")
    form_id = f"{form_key}_felix_form"
    
    operators_default = list_to_csv(payload.get("operators"))
    precursors_default = list_to_csv(payload.get("precursor_molecules"))
    mass_channels_default = list_to_csv(payload.get("target_mass_channels"))
    next_steps_default = list_to_multiline(payload.get("next_steps"))
    mass_files_default = list_to_multiline(payload.get("mass_spectra_files"))
    ir_files_default = list_to_multiline(payload.get("ir_depletion_files"))
    
    actions_records = ensure_table_records(payload.get("actions"), ACTION_COLUMNS)
    
    with st.form(form_id):
        title = st.text_input("Entry Title*", value=entry.title if entry else "")
        
        st.markdown("### 1. Metadata")
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            run_date = st.date_input(
                "Run Date",
                value=parse_saved_date(payload.get("run_date")) or date.today()
            )
            start_time = st.text_input("Start Time", value=payload.get("start_time") or "", placeholder="HH:MM")
            operators_input = st.text_input("Operator(s)", value=operators_default, help="Comma-separated list")
            beamtime_campaign = st.text_input("Beamtime / Campaign", value=payload.get("beamtime_campaign") or "")
        with meta_col2:
            instrument_location = st.text_input("Location / Instrument", value=payload.get("instrument_location") or "")
            end_time = st.text_input("End Time", value=payload.get("end_time") or "", placeholder="HH:MM")
            experiment_type = st.selectbox(
                "Experiment Type",
                options=FELIX_EXPERIMENT_TYPES,
                index=safe_option_index(FELIX_EXPERIMENT_TYPES, payload.get("experiment_type"), fallback=0)
            )
        
        st.markdown("### 2. Experiment Goal (Required)")
        goal_text = st.text_input("Goal of This Run*", value=payload.get("goal_text") or "", placeholder="e.g., Identify IR absorption features at m/z 116")
        
        st.markdown("### 3. Species & Target Selection")
        precursors_input = st.text_input("Precursor Molecule(s)", value=precursors_default, help="Comma-separated")
        discharge_enabled = st.checkbox("Discharge Enabled", value=payload.get("discharge_enabled", False))
        discharge_cols = st.columns(3)
        with discharge_cols[0]:
            discharge_voltage = st.text_input("Discharge Voltage (V)", value=str(payload.get("discharge_voltage") or ""))
        with discharge_cols[1]:
            discharge_current = st.text_input("Discharge Current (mA)", value=str(payload.get("discharge_current") or ""))
        with discharge_cols[2]:
            discharge_timing_offset = st.text_input("Timing Offset (µs)", value=str(payload.get("discharge_timing_offset") or ""))
        expected_products = st.text_area("Expected Products", value=payload.get("expected_products") or "", height=80)
        target_mass_channels_input = st.text_input("Target Mass Channels (m/z)", value=mass_channels_default, help="Comma-separated")
        
        st.markdown("### 4. Experimental Conditions")
        st.markdown("#### Molecular Beam")
        beam_cols = st.columns(3)
        with beam_cols[0]:
            carrier_gas = st.text_input("Carrier Gas", value=payload.get("carrier_gas") or "")
            valve_type = st.text_input("Valve Type", value=payload.get("valve_type") or "")
        with beam_cols[1]:
            backing_pressure = st.text_input("Backing Pressure", value=str(payload.get("backing_pressure") or ""))
            valve_timing = st.text_input("Valve Timing", value=payload.get("valve_timing") or "")
        with beam_cols[2]:
            pressure_units = ["bar", "Torr", "mbar"]
            backing_pressure_unit = st.selectbox(
                "Pressure Unit",
                pressure_units,
                index=safe_option_index(pressure_units, payload.get("backing_pressure_unit"), fallback=0)
            )
            skimmer_in_place = st.checkbox("Skimmer In Place", value=payload.get("skimmer_in_place", False))
        
        st.markdown("#### IR / FELIX")
        ir_cols = st.columns(3)
        with ir_cols[0]:
            ir_source = st.text_input("IR Source", value=payload.get("ir_source") or "FELIX")
            wavelength_start = st.text_input("Wavelength Start", value=str(payload.get("wavelength_start") or ""))
            pulse_energy = st.text_input("Pulse Energy", value=str(payload.get("pulse_energy") or ""))
        with ir_cols[1]:
            repetition_rate = st.text_input("Repetition Rate (Hz)", value=str(payload.get("repetition_rate") or ""))
            wavelength_end = st.text_input("Wavelength End", value=str(payload.get("wavelength_end") or ""))
            pulse_units = ["mJ", "µJ", "J"]
            pulse_energy_unit = st.selectbox(
                "Pulse Energy Unit",
                pulse_units,
                index=safe_option_index(pulse_units, payload.get("pulse_energy_unit"), fallback=0)
            )
        with ir_cols[2]:
            step_size = st.text_input("Step Size", value=str(payload.get("step_size") or ""))
        
        st.markdown("#### UV / REMPI")
        uv_cols = st.columns(3)
        with uv_cols[0]:
            uv_wavelength = st.text_input("UV Wavelength (nm)", value=str(payload.get("uv_wavelength") or ""))
        with uv_cols[1]:
            uv_pulse_energy = st.text_input("UV Pulse Energy", value=str(payload.get("uv_pulse_energy") or ""))
        with uv_cols[2]:
            ionization_scheme = st.text_input("Ionization Scheme", value=payload.get("ionization_scheme") or "")
        
        st.markdown("### 5. Run Configuration Snapshot")
        snapshot_cols = st.columns(3)
        with snapshot_cols[0]:
            alignment_status = st.selectbox(
                "Alignment Status",
                RUN_STATUS_OPTIONS,
                index=safe_option_index(RUN_STATUS_OPTIONS, payload.get("alignment_status"), fallback=0)
            )
        with snapshot_cols[1]:
            signal_stability = st.selectbox(
                "Signal Stability",
                STABILITY_OPTIONS,
                index=safe_option_index(STABILITY_OPTIONS, payload.get("signal_stability"), fallback=0)
            )
        with snapshot_cols[2]:
            background_level = st.selectbox(
                "Background Level",
                BACKGROUND_OPTIONS,
                index=safe_option_index(BACKGROUND_OPTIONS, payload.get("background_level"), fallback=0)
            )
        
        st.markdown("### 6. Actions Taken")
        actions_editor = st.data_editor(
            actions_records,
            num_rows="dynamic",
            use_container_width=True,
            key=f"{form_key}_actions_editor"
        )
        
        st.markdown("### 7. Observations (Factual)")
        obs_cols = st.columns(2)
        with obs_cols[0]:
            ir_depletion_observed = st.checkbox("IR Depletion Observed", value=observations.get("ir_depletion_observed", False))
            trend_options = ["Increasing", "Stable", "Decreasing", "None"]
            signal_trend = st.selectbox(
                "Signal Trend",
                trend_options,
                index=safe_option_index(trend_options, observations.get("signal_trend"), fallback=1)
            )
            noise_options = ["Low", "Medium", "High"]
            noise_level = st.selectbox(
                "Noise Level",
                noise_options,
                index=safe_option_index(noise_options, observations.get("noise_level"), fallback=0)
            )
        with obs_cols[1]:
            depletion_positions = st.text_input("Approx. Depletion Positions", value=list_to_csv(observations.get("depletion_positions")))
            unexpected_tags = st.multiselect("Unexpected Behavior Tags", OBSERVATION_TAGS, default=[tag for tag in observations.get("unexpected_tags", []) if tag in OBSERVATION_TAGS])
            observation_notes = st.text_area("Observation Notes", value=observations.get("notes") or "", height=80)
        
        st.markdown("### 8. Interpretation & Hypotheses")
        interpretation_notes = st.text_area("Interpretation Notes", value=payload.get("interpretation_notes") or "", height=100)
        reference_comparison = st.text_area("Comparison to References", value=payload.get("reference_comparison") or "", height=80)
        confidence_level = st.selectbox(
            "Confidence Level",
            CONFIDENCE_OPTIONS,
            index=safe_option_index(CONFIDENCE_OPTIONS, payload.get("confidence_level"), fallback=1)
        )
        
        st.markdown("### 9. Data & Files")
        data_folder_path = st.text_input("Data Folder Path / Run ID", value=payload.get("data_folder_path") or "")
        mass_spectra_files_input = st.text_area("Mass Spectra Files (one per line)", value=mass_files_default, height=80)
        ir_depletion_files_input = st.text_area("IR Depletion Files (one per line)", value=ir_files_default, height=80)
        data_quality_notes = st.text_area("Data Quality Notes", value=payload.get("data_quality_notes") or "", height=80)
        
        st.markdown("### 10. Outcome Summary (Required)")
        goal_outcome = st.selectbox(
            "Goal Achieved?",
            GOAL_OUTCOMES,
            index=safe_option_index(GOAL_OUTCOMES, payload.get("goal_outcome"), fallback=1)
        )
        key_result = st.text_area("Key Result", value=payload.get("key_result") or "", height=60)
        main_limitation = st.text_area("Main Limitation", value=payload.get("main_limitation") or "", height=60)
        
        st.markdown("### 11. Next Steps")
        next_steps_input = st.text_area("Next Steps (one per line)", value=next_steps_default, height=80)
        
        st.markdown("### 12. Flags & Quality Control")
        flag_cols = st.columns(2)
        with flag_cols[0]:
            reproducible_run = st.checkbox("Reproducible Run", value=flags.get("reproducible_run", False))
            calibration_valid = st.checkbox("Calibration Valid", value=flags.get("calibration_valid", True))
        with flag_cols[1]:
            alignment_issues = st.checkbox("Alignment Issues", value=flags.get("alignment_issues", False))
            data_questionable = st.checkbox("Data Questionable", value=flags.get("data_questionable", False))
        
        st.markdown("### Narrative Summary")
        summary_notes = st.text_area("Summary / Narrative", value=summary_default, height=180, help="Free-form summary useful for thesis-ready text")
        
        action_col1, action_col2 = st.columns(2)
        save_clicked = action_col1.form_submit_button("💾 Save FELIX Entry", type="primary")
        lock_clicked = action_col2.form_submit_button("🔒 Save & Lock FELIX Entry")
    
    if save_clicked or lock_clicked:
        if not title.strip():
            display_error("Title is required")
            return
        if not goal_text.strip():
            display_error("Goal is required for FELIX entries")
            return
        
        payload.update({
            "run_date": run_date.isoformat() if run_date else None,
            "start_time": start_time.strip(),
            "end_time": end_time.strip(),
            "operators": csv_to_list(operators_input),
            "beamtime_campaign": beamtime_campaign.strip(),
            "instrument_location": instrument_location.strip(),
            "goal_text": goal_text.strip(),
            "experiment_type": experiment_type,
            "precursor_molecules": csv_to_list(precursors_input),
            "discharge_enabled": discharge_enabled,
            "discharge_voltage": parse_float_or_none(discharge_voltage),
            "discharge_current": parse_float_or_none(discharge_current),
            "discharge_timing_offset": parse_float_or_none(discharge_timing_offset),
            "expected_products": expected_products.strip(),
            "target_mass_channels": csv_to_list(target_mass_channels_input),
            "carrier_gas": carrier_gas.strip(),
            "backing_pressure": parse_float_or_none(backing_pressure),
            "backing_pressure_unit": backing_pressure_unit,
            "valve_type": valve_type.strip(),
            "valve_timing": valve_timing.strip(),
            "skimmer_in_place": skimmer_in_place,
            "ir_source": ir_source.strip(),
            "wavelength_start": parse_float_or_none(wavelength_start),
            "wavelength_end": parse_float_or_none(wavelength_end),
            "step_size": parse_float_or_none(step_size),
            "pulse_energy": parse_float_or_none(pulse_energy),
            "pulse_energy_unit": pulse_energy_unit,
            "repetition_rate": parse_float_or_none(repetition_rate),
            "uv_wavelength": parse_float_or_none(uv_wavelength),
            "uv_pulse_energy": parse_float_or_none(uv_pulse_energy),
            "ionization_scheme": ionization_scheme.strip(),
            "alignment_status": alignment_status,
            "signal_stability": signal_stability,
            "background_level": background_level,
            "actions": clean_editor_rows(actions_editor, ACTION_COLUMNS),
            "observations": {
                "ir_depletion_observed": ir_depletion_observed,
                "depletion_positions": csv_to_list(depletion_positions),
                "signal_trend": signal_trend,
                "noise_level": noise_level,
                "unexpected_tags": unexpected_tags,
                "notes": observation_notes.strip(),
            },
            "interpretation_notes": interpretation_notes.strip(),
            "reference_comparison": reference_comparison.strip(),
            "confidence_level": confidence_level,
            "data_folder_path": data_folder_path.strip(),
            "mass_spectra_files": multiline_to_list(mass_spectra_files_input),
            "ir_depletion_files": multiline_to_list(ir_depletion_files_input),
            "data_quality_notes": data_quality_notes.strip(),
            "goal_outcome": goal_outcome,
            "key_result": key_result.strip(),
            "main_limitation": main_limitation.strip(),
            "next_steps": multiline_to_list(next_steps_input),
            "flags": {
                "reproducible_run": reproducible_run,
                "calibration_valid": calibration_valid,
                "alignment_issues": alignment_issues,
                "data_questionable": data_questionable,
            },
            "summary_notes": summary_notes.strip(),
        })
        
        felix_content = summary_notes.strip()
        if entry:
            updated_entry = db.update_entry(
                entry.id,
                title=title,
                content=felix_content,
                content_type="markdown",
                entry_format=FELIX_FORMAT_KEY,
                felix_payload=payload,
            )
            entry_id = updated_entry.id if updated_entry else None
        else:
            new_entry = db.create_entry(
                experiment_id=experiment.id,
                title=title,
                content=felix_content,
                content_type="markdown",
                entry_format=FELIX_FORMAT_KEY,
                felix_payload=payload,
            )
            entry_id = new_entry.id
        
        if entry_id:
            if lock_clicked:
                st.session_state.lock_entry = entry_id
                display_success("Entry saved. Complete locking in the Lock Entry dialog.")
            else:
                display_success("FELIX entry saved successfully!")
            st.rerun()
        else:
            display_error("Failed to save FELIX entry")
        
        with col2:
            if st.form_submit_button("🔒 Save & Lock"):
                if title.strip():
                    if entry:
                        updated_entry = db.update_entry(
                            entry.id,
                            title=title,
                            content=content,
                            content_type=content_type,
                            entry_format=entry_format,
                            felix_payload=None,
                        )
                        entry_id = updated_entry.id if updated_entry else None
                    else:
                        new_entry = db.create_entry(
                            experiment_id=experiment.id,
                            title=title,
                            content=content,
                            content_type=content_type,
                            entry_format=entry_format,
                            felix_payload=None,
                        )
                        entry_id = new_entry.id
                    
                    if entry_id:
                        st.session_state.lock_entry = entry_id
                        st.rerun()
                else:
                    display_error("Title is required")

def render_preview(entry, db):
    """Render the preview of the entry content"""
    
    if not entry:
        st.info("No entry loaded")
        return
    
    st.markdown(f"### {entry.title}")
    
    if entry.entry_format == FELIX_FORMAT_KEY:
        payload = hydrate_felix_payload(entry)
        render_felix_preview(payload, entry)
    elif entry.content:
        if entry.content_type == "markdown":
            rendered_content = render_markdown_with_latex(entry.content)
            st.markdown(rendered_content, unsafe_allow_html=True)
        else:
            st.text(entry.content)
    else:
        st.info("No content to preview. Add content in the Edit tab.")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Created:** {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        st.markdown(f"**Updated:** {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")
    
    with col3:
        lock_status = "🔒 Locked" if entry.is_locked else "📝 Editable"
        st.markdown(f"**Status:** {lock_status}")


def render_felix_preview(payload, entry=None):
    """Display FELIX structured data"""
    st.markdown("#### Metadata")
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.markdown(f"**Run Date:** {payload.get('run_date') or '—'}")
        st.markdown(f"**Start:** {payload.get('start_time') or '—'}")
        st.markdown(f"**End:** {payload.get('end_time') or '—'}")
    with meta_cols[1]:
        st.markdown(f"**Operators:** {format_list(payload.get('operators'))}")
        st.markdown(f"**Campaign:** {payload.get('beamtime_campaign') or '—'}")
        st.markdown(f"**Instrument:** {payload.get('instrument_location') or '—'}")
    with meta_cols[2]:
        st.markdown(f"**Experiment Type:** {payload.get('experiment_type') or '—'}")
        st.markdown(f"**Goal Outcome:** {payload.get('goal_outcome') or '—'}")
        st.markdown(f"**Confidence:** {payload.get('confidence_level') or '—'}")
    
    st.markdown("#### Goal")
    st.markdown(payload.get("goal_text") or "—")
    
    st.markdown("#### Species & Target")
    st.markdown(f"- **Precursors:** {format_list(payload.get('precursor_molecules'))}")
    st.markdown(f"- **Discharge:** {'On' if payload.get('discharge_enabled') else 'Off'} "
                f"(V={payload.get('discharge_voltage') or '—'}, I={payload.get('discharge_current') or '—'}, Δt={payload.get('discharge_timing_offset') or '—'})")
    st.markdown(f"- **Expected Products:** {payload.get('expected_products') or '—'}")
    st.markdown(f"- **Target m/z:** {format_list(payload.get('target_mass_channels'))}")
    
    st.markdown("#### Experimental Conditions")
    st.markdown(f"- **Carrier Gas:** {payload.get('carrier_gas') or '—'} | **Backing Pressure:** {payload.get('backing_pressure') or '—'} {payload.get('backing_pressure_unit') or ''}")
    st.markdown(f"- **Valve:** {payload.get('valve_type') or '—'} @ {payload.get('valve_timing') or '—'} | **Skimmer:** {'Yes' if payload.get('skimmer_in_place') else 'No'}")
    st.markdown(f"- **IR Source:** {payload.get('ir_source') or '—'} "
                f"({payload.get('wavelength_start') or '—'}–{payload.get('wavelength_end') or '—'}, step {payload.get('step_size') or '—'})")
    st.markdown(f"- **Pulse Energy:** {payload.get('pulse_energy') or '—'} {payload.get('pulse_energy_unit') or ''} | **Rep Rate:** {payload.get('repetition_rate') or '—'} Hz")
    st.markdown(f"- **UV:** λ={payload.get('uv_wavelength') or '—'} nm, Energy={payload.get('uv_pulse_energy') or '—'}, Scheme={payload.get('ionization_scheme') or '—'}")
    
    st.markdown("#### Run Configuration Snapshot")
    snapshot_cols = st.columns(3)
    with snapshot_cols[0]:
        st.metric("Alignment", payload.get("alignment_status") or "—")
    with snapshot_cols[1]:
        st.metric("Signal Stability", payload.get("signal_stability") or "—")
    with snapshot_cols[2]:
        st.metric("Background", payload.get("background_level") or "—")
    
    actions = payload.get("actions") or []
    if actions:
        st.markdown("#### Actions Taken")
        for action in actions:
            timestamp = action.get("timestamp") or "—"
            parameter = action.get("parameter") or "Parameter"
            old_value = action.get("old_value") or "—"
            new_value = action.get("new_value") or "—"
            reason = action.get("reason")
            st.markdown(f"- **{timestamp}** — {parameter}: {old_value} → {new_value}" + (f" ({reason})" if reason else ""))
    
    observations = payload.get("observations") or {}
    st.markdown("#### Observations")
    st.markdown(f"- **IR Depletion:** {'Yes' if observations.get('ir_depletion_observed') else 'No'}")
    st.markdown(f"- **Positions:** {format_list(observations.get('depletion_positions'))}")
    st.markdown(f"- **Signal Trend:** {observations.get('signal_trend') or '—'}")
    st.markdown(f"- **Noise Level:** {observations.get('noise_level') or '—'}")
    st.markdown(f"- **Tags:** {format_list(observations.get('unexpected_tags'))}")
    if observations.get("notes"):
        st.markdown(f"- **Notes:** {observations.get('notes')}")
    
    st.markdown("#### Interpretation & Outcome")
    st.markdown(f"- **Interpretation:** {payload.get('interpretation_notes') or '—'}")
    st.markdown(f"- **Reference Comparison:** {payload.get('reference_comparison') or '—'}")
    st.markdown(f"- **Key Result:** {payload.get('key_result') or '—'}")
    st.markdown(f"- **Main Limitation:** {payload.get('main_limitation') or '—'}")
    
    st.markdown("#### Data & Files")
    st.markdown(f"- **Data Folder:** {payload.get('data_folder_path') or '—'}")
    st.markdown(f"- **Mass Spectra Files:** {format_list(payload.get('mass_spectra_files'))}")
    st.markdown(f"- **IR Depletion Files:** {format_list(payload.get('ir_depletion_files'))}")
    st.markdown(f"- **Data Quality:** {payload.get('data_quality_notes') or '—'}")
    
    next_steps = payload.get("next_steps") or []
    if next_steps:
        st.markdown("#### Next Steps")
        for step in next_steps:
            st.markdown(f"- {step}")
    
    flags = payload.get("flags") or {}
    st.markdown("#### Flags")
    flag_cols = st.columns(4)
    flag_cols[0].metric("Reproducible", "Yes" if flags.get("reproducible_run") else "No")
    flag_cols[1].metric("Calibration", "Valid" if flags.get("calibration_valid") else "Check")
    flag_cols[2].metric("Alignment Issues", "Yes" if flags.get("alignment_issues") else "No")
    flag_cols[3].metric("Data Questionable", "Yes" if flags.get("data_questionable") else "No")
    
    if entry and entry.content:
        st.markdown("#### Narrative Summary")
        st.markdown(render_markdown_with_latex(entry.content), unsafe_allow_html=True)

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

def render_linked_materials(entry, experiment, db):
    """Render material linking functionality"""
    
    st.markdown("### Linked Materials")
    
    if entry:
        linked_materials = db.get_linked_materials(entry.id)
        
        if linked_materials:
            st.markdown(f"**Currently Linked ({len(linked_materials)}):**")
            
            for link in linked_materials:
                material = db.get_material(link.material_id)
                if not material:
                    continue
                
                with st.container(border=True):
                    st.markdown(f"#### 🧱 {material.name}")
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if material.material_type:
                            st.markdown(f"**Type:** {material.material_type}")
                        if material.vendor:
                            st.markdown(f"**Vendor:** {material.vendor}")
                        if material.part_number:
                            st.markdown(f"**Part #:** {material.part_number}")
                        if link.usage_context:
                            st.markdown(f"**Usage:** {link.usage_context}")
                        if link.quantity_used:
                            st.markdown(f"**Quantity Used:** {link.quantity_used} {link.unit or 'units'}")
                        if link.notes:
                            st.markdown(f"**Notes:** {link.notes}")
                        st.markdown(f"**Linked:** {link.linked_at.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        if st.button("🗑️ Remove", key=f"remove_material_{link.id}"):
                            if db.remove_linked_material(link.id):
                                display_success("Material link removed")
                                st.rerun()
                            else:
                                display_error("Failed to remove material link")
                
                st.markdown("")
        else:
            st.info("No materials linked to this entry")
        
        st.markdown("### Link New Material")
        
        materials = db.get_materials()
        
        if materials:
            material_options = {f"{m.name} ({m.material_type or 'Unknown type'})": m.id for m in materials}
            
            with st.form("link_material_form"):
                selected_material = st.selectbox("Select Material*", options=list(material_options.keys()))
                material_id = material_options[selected_material]
                
                usage_context = st.text_input("Usage Context", help="e.g., IR window, OPO crystal, fiber delivery")
                quantity_used = st.number_input("Quantity Used", min_value=0.0, format="%.4f")
                unit = st.selectbox("Unit", ["m", "cm", "mm", "µm", "°", "W", "mJ", "unit", ""])
                notes = st.text_area("Notes (optional)")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("🔗 Link Material", type="primary"):
                        link = db.link_material_to_entry(
                            entry_id=entry.id,
                            material_id=material_id,
                            quantity_used=quantity_used if quantity_used > 0 else None,
                            unit=unit if unit else None,
                            usage_context=usage_context if usage_context else None,
                            notes=notes if notes else None
                        )
                        display_success("Material linked successfully!")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.rerun()
        else:
            st.warning("No materials available in inventory. Add materials in the Physics Inventory section first.")
    else:
        st.info("Please save the entry first before linking materials")

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
        content_tab, attachments_tab, materials_tab, audit_tab = st.tabs(
            ["📄 Content", "📎 Attachments", "🧱 Linked Materials", "📋 Audit Trail"]
        )
        
        with content_tab:
            if entry.entry_format == FELIX_FORMAT_KEY:
                payload = hydrate_felix_payload(entry)
                render_felix_preview(payload, entry)
            elif entry.content:
                if entry.content_type == "markdown":
                    rendered_content = render_markdown_with_latex(entry.content)
                    st.markdown(rendered_content, unsafe_allow_html=True)
                else:
                    st.text(entry.content)
            else:
                st.info("No content")
        
        with attachments_tab:
            render_attachments(entry, db)
        
        with materials_tab:
            render_linked_materials(entry, experiment, db)
        
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
