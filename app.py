import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import ezdxf
import io
import zipfile

st.set_page_config(
    page_title="Shirt Pattern Generator",
    page_icon="👔",
    layout="wide"
)

st.title("2D Shirt Pattern Generator")
st.write("Upload JSON measurements to generate shirt cutting patterns.")

# Sample measurements
sample_measurements = {
    "chest": 100,  # cm
    "waist": 90,  # cm
    "shoulder_width": 46,  # cm
    "back_length": 75,  # cm
    "sleeve_length": 60,  # cm
    "neck_circumference": 40,  # cm
    "armhole_depth": 25,  # cm
    "cuff_circumference": 20,  # cm
    "hem_width": 110  # cm
}


# Functions to generate pattern pieces
def generate_front_panel(measurements):
    """Generate the front panel pattern piece."""
    # Pattern calculations based on measurements
    chest = measurements["chest"] / 2 + 5  # Half chest with ease
    shoulder = measurements["shoulder_width"] / 2
    length = measurements["back_length"]
    neck_width = measurements["neck_circumference"] / 6
    neck_depth = measurements["neck_circumference"] / 12 + 2
    armhole = measurements["armhole_depth"]
    waist = measurements["waist"] / 2 + 3
    hem = measurements["hem_width"] / 2

    # Define the points for the pattern
    # Origin is at top left corner of the pattern
    points = [
        (0, 0),  # 0: Top left (shoulder point)
        (shoulder, 0),  # 1: Shoulder right
        (chest, armhole),  # 2: Armhole bottom
        (chest, length * 0.4),  # 3: Waist
        (hem / 2 + chest / 2, length),  # 4: Hem
        (0, length),  # 5: Left hem
        (0, armhole),  # 6: Left armhole
        (neck_width, neck_depth)  # 7: Neck point
    ]

    # Define the path
    codes = [
        Path.MOVETO,  # 0
        Path.LINETO,  # 1
        Path.LINETO,  # 2
        Path.LINETO,  # 3
        Path.LINETO,  # 4
        Path.LINETO,  # 5
        Path.LINETO,  # 6
        Path.CURVE3,  # 7 - Neck curve control point
        Path.CURVE3,  # Back to 0
    ]

    # Defining the path
    path = Path(points + [points[0]], codes)

    return path, points


def generate_back_panel(measurements):
    """Generate the back panel pattern piece."""
    # Pattern calculations based on measurements
    chest = measurements["chest"] / 2 + 3  # Half chest with ease
    shoulder = measurements["shoulder_width"] / 2
    length = measurements["back_length"]
    neck_width = measurements["neck_circumference"] / 6
    neck_depth = measurements["neck_circumference"] / 24  # Shallower than front
    armhole = measurements["armhole_depth"]
    waist = measurements["waist"] / 2 + 2
    hem = measurements["hem_width"] / 2

    # Define the points for the pattern
    points = [
        (0, 0),  # 0: Top left (shoulder point)
        (shoulder, 0),  # 1: Shoulder right
        (chest, armhole),  # 2: Armhole bottom
        (chest, length * 0.4),  # 3: Waist
        (hem / 2 + chest / 2, length),  # 4: Hem
        (0, length),  # 5: Left hem
        (0, armhole),  # 6: Left armhole
        (neck_width, neck_depth)  # 7: Neck point
    ]

    # Define the path
    codes = [
        Path.MOVETO,  # 0
        Path.LINETO,  # 1
        Path.LINETO,  # 2
        Path.LINETO,  # 3
        Path.LINETO,  # 4
        Path.LINETO,  # 5
        Path.LINETO,  # 6
        Path.CURVE3,  # 7 - Neck curve control point
        Path.CURVE3,  # Back to 0
    ]

    # Defining the path
    path = Path(points + [points[0]], codes)

    return path, points


