import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import uuid

# --- GOOGLE SHEETS SETUP ---
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    # Open the sheet by name
    sheet = client.open("rahimia_instituate_qurbani_data").sheet1
    return sheet

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rahimia Institute Portal", layout="wide")

# Custom CSS for a Premium Look
st.markdown("""
    <style>
    .main-head { font-size: 38px; color: #1E3A8A; text-align: center; font-weight: bold; padding: 10px; border-radius: 10px; background: #f0f2f6; margin-bottom: 20px; }
    .invoice-box { border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #ffffff; color: #333; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-head">Rahimia Institute Qurbani Management</div>', unsafe_allow_html=True)

# --- APP LOGIC ---
tab1, tab2 = st.tabs(["📋 Registration & Invoice", "🐄 Cow Management & Tracking"])

with tab1:
    st.subheader("New Booking Entry")
    
    with st.form("booking_form"):
        c1, c2 = st.columns(2)
        with c1:
            booking_date = st.date_input("Date", date.today())
            cust_name = st.text_input("Contributor Name")
            phone = st.text_input("WhatsApp Number")
            cnic = st.text_input("CNIC")
        
        with c2:
            share_type = st.selectbox("Participation Type", ["Part (1/7 Cow)", "Full Cow", "Goat"])
            meat_dest = st.selectbox("Meat Contribution", ["Keep for Self", "Donate to Rahimia Institute", "50% Self / 50% Donation"])
            qty = st.number_input("Quantity", min_value=1, max_value=7, value=1)
        
        submit = st.form_submit_button("Submit & Generate Invoice")

    if submit:
        try:
            # 1. Connect and Save to Sheet
            sheet = connect_to_sheet()
            order_id = f"RI-{uuid.uuid4().hex[:6].upper()}"
            
            # Logic to assign a Cow Number automatically
            existing_data = pd.DataFrame(sheet.get_all_records())
            current_total_parts = existing_data[existing_data['Type'] == "Part (1/7 Cow)"]['Qty'].astype(int).sum() if not existing_data.empty else 0
            cow_number = (current_total_parts // 7) + 1
            
            row = [order_id, str(booking_date), cust_name, phone, cnic, share_type, qty, meat_dest, f"Cow-{cow_number}"]
            sheet.append_row(row)
            
            # 2. Display Visual Invoice
            st.success("Data Saved to Google Sheets!")
            st.markdown("### 📄 Booking Invoice")
            st.info("💡 Tip: Take a screenshot of the box below to send to the customer via WhatsApp.")
            
            invoice_html = f"""
            <div class="invoice-box">
                <h2 style="text-align:center; color:#1E3A8A;">RAHIMIA INSTITUTE</h2>
                <p style="text-align:center;">OFFICIAL QURBANI RECEIPT 2026</p>
                <hr>
                <table style="width:100%">
                    <tr><td><b>Order ID:</b> {order_id}</td><td><b>Date:</b> {booking_date}</td></tr>
                    <tr><td><b>Customer:</b> {cust_name}</td><td><b>Phone:</b> {phone}</td></tr>
                    <tr><td><b>CNIC:</b> {cnic}</td><td><b>Assigned:</b> Cow #{cow_number}</td></tr>
                    <tr><td><b>Type:</b> {share_type}</td><td><b>Meat:</b> {meat_dest}</td></tr>
                </table>
                <hr>
                <p style="text-align:center; font-size:12px;">This is a computer-generated receipt.</p>
            </div>
            """
            st.markdown(invoice_html, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Connection Error: {e}. Please check your credentials.json")

with tab2:
    st.subheader("Inventory & Contributor Search")
    
    try:
        sheet = connect_to_sheet()
        data = pd.DataFrame(sheet.get_all_records())
        
        if not data.empty:
            # --- FILTER SECTION ---
            st.write("### 🔍 Filter by Cow Number")
            all_cows = sorted(data['Cow_Number'].unique())
            selected_cow = st.selectbox("Select Cow to View Contributors:", ["All Cows"] + list(all_cows))
            
            filtered_df = data if selected_cow == "All Cows" else data[data['Cow_Number'] == selected_cow]
            
            # Display metrics
            m1, m2 = st.columns(2)
            m1.metric("Total Contributors", len(filtered_df))
            m2.metric("Target Cow", selected_cow)
            
            # Clean Table View
            st.table(filtered_df[['ID', 'Name', 'Type', 'Qty', 'Meat_Contribution', 'Cow_Number']])
            
            st.download_button("Download Report", data.to_csv(index=False), "Rahimia_Qurbani_Report.csv")
            
        else:
            st.warning("No data found in the Google Sheet.")
    except:
        st.info("Awaiting connection or data entry...")
