import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import base64
import io
from PIL import Image
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

st.set_page_config(page_title="Pallet Builder Tool", layout="centered")

st.title("📦 Pallet Builder Tool")
st.write("Enter product and pallet dimensions to calculate stack configuration, dimensions, and total weight.")

# Pallet selection
pallet_type = st.radio("Select Pallet Type", ["US Pallet (inches)", "EU Pallet (cm)"])

# Presets
preset = st.selectbox("Choose a Product Preset", ["Custom", "Small Box", "Large Box"])
if preset == "Small Box":
    product_length = 24
    product_width = 18
    product_height = 10
    product_weight = 3.0
elif preset == "Large Box":
    product_length = 39
    product_width = 21
    product_height = 15
    product_weight = 6.0
else:
    product_length = 39
    product_width = 21
    product_height = 9
    product_weight = 5.0

if pallet_type == "EU Pallet (cm)":
    unit = "cm"
    weight_unit = "kg"
    pallet_length = 120
    pallet_width = 80
    pallet_height = 180
else:
    unit = "in"
    weight_unit = "lbs"
    pallet_length = 48
    pallet_width = 40
    pallet_height = 60

# Input form
with st.form("pallet_input_form"):
    col1, col2 = st.columns(2)
    with col1:
        pallet_length = st.number_input(f"Pallet Length ({unit})", value=pallet_length)
        pallet_width = st.number_input(f"Pallet Width ({unit})", value=pallet_width)
        pallet_height = st.number_input(f"Max Stack Height ({unit})", value=pallet_height)
    with col2:
        product_length = st.number_input(f"Product Length ({unit})", value=product_length)
        product_width = st.number_input(f"Product Width ({unit})", value=product_width)
        product_height = st.number_input(f"Product Height ({unit})", value=product_height)

    total_units = st.number_input("Total Units to Ship", value=20, step=1)
    product_weight = st.number_input(f"Product Weight ({weight_unit})", value=product_weight)
    rotation_allowed = st.checkbox("Allow Rotation", value=True)
    pallet_base_weight = st.number_input(f"Pallet Base Weight (avg ~38 {weight_unit})", value=38.0)
    wrap_weight = st.number_input(f"Wrapping Material Weight (avg ~2 {weight_unit})", value=2.0)
    view_option = st.radio("Select Visualization View", ["2D Top-Down", "Static 3D Render"])
    submitted = st.form_submit_button("Calculate & Visualize")

if submitted:
    if rotation_allowed:
        fit_normal = (pallet_length // product_length) * (pallet_width // product_width)
        fit_rotated = (pallet_length // product_width) * (pallet_width // product_length)
        if fit_rotated > fit_normal:
            unit_l, unit_w = product_width, product_length
            units_per_layer = fit_rotated
        else:
            unit_l, unit_w = product_length, product_width
            units_per_layer = fit_normal
    else:
        unit_l, unit_w = product_length, product_width
        units_per_layer = (pallet_length // unit_l) * (pallet_width // unit_w)

    layers_per_pallet = min(pallet_height // product_height, total_units // units_per_layer + (total_units % units_per_layer > 0))
    max_units_per_pallet = units_per_layer * layers_per_pallet
    total_pallets_needed = total_units // max_units_per_pallet + (total_units % max_units_per_pallet > 0)

    used_volume = product_length * product_width * product_height * min(total_units, max_units_per_pallet)
    pallet_volume = pallet_length * pallet_width * pallet_height
    volume_utilization = used_volume / pallet_volume * 100
    total_weight = product_weight * total_units
    total_stack_height = layers_per_pallet * product_height + 5.5
    total_weight_gross = total_weight + pallet_base_weight + wrap_weight
    dims_string = f"{pallet_length} × {pallet_width} × {int(total_stack_height)} {unit}"

    st.subheader("📊 Pallet Summary")
    st.write(f"**Units per Layer:** {units_per_layer}")
    st.write(f"**Layers per Pallet:** {layers_per_pallet}")
    st.write(f"**Max Units per Pallet:** {max_units_per_pallet}")
    st.write(f"**Total Pallets Needed:** {total_pallets_needed}")
    st.write(f"**Volume Utilization (one pallet):** {volume_utilization:.1f}%")
    st.write(f"**Total Net Product Weight:** {total_weight:.1f} {weight_unit}")
    st.write(f"**Gross Shipping Weight:** {total_weight_gross:.1f} {weight_unit}")
    st.write(f"**Final Dimensions:** {dims_string}")

    summary_data = {
        "Metric": [
            "Units per Layer",
            "Layers per Pallet",
            "Max Units per Pallet",
            "Total Pallets Needed",
            "Volume Utilization (%)",
            f"Net Product Weight ({weight_unit})",
            f"Gross Shipping Weight ({weight_unit})",
            f"Final Dimensions ({unit})"
        ],
        "Value": [
            units_per_layer,
            layers_per_pallet,
            max_units_per_pallet,
            total_pallets_needed,
            round(volume_utilization, 1),
            round(total_weight, 1),
            round(total_weight_gross, 1),
            dims_string
        ]
    }
    df = pd.DataFrame(summary_data)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="pallet_summary.csv">📥 Download Summary as CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

    if view_option == "2D Top-Down":
        st.subheader("📐 Top-Down and Side Pallet Views")

        fig_top, ax_top = plt.subplots(figsize=(6, 4))
        ax_top.set_xlim(0, pallet_length)
        ax_top.set_ylim(0, pallet_width)
        ax_top.set_title('Top-Down View (1 Layer)')
        ax_top.set_xlabel(f'Length ({unit})')
        ax_top.set_ylabel(f'Width ({unit})')
        ax_top.grid(True, linestyle='--', linewidth=0.5)
        ax_top.add_patch(patches.Rectangle((0, 0), pallet_length, pallet_width, edgecolor='black', facecolor='none', linewidth=2))

        x = y = units_drawn = 0
        while y + unit_w <= pallet_width:
            x = 0
            while x + unit_l <= pallet_length:
                ax_top.add_patch(patches.Rectangle((x, y), unit_l, unit_w, edgecolor='blue', facecolor='lightblue'))
                units_drawn += 1
                if units_drawn >= min(units_per_layer, total_units):
                    break
                x += unit_l
            if units_drawn >= min(units_per_layer, total_units):
                break
            y += unit_w

        fig_side, ax_side = plt.subplots(figsize=(6, 4))
        ax_side.set_xlim(0, pallet_length)
        ax_side.set_ylim(0, product_height * layers_per_pallet + 5.5)
        ax_side.set_title('Side View (Stacked Height)')
        ax_side.set_xlabel(f'Length ({unit})')
        ax_side.set_ylabel(f'Height ({unit})')
        ax_side.grid(True, linestyle='--', linewidth=0.5)
        for layer in range(layers_per_pallet):
            y_pos = 5.5 + layer * product_height
            x = 0
            while x + unit_l <= pallet_length:
                ax_side.add_patch(patches.Rectangle((x, y_pos), unit_l, product_height, edgecolor='blue', facecolor='lightblue'))
                x += unit_l

        st.pyplot(fig_top)
        st.pyplot(fig_side)

    else:
        st.info("3D rendering is temporarily disabled due to compatibility issues.")