def generate_sleeve(measurements):
    """Generate the sleeve pattern piece."""
    # Pattern calculations
    sleeve_length = measurements["sleeve_length"]
    armhole = measurements["armhole_depth"] * 2  # Total armhole circumference
    cuff = measurements["cuff_circumference"] + 2  # Cuff width with ease

    # Sleeve cap height
    cap_height = armhole / 3

    # Sleeve width at widest point (bicep)
    sleeve_width = armhole / 2 + 5

    # Define the points for the pattern
    points = [
        (0, 0),  # 0: Top middle of sleeve cap
        (sleeve_width / 2, cap_height),  # 1: Right side of sleeve
        (sleeve_width / 3, sleeve_length),  # 2: Right cuff
        (-sleeve_width / 3, sleeve_length),  # 3: Left cuff
        (-sleeve_width / 2, cap_height),  # 4: Left side of sleeve
    ]

    # Define the path
    codes = [
        Path.MOVETO,  # 0
        Path.CURVE4,  # Control point for curve
        Path.CURVE4,  # Control point for curve
        Path.CURVE4,  # 1
        Path.LINETO,  # 2
        Path.LINETO,  # 3
        Path.LINETO,  # 4
        Path.CURVE4,  # Control point for curve
        Path.CURVE4,  # Control point for curve
        Path.CURVE4,  # Back to 0
    ]

    # We need to add control points for the Bézier curves
    control_points = [
        points[0],  # Starting point
        (sleeve_width / 4, cap_height / 3),  # Right control point 1
        (sleeve_width / 2, cap_height / 1.5),  # Right control point 2
        points[1],  # Right sleeve point
        points[2],  # Right cuff
        points[3],  # Left cuff
        points[4],  # Left sleeve point
        (-sleeve_width / 2, cap_height / 1.5),  # Left control point 1
        (-sleeve_width / 4, cap_height / 3),  # Left control point 2
        points[0]  # Back to starting point
    ]

    # Defining the path
    path = Path(control_points, codes)

    return path, points


def generate_collar(measurements):
    """Generate the collar pattern piece."""
    # Collar is based on neck circumference
    neck = measurements["neck_circumference"]
    collar_length = neck + 2  # Add some ease
    collar_width = 5  # Standard collar width

    # Define the points for the pattern
    points = [
        (0, 0),  # 0: Bottom left
        (collar_length, 0),  # 1: Bottom right
        (collar_length, collar_width),  # 2: Top right
        (0, collar_width)  # 3: Top left
    ]

    # Define the path
    codes = [
        Path.MOVETO,  # 0
        Path.LINETO,  # 1
        Path.LINETO,  # 2
        Path.LINETO,  # 3
        Path.CLOSEPOLY  # Close the shape
    ]

    # Defining the path
    path = Path(points + [(0, 0)], codes)

    return path, points


def generate_cuff(measurements):
    """Generate the cuff pattern piece."""
    # Cuff is based on wrist circumference
    cuff_circumference = measurements["cuff_circumference"]
    cuff_length = cuff_circumference + 2  # Add some ease
    cuff_width = 6  # Standard cuff width

    # Define the points for the pattern
    points = [
        (0, 0),  # 0: Bottom left
        (cuff_length, 0),  # 1: Bottom right
        (cuff_length, cuff_width),  # 2: Top right
        (0, cuff_width)  # 3: Top left
    ]

    # Define the path
    codes = [
        Path.MOVETO,  # 0
        Path.LINETO,  # 1
        Path.LINETO,  # 2
        Path.LINETO,  # 3
        Path.CLOSEPOLY  # Close the shape
    ]

    # Defining the path
    path = Path(points + [(0, 0)], codes)

    return path, points


def plot_pattern(path, points, title, ax):
    """Plot a pattern piece on the given axis."""
    patch = patches.PathPatch(path, facecolor='none', lw=2)
    ax.add_patch(patch)

    # Add points and labels for key measurements
    for i, (x, y) in enumerate(points):
        ax.plot(x, y, 'o', color='red', markersize=4)
        ax.text(x, y, f'{i}', fontsize=8, ha='right')

    # Set axis properties
    ax.set_xlim(min([p[0] for p in points]) - 5, max([p[0] for p in points]) + 5)
    ax.set_ylim(min([p[1] for p in points]) - 5, max([p[1] for p in points]) + 5)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title(title)

    # Add seam allowance (dashed line)
    seam_allowance = 1.5  # cm
    seam_path = Path.make_compound_path(
        Path([(p[0] + seam_allowance if i != len(points) - 1 else p[0],
               p[1] + seam_allowance if i != len(points) - 1 else p[1])
              for i, p in enumerate(points)] + [(points[0][0] + seam_allowance, points[0][1] + seam_allowance)]),
        path
    )
    seam_patch = patches.PathPatch(seam_path, facecolor='lightgray', alpha=0.3, lw=1, ls='--')
    ax.add_patch(seam_patch)


