import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import uuid

# --- GOOGLE SHEETS CONNECTION (SECURE VERSION) ---
def connect_to_sheet():
    try:
        # Pulls from Streamlit Cloud Secrets
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Ensure your Google Sheet is named exactly this
        sheet = client.open("rahimia_instituate_qurbani_data").sheet1
        return sheet
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        return None

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rahimia Institute Portal", layout="wide", page_icon="🐄")

# Custom UI Styling
st.markdown("""
    <style>
    .main-head { font-size: 38px; color: #1E3A8A; text-align: center; font-weight: bold; padding: 15px; border-radius: 10px; background: #f0f2f6; margin-bottom: 20px; border: 1px solid #d1d5db; }
    .invoice-box { border: 2px dashed #1E3A8A; padding: 25px; border-radius: 15px; background-color: #ffffff; color: #1e293b; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-head">Rahimia Institute: Qurbani Management System</div>', unsafe_allow_html=True)

# --- APP LOGIC ---
tab1, tab2 = st.tabs(["📝 Booking & Invoice", "📊 Cow Tracking & Records"])

with tab1:
    st.subheader("New Entry Form")
    
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        
        with c1:
            # AUTO DATE - No user input needed
            today_date = date.today()
            st.info(f"📅 Booking Date: **{today_date.strftime('%d-%m-%Y')}** (Set Automatically)")
            
            cust_name = st.text_input("Contributor Name", placeholder="e.g. Muhammad Ahmad")
            phone = st.text_input("WhatsApp Number", placeholder="03XXXXXXXXX")
            cnic = st.text_input("CNIC (Optional)", placeholder="42101-XXXXXXX-X")
        
        with c2:
            share_type = st.selectbox("Participation Type", ["Part (1/7 Cow)", "Full Cow", "Goat"])
            meat_dest = st.selectbox("Meat Contribution", ["Keep for Self", "Donate to Rahimia Institute", "50% Self / 50% Donation"])
            # RENAMED FIELD
            qty = st.number_input("Number of Shares / Animals", min_value=1, max_value=7, value=1, help="Select how many parts or full animals")
        
        submit = st.form_submit_button("Submit & Generate Receipt")

    if submit:
        if not cust_name or not phone:
            st.warning("⚠️ Please fill in Name and Phone Number.")
        else:
            sheet = connect_to_sheet()
            if sheet:
                # Generate tracking data
                order_id = f"RI-{uuid.uuid4().hex[:6].upper()}"
                
                # Logic to assign a Cow Number
                existing_data = pd.DataFrame(sheet.get_all_records())
                current_total_parts = 0
                if not existing_data.empty:
                    # Sum parts specifically from "Part" bookings
                    current_total_parts = existing_data[existing_data['Type'] == "Part (1/7 Cow)"]['Qty'].astype(int).sum()
                
                cow_number = (current_total_parts // 7) + 1
                
                # Prepare data for Google Sheet
                row = [order_id, str(today_date), cust_name, phone, cnic, share_type, qty, meat_dest, f"Cow-{cow_number}"]
                sheet.append_row(row)
                
                # VISUAL INVOICE
                st.success("🎉 Record Saved Successfully!")
                st.markdown("### 📄 Digital Receipt")
                st.write("Take a screenshot to send to the customer via WhatsApp.")
                
                invoice_html = f"""
                <div class="invoice-box">
                    <h2 style="text-align:center; color:#1E3A8A; margin-top:0;">RAHIMIA INSTITUTE</h2>
                    <p style="text-align:center; font-weight:bold;">Qurbani Registration Receipt 2026</p>
                    <hr>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span><b>Receipt ID:</b> {order_id}</span>
                        <span><b>Date:</b> {today_date}</span>
                    </div>
                    <p><b>Name:</b> {cust_name}</p>
                    <p><b>WhatsApp:</b> {phone}</p>
                    <p><b>Participation:</b> {qty} x {share_type}</p>
                    <p><b>Assigned Cow:</b> Cow #{cow_number}</p>
                    <p><b>Meat Instruction:</b> {meat_dest}</p>
                    <hr>
                    <p style="text-align:center; font-size:12px; color:gray;">Thank you for your contribution. May Allah accept your sacrifice.</p>
                </div>
                """
                st.markdown(invoice_html, unsafe_allow_html=True)

with tab2:
    st.subheader("Inventory Management")
    
    sheet = connect_to_sheet()
    if sheet:
        data = pd.DataFrame(sheet.get_all_records())
        
        if not data.empty:
            # Summary Metrics
            full_cows = data[data['Type'] == "Full Cow"].shape[0]
            total_shares = data[data['Type'] == "Part (1/7 Cow)"]['Qty'].astype(int).sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Bookings", len(data))
            m2.metric("Full Cows Booked", full_cows)
            m3.metric("Shares Progress", f"{total_shares % 7}/7 of Cow-{(total_shares // 7) + 1}")
            
            st.divider()
            
            # COW FILTER SYSTEM
            st.write("### 🐄 Cow-wise Contributor List")
            cow_list = sorted(data['Cow_Number'].unique())
            selected_cow = st.selectbox("Select Cow Number to filter:", ["View All"] + list(cow_list))
            
            display_df = data if selected_cow == "View All" else data[data['Cow_Number'] == selected_cow]
            
            # User Friendly Table
            st.dataframe(
                display_df[['ID', 'Name', 'Type', 'Qty', 'Cow_Number', 'Meat_Contribution', 'Phone']],
                use_container_width=True,
                hide_index=True
            )
            
            # CSV Download
            st.download_button("📩 Download Full Record", data.to_csv(index=False), "Rahimia_Records.csv", "text/csv")
        else:
            st.info("No bookings recorded yet. Waiting for first entry.")
