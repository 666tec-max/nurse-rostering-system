import os
import streamlit.components.v1 as components

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "grades_hierarchy",
        url="http://localhost:3002",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend")
    _component_func = components.declare_component("grades_hierarchy", path=build_dir)

def grades_hierarchy(hierarchy, pool, key=None):
    """
    Renders an interactive drag-and-drop grades hierarchy pyramid.

    Args:
        hierarchy: List of layers (top=senior). Each layer is a list of grade dicts: {"code": "SN", "name": "Senior Nurse"}
        pool: List of unassigned grade dicts.
        key: Unique Streamlit component key.

    Returns:
        A dict with 'hierarchy' and 'pool' if state changed, else None.
    """
    component_value = _component_func(
        hierarchy=hierarchy,
        pool=pool,
        key=key,
        default=None
    )
    return component_value
