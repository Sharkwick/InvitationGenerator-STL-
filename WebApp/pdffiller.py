import streamlit as st
import pandas as pd
import tempfile
import os
import zipfile
from fillpdf import fillpdfs
import fitz  # PyMuPDF

st.set_page_config(page_title="Bulk PDF to JPEG Generator", layout="centered")

st.title("🖼️ Bulk PDF to JPEG Generator")
st.markdown("Upload a fillable PDF template and a CSV file. Map fields and download all filled PDFs as JPEG images.")

# Upload PDF template
template_file = st.file_uploader("Upload Fillable PDF Template", type=["pdf"])
# Upload CSV file
csv_file = st.file_uploader("Upload CSV File", type=["csv"])

if template_file and csv_file:
    # Save template to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_template:
        tmp_template.write(template_file.read())
        template_path = tmp_template.name

    # Read CSV
    df = pd.read_csv(csv_file)

    # Extract form fields from template
    form_fields = fillpdfs.get_form_fields(template_path)
    field_names = list(form_fields.keys())

    st.subheader("🧩 Field Mapping")
    st.markdown("Map CSV columns to PDF form fields:")

    mapping = {}
    for field in field_names:
        selected_column = st.selectbox(f"Map PDF field '{field}' to CSV column:", options=["--None--"] + list(df.columns), key=field)
        if selected_column != "--None--":
            mapping[field] = selected_column

    flatten = st.checkbox("🔒 Flatten PDFs before converting to JPEG", value=True)

    if st.button("Generate JPEGs"):
        with tempfile.TemporaryDirectory() as tmp_dir:
            jpeg_paths = []

            for index, row in df.iterrows():
                data_dict = {pdf_field: str(row[csv_col]) for pdf_field, csv_col in mapping.items()}
                filled_pdf_path = os.path.join(tmp_dir, f"{row[mapping[field_names[0]]]}_filled.pdf")

                # Fill and optionally flatten
                fillpdfs.write_fillable_pdf(template_path, filled_pdf_path, data_dict)
                if flatten:
                    fillpdfs.flatten_pdf(filled_pdf_path, filled_pdf_path)

                # Convert to JPEG using PyMuPDF
                doc = fitz.open(filled_pdf_path)
                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=200)
                    jpeg_path = os.path.join(tmp_dir, f"{row[mapping[field_names[0]]]}_page{i+1}.jpg")
                    pix.save(jpeg_path)
                    jpeg_paths.append(jpeg_path)

            # Create ZIP
            zip_path = os.path.join(tmp_dir, "filled_jpegs.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for jpeg in jpeg_paths:
                    zipf.write(jpeg, arcname=os.path.basename(jpeg))

            with open(zip_path, "rb") as f:
                st.download_button("📥 Download All JPEGs as ZIP", f, file_name="filled_jpegs.zip", mime="application/zip")