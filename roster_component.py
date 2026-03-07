import streamlit.components.v1 as components
import json

def professional_roster(
    nurse_names, 
    date_labels, 
    schedule_data, 
    shift_info, 
    locked_assignments, 
    zoom_level=100,
    painter_shift=None,
    key=None
):
    """
    Renders a professional, interactive roster using HTML/JS/CSS.
    
    Args:
        nurse_names: List of nurse names (rows).
        date_labels: List of dates (columns).
        schedule_data: Dict {nurse_name: [shifts]}.
        shift_info: List of shift dicts (code, color, etc).
        locked_assignments: List of (nurse_name, day_idx) tuples.
        zoom_level: Scale percentage (50-150).
        painter_shift: Currently selected shift for painting.
        key: Streamlit component key.
    """
    
    # Prepare colors
    colors = {s['code']: s.get('color', '#E0E0E0') for s in shift_info}
    colors['-'] = '#FFFFFF'
    
    # Prepare weekend flags
    is_weekend = [label.startswith(('Sat', 'Sun')) for label in date_labels]

    # Convert locked assignments to a format JS can consume easily
    # (using string keys 'nurse_name|day_idx')
    locked_set = {f"{nurse}|{day}" for nurse, day in locked_assignments}

    html_content = f"""
    <div id="roster-container" style="zoom: {zoom_level/100};">
        <style>
            :root {{
                --cell-width: 80px;
                --cell-height: 40px;
                --header-bg: #F8F9FA;
                --border-color: #DEE2E6;
                --locked-outline: #E74C3C;
                --weekend-bg: #F1F3F5;
            }}
            
            #roster-table-wrapper {{
                overflow: auto;
                max-height: 600px;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                position: relative;
                font-family: 'Inter', -apple-system, sans-serif;
            }}
            
            table {{
                border-collapse: separate;
                border-spacing: 0;
                width: max-content;
            }}
            
            th, td {{
                width: var(--cell-width);
                height: var(--cell-height);
                text-align: center;
                border-right: 1px solid var(--border-color);
                border-bottom: 1px solid var(--border-color);
                user-select: none;
                transition: background-color 0.1s;
            }}
            
            /* Sticky Headers */
            thead th {{
                position: sticky;
                top: 0;
                background: var(--header-bg);
                z-index: 10;
                font-weight: 600;
                font-size: 0.85rem;
                padding: 8px;
            }}
            
            th.nurse-name-col, td.nurse-name-col {{
                position: sticky;
                left: 0;
                background: var(--header-bg);
                z-index: 11;
                width: 150px;
                text-align: left;
                padding-left: 12px;
                border-right: 2px solid var(--border-color);
            }}
            
            thead th.nurse-name-col {{
                z-index: 12;
            }}
            
            /* Cell States */
            .shift-cell {{
                cursor: pointer;
                font-weight: 500;
                font-size: 0.9rem;
            }}
            
            .shift-cell:hover {{
                filter: brightness(0.95);
                box-shadow: inset 0 0 0 2px rgba(0,0,0,0.05);
            }}
            
            .locked {{
                outline: 2px solid var(--locked-outline);
                outline-offset: -2px;
                position: relative;
            }}
            
            .weekend {{
                background-color: var(--weekend-bg);
            }}
            
            .day-label {{
                font-size: 0.7rem;
                display: block;
                color: #6C757D;
            }}

            /* Painter Cursor */
            .painting-mode .shift-cell {{
                cursor: crosshair;
            }}
        </style>
        
        <div id="roster-table-wrapper">
            <table id="roster-table">
                <thead>
                    <tr>
                        <th class="nurse-name-col">Staff Name</th>
                        {"".join([f'<th class="{"weekend" if w else ""}">{l.split(", ")[0]}<span class="day-label">{l.split(", ")[1]}</span></th>' for l, w in zip(date_labels, is_weekend)])}
                    </tr>
                </thead>
                <tbody>
                    {"".join([
                        f'<tr>'
                        f'<td class="nurse-name-col">{name}</td>'
                        + "".join([
                            f'<td class="shift-cell {"weekend" if is_weekend[d] else ""} {"locked" if f"{name}|{d}" in locked_set else ""}" '
                            f'data-nurse="{name}" data-day="{d}" '
                            f'style="background-color: {colors.get(schedule_data[name][d], "#FFFFFF")};">'
                            f'{schedule_data[name][d]}'
                            f'</td>'
                            for d in range(len(date_labels))
                        ]) +
                        '</tr>'
                        for name in nurse_names
                    ])}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const colors = {json.dumps(colors)};
        const painterShift = {json.dumps(painter_shift)};
        let isMouseDown = false;
        let pendingEdits = {{}};

        const cells = document.querySelectorAll('.shift-cell');
        
        function applyShift(cell) {{
            if (!painterShift) return;
            
            const nurse = cell.dataset.nurse;
            const day = cell.dataset.day;
            
            cell.innerText = painterShift;
            cell.style.backgroundColor = colors[painterShift] || '#FFFFFF';
            cell.classList.add('locked');
            
            pendingEdits[`${{nurse}}|${{day}}`] = painterShift;
            
            // Notify Streamlit (debounced or on mouseup)
            // For now, let's collect and send on mouseup
        }}

        cells.forEach(cell => {{
            cell.addEventListener('mousedown', (e) => {{
                isMouseDown = true;
                applyShift(cell);
            }});
            
            cell.addEventListener('mouseover', () => {{
                if (isMouseDown) {{
                    applyShift(cell);
                }}
            }});
        }});

        window.addEventListener('mouseup', () => {{
            if (isMouseDown) {{
                isMouseDown = false;
                if (Object.keys(pendingEdits).length > 0) {{
                    // Send back to Streamlit
                    // Using a window message that and then we can capture or 
                    // a more robust way like a hidden button click
                    window.parent.postMessage({{
                        type: 'ROSTER_EDIT',
                        edits: pendingEdits
                    }}, '*');
                    pendingEdits = {{}};
                }}
            }}
        }});
        
        // Add class to container if painter active
        if (painterShift) {{
            document.getElementById('roster-container').classList.add('painting-mode');
        }}
    </script>
    """

    # We use a fixed height for the component and handle scrolling inside it
    return components.html(html_content, height=650, scrolling=True)
