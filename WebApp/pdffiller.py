import streamlit as st
import pandas as pd
import tempfile
import os
import zipfile
from fillpdf import fillpdfs

st.set_page_config(page_title="Bulk PDF Filler", layout="centered")

st.title("📄 Bulk PDF Filler")
st.markdown("Upload a fillable PDF template and a CSV file. Map fields and download all filled PDFs.")

template_file = st.file_uploader("Upload Fillable PDF Template", type=["pdf"])
csv_file = st.file_uploader("Upload CSV File", type=["csv"])

if template_file and csv_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_template:
        tmp_template.write(template_file.read())
        template_path = tmp_template.name

    df = pd.read_csv(csv_file)

    form_fields = fillpdfs.get_form_fields(template_path)
    field_names = list(form_fields.keys())

    st.subheader("Field Mapping")
    st.markdown("Map CSV columns to PDF form fields:")

    mapping = {}
    for field in field_names:
        selected_column = st.selectbox(f"Map PDF field '{field}' to CSV column:", options=["--None--"] + list(df.columns), key=field)
        if selected_column != "--None--":
            mapping[field] = selected_column

    if st.button("Generate PDFs"):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_paths = []

            for index, row in df.iterrows():
                data_dict = {pdf_field: str(row[csv_col]) for pdf_field, csv_col in mapping.items()}
                output_path = os.path.join(tmp_dir, f"{row[mapping[field_names[0]]]}_filled.pdf")

                fillpdfs.write_fillable_pdf(template_path, output_path, data_dict)
                fillpdfs.flatten_pdf(output_path, output_path)
                pdf_paths.append(output_path)

            zip_path = os.path.join(tmp_dir, "filled_pdfs.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for pdf in pdf_paths:
                    zipf.write(pdf, arcname=os.path.basename(pdf))

            with open(zip_path, "rb") as f:
                st.download_button("📥 Download All PDFs as ZIP", f, file_name="filled_pdfs.zip", mime="application/zip")