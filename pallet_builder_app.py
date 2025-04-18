import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import io
import base64
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Pallet Builder Tool", layout="centered")

st.title("📦 Pallet Builder Tool")
st.write("Enter product and pallet dimensions to visualize your pallet stacking layout.")

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

    view_option = st.radio("Select Visualization View", ["2D Top-Down", "3D Interactive"])
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

    if view_option == "2D Top-Down":
        st.subheader("📐 Top-Down Pallet View (1 Layer)")
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.set_xlim(0, pallet_length)
        ax.set_ylim(0, pallet_width)
        ax.set_title('Top-Down View of One Pallet Layer')
        ax.set_xlabel(f'Length ({unit})')
        ax.set_ylabel(f'Width ({unit})')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

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

    else:
        st.subheader("🔹 Interactive 3D Pallet Stack")

    # Display static 3D render with outlines
    from PIL import Image
    static_path = "static_3d_pallet_outline.png"
    try:
        image = Image.open(f"/mnt/data/{static_path}")
        st.image(image, caption="Static 3D Pallet Stack with Outlined Boxes", use_column_width=True)
        with open(f"/mnt/data/{static_path}", "rb") as f:
            btn = st.download_button(label="📥 Download 3D Render (PNG)", data=f, file_name="pallet_3d_render.png", mime="image/png")
    except FileNotFoundError:
        st.warning("Static image not available yet.")

        def create_box(x, y, z, dx, dy, dz, color='lightblue', opacity=1.0):
            vertices = [
                [x, y, z], [x + dx, y, z], [x + dx, y + dy, z], [x, y + dy, z],
                [x, y, z + dz], [x + dx, y, z + dz], [x + dx, y + dy, z + dz], [x, y + dy, z + dz]
            ]
            faces = [
                (0, 1, 2), (0, 2, 3),
                (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4),
                (1, 2, 6), (1, 6, 5),
                (2, 3, 7), (2, 7, 6),
                (3, 0, 4), (3, 4, 7)
            ]
            x_vals, y_vals, z_vals = zip(*vertices)
            i, j, k = zip(*faces)
            return go.Mesh3d(
                x=x_vals, y=y_vals, z=z_vals,
                i=i, j=j, k=k,
                opacity=opacity,
                color=color,
                flatshading=True
            )

        objects = []
        pallet_height_actual = 5.5
        objects.append(create_box(0, 0, 0, pallet_length, pallet_width, pallet_height_actual, color='saddlebrown'))

        # Render 1 layer of boxes
        z_start = pallet_height_actual
        units_drawn = 0
        y = 0
        while y + unit_w <= pallet_width:
            x = 0
            while x + unit_l <= pallet_length:
                if units_drawn >= min(units_per_layer, total_units):
                    break
                objects.append(create_box(x, y, z_start, unit_l, unit_w, product_height))
                units_drawn += 1
                x += unit_l
            if units_drawn >= min(units_per_layer, total_units):
                break
            y += unit_w

        # Add transparent bounding box to show full stack height
        stack_height = layers_per_pallet * product_height
        objects.append(create_box(0, 0, pallet_height_actual, pallet_length, pallet_width, stack_height, color='lightgray', opacity=0.1))

        fig3d = go.Figure(data=objects)
        fig3d.update_layout(
            scene=dict(
                xaxis_title='Length',
                yaxis_title='Width',
                zaxis_title='Height',
                aspectratio=dict(x=1, y=1, z=2),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
            title="3D Pallet Stack – Layer View + Stack Volume"
        )
        components.html(fig3d.to_html(), height=600)
