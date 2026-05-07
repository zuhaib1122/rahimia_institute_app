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
    .stMetric { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-head">Rahimia Institute: Qurbani Management</div>', unsafe_allow_html=True)

df, sheet_conn = fetch_data()

tab1, tab2 = st.tabs(["📝 Booking Form", "📊 Cow Inventory & Parts"])

with tab1:
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"📅 Date: {date.today().strftime('%d-%m-%Y')}")
            name = st.text_input("Contributor Name")
            whatsapp = st.text_input("WhatsApp Number")
            cnic = st.text_input("CNIC (Optional)")
        with c2:
            p_type = st.selectbox("Participation Type", ["Cow Share", "Full Cow", "Goat"])
            meat = st.selectbox("Meat Contribution", ["Keep for Self", "Donate to Rahimia Institute", "50/50 Split"])
            qty = st.number_input("How many Shares/Animals?", min_value=1, max_value=70, value=1)
        
        submitted = st.form_submit_button("Confirm & Save Booking")

    if submitted:
        if name and whatsapp:
            # 1. Calculate Current Global Share Count
            # We filter for 'Cow Share' or 'Full Cow' because Goats don't have parts
            shares_df = df[df['Type'].isin(['Cow Share', 'Full Cow'])] if not df.empty else pd.DataFrame()
            current_total_parts = len(shares_df)
            
            new_rows = []
            # Determine how many "parts" to add
            loops = (qty * 7) if p_type == "Full Cow" else qty
            if p_type == "Goat": loops = 1 # Goats are separate

            for i in range(loops):
                current_total_parts += 1
                cow_num = ((current_total_parts - 1) // 7) + 1
                part_num = ((current_total_parts - 1) % 7) + 1
                order_id = f"RI-{uuid.uuid4().hex[:5].upper()}"
                
                # Format: ID | Date | Name | Phone | CNIC | Type | Qty | Meat | Cow | Part_No
                assigned_cow = f"Cow-{cow_num}" if p_type != "Goat" else "Goat-N/A"
                assigned_part = f"Part-{part_num}" if p_type != "Goat" else "1/1"
                
                row = [order_id, str(date.today()), name, whatsapp, cnic, p_type, 1, meat, assigned_cow, assigned_part]
                new_rows.append(row)
            
            # Save to Sheet
            sheet_conn.append_rows(new_rows)
            st.success(f"✅ Successfully booked {qty} {p_type}(s). Total entries created: {len(new_rows)}")
            
            # Show Simple Receipt
            st.markdown(f"""
            <div class="invoice-box">
                <h3 style="text-align:center;">RAHIMIA INSTITUTE RECEIPT</h3>
                <p><b>Name:</b> {name} | <b>WhatsApp:</b> {whatsapp}</p>
                <p><b>Total {p_type}s:</b> {qty}</p>
                <p><b>Last Assigned:</b> {new_rows[-1][-2]} ({new_rows[-1][-1]})</p>
                <hr>
                <p style="text-align:center; font-size:12px;">Data synced. Please switch to Tab 2 to see the Cow Chart.</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("🔄 Update Records")
        else:
            st.error("Please enter Name and WhatsApp.")

with tab2:
    df_fresh, _ = fetch_data()
    
    if not df_fresh.empty:
        # Filter out Goats for the Cow-specific view
        cow_df = df_fresh[df_fresh['Cow_Number'].str.contains("Cow", na=False)]
        
        st.subheader("🐄 Detailed Cow Share Chart")
        
        # Metrics
        total_parts_filled = len(cow_df)
        full_cows = total_parts_filled // 7
        remaining_in_last = total_parts_filled % 7
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Shares Filled", total_parts_filled)
        m2.metric("Complete Cows", full_cows)
        m3.metric("Current Cow Slots", f"{remaining_in_last}/7")
        
        st.divider()

        # Selection Filter
        cow_list = sorted(cow_df['Cow_Number'].unique(), key=lambda x: int(x.split('-')[1]))
        selected_cow = st.selectbox("🎯 Select Cow to View All 7 Parts:", cow_list)
        
        # Display the specific Cow's Breakdown
        display_df = cow_df[cow_df['Cow_Number'] == selected_cow].copy()
        # Sort by Part Number
        display_df['sort_val'] = display_df['Part_Number'].apply(lambda x: int(x.split('-')[1]))
        display_df = display_df.sort_values('sort_val')
        
        st.write(f"### {selected_cow} Contributors")
        st.table(display_df[['Part_Number', 'Name', 'ID', 'Phone', 'CNIC', 'Meat_Contribution']])
        
        if st.button("🔄 Sync Live Data"):
            st.rerun()
    else:
        st.info("No records found yet.")
