import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set it to False while we're developing
# the component, and True when we're ready to use it in production.
_RELEASE = True

if not _RELEASE:
    # Use the local development server for the component
    _component_func = components.declare_component(
        "professional_roster",
        url="http://localhost:3001",
    )
else:
    # Use the compiled version of the component
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend")
    _component_func = components.declare_component("professional_roster", path=build_dir)

def professional_roster(nurse_names, date_labels, schedule_data, shift_colors, locked_assignments=None, nurse_details=None, remarks=None, zoom_level=100, painter_shift=None, key=None):
    """
    Renders a professional interactive roster grid.
    
    Returns: 
        A dict with 'nurse', 'day', 'shift', 'locked', 'remark' if an edit occurred, else None.
    """
    component_value = _component_func(
        nurse_names=nurse_names,
        date_labels=date_labels,
        schedule_data=schedule_data,
        shift_colors=shift_colors,
        locked_assignments=locked_assignments,
        nurse_details=nurse_details,
        remarks=remarks,
        zoom_level=zoom_level,
        painter_shift=painter_shift,
        key=key,
        default=None
    )
    return component_value
