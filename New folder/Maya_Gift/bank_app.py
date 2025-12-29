import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# --- FILE & FOLDER SETUP ---
CLIENT_FILE = "ledger.csv"
PERSONAL_FILE = "my_budget.csv"
QUOTES_FILE = "quotes.csv"
GOALS_FILE = "goals.csv"
FACTS_FILE = "facts.csv"
PIG_FILE = "pig_map.csv"
GIF_DIR = "gifs"  # The main folder

# --- BANNER FILES ---
EMPIRE_BANNER = "banner.png"
FIRM_BANNER = "firm_banner.png"

# --- DATA LOADING ---
def load_client_data():
    if not os.path.exists(CLIENT_FILE):
        return pd.DataFrame(columns=["Date", "Client", "Type", "Amount", "Note", "Savings_Balance", "Niece_Earnings", "Target", "Frequency"])
    df = pd.read_csv(CLIENT_FILE)
    if "Target" not in df.columns: df["Target"] = 0.0
    if "Frequency" not in df.columns: df["Frequency"] = ""
    return df

def load_personal_data():
    if not os.path.exists(PERSONAL_FILE):
        return pd.DataFrame(columns=["Date", "Category", "Item", "Amount", "Sass_Level"])
    return pd.read_csv(PERSONAL_FILE)

def save_personal_data(df):
    df.to_csv(PERSONAL_FILE, index=False)

