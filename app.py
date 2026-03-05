import streamlit as st
import pandas as pd
import pdfrw
import zipfile
import io
import os
from datetime import datetime


ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'
'

def fill_pdf(template_path, output_path, data_dict):
    template = pdfrw.PdfReader(template_path)
    
    fields = template.Root.AcroForm.Fields
    for field in fields:
        key = field.T[1:-1]  # strip the parentheses
        if key in data_dict:
            field.update(
                pdfrw.PdfDict(V=data_dict[key])
            )
            field[pdfrw.PdfName.AP] = pdfrw.PdfDict()
    
    template.Root.AcroForm.update(
        pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))
    )
    writer = pdfrw.PdfWriter()
    writer.write(output_path, template)  # works with both file paths and buffers


def clean(val):
    if pd.isna(val):
        return ""
    return str(val)

password = st.text_input("Enter password", type="password")

if password != st.secrets["app_password"]:
    st.error("Incorrect password")
    st.stop()

st.title("Rent Increase Notice Generator")

excel_file = st.file_uploader("Upload Tenant Excel File", type=["xlsx"])

if excel_file:
    df = pd.read_excel(excel_file)
    st.success(f"{len(df)} tenants loaded")
    st.dataframe(df.head())

    if st.button("Generate Notices"):
        # Load template from repo
        template_path = "DEMO AUTOMATED PDF - RENT INCREASE NOTICE.pdf"
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for index, row in df.iterrows():
                data = {
                "Resident Name 2": clean(row["Tenant(s) Name"]),
                "Premises Address 2": clean(row["Property Address"]),
                "effective date": pd.to_datetime(row["New Rent Increase Start Date"]).strftime("%m/%d/%Y"),    
                "percent": f"{row['% Increase'] * 100:.2f}%",
                "Increased amount": f"{row['Total Increase $']:.2f}",
                "Total amount": f"{row['New Monthly Rate']:.2f}",
                "Text2": f"{row['Amount of Increase']:.2f}",
                "Text3": f"{row['New Rent Amount']:.2f}",
                "Text5": f"{row['Amount of Increase2']:.2f}",
                "Text6": f"{row['New Fees Amount']:.2f}",
                "Text16": f"{row['New Monthly Rate']:.2f}",


            }   

                # Write PDF to memory instead of disk
                pdf_buffer = io.BytesIO()
                fill_pdf(template_path, pdf_buffer, data)
                
                safe_name = clean(row["Tenant(s) Name"]).replace(" ", "_")
                zip_file.writestr(f"notice_{safe_name}.pdf", pdf_buffer.getvalue())

        zip_buffer.seek(0)
        st.download_button(
            label="Download All Notices (ZIP)",
            data=zip_buffer,
            file_name=f"notices_{datetime.today().strftime('%Y%m%d')}.zip",
            mime="application/zip"
        )