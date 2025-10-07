import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import zipfile
import io
import os

st.set_page_config(page_title="Invitation Generator", layout="centered")
st.title("🎉 Invitation Generator")

# Upload template image
template_file = st.file_uploader("Upload Invitation Template Image", type=["png", "jpg", "jpeg"])
# Upload CSV
csv_file = st.file_uploader("Upload CSV with Names", type=["csv"])

# Font customization
font_size = st.slider("Font Size", min_value=10, max_value=100, value=40)
font_color = st.color_picker("Font Color", "#000000")

# Vertical position and horizontal alignment
y_percent = st.slider("Y Position (%)", min_value=0, max_value=100, value=50)
alignment = st.selectbox("Horizontal Alignment", ["Left", "Center", "Right"])

# Preview name
preview_name = st.text_input("Preview Name", value="Sample Name")

# Load default font
def load_default_font(font_size):
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to DejaVuSans (bundled with Pillow)
        fallback_path = os.path.join(os.path.dirname(ImageFont.__file__), "fonts", "DejaVuSans.ttf")
        return ImageFont.truetype(fallback_path, font_size)

# Calculate X position based on alignment
def calculate_x_position(alignment, image_width, text_width, margin=10):
    if alignment == "Left":
        return margin
    elif alignment == "Center":
        return (image_width - text_width) // 2
    elif alignment == "Right":
        return image_width - text_width - margin

# Show live preview
if template_file:
    try:
        template = Image.open(template_file).convert("RGB")
        width, height = template.size
        y_pos = int((y_percent / 100) * height)

        preview = template.copy()
        draw = ImageDraw.Draw(preview)
        font = load_default_font(font_size)

        bbox = draw.textbbox((0, 0), preview_name, font=font)
        text_width = bbox[2] - bbox[0]
        x_pos = calculate_x_position(alignment, width, text_width)

        draw.text((x_pos, y_pos), preview_name, font=font, fill=font_color)
        st.image(preview, caption="Live Preview", use_container_width=True)

    except Exception as e:
        st.error(f"Preview error: {e}")

# Generate and zip invitations
if st.button("Generate & Download Invitations"):
    if not template_file or not csv_file:
        st.error("Please upload both template image and CSV file.")
    else:
        try:
            df = pd.read_csv(csv_file)
            names = df.iloc[:, 0].dropna().tolist()
            font = load_default_font(font_size)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for name in names:
                    img = template.copy()
                    draw = ImageDraw.Draw(img)

                    bbox = draw.textbbox((0, 0), name, font=font)
                    text_width = bbox[2] - bbox[0]
                    x_pos = calculate_x_position(alignment, width, text_width)
                    y_pos = int((y_percent / 100) * height)

                    draw.text((x_pos, y_pos), name, font=font, fill=font_color)

                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="JPEG")
                    zipf.writestr(f"{name}.jpg", img_bytes.getvalue())

            zip_buffer.seek(0)
            st.success(f"✅ Generated {len(names)} invitations.")
            st.download_button(
                label="📦 Download ZIP",
                data=zip_buffer,
                file_name="invitations.zip",
                mime="application/zip"
            )

        except Exception as e:
            st.error(f"Generation error: {e}")