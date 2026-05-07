import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import uuid

# --- GOOGLE SHEETS CONNECTION ---
def connect_to_sheet():
    try:
        # Uses Streamlit Secrets - ensures no 'credentials.json' file is needed
        creds_dict = st.secrets["gcp_service_account"] 
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("rahimia_instituate_qurbani_data").sheet1
        
        # Auto-Header Fix: Ensures the sheet structure is perfect
        expected = ["ID", "Date", "Name", "Phone", "CNIC", "Type", "Qty", "Meat_Contribution", "Cow_Number", "Part_Number"]
        try:
            first_row = sheet.row_values(1)
            if not first_row or first_row != expected:
                sheet.insert_row(expected, 1)
        except:
            sheet.insert_row(expected, 1)
            
        return sheet
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

def fetch_data(sheet):
    if sheet:
        try:
            records = sheet.get_all_records()
            return pd.DataFrame(records)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rahimia Institute Portal", layout="wide", page_icon="🐄")

st.markdown("""
    <style>
    .main-head { font-size: 38px; color: #1E3A8A; text-align: center; font-weight: bold; padding: 15px; background: #f0f2f6; border-radius: 10px; margin-bottom: 20px; border: 1px solid #d1d5db; }
    .invoice-box { border: 3px solid #1E3A8A; padding: 25px; border-radius: 15px; background-color: #ffffff; color: #000000; box-shadow: 10px 10px 5px #eeeeee; }
    .slot-highlight { background-color: #f0f4f8; padding: 10px; border-radius: 5px; border-left: 5px solid #1E3A8A; font-family: monospace; font-size: 18px; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-head">Rahimia Institute: Qurbani Management</div>', unsafe_allow_html=True)

sheet_conn = connect_to_sheet()

tab1, tab2 = st.tabs(["📝 Booking Form", "📊 Cow Inventory & Parts"])

with ta
    if 'last_receipt' not in st.session_state:
        st.session_state.last_receipt = None

    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"📅 Date: {date.today().strftime('%d-%m-%Y')}")
            name = st.text_input("Contributor Name")
            whatsapp = st.text_input("WhatsApp Number")
            cnic = st.text_input("CNIC (Optional)")
        with c2:
            p_type = st.selectbox("Participation Type", ["Cow Share", "Full Cow"])
            meat = st.selectbox("Charity Decision", ["Keep for Self", "Donate to Rahimia Institute"])
            qty = st.number_input("How many Shares/Animals?", min_value=1, max_value=7, value=1)
        
        submitted = st.form_submit_button("Confirm & Save Booking")

    if submitted:
        if name and whatsapp:
            df = fetch_data(sheet_conn)
            # Safe filter for cow parts
            if not df.empty and 'Cow_Number' in df.columns:
                cow_parts_df = df[df['Cow_Number'].astype(str).str.contains("Cow", na=False)]
            else:
                cow_parts_df = pd.DataFrame()
                
            current_total_parts = len(cow_parts_df)
            new_rows, receipt_slots = [], []
            
            loops = (qty * 7) if p_type == "Full Cow" else qty
            if p_type == "Goat": loops = 1

            for i in range(loops):
                current_total_parts += 1
                cow_num = ((current_total_parts - 1) // 7) + 1
                part_num = ((current_total_parts - 1) % 7) + 1
                order_id = f"RI-{uuid.uuid4().hex[:5].upper()}"
                
                assigned_cow = f"Cow-{cow_num}" if p_type != "Goat" else "Goat-N/A"
                assigned_part = f"Part-{part_num}" if p_type != "Goat" else "1/1"
                
                if p_type != "Goat":
                    receipt_slots.append(f"C{cow_num}-P{part_num}")
                
                row = [order_id, str(date.today()), name, whatsapp, cnic, p_type, 1, meat, assigned_cow, assigned_part]
                new_rows.append(row)
            
            sheet_conn.append_rows(new_rows)
            st.session_state.last_receipt = {
                "name": name, "whatsapp": whatsapp, "cnic": cnic if cnic else "N/A",
                "qty": qty, "p_type": p_type, "date": date.today().strftime('%d-%m-%Y'),
                "slots": ", ".join(receipt_slots) if receipt_slots else "Goat Booking"
            }
            st.rerun()
        else:
            st.error("⚠️ Please enter Name and WhatsApp.")

    if st.session_state.last_receipt:
        res = st.session_state.last_receipt
        st.success("✅ Recorded Successfully!")
        st.markdown(f"""
            <div class="invoice-box">
                <h2 style="text-align:center; color:#1E3A8A; margin-bottom:0;">RAHIMIA INSTITUTE</h2>
                <hr><p><b>Contributor:</b> {res['name']}</p>
                <p><b>WhatsApp:</b> {res['whatsapp']}</p>
                <p><b>Booking:</b> {res['qty']} : {res['p_type']}</p>
                <div class="slot-highlight"><b>Assigned Slots:</b><br>{res['slots']}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("New Booking"):
            st.session_state.last_receipt = None
            st.rerun()

with tab2:
    df_fresh = fetch_data(sheet_conn)
    if not df_fresh.empty and 'Cow_Number' in df_fresh.columns:
        cow_df = df_fresh[df_fresh['Cow_Number'].astype(str).str.contains("Cow", na=False)]
        
        if not cow_df.empty:
            st.subheader("🐄 Cow Allocation Chart")
            
            # --- SAFE SORTING LOGIC ---
            def get_num(val):
                try: return int(str(val).split('-')[1])
                except: return 0

            cow_list = sorted(cow_df['Cow_Number'].unique(), key=get_num)
            selected_cow = st.selectbox("View Cow:", cow_list)
            
            display_df = cow_df[cow_df['Cow_Number'] == selected_cow].copy()
            display_df['p_val'] = display_df['Part_Number'].apply(get_num)
            display_df = display_df.sort_values('p_val')
            
            st.table(display_df[['Part_Number', 'Name', 'Phone', 'ID', 'Meat_Contribution']])
        else:
            st.info("No Cow bookings found.")
    else:
        st.info("System is currently empty.")
