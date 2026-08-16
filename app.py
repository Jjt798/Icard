import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from card import create_id_card
from utils import load_student_sheets
 
st.set_page_config(
    page_title="School ID Card Generator",
    page_icon="🎓",
    layout="wide"
)
 
st.markdown("""
<style>
.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}
div.stDownloadButton > button{
    width:100%;
    height:42px;
    border-radius:8px;
    font-size:16px;
    background-color:#1565C0;
    color:white;
    border:none;
}
div.stDownloadButton > button:hover{
    background-color:#0D47A1;
    color:white;
    border:none;
}
div.stDownloadButton > button:active{
    background-color:#0D47A1;
    color:white;
}
[data-testid="stImage"] img{
    border-radius:10px;
    box-shadow:0 4px 18px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)
 
st.title("🎓 School ID Card Generator")
 
 
def _clean(value):
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:
            return ""
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, str) and value.strip() == "":
        return ""
    return value
 
 
uploaded_file = st.file_uploader(
    "📄 Upload Student Excel File",
    type=["xlsx"]
)
 
if uploaded_file is None:
    st.info("Please upload an Excel file to continue.")
    st.stop()
 
with st.spinner("Reading Excel file..."):
    try:
        df, used_sheets, skipped_sheets = load_student_sheets(uploaded_file)
    except Exception as e:
        st.error(f"Could not read this Excel file. Please check the format and try again.\n\n{e}")
        st.stop()
 
if df.empty:
    st.warning("This file doesn't contain any student rows.")
    st.stop()
 
sheet_note = f" across {len(used_sheets)} sheets ({', '.join(used_sheets)})" if len(used_sheets) > 1 else ""
st.success(f"✅ {len(df)} Students Loaded Successfully{sheet_note}")
if skipped_sheets:
    st.caption(f"Skipped empty sheet(s): {', '.join(skipped_sheets)}")
 
columns = [c for c in df.columns.tolist() if c != "Sheet"]
 
with st.sidebar:
    st.header("⚙️ Setup")
 
    with st.expander("🏫 School Details", expanded=True):
        school_name = st.text_input("School Name")
        school_address = st.text_area("School Address")
        session = st.text_input("Session")
 
        school_logo = st.file_uploader(
            "Upload School Logo",
            type=["png", "jpg", "jpeg"]
        )
        if school_logo is not None:
            st.image(school_logo, width=60)
 
        principal_signature = st.file_uploader(
            "Upload Principal Signature",
            type=["png"]
        )
        if principal_signature is not None:
            st.image(principal_signature, width=100)
 
        school = {
            "name": school_name,
            "address": school_address,
            "logo": school_logo,
            "signature": principal_signature,
            "session": session
        }
 
    with st.expander("📄 Student Data Mapping", expanded=True):
        mapping = {}
        mapping["name"] = st.selectbox("Name", columns, key="map_name")
        mapping["father"] = st.selectbox("Father's Name", columns, key="map_father")
        mapping["mother"] = st.selectbox("Mother's Name", columns, key="map_mother")
        mapping["class"] = st.selectbox("Class", columns, key="map_class")
        mapping["sr"] = st.selectbox("Admission Number / SR Number", columns, key="map_sr")
        mapping["dob"] = st.selectbox("Date of Birth", columns, key="map_dob")
        mapping["phone"] = st.selectbox("Phone Number", columns, key="map_phone")
        student_address = st.text_area("Student Address")
 
        photo_default = columns.index("Photo") if "Photo" in columns else 0
        mapping["photo"] = st.selectbox(
            "Student Photo", columns, index=photo_default, key="map_photo"
        )
        if "Photo" in columns:
            st.caption("📸 Photos embedded in the Excel sheet were found and matched to students automatically.")
 
        chosen = list(mapping.values())
        duplicates = {c for c in chosen if chosen.count(c) > 1}
        if duplicates:
            st.warning(
                "⚠️ The same column is mapped to more than one field: "
                + ", ".join(sorted(duplicates))
            )
 
student_sr_number = sorted(df[mapping["sr"]].dropna().astype(str).unique())
 
if not student_sr_number:
    st.warning("No admission number found in the selected column.")
    st.stop()
 
student_sr_number = st.selectbox("Select Admission Number", student_sr_number)
 
matches = df[df[mapping["sr"]].astype(str) == student_sr_number]
row = matches.iloc[0]
 
try:
    dob = pd.to_datetime(row[mapping["dob"]]).strftime("%d-%m-%Y")
except Exception:
    dob = str(_clean(row[mapping["dob"]]))
 
student = {
    "sr": _clean(row[mapping["sr"]]),
    "name": _clean(row[mapping["name"]]),
    "father": _clean(row[mapping["father"]]),
    "mother": _clean(row[mapping["mother"]]),
    "class": _clean(row[mapping["class"]]),
    "dob": dob,
    "phone": _clean(row[mapping["phone"]]),
    "photo": row[mapping["photo"]],
    "address": student_address
}
 
with st.spinner("Generating ID card..."):
    try:
        card = create_id_card(student, school)
    except Exception as e:
        st.error(f"Something went wrong while generating the ID card.\n\n{e}")
        st.stop()
 
left, right = st.columns([1, 2])
 
with left:
    st.subheader("📋 Student Details")
    st.write(f"**SR Number :** {student['sr'] or '—'}")
    st.write(f"**Student Name :** {student['name'] or '—'}")
    st.write(f"**Father's Name :** {student['father'] or '—'}")
    st.write(f"**Mother's Name :** {student['mother'] or '—'}")
    st.write(f"**Class :** {student['class'] or '—'}")
    st.write(f"**Date of Birth :** {student['dob'] or '—'}")
    st.write(f"**Phone Number :** {student['phone'] or '—'}")
    st.write(f"**Student Address :** {student_address or '—'}")
 
with right:
    st.subheader("🪪 ID Card Preview")
    st.image(card, use_container_width=True)
 
    buffer = BytesIO()
    card.save(buffer, format="JPEG", quality=95)
    img_bytes = buffer.getvalue()
 
    safe_sr = str(student['sr'] or "card").strip().replace(" ", "_")
    safe_name = str(student['name'] or "student").strip().replace(" ", "_")
    file_name = f"{safe_sr}_{safe_name}.jpg"
 
    download_col, print_col = st.columns(2)
 
    with download_col:
        st.download_button(
            label="📥 Download",
            data=img_bytes,
            file_name=file_name,
            mime="image/jpeg",
            use_container_width=True
        )
 
    with print_col:
        b64 = base64.b64encode(img_bytes).decode()
 
        print_html = f"""
        <script>
        function printCard(){{
            var win = window.open("", "_blank");
 
            win.document.write(`
            <html>
            <head>
                <title>Print ID Card</title>
                <style>
                    body{{
                        margin:0;
                        display:flex;
                        justify-content:center;
                        align-items:center;
                        background:white;
                    }}
                    img{{
                        width:420px;
                    }}
                </style>
            </head>
            <body>
                <img src="data:image/jpeg;base64,{b64}"
                    onload="window.print();window.onafterprint=function(){{window.close();}}">
            </body>
            </html>
            `);
 
            win.document.close();
        }}
        </script>
 
        <button onclick="printCard()"
            style="
                width:100%;
                height: 35px;
                border:none;
                border-radius:8px;
                background:#1565C0;
                color:white;
                font-size:16px;
                cursor:pointer;">
            🖨️ Print
        </button>
        """
 
        st.components.v1.html(print_html, height=42)
 
st.markdown("---")
 









