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

    st.subheader("📊 Summary")
    st.write(f"**Units per Layer:** {units_per_layer}")
    st.write(f"**Layers per Pallet:** {layers_per_pallet}")
    st.write(f"**Max Units per Pallet:** {max_units_per_pallet}")
    st.write(f"**Total Pallets Needed:** {total_pallets_needed}")
    st.write(f"**Volume Utilization (one pallet):** {volume_utilization:.1f}%")
    st.write(f"**Total Shipment Weight:** {total_weight:.1f} {weight_unit}")

        # Additional user inputs for real-world pallet estimates
    st.markdown("---")
    st.subheader("📏 Real-World Shipping Estimate")
    pallet_base_weight = st.number_input("Pallet Base Weight (avg ~38 lbs)", value=38.0)
    wrap_weight = st.number_input("Wrapping Material Weight (avg ~2 lbs)", value=2.0)

    total_stack_height = layers_per_pallet * product_height + 5.5  # includes pallet
    total_weight_gross = total_weight + pallet_base_weight + wrap_weight

    dims_string = f"{pallet_length} × {pallet_width} × {int(total_stack_height)} {unit}"

    st.markdown(f"**Estimated Palletized Dimensions:** {dims_string}")
    st.markdown(f"**Estimated Gross Shipping Weight:** {total_weight_gross:.1f} {weight_unit}")

    summary_df = pd.DataFrame({
        "Metric": ["Units per Layer", "Layers per Pallet", "Max Units per Pallet", "Total Pallets Needed", "Volume Utilization (%)", f"Total Weight ({weight_unit})"],
        "Value": [units_per_layer, layers_per_pallet, max_units_per_pallet, total_pallets_needed, round(volume_utilization, 1), round(total_weight, 1)]
    })"],
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
        st.subheader("🖼 Static 3D Pallet Render")
        from PIL import Image
        static_img_path = "/mnt/data/simplified_3d_pallet_render.png"
        try:
            img = Image.open(static_img_path)
            st.image(img, caption="Static 3D Pallet with Boxes")
            with open(static_img_path, "rb") as f:
                st.download_button("📥 Download Render (PNG)", f, file_name="pallet_render.png", mime="image/png")
        except FileNotFoundError:
            st.warning("Render not available yet. Please generate or upload the image.")