def load_goals():
    if not os.path.exists(GOALS_FILE):
        data = {
            "Goal_ID": ["Goal 1", "Goal 2", "Goal 3"],
            "Name": ["Spring Fling Dress", "College", "Pink Jeep"],
            "Target": [1000.0, 5000.0, 300.0],
            "Balance": [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(GOALS_FILE, index=False)
        return df
    return pd.read_csv(GOALS_FILE)

def get_daily_content(file_path, column_name, fallback):
    if not os.path.exists(file_path):
        return fallback
    try:
        df = pd.read_csv(file_path)
        day_of_year = datetime.now().timetuple().tm_yday
        index = (day_of_year - 1) % len(df)
        return df.iloc[index][column_name]
    except:
        return fallback

# --- HELPER: SMART BANNER ---
def show_smart_banner(base_name, fallback_title):
    possible_files = [f"{base_name}.png", f"{base_name}.PNG", f"{base_name}.jpg", f"{base_name}.JPG"]
    found = False
    for f in possible_files:
        if os.path.exists(f):
            st.image(f, use_column_width=True)
            found = True
            break
    if not found:
        st.markdown(f"<h1 style='color:#D81B60; font-family: Brush Script MT, cursive;'>{fallback_title}</h1>", unsafe_allow_html=True)

# --- PIGGY BANK LOGIC ---
def get_pig_image(current_percent):
    if not os.path.exists(PIG_FILE):
        return None
    try:
        df = pd.read_csv(PIG_FILE)
        df = df.sort_values(by="Threshold")
        selected_image = df.iloc[0]["Image_File"]
        for index, row in df.iterrows():
            if current_percent >= row["Threshold"]:
                selected_image = row["Image_File"]
        return selected_image
    except:
        return None

# --- SAVE FUNCTIONS ---
def save_client_transaction(client_name, type, amount, note, savings_change, earnings_change, target=0.0, freq=""):
    df = load_client_data()
    client_data = df[df["Client"] == client_name]
    current_savings = client_data.iloc[-1]["Savings_Balance"] if not client_data.empty else 0.0
    new_savings = current_savings + savings_change
    
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), 
        "Client": client_name, "Type": type, 
        "Amount": amount, "Note": note, 
        "Savings_Balance": new_savings, "Niece_Earnings": earnings_change,
        "Target": target, "Frequency": freq
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(CLIENT_FILE, index=False)

def save_personal_transaction(category, item, amount, sass):
    df = load_personal_data()
    if category in ["Spending", "Withdraw from Savings", "Early Withdrawal"]:
        amount = -amount
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Category": category, 
        "Item": item, "Amount": amount, "Sass_Level": sass
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(PERSONAL_FILE, index=False)

def update_goal(goal_name, amount_change):
    df = load_goals()
    idx = df.index[df['Name'] == goal_name].tolist()[0]
    df.at[idx, 'Balance'] += amount_change
    df.to_csv(GOALS_FILE, index=False)

# --- FOLDER-BASED GIF ENGINE ---
def show_sass_gif(folder_name):
    target_folder = os.path.join(GIF_DIR, folder_name)
    if not os.path.exists(target_folder): return
    all_files = os.listdir(target_folder)
    valid_images = [f for f in all_files if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp'))]
    if valid_images:
        chosen = random.choice(valid_images)
        st.image(os.path.join(target_folder, chosen), width=400)

# --- MEAN GIRLS TEXT SASS ENGINE ---
def get_sass(mood):
    if mood == "good_math": return random.choice(["You go, Glen Coco! 4 for you!", "The limit does not exist!", "That is so fetch.", "Grool. (Great + Cool)."])
    elif mood == "bad_math": return random.choice(["Stop trying to make that math happen.", "You can't sit with us.", "Social suicide.", "Boo, you whore."])
    elif mood == "spending": return random.choice(["Get in loser, we're going shopping.", "Is butter a carb?", "I'm a cool mom.", "Whatever, I'm getting cheese fries."])
    elif mood == "saving": return random.choice(["That is so fetch.", "You're like, really pretty.", "On Wednesdays we wear pink (and save money)."])
    elif mood == "goal_hit": return "Spring Fling Queen! 👑"
    elif mood == "early_withdraw": return "She doesn't even go here!"
    elif mood == "refund": return "We love a return policy."
    elif mood == "gift": return random.choice(["Is your muffin buttered?", "I love her, she's like a Martian."])

# --- CONFIG & STYLE (MEAN GIRLS THEME) ---
st.set_page_config(page_title="The Burn Book", page_icon="💋", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Indie+Flower&family=Montserrat:wght@400;700&display=swap');
    .stApp { background-color: #FFF0F5; color: #000000; font-family: 'Montserrat', sans-serif; }
    h1, h2, h3 { color: #D81B60 !important; font-family: 'Indie Flower', cursive !important; font-weight: bold; letter-spacing: 1px; }
    .stButton>button { background-color: #E91E63; color: white; border-radius: 0px; border: 2px solid black; font-family: 'Indie Flower', cursive; font-size: 20px; }
    .stButton>button:hover { background-color: #FF69B4; border: 2px dashed black; }
    
    /* CARDS */
    .history-card { 
        background-color: white; 
        padding: 15px; 
        border: 2px solid #E91E63;
        margin-bottom: 8px; 
        color: black;
        font-family: 'Indie Flower', cursive;
        box-shadow: 3px 3px 0px #000;
    }
    .pos { border-left: 10px solid #00cc00; }
    .neg { border-left: 10px solid #ff4b4b; }
    .gold { border-left-color: #ffd700; }

    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] { background-color: white; border: 2px solid #E91E63; color: black; font-family: 'Indie Flower', cursive; font-size: 18px; }
    .stTabs [aria-selected="true"] { background-color: #E91E63; color: white; }
</style>
""", unsafe_allow_html=True)

# --- INTRO LOGIC ---
if 'intro_seen' not in st.session_state:
    st.session_state['intro_seen'] = False

if not st.session_state['intro_seen']:
    is_first_run = not os.path.exists(CLIENT_FILE)
    if is_first_run:
        st.balloons()
        st.title("💋 Get in Loser, We're Doing Accounting.")
        st.write("Welcome to the Plastics. This is where you run the school.")
        if st.button("🚀 Open the Burn Book"):
            st.session_state['intro_seen'] = True
            st.rerun()
    else:
        daily_fact = get_daily_content(FACTS_FILE, "Daily Gossip", "On Wednesdays we wear pink.")
        st.markdown(f"### 💋 Gossip: {daily_fact}")
        if st.button("✨ Enter World Domination ✨"):
            st.session_state['intro_seen'] = True
            st.rerun()

# --- MAIN NAVIGATION ---
else:
    tab_firm, tab_empire, tab_help = st.tabs(["💅 The Plastics (Clients)", "👑 World Domination", "📕 The Rules"])

    # ==========================
    # TAB 1: THE PLASTICS (Clients)
    # ==========================
    with tab_firm:
        show_smart_banner("firm_banner", "The Plastics")
        
        firm_sub_nav = st.radio("Menu:", ["📊 The Table", "📝 New Recruit", "💸 Transaction"], horizontal=True, label_visibility="collapsed")
        st.markdown("---")

        df = load_client_data()
        existing_clients = df["Client"].unique().tolist() if not df.empty else []
        
        # A. DASHBOARD
        if firm_sub_nav == "📊 The Table":
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_client = st.selectbox("Who is sitting with us?", existing_clients, key="dash_client_select") if existing_clients else None
            
            if selected_client:
                client_df = df[df["Client"] == selected_client]
                bal = client_df.iloc[-1]["Savings_Balance"] if not client_df.empty else 0.0
                revenue = df["Niece_Earnings"].sum()
                
                try: target = client_df["Target"].max()
                except: target = 0
                
                col_a, col_b = st.columns(2)
                col_a.metric(f"{selected_client}'s Stash", f"${bal:,.2f}")
                col_b.metric("Your Cut (15%)", f"${revenue:,.2f}")
                
                st.markdown("### Progress")
                if target > 0:
                    percent = bal / target
                    st.progress(min(percent, 1.0))
                    st.caption(f"Goal: ${target:,.2f} | Current: ${bal:,.2f}")
                    pig_pic = get_pig_image(percent * 100)
                    if pig_pic: st.image(pig_pic, width=150)
                    if percent >= 1.0: 
                        show_sass_gif("good_math") 
                        st.success("Is that a new goal? It's really pretty. 🎉")
                else:
                    st.info("No goal. Social suicide.")
                
                st.markdown("### The Burn Book (History)")
                st.dataframe(client_df[["Date", "Type", "Amount", "Note", "Savings_Balance"]].sort_index(ascending=False), use_container_width=True)
            else:
                st.info("No clients yet. Add a Recruit!")

        # B. ADD CLIENT
        elif firm_sub_nav == "📝 New Recruit":
            st.subheader("Plastic Onboarding")
            with st.form("onboarding_form"):
                new_name = st.text_input("1. Name (Are they cool?)", key="new_client_name")
                col_q1, col_q2 = st.columns(2)
                with col_q1: new_goal = st.number_input("Savings Goal ($)", value=100.0, key="new_client_goal")
                with col_q2: new_freq = st.selectbox("Frequency", ["Weekly", "Bi-Weekly", "Whenever"], key="new_client_freq")
                
                if st.form_submit_button("Make them a Plastic"):
                    if new_name and new_name not in existing_clients:
                        save_client_transaction(new_name, "Open", 0, "Joined the Clique", 0, 0, target=new_goal, freq=new_freq)
                        st.success(f"{new_name} can sit with us.")
                        show_sass_gif("burn_book") 
                        st.balloons()
                    elif new_name in existing_clients:
                        st.error("She doesn't even go here! (Already exists)")

        # C. TRANSACTION
        elif firm_sub_nav == "💸 Transaction":
            if not existing_clients:
                st.warning("No clients.")
            else:
                c_client = st.selectbox("Client", existing_clients, key="trans_client_select")
                c_action = st.radio("Action", ["Deposit", "Loan (Gross)", "Penalty (Late)"], horizontal=True, key="trans_action_select")
                
                # DEPOSIT
                if c_action == "Deposit":
                    c_amount = st.number_input("Amount", value=10.00, key="trans_deposit_amount")
                    st.write(f"**Mathletes Tryout:** 15% of ${c_amount}?")
                    guess = st.number_input("Answer:", value=0.0, key="trans_deposit_guess")
                    if st.button("Secure the Bag"):
                        real_earn = round(c_amount * 0.15, 2)
                        client_save = c_amount - real_earn
                        note = "Deposit (So Fetch)" if abs(guess - real_earn) < 0.01 else "Deposit (Fixed)"
                        
                        if abs(guess - real_earn) < 0.01: 
                            st.balloons()
                            show_sass_gif("good_math") 
                            st.success(get_sass("good_math"))
                        else:
                            show_sass_gif("bad_math") 
                            st.error(get_sass("bad_math"))
                        
                        save_client_transaction(c_client, "Deposit", c_amount, note, client_save, real_earn)
                
                # WITHDRAWAL
                elif c_action == "Loan (Gross)":
                    c_amount = st.number_input("Loan Amount", value=10.00, key="trans_loan_amount")
                    st.warning("⚠️ Warning: This will ruin their Piggy Bank status.")
                    if st.button("Give Loan"):
                        show_sass_gif("spent") 
                        save_client_transaction(c_client, "Withdrawal", c_amount, "Client Loan", -c_amount, 0)
                        st.success("Processed. Whatever, I'm getting cheese fries.")
                
                # PENALTY
                elif c_action == "Penalty (Late)":
                    st.subheader("💀 Late Fee")
                    days_late = st.number_input("Days Late", min_value=1, value=1, key="trans_penalty_days")
                    total_fee = days_late * 5.00
                    
                    st.write(f"**Mathletes:** $5.00 x {days_late} days = ?")
                    fee_guess = st.number_input("Your Calculation:", value=0.00, key="trans_penalty_guess")
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        if st.button("Charge it 💅"):
                            if abs(fee_guess - total_fee) < 0.01:
                                save_client_transaction(c_client, "Penalty", total_fee, "Late Fee", 0, total_fee)
                                show_sass_gif("burn_book") 
                                st.success("The limit does not exist!")
                            else:
                                st.error("Wrong math. Charged anyway.")
                                show_sass_gif("bad_math") 
                                save_client_transaction(c_client, "Penalty", total_fee, "Late Fee", 0, total_fee)
                    with col_p2:
                        if st.button("Waive it (Be Nice) 😇"):
                            save_client_transaction(c_client, "Waived", 0, "Fee Waived", 0, 0)
                            st.balloons()
                            show_sass_gif("good_math") 
                            st.success("You are a cool mom.")

    # ==========================
    # TAB 2: WORLD DOMINATION (Empire)
    # ==========================
    with tab_empire:
        show_smart_banner("banner", "👑 World Domination")
        quote = get_daily_content(QUOTES_FILE, "DailyMotoQuote", "Get in loser, we're going shopping.")
        st.caption(f"Gossip: {quote}")
        
        empire_nav = st.radio("Menu:", ["🏆 Spring Fling Goals", "💸 Money Mover", "📜 The Burn Book"], horizontal=True, label_visibility="collapsed")
        st.markdown("---")
        
        personal_df = load_personal_data()
        goals_df = load_goals()
        client_df = load_client_data()
        
        total_earned = client_df["Niece_Earnings"].sum() if not client_df.empty else 0.0
        total_in_goals = goals_df["Balance"].sum()
        available_cash = total_earned + personal_df["Amount"].sum() - total_in_goals

        if empire_nav == "🏆 Spring Fling Goals":
            st.metric("💵 Shopping Money", f"${available_cash:,.2f}")
            cols = st.columns(3)
            for index, row in goals_df.iterrows():
                with cols[index]:
                    st.markdown(f"### {row['Name']}")
                    percent = row['Balance'] / row['Target'] if row['Target'] > 0 else 0
                    st.progress(min(percent, 1.0))
                    st.write(f"${row['Balance']:.0f} / ${row['Target']:.0f}")
                    pig_pic = get_pig_image(percent * 100)
                    if pig_pic: st.image(pig_pic, width=150)
            
            with st.expander("Edit Goals"):
                e_goal = st.selectbox("Goal", goals_df["Name"], key="empire_edit_goal")
                new_n = st.text_input("New Name", key="empire_edit_name")
                new_t = st.number_input("New Target", value=100.0, key="empire_edit_target")
                if st.button("Update Goal"):
                    idx = goals_df.index[goals_df['Name'] == e_goal].tolist()[0]
                    goals_df.at[idx, 'Name'] = new_n if new_n else e_goal
                    goals_df.at[idx, 'Target'] = new_t
                    goals_df.to_csv(GOALS_FILE, index=False)
                    st.rerun()

        elif empire_nav == "💸 Money Mover":
            st.subheader("Move Money")
            move_type = st.selectbox("Action", ["Deposit Cash (Gift)", "Shopping Spree", "Save to Goal", "Withdraw from Goal"], key="empire_move_type")
            amt = st.number_input("Amount", value=10.0, key="empire_move_amt")
            
            # 1. DEPOSIT
            if move_type == "Deposit Cash (Gift)":
                source = st.text_input("From who?", "Nana", key="empire_dep_source")
                if st.button("Add Cash"):
                    save_personal_transaction("Income", source, amt, get_sass("gift"))
                    st.balloons()
                    show_sass_gif("saved") 
                    st.rerun()
            
            # 2. SAVE TO GOAL
            elif move_type == "Save to Goal":
                goal = st.selectbox("To Goal", goals_df["Name"], key="empire_save_goal")
                if st.button("Save"):
                    if amt <= available_cash:
                        update_goal(goal, amt)
                        save_personal_transaction("Savings Transfer", f"Saved to {goal}", 0, get_sass("saving"))
                        st.balloons()
                        show_sass_gif("saved") 
                        st.rerun()
                    else: st.error("You have no money. Boo.")
            
            # 3. SPENDING
            elif move_type == "Shopping Spree":
                item = st.text_input("What did you buy?", key="empire_spend_item")
                if st.button("Spend"):
                    if amt <= available_cash:
                        save_personal_transaction("Spending", item, amt, get_sass("spending"))
                        show_sass_gif("spent") 
                        st.rerun()
                    else: st.error("Insufficient funds.")

            # 4. WITHDRAW FROM GOAL (This was missing!)
            elif move_type == "Withdraw from Goal":
                goal = st.selectbox("From Goal", goals_df["Name"], key="empire_withdraw_goal")
                if st.button("Withdraw to Cash"):
                    goal_row = goals_df[goals_df["Name"] == goal].iloc[0]
                    if amt > goal_row["Balance"]:
                        st.error("You don't have that much saved!")
                    else:
                        update_goal(goal, -amt)
                        save_personal_transaction("Early Withdrawal", f"Took from {goal}", 0, get_sass("early_withdraw"))
                        show_sass_gif("early_withdraw")
                        st.warning("Processed. Don't spend it all in one place.")
                        st.rerun()

        elif empire_nav == "📜 The Burn Book":
            st.write("### Your Personal Ledger")
            
            # HIDDEN EDITOR
            with st.expander("✎ Edit Entries (Fix Mistakes)"):
                edited_df = st.data_editor(personal_df, num_rows="dynamic", key="empire_editor")
                if st.button("Save Changes"):
                    save_personal_data(edited_df)
                    st.success("Burn Book Updated.")
                    st.rerun()
            
            st.markdown("---")
            
            # COLORFUL CARD FEED
            if not personal_df.empty:
                for index, row in personal_df.sort_index(ascending=False).iterrows():
                    amt = row['Amount']
                    css_class = "pos"  # Default Green (Fetch)
                    display_amt = f"+${abs(amt):.2f}"
                    
                    if amt < 0:
                        css_class = "neg" # Red (Gross)
                        display_amt = f"-${abs(amt):.2f}"
                    elif row['Category'] == "Reward":
                        css_class = "gold"
                        display_amt = f"+${abs(amt):.2f} (Reward)"
                    
                    st.markdown(f"""
                    <div class="history-card {css_class}">
                        <div style="display:flex; justify-content:space-between;">
                            <strong>{row['Item']} ({row['Category']})</strong>
                            <span>{row['Date']}</span>
                        </div>
                        <div style="font-size: 20px; font-weight: bold;">{display_amt}</div>
                        <div style="font-style: italic; color: #888;">"{row['Sass_Level']}"</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("The book is empty. Go buy something.")

    # ==========================
    # TAB 3: THE RULES
    # ==========================
    with tab_help:
        st.title("📕 The Rules of Feminism")
        st.markdown("""
        ### 1. The Plastics (Clients)
        - You are the Queen Bee. They save money, you take **15%**.
        - If they are late, you charge them **$5/day**.
        - If you feel like a Cool Mom, you can waive the fee.
        
        ### 2. World Domination (Goals)
        - **The Pig:** As you save, the pig fills up. It's like, the rules of physics.
        - **Shopping Money:** This is your cash. Don't spend it all at once.
        """)