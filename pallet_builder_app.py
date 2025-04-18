import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pandas as pd
import io
import base64

st.set_page_config(page_title="Pallet Builder Tool", layout="centered")

st.title("📦 Pallet Builder Tool")
st.write("Enter product and pallet dimensions to visualize your pallet stacking layout.")

pallet_type = st.radio("Select Pallet Type", ["US Pallet (inches)", "EU Pallet (cm)"])

if pallet_type == "EU Pallet (cm)":
    unit = "cm"
    weight_unit = "kg"
    pallet_length = 120
    pallet_width = 80
    pallet_height = 180
    product_length = 100
    product_width = 50
    product_height = 22
else:
    unit = "in"
    weight_unit = "lbs"
    pallet_length = 48
    pallet_width = 40
    pallet_height = 60
    product_length = 39
    product_width = 21
    product_height = 9

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
    product_weight = st.number_input(f"Product Weight ({weight_unit})", value=5.0)
    rotation_allowed = st.checkbox("Allow Rotation", value=True)

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

    st.subheader("📊 Summary")
    st.write(f"**Units per Layer:** {units_per_layer}")
    st.write(f"**Layers per Pallet:** {layers_per_pallet}")
    st.write(f"**Max Units per Pallet:** {max_units_per_pallet}")
    st.write(f"**Total Pallets Needed:** {total_pallets_needed}")
    st.write(f"**Volume Utilization (one pallet):** {volume_utilization:.1f}%")
    st.write(f"**Total Shipment Weight:** {total_weight:.1f} {weight_unit}")

    summary_df = pd.DataFrame({
        "Metric": ["Units per Layer", "Layers per Pallet", "Max Units per Pallet", "Total Pallets Needed", "Volume Utilization (%)", f"Total Weight ({weight_unit})"],
        "Value": [units_per_layer, layers_per_pallet, max_units_per_pallet, total_pallets_needed, round(volume_utilization, 1), round(total_weight, 1)]
    })

    csv = summary_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="pallet_summary.csv">📥 Download Summary as CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

    # Top-down visualization
    st.subheader("📐 Top-Down Pallet View (1 Layer)")
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_xlim(0, pallet_length)
    ax.set_ylim(0, pallet_width)
    ax.set_title('Top-Down View of One Pallet Layer')
    ax.set_xlabel(f'Length ({unit})')
    ax.set_ylabel(f'Width ({unit})')

    ax.add_patch(patches.Rectangle((0, 0), pallet_length, pallet_width, edgecolor='black', facecolor='none', linewidth=2))

    x = 0
    y = 0
    units_drawn = 0
    while y + unit_w <= pallet_width:
        while x + unit_l <= pallet_length:
            ax.add_patch(patches.Rectangle((x, y), unit_l, unit_w, edgecolor='blue', facecolor='lightblue'))
            units_drawn += 1
            if units_drawn >= min(units_per_layer, total_units):
                break
            x += unit_l
        if units_drawn >= min(units_per_layer, total_units):
            break
        x = 0
        y += unit_w

    st.pyplot(fig)

    # 3D stack visualization
    st.subheader("🔹 3D Stack View")
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("3D Side View of Pallet Stack")
    ax.set_xlabel(f"Length ({unit})")
    ax.set_ylabel(f"Width ({unit})")
    ax.set_zlabel(f"Height ({unit})")
    ax.set_xlim(0, pallet_length)
    ax.set_ylim(0, pallet_width)
    ax.set_zlim(0, product_height * layers_per_pallet)

    units_drawn = 0
    for z in range(layers_per_pallet):
        y = 0
        while y + unit_w <= pallet_width:
            x = 0
            while x + unit_l <= pallet_length:
                if units_drawn >= total_units:
                    break
                box = [
                    [x, y, z * product_height],
                    [x + unit_l, y, z * product_height],
                    [x + unit_l, y + unit_w, z * product_height],
                    [x, y + unit_w, z * product_height],
                    [x, y, (z + 1) * product_height],
                    [x + unit_l, y, (z + 1) * product_height],
                    [x + unit_l, y + unit_w, (z + 1) * product_height],
                    [x, y + unit_w, (z + 1) * product_height],
                ]
                faces = [
                    [box[0], box[1], box[2], box[3]],
                    [box[4], box[5], box[6], box[7]],
                    [box[0], box[1], box[5], box[4]],
                    [box[2], box[3], box[7], box[6]],
                    [box[1], box[2], box[6], box[5]],
                    [box[4], box[7], box[3], box[0]],
                ]
                ax.add_collection3d(Poly3DCollection(faces, facecolors='lightblue', edgecolors='gray', linewidths=0.5, alpha=0.8))
                units_drawn += 1
                x += unit_l
            if units_drawn >= total_units:
                break
            y += unit_w
        if units_drawn >= total_units:
            break

    st.pyplot(fig)
