import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import uuid

# --- GOOGLE SHEETS CONNECTION ---
def connect_to_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("rahimia_instituate_qurbani_data").sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# --- FETCH DATA ---
def fetch_data():
    conn = connect_to_sheet()
    if conn:
        records = conn.get_all_records()
        return pd.DataFrame(records), conn
    return pd.DataFrame(), None

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rahimia Institute Portal", layout="wide", page_icon="🐄")

st.markdown("""
    <style>
    .main-head { font-size: 38px; color: #1E3A8A; text-align: center; font-weight: bold; padding: 15px; background: #f0f2f6; border-radius: 10px; margin-bottom: 20px; }
    .invoice-box { border: 2px dashed #1E3A8A; padding: 20px; border-radius: 15px; background: white; color: black; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-head">Rahimia Institute: Qurbani Management</div>', unsafe_allow_html=True)

# Load data at start
df, sheet_conn = fetch_data()

tab1, tab2 = st.tabs(["📝 Booking Form", "📊 Records & Inventory"])

with tab1:
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"📅 Date: {date.today().strftime('%d-%m-%Y')}")
            name = st.text_input("Contributor Name")
            whatsapp = st.text_input("WhatsApp Number")
            cnic = st.text_input("CNIC (Optional)")
        with c2:
            p_type = st.selectbox("Participation Type", ["Part (1/7 Cow)", "Full Cow", "Goat"])
            meat = st.selectbox("Meat Contribution", ["Keep for Self", "Donate to Rahimia Institute", "50/50 Split"])
            qty = st.number_input("Number of Shares / Animals", min_value=1, max_value=7)
        
        submitted = st.form_submit_button("Submit & Save")

    if submitted:
        if name and whatsapp:
            # Calculate Cow Number logic
            current_parts = 0
            if not df.empty and 'Type' in df.columns:
                current_parts = df[df['Type'] == "Part (1/7 Cow)"]['Qty'].astype(int).sum()
            
            cow_num = (current_parts // 7) + 1
            order_id = f"RI-{uuid.uuid4().hex[:5].upper()}"
            
            # Save to Sheet
            new_row = [order_id, str(date.today()), name, whatsapp, cnic, p_type, qty, meat, f"Cow-{cow_num}"]
            sheet_conn.append_row(new_row)
            
            st.success("✅ Saved to Google Sheets!")
            
            # Show Receipt
            st.markdown(f"""
            <div class="invoice-box">
                <h3 style="text-align:center;">RAHIMIA INSTITUTE RECEIPT</h3>
                <p><b>ID:</b> {order_id} | <b>Name:</b> {name}</p>
                <p><b>Booking:</b> {qty} x {p_type} (Cow #{cow_num})</p>
                <p><b>Meat:</b> {meat}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Force refresh so Tab 2 sees it
            st.button("Click to Refresh All Lists")
        else:
            st.error("Please enter Name and WhatsApp.")

with tab2:
    # RE-FETCH DATA ON TAB SWITCH
    df_fresh, _ = fetch_data()
    
    if not df_fresh.empty:
        st.subheader("Current Inventory")
        m1, m2 = st.columns(2)
        m1.metric("Total Entries", len(df_fresh))
        
        if 'Cow_Number' in df_fresh.columns:
            cow_choice = st.selectbox("Filter by Cow Number", ["All"] + list(df_fresh['Cow_Number'].unique()))
            display_df = df_fresh if cow_choice == "All" else df_fresh[df_fresh['Cow_Number'] == cow_choice]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_fresh, use_container_width=True)
            
        if st.button("🔄 Manual Sync"):
            st.rerun()
    else:
        st.info("No records found in the sheet yet.")