def generate_all_patterns(measurements):
    """Generate all pattern pieces and return them as a figure for display."""
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))

    # Generate and plot each pattern piece
    front_path, front_points = generate_front_panel(measurements)
    plot_pattern(front_path, front_points, "Front Panel", axs[0, 0])

    back_path, back_points = generate_back_panel(measurements)
    plot_pattern(back_path, back_points, "Back Panel", axs[0, 1])

    sleeve_path, sleeve_points = generate_sleeve(measurements)
    plot_pattern(sleeve_path, sleeve_points, "Sleeve", axs[0, 2])

    collar_path, collar_points = generate_collar(measurements)
    plot_pattern(collar_path, collar_points, "Collar", axs[1, 0])

    cuff_path, cuff_points = generate_cuff(measurements)
    plot_pattern(cuff_path, cuff_points, "Cuff", axs[1, 1])

    # Add an empty plot with pattern key
    axs[1, 2].axis('off')
    axs[1, 2].text(0.1, 0.9, "Pattern Key:", fontsize=12, fontweight='bold')
    axs[1, 2].text(0.1, 0.8, "Red dots: Key points", fontsize=10)
    axs[1, 2].text(0.1, 0.7, "Solid line: Cut line", fontsize=10)
    axs[1, 2].text(0.1, 0.6, "Dashed gray area: 1.5cm seam allowance", fontsize=10)

    plt.tight_layout()
    return fig, [
        {"name": "front_panel", "points": front_points},
        {"name": "back_panel", "points": back_points},
        {"name": "sleeve", "points": sleeve_points},
        {"name": "collar", "points": collar_points},
        {"name": "cuff", "points": cuff_points}
    ]


def generate_dxf_from_points(points, filename, add_seam_allowance=True):
    """Generate a DXF file from pattern points."""
    # Create a new DXF document with the R2010 specification
    doc = ezdxf.new('R2010')

    # Create a new layer for the pattern outline
    doc.layers.new(name='PATTERN_OUTLINE', dxfattribs={'color': 1})  # Color 1 = red

    # Create a layer for points
    doc.layers.new(name='POINTS', dxfattribs={'color': 5})  # Color 5 = blue

    # Create a layer for text labels
    doc.layers.new(name='TEXT', dxfattribs={'color': 3})  # Color 3 = green

    # Get the modelspace
    msp = doc.modelspace()

    # Create a polyline for the main pattern on the PATTERN_OUTLINE layer
    polyline = msp.add_lwpolyline(points, dxfattribs={'layer': 'PATTERN_OUTLINE', 'color': 1})
    polyline.close(True)  # Close the polyline

    # Add points as reference on the POINTS layer
    for i, (x, y) in enumerate(points):
        # Add a point marker (small circle)
        msp.add_circle((x, y), radius=0.5, dxfattribs={'layer': 'POINTS', 'color': 5})

        # Add point number label on the TEXT layer
        msp.add_text(f"P{i}", dxfattribs={
            'height': 0.8,
            'layer': 'TEXT',
            'color': 3,
            'insert': (x + 0.6, y + 0.6)
        })

    # Add filename as title
    msp.add_text(f"{filename.upper()} PATTERN", dxfattribs={
        'height': 2.0,
        'layer': 'TEXT',
        'color': 2,  # Color 2 = yellow
        'insert': (points[0][0], max(p[1] for p in points) + 5)
    })

    # Add a note about seam allowance
    msp.add_text("NOTE: ADD 1.5cm SEAM ALLOWANCE", dxfattribs={
        'height': 1.0,
        'layer': 'TEXT',
        'color': 2,
        'insert': (points[0][0], min(p[1] for p in points) - 5)
    })

    # Create a string buffer for the DXF data
    string_io = io.StringIO()
    doc.write(string_io)
    return string_io.getvalue()


def create_dxf_zip(patterns):
    """Create a ZIP file containing all pattern pieces as DXF files."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        for pattern in patterns:
            # Convert points to a list of tuples with explicit float values
            # This ensures compatibility with ezdxf
            clean_points = [(float(p[0]), float(p[1])) for p in pattern["points"]]
            dxf_data = generate_dxf_from_points(clean_points, pattern["name"])
            zip_file.writestr(f"{pattern['name']}.dxf", dxf_data)

    zip_buffer.seek(0)
    return zip_buffer


# Interface to input measurements
st.subheader("Upload Measurements")

uploaded_file = st.file_uploader("Upload measurements JSON file", type="json")
if uploaded_file is not None:
    try:
        measurements = json.load(uploaded_file)
        st.success("Measurements loaded successfully!")
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        measurements = sample_measurements
else:
    # Default to sample measurements if no file uploaded
    measurements = sample_measurements
    st.info("Using default measurements. Upload a JSON file to use custom measurements.")

# Button to generate patterns
if st.button("Generate Patterns"):
    st.subheader("Shirt Pattern Pieces")

    try:
        # Generate the patterns
        fig, pattern_data = generate_all_patterns(measurements)

        # Display the figure
        st.pyplot(fig)

        # Create a ZIP file with all pattern pieces in DXF format
        zip_buffer = create_dxf_zip(pattern_data)

        # Provide a download button for the DXF files
        st.download_button(
            label="Download DXF Patterns",
            data=zip_buffer,
            file_name="shirt_patterns.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Error generating patterns: {e}")
        st.error("Please check if your measurements are valid.")

# Footer
st.markdown("---")
st.markdown("Shirt Pattern Generator")