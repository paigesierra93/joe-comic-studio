import streamlit as st
import pandas as pd
import random
import os
import shutil
import time
import warnings
import glob
import base64
import re
import csv
from datetime import datetime
import google.generativeai as genai

# --- SUPPRESS WARNINGS ---
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Joe's Comic Studio", page_icon="🦇", layout="wide")

# ==========================================
# 1. DAD CONFIGURATION (EDIT THIS!)
# ==========================================
DAD_PASSWORD = "admin"  
FLAGGED_WORDS = [
    "kill", "murder", "blood", "death", "stupid", "idiot", "hate", 
    "shut up", "damn", "hell", "die"
] 

# ==========================================
# 2. ETHICS & SAFETY MODULE
# ==========================================

SESSION_LIMIT_SECONDS = 7200 
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = time.time()

def get_time_remaining():
    elapsed = time.time() - st.session_state['start_time']
    remaining = SESSION_LIMIT_SECONDS - elapsed
    return max(0, remaining)

LOG_FILE = "security_log.csv"
def log_security_event(event_type, user_input):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Type", "Input"])
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, event_type, user_input])

def check_safety(user_input):
    if not isinstance(user_input, str): return True, ""
    
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    if re.search(phone_pattern, user_input) or re.search(email_pattern, user_input):
        log_security_event("PII_ATTEMPT", user_input)
        return False, "⚠️ **SECURITY ALERT:** Secret Identity detected! That data has been redacted."

    copyrights = ["batman", "superman", "spiderman", "spider-man", "iron man", "hulk", "wonder woman", "captain america", "marvel", "dc comics"]
    if any(c in user_input.lower() for c in copyrights):
        log_security_event("COPYRIGHT_ATTEMPT", user_input)
        return False, "🛑 **CREATIVE OVERRIDE:** That hero already exists! Invent someone new."

    if any(w in user_input.lower() for w in FLAGGED_WORDS):
        log_security_event("PROFANITY_VIOLENCE", user_input)
        return False, "🛡️ **HERO'S CODE VIOLATION:** That language violates the Code of Honor."

    return True, ""

# ==========================================
# 3. VISUAL SETUP
# ==========================================

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

banner_main_bg = get_img_as_base64("banner4.jpg")
banner_char_bg = get_img_as_base64("banner3.jpg")
banner_add_bg  = get_img_as_base64("banner7.jpg")
banner_chat_bg = get_img_as_base64("banner8.jpg")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@300;400;700&display=swap');
    
    .stApp, .stMarkdown, .stText, p, div, input, textarea, button {{
        font-family: 'Comic Neue', cursive !important;
        font-weight: 400;
        font-size: 20px !important; 
    }}
    
    h1, h2, h3 {{ 
        font-family: 'Bangers', cursive !important; 
        color: #000000 !important; 
        letter-spacing: 2px;
        text-shadow: none; 
    }}

    div.block-container {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 30px;
        border: 3px solid #000000;
        box-shadow: 10px 10px 0px rgba(0,0,0,0.5);
        margin-top: 20px;
        max-width: 1200px;
    }}

    [data-testid="stSidebar"] {{ background-color: #89CFF0; border-right: 3px solid black; }}
    [data-testid="stSidebar"] * {{
        font-family: 'Bangers', cursive !important;
        color: #FFFF00 !important; 
        font-size: 24px !important;
        text-shadow: 2px 2px 0px #000000;
        letter-spacing: 1px;
    }}
    
    .stTextInput input, .stTextArea textarea {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        background-color: #ffffff !important;
        border: 3px solid #000000 !important;
        font-weight: bold !important;
    }}
    
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
    }}
    div[data-testid="stSelectbox"] div {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}

    div[data-testid="stButton"] button {{
        background-color: #FF0000;
        color: white;
        border: 2px solid white;
        border-radius: 10px;
        font-family: 'Bangers', cursive !important;
        font-size: 22px !important;
        box-shadow: 3px 3px 0px rgba(0,0,0,1);
    }}
    div[data-testid="stButton"] button:hover {{
        border-color: yellow;
        background-color: #cc0000;
        transform: translate(1px, 1px);
    }}

    .user-msg {{ background-color: #2b313e; color: white; padding: 10px; border-radius: 10px; text-align: right; margin-bottom: 10px; border: 2px solid #FFFF00; }}
    .ai-msg {{ background-color: #ffffff; color: black; padding: 10px; border-radius: 10px; text-align: left; margin-bottom: 10px; font-weight: bold; border: 3px solid black; }}
    
    .gen-card {{
        background-color: #f0f2f6;
        border: 2px dashed black;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        color: black;
    }}
    
    .warning-banner {{
        background-color: #000; color: #00FF00; font-family: monospace !important; font-size: 14px; padding: 5px; text-align: center; border-top: 2px solid #00FF00;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. FILE OPERATIONS
# ==========================================
PORTFOLIO_FILE = "portfolio.csv"
TIMELINE_FILE = "timeline.csv"
ROSTER_FILES = ["roster_completed.csv"]
IMAGE_DIR = "character_images"
PORTFOLIO_DIR = "portfolio_images"
SCRIPT_DIR = "saved_scripts"

for folder in [IMAGE_DIR, PORTFOLIO_DIR, SCRIPT_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_universe_filename(universe_name):
    safe_name = universe_name.strip().lower().replace(" ", "_").replace("-", "")
    return f"universe_{safe_name}.csv"

FULL_CHAR_COLUMNS = [
    "Hero Name", "Real Name", "Role", "Universe", "Super Power", 
    "Weakness", "Costume", "Signature Move", "Magic", "Strength", 
    "Origin", "Personality", "Catchphrase", "Enemies", "Allies", 
    "Speaking Style", "Relationships", "Image_Path"
]

def load_data(file_path, columns):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(file_path)
        for col in columns:
            if col not in df.columns:
                df[col] = "" 
        return df[columns]
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

def save_image(image_file, folder, alias):
    if image_file is None:
        return None
    safe_name = alias.replace(" ", "_")[:20]
    ext = os.path.splitext(image_file.name)[1]
    filename = f"{safe_name}{ext}"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(image_file.getbuffer())
    return path

def delete_character(universe, alias):
    target_file = get_universe_filename(universe)
    if not os.path.exists(target_file): return False
    df = pd.read_csv(target_file)
    if df.empty: return False
    df = df[df['Hero Name'] != alias] 
    df.to_csv(target_file, index=False)
    return True

def save_character(data_dict):
    universe = data_dict['Universe']
    target_file = get_universe_filename(universe)
    df = load_data(target_file, FULL_CHAR_COLUMNS)
    if not df.empty:
        df = df[df['Hero Name'] != data_dict['Hero Name']]
    new_entry = pd.DataFrame([data_dict])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(target_file, index=False)
    return target_file

def save_timeline_event(year, event, type):
    df = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])
    new_entry = pd.DataFrame([{ "Year": year, "Event": event, "Type": type }])
    df = pd.concat([df, new_entry], ignore_index=True)
    try:
        df["Year"] = df["Year"].astype(int)
        df = df.sort_values(by="Year")
    except: pass 
    df.to_csv(TIMELINE_FILE, index=False)

def save_portfolio_entry(title, issue_num, description, image_file=None, local_path=None):
    final_path = None
    if image_file:
        final_path = save_image(image_file, PORTFOLIO_DIR, title)
    elif local_path:
        filename = os.path.basename(local_path)
        target = os.path.join(PORTFOLIO_DIR, filename)
        if not os.path.exists(target): shutil.copy(local_path, target)
        final_path = target
    df = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
    if not df.empty and title in df["Title"].values: return
    new_entry = pd.DataFrame([{"Title": title, "Issue": issue_num, "Description": description, "Image_Path": final_path}])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(PORTFOLIO_FILE, index=False)

def save_script_file(title, content):
    if not title: title = f"Script_{datetime.now().strftime('%Y%m%d_%H%M')}"
    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title)
    filename = f"{safe_title}.txt"
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def load_script_file(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# --- UPDATED INITIALIZE ROSTER WITH MAPPING ---
def initialize_roster():
    target_file = None
    for f in ROSTER_FILES:
        if os.path.exists(f): target_file = f; break     
    if target_file:
        try:
            ex_df = pd.read_csv(target_file)
            ex_df.columns = ex_df.columns.str.strip() # Remove spaces like 'Strength '
            
            if 'Hero Name' not in ex_df.columns: return False
            ex_df = ex_df.dropna(subset=['Hero Name'])
            
            for f in glob.glob("universe_*.csv"): os.remove(f)
            
            for index, row in ex_df.iterrows():
                # --- MAPPING OLD COLUMNS TO NEW ---
                data = {}
                data['Hero Name'] = str(row.get('Hero Name', ''))
                data['Real Name'] = str(row.get('Real Name', ''))
                
                # Map 'Role / Archetype' to 'Role'
                data['Role'] = str(row.get('Role / Archetype', row.get('Role', '')))
                
                # Map 'Super Powers' to 'Super Power'
                data['Super Power'] = str(row.get('Super Powers', row.get('Super Power', '')))
                
                # Map 'Weaknesses' to 'Weakness'
                data['Weakness'] = str(row.get('Weaknesses', row.get('Weakness', '')))
                
                # Map 'Costume / Visuals' to 'Costume'
                data['Costume'] = str(row.get('Costume / Visuals', row.get('Costume', '')))
                
                data['Signature Move'] = str(row.get('Signature Move', ''))
                data['Magic'] = str(row.get('Magic', ''))
                data['Strength'] = str(row.get('Strength', '')) # Strip already handled
                data['Origin'] = str(row.get('Origin', ''))
                data['Personality'] = str(row.get('Personality', ''))
                data['Catchphrase'] = str(row.get('Catchphrase', ''))
                data['Enemies'] = str(row.get('Enemies', ''))
                data['Allies'] = str(row.get('Allies', ''))
                data['Speaking Style'] = str(row.get('Speaking Style', ''))
                data['Relationships'] = str(row.get('Relationships', ''))
                data['Universe'] = str(row.get('Universe', 'Home'))
                if not data['Universe']: data['Universe'] = "Home"

                # Image Logic
                img_filename = row.get('Picture Link', '')
                if not img_filename or str(img_filename).lower() == 'nan':
                    # Try alternate column
                    img_filename = row.get('Uploaded Sketch', row.get('Uploaded Photo', ''))
                
                final_img_path = ""
                if img_filename and str(img_filename).lower() != 'nan':
                    img_filename = str(img_filename).strip()
                    target_path = os.path.join(IMAGE_DIR, os.path.basename(img_filename))
                    if os.path.exists(img_filename): 
                        shutil.copy(img_filename, target_path)
                        final_img_path = target_path
                    elif os.path.exists(target_path): 
                        final_img_path = target_path
                data['Image_Path'] = final_img_path
                
                save_character(data)
            return True 
        except Exception as e: 
            print(f"Error initializing: {e}")
            return False
    return False

# --- AI LOGIC ---
def generate_ai_content(prompt):
    models_to_try = [
        "gemini-2.0-flash", "gemini-2.0-flash-exp", 
        "gemini-2.5-flash", "gemini-1.5-pro-latest"
    ]
    safety_prompt_add = ""
    if "villain" in prompt.lower() or "bad guy" in prompt.lower():
        safety_prompt_add = "\n(INSTRUCTION: Focus on backstory/motivation.)"
    full_prompt = prompt + safety_prompt_add
    
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue 
    return f"⚠️ **CONNECTION FAILED.** Error Code: {last_error}"

def check_timeline_logic(new_event, existing_df):
    if existing_df.empty: return True, ""
    history = existing_df['Event'].tolist()
    history_str = "\n".join(history)
    prompt = f"Analyze timeline consistency.\nHISTORY:\n{history_str}\nNEW EVENT: {new_event}\nDoes this contradict logic? Answer YES or NO with reason."
    ai_check = generate_ai_content(prompt)
    if "YES" in ai_check.upper(): return False, ai_check
    return True, ""

# ==========================================
# 5. STARTUP LOGIC
# ==========================================
if 'script_text' not in st.session_state: st.session_state['script_text'] = "TITLE: \nISSUE: \n\n[PAGE 1]\n"
if 'roster_loaded' not in st.session_state:
    if not glob.glob("universe_*.csv"):
        if initialize_roster(): st.toast("🚀 Auto-loaded Full Roster!", icon="🦸")
    if os.path.exists("comic_story1.png"):
        save_portfolio_entry("Example Comic", "1", "An automated example of the comic studio portfolio.", local_path="comic_story1.png")
    st.session_state['roster_loaded'] = True

# ==========================================
# 6. SIDEBAR
# ==========================================
st.sidebar.title("🔑 Security Check")
api_key_input = st.sidebar.text_input("Paste Google API Key here:", type="password")

if not api_key_input:
    st.warning("👈 Please paste your Google API Key in the sidebar to start!")
    st.stop() 

try:
    genai.configure(api_key=api_key_input)
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- POWER LEVEL ---
remaining = get_time_remaining()
progress = remaining / SESSION_LIMIT_SECONDS
st.sidebar.markdown("---")
st.sidebar.write(f"**⚡ SUIT POWER: {int((remaining/SESSION_LIMIT_SECONDS)*100)}%**")
st.sidebar.progress(progress)

if remaining <= 0:
    st.error("⚠️ **SYSTEM OVERHEATING**")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.title("🦇 Studio Tools")
if st.sidebar.button("🔄 Reload Roster"):
    with st.spinner("Rebuilding Universe files..."):
        if initialize_roster():
            st.success("Universes Synced!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Could not find roster_completed.csv")

# --- ADMIN LOGIN ---
if st.sidebar.checkbox("Admin Access"):
    admin_pwd = st.sidebar.text_input("Password", type="password")
    if admin_pwd == DAD_PASSWORD: 
        if st.sidebar.button("View Security Logs"):
            if os.path.exists(LOG_FILE):
                st.sidebar.dataframe(pd.read_csv(LOG_FILE))
            else:
                st.sidebar.info("No security incidents logged.")

st.sidebar.markdown("---")
mode = st.sidebar.radio("Go to:", [
    "💬 Chat with Hero", 
    "🦸 Character Dashboard", 
    "⏳ Timeline", 
    "📝 Script Writer", 
    "📚 Portfolio", 
    "🎲 Idea Generator",
    "❓ Help / Tutorial" 
])

# ==========================================
# 7. MAIN APP
# ==========================================
current_bg = banner_chat_bg if mode == "💬 Chat with Hero" else banner_main_bg

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{current_bg}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
""", unsafe_allow_html=True)

try:
    st.image("main_banner.jpg", width="stretch")
except: pass

st.markdown('<div class="warning-banner">⚠️ SIMULATION MODE ACTIVE: AI IS A TOOL, NOT A PERSON. DATA MAY BE INACCURATE. ALWAYS VERIFY INTEL.</div>', unsafe_allow_html=True)

if 'intro_seen' not in st.session_state: st.session_state['intro_seen'] = False

if not st.session_state['intro_seen']:
    st.balloons()
    st.markdown(f"""<div class="intro-card"><h1>🎄 Merry Christmas, Joe! 🎄</h1><h3>Welcome to your Secret Headquarters.</h3><p>Let's make some comics.</p></div>""", unsafe_allow_html=True)
    if st.button("🚀 ACCESS THE STUDIO", type="primary"):
        st.session_state['intro_seen'] = True
        st.rerun()

else:
    if mode == "💬 Chat with Hero":
        st.title("💬 Chat with your Characters")
        universe_files = glob.glob("universe_*.csv")
        universe_map = {f: f.replace("universe_", "").replace(".csv", "").title() for f in universe_files}
        
        if not universe_files:
             st.warning("No universes found. Go to the Dashboard to add one.")
        else:
            selected_univ_name = st.selectbox("Select Universe", list(universe_map.values()))
            selected_file = [k for k, v in universe_map.items() if v == selected_univ_name][0]
            df = load_data(selected_file, FULL_CHAR_COLUMNS)
            
            if df.empty:
                st.warning("No characters here yet!")
            else:
                selected_alias = st.selectbox("Who do you want to talk to?", df['Hero Name'].unique())
                char_data = df[df['Hero Name'] == selected_alias].iloc[0]

                # --- UNIVERSE CONTEXT ---
                all_aliases = df['Hero Name'].tolist()
                if selected_alias in all_aliases:
                    all_aliases.remove(selected_alias)
                universe_roster_str = ", ".join(all_aliases) if all_aliases else "No other known heroes."
                
                # --- SANITIZE DATA ---
                def sanitize(val):
                    s = str(val)
                    if s.lower() in ["nan", "none", "unknown"]: return ""
                    return s

                specific_rel = sanitize(char_data['Relationships'])
                my_personality = sanitize(char_data['Personality'])
                my_catchphrase = sanitize(char_data['Catchphrase'])

                # --- VISUAL DEBUG ---
                with st.expander("🛠️ AI Context (Debug View)"):
                    st.write(f"**Loaded Relationships:** {specific_rel}")
                    st.write(f"**Loaded Teammates:** {universe_roster_str}")

                if "messages" not in st.session_state: st.session_state.messages = []
                if "current_char" not in st.session_state: st.session_state.current_char = ""
                if st.session_state.current_char != selected_alias:
                    st.session_state.messages = []
                    st.session_state.current_char = selected_alias

                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown(f"""
                    <div style="background-image: url('data:image/jpg;base64,{banner_char_bg}'); background-size: cover; padding: 15px; border-radius: 10px; border: 2px solid white; text-align: center; color: white; text-shadow: 2px 2px 0 #000;">
                        <h3>{char_data['Hero Name']}</h3>
                        <p>{char_data['Role']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if char_data['Image_Path'] and os.path.exists(str(char_data['Image_Path'])):
                        st.image(str(char_data['Image_Path']), width=150)
                
                with c2:
                    for msg in st.session_state.messages:
                        role_class = 'user-msg' if msg["role"] == "user" else 'ai-msg'
                        icon = '👤' if msg["role"] == "user" else '🦸‍♂️'
                        st.markdown(f"<div class='{role_class}'>{icon} {msg['content']}</div>", unsafe_allow_html=True)

                    if prompt := st.chat_input(f"Say something to {selected_alias}..."):
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        is_safe, warning_msg = check_safety(prompt)
                        if not is_safe:
                            st.session_state.messages.append({"role": "assistant", "content": warning_msg})
                            st.rerun()
                        else:
                            st.rerun()

                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    with c2:
                        with st.spinner("Thinking..."):
                            user_text = st.session_state.messages[-1]["content"]
                            
                            forced_instruction = ""
                            if "who is" in user_text.lower():
                                if specific_rel and any(part.strip().lower() in user_text.lower() for part in specific_rel.split()):
                                     forced_instruction = f"SYSTEM ORDER: The user asked about someone in your RELATIONSHIP LIST ({specific_rel}). You MUST answer specifically about them first. Example: 'He is my Dad.'"

                            full_prompt = f"""
                            You are acting as {char_data['Hero Name']}.
                            
                            CONTEXT:
                            - Relationships: {specific_rel}
                            - Personality: {my_personality}
                            - Catchphrase: {my_catchphrase}
                            
                            {forced_instruction}
                            
                            User: {user_text}
                            You:
                            """
                            ai_reply = generate_ai_content(full_prompt)
                            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                            st.rerun()

    elif mode == "🦸 Character Dashboard":
        # --- INIT ALL EDIT FIELDS ---
        for col in FULL_CHAR_COLUMNS:
            key = f"edit_{col}"
            if key not in st.session_state: st.session_state[key] = ""

        col_create, col_vault = st.columns([1, 2], gap="large")
        with col_create:
            st.markdown(f"""
            <div style="background-image: url('data:image/jpg;base64,{banner_add_bg}'); background-size: cover; padding: 20px; border-radius: 15px 15px 0 0; border: 3px solid #000; color: white; text-shadow: 2px 2px 0 #000; text-align:center;">
                <h2 style='color: #FFFF00; margin:0;'>CREATE / EDIT</h2>
                <h3 style='color: #FFFFFF; margin:0;'>CHARACTER</h3>
            </div>
            <div style="background-color: #FFFFE0; padding: 20px; border-radius: 0 0 15px 15px; border: 3px solid #000; border-top: none;">
            """, unsafe_allow_html=True)
            
            # --- TABBED INPUT FORM ---
            tab_id, tab_power, tab_lore, tab_social = st.tabs(["🆔 Identity", "⚡ Powers", "📜 Lore", "👥 Social"])
            
            with tab_id:
                name = st.text_input("Real Name", value=st.session_state['edit_Real Name'])
                alias = st.text_input("Hero Name", value=st.session_state['edit_Hero Name'])
                
                # Universe Logic
                existing_universes = []
                for f in glob.glob("universe_*.csv"):
                    u_name = f.replace("universe_", "").replace(".csv", "").title()
                    existing_universes.append(u_name)
                univ_choice = st.selectbox("Universe", existing_universes + ["Create New..."])
                universe = st.text_input("New Universe Name") if univ_choice == "Create New..." else univ_choice
                
                role = st.text_input("Role / Archetype", value=st.session_state['edit_Role'])
                
            with tab_power:
                power = st.text_area("Super Power", value=st.session_state['edit_Super Power'])
                weakness = st.text_input("Weakness", value=st.session_state['edit_Weakness'])
                sig_move = st.text_input("Signature Move", value=st.session_state['edit_Signature Move'])
                c1, c2 = st.columns(2)
                with c1: strength = st.text_input("Strength (0-10)", value=st.session_state['edit_Strength'])
                with c2: magic = st.text_input("Magic (0-10)", value=st.session_state['edit_Magic'])
            
            with tab_lore:
                origin = st.text_area("Origin Story", value=st.session_state['edit_Origin'])
                personality = st.text_area("Personality", value=st.session_state['edit_Personality'])
                costume = st.text_input("Costume / Visuals", value=st.session_state['edit_Costume'])
                catchphrase = st.text_input("Catchphrase", value=st.session_state['edit_Catchphrase'])
                speak_style = st.text_input("Speaking Style", value=st.session_state['edit_Speaking Style'])
                
            with tab_social:
                relationships = st.text_area("Relationships (Name (Role))", value=st.session_state['edit_Relationships'])
                allies = st.text_input("Allies", value=st.session_state['edit_Allies'])
                enemies = st.text_input("Enemies", value=st.session_state['edit_Enemies'])
            
            uploaded_file = st.file_uploader("Upload Sketch", type=['png', 'jpg'])
            
            if st.button("SAVE CHARACTER", type="primary", width="stretch"): 
                is_safe_name, warn_name = check_safety(name + " " + alias)
                if not is_safe_name: st.error(warn_name)
                elif alias and universe:
                    img_path = None
                    if uploaded_file: img_path = save_image(uploaded_file, IMAGE_DIR, alias)
                    elif st.session_state['edit_Image_Path']: img_path = st.session_state['edit_Image_Path'] # Keep old image if editing
                    
                    data = {
                        "Real Name": name, "Hero Name": alias, "Universe": universe, "Role": role,
                        "Super Power": power, "Weakness": weakness, "Signature Move": sig_move,
                        "Strength": strength, "Magic": magic, "Origin": origin,
                        "Personality": personality, "Costume": costume, "Catchphrase": catchphrase,
                        "Speaking Style": speak_style, "Relationships": relationships,
                        "Allies": allies, "Enemies": enemies, "Image_Path": img_path,
                        "Age": "Unknown" # Default
                    }
                    
                    save_character(data)
                    st.success(f"Saved {alias}!")
                    # Clear state
                    for col in FULL_CHAR_COLUMNS: st.session_state[f"edit_{col}"] = ""
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_vault:
            st.markdown(f"""
            <div style="text-align: center; background-color: white; border: 3px solid black; border-radius: 10px; margin-bottom: 20px; box-shadow: 5px 5px 0px #000; padding: 5px;">
                <h1 style="color: black !important; text-shadow: none; margin: 5px; font-size: 40px !important;">CHARACTER VAULT</h1>
            </div>
            """, unsafe_allow_html=True)
            universe_files = glob.glob("universe_*.csv")
            if not universe_files: st.info("Vault is empty.")
            else:
                universe_map = {f: f.replace("universe_", "").replace(".csv", "").title() for f in universe_files}
                selected_univ_view = st.selectbox("Select Universe:", list(universe_map.values()))
                view_file = [k for k, v in universe_map.items() if v == selected_univ_view][0]
                df = load_data(view_file, FULL_CHAR_COLUMNS)
                
                if not df.empty:
                    cols = st.columns(2)
                    for index, row in df.iterrows():
                        with cols[index % 2]:
                            st.markdown(f"""
                            <div style="background-image: url('data:image/jpg;base64,{banner_char_bg}'); background-size: cover; padding: 10px; border: 3px solid black; border-radius: 5px; margin-bottom: 15px; box-shadow: 5px 5px 0px rgba(0,0,0,0.5);">
                            """, unsafe_allow_html=True)
                            if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                                st.image(str(row['Image_Path']), width="stretch")
                            else:
                                st.markdown("<div style='height:150px; background-color: white; border: 2px dashed black; display:flex; align-items:center; justify-content:center;'>No Image</div>", unsafe_allow_html=True)
                            
                            st.markdown(f"""
                                <div style="background-color: #FFFF00; padding: 10px; border: 2px solid black; margin-top: 10px;">
                                    <h3 style="margin:0; color: black !important; text-shadow: none; font-size: 24px;">{row['Hero Name']}</h3>
                                    <p style="margin:0; font-size:16px; color:black; font-weight: bold;">{row['Role']}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with st.expander("📂 View Full Dossier"):
                                for col in FULL_CHAR_COLUMNS:
                                    if col != "Image_Path" and row[col]:
                                        st.write(f"**{col}:** {row[col]}")
                            
                            # --- EDIT CALLBACK ---
                            def load_edit(r):
                                for col in FULL_CHAR_COLUMNS:
                                    st.session_state[f"edit_{col}"] = r[col]
                            
                            st.button(f"✏️ Edit {row['Hero Name']}", key=f"edit_{index}", on_click=load_edit, args=(row,))

                            if st.button(f"Delete {row['Hero Name']}", key=f"del_{index}"):
                                delete_character(selected_univ_view, row['Hero Name'])
                                st.rerun()
                else: st.info("No heroes found.")

    elif mode == "⏳ Timeline":
        st.title("⏳ Universe History")
        st.info("👮 **LOGIC COP ACTIVE:** The AI checks for chronological errors.")
        
        c1, c2 = st.columns([1, 2])
        df_t = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])

        with c1:
            t_year = st.text_input("Year", value="2024")
            t_event = st.text_area("Event")
            
            if st.button("Add to Timeline"):
                with st.spinner("Logic Cop is checking consistency..."):
                    consistent, reason = check_timeline_logic(t_event, df_t)
                
                if consistent:
                    save_timeline_event(t_year, t_event, "Event")
                    st.success("Event Added!")
                    st.rerun()
                else:
                    st.error(f"LOGIC ERROR DETECTED: {reason}")
                    if st.button("Force Add Anyway (Multiverse Logic)"):
                        save_timeline_event(t_year, t_event, "Event")
                        st.rerun()
                        
        with c2:
            for index, row in df_t.iterrows():
                st.markdown(f"<div style='background:rgba(0,0,0,0.5); padding:10px; margin:5px; border-left:4px solid yellow; color:white;'><b>{row['Year']}</b>: {row['Event']}</div>", unsafe_allow_html=True)

    elif mode == "📝 Script Writer":
        st.title("Script Editor")
        st.caption("Write your comic script here. Remember: PAGE 1, PANEL 1 format.")
        
        # Load existing scripts
        scripts = glob.glob(os.path.join(SCRIPT_DIR, "*.txt"))
        script_names = [os.path.basename(s) for s in scripts]
        selected_script = st.selectbox("📂 Load Previous Script", ["New Script"] + script_names)
        
        if selected_script != "New Script":
            loaded_content = load_script_file(selected_script)
            if 'script_text' not in st.session_state or st.session_state['script_text'] != loaded_content:
                st.session_state['script_text'] = loaded_content
        
        s_title = st.text_input("Script Title", value=selected_script.replace(".txt", "") if selected_script != "New Script" else "New Script")
        st.text_area("Content", height=400, key="script_text")
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download to Computer", st.session_state['script_text'], file_name=f"{s_title}.txt")
        with c2:
            if st.button("💾 Save to Script Archive"):
                fname = save_script_file(s_title, st.session_state['script_text'])
                st.success(f"Saved to {SCRIPT_DIR}/{fname}")

    elif mode == "🎲 Idea Generator":
        st.title("The Idea Machine ⚡")
        st.markdown(f"""<div style="background-color: #2b313e; color: white; padding: 20px; border-radius: 10px; border: 2px solid #00adb5; margin-bottom: 20px;"><h3>🤖 AI SCENARIO GENERATOR</h3></div>""", unsafe_allow_html=True)
        genre = st.selectbox("Choose Genre:", ["Action Crossover", "Mystery", "Comedy", "Dark Sci-Fi", "Daily Life"])
        if st.button("⚡ Generate Crossover Event", type="primary", width="stretch"):
            universe_files = glob.glob("universe_*.csv")
            all_chars = []
            for f in universe_files:
                df = load_data(f, FULL_CHAR_COLUMNS)
                if not df.empty: all_chars.extend(df.to_dict('records'))
            if len(all_chars) < 2:
                st.warning("⚠️ You need at least 2 characters in your Vault to generate a crossover!")
            else:
                with st.spinner("Consulting the Multiverse..."):
                    c1 = random.choice(all_chars)
                    c2 = random.choice(all_chars)
                    while c2['Hero Name'] == c1['Hero Name'] and len(all_chars) > 1: c2 = random.choice(all_chars)
                    prompt = f"Write a comic book plot outline for a '{genre}' story. Starring {c1['Hero Name']} and {c2['Hero Name']}."
                    ai_response = generate_ai_content(prompt)
                    st.markdown(f"""<div class="gen-card"><h2 style="color:black; text-shadow:none;">✨ {genre.upper()} EVENT GENERATED</h2><p style="color:black;"><b>Starring:</b> {c1['Hero Name']} & {c2['Hero Name']}</p><hr style="border-top: 2px dashed black;">{ai_response}</div>""", unsafe_allow_html=True)

    elif mode == "📚 Portfolio":
        st.title("Professional Portfolio 🎨")
        st.caption("This is your permanent record. Only upload finished work here!")
        tab1, tab2 = st.tabs(["📤 Upload", "🖼️ Gallery"])
        with tab1:
            p_title = st.text_input("Title")
            p_issue = st.text_input("Issue #")
            p_desc = st.text_area("Description")
            p_file = st.file_uploader("Upload Art", type=['png', 'jpg'])
            if st.button("Add to Portfolio", type="primary"):
                if p_title and p_file:
                    save_portfolio_entry(p_title, p_issue, p_desc, image_file=p_file)
                    st.success("Uploaded!")
                    st.rerun()
        with tab2:
            df_p = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
            if not df_p.empty:
                cols = st.columns(3)
                for index, row in df_p.iterrows():
                    with cols[index % 3]:
                        if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                            st.image(str(row['Image_Path']), width="stretch") 
                        st.markdown(f"**{row['Title']}** #{row['Issue']}")
                        st.caption(row['Description'])
            else: st.info("No art uploaded yet.")

    elif mode == "❓ Help / Tutorial":
        st.title("🎓 HERO ACADEMY: BASIC TRAINING")
        
        tab_joe, tab_dad = st.tabs(["🦸‍♂️ CADET TRAINING", "🔒 COMMANDER ACCESS (Dad)"])
        
        with tab_joe:
            st.markdown("### 🦸‍♂️ CADET TRAINING MANUAL")
            
            with st.expander("1. CHARACTER DASHBOARD (How to Build Heroes)"):
                st.markdown("""
                This is your Headquarters. You have 4 Tabs to fill out:
                * **🆔 Identity:** Name, Hero Name, Role (Hero/Villain).
                * **⚡ Powers:** Super Power, Weakness, Signature Move.
                * **📜 Lore:** Origin (Backstory), Personality, Catchphrase.
                * **👥 Social:** Relationships (VERY IMPORTANT), Allies, Enemies.
                
                **Pro Tip:** If you want the Chat to be smart, fill out the "Relationships" box correctly: `Megawatt (Dad), Zoom (Friend)`.
                """)

            with st.expander("2. CHAT WITH HERO (Universes & Safety)"):
                st.markdown("""
                Talk to your characters!
                * **Universe Context:** The computer knows who else is in that universe. If you talk to Batman, he knows who Robin is.
                * **Safety Shields:**
                  * If you type a phone number, the shield blocks it.
                  * If you try to copy a copyright hero (like Iron Man), the shield blocks it.
                  * If you use a Villain Word (bad word), the shield blocks it.
                """)

            with st.expander("3. TIMELINE (The Logic Cop)"):
                st.markdown("""
                This tracks the history of your world.
                * **The Logic Cop:** If you try to add an event that makes no sense (like *'Nana was trained by her own grandson'*), the AI will stop you and say **"LOGIC ERROR"**.
                * **Override:** You can force it to happen if you explain it's Time Travel or Multiverse weirdness.
                """)

            with st.expander("4. SCRIPT WRITER (The Archive)"):
                st.markdown("""
                Use this to write full comic pages (Page 1, Panel 1...).
                * **Saving:** Click `💾 Save to Script Archive`. This saves it to a special folder (`saved_scripts`) on your computer.
                * **Loading:** Use the dropdown menu to pick an old script and keep working on it.
                """)

            with st.expander("5. PORTFOLIO (The Vault)"):
                st.markdown("""
                * **Why use this?** This is for FINISHED work only.
                * **Permanence:** Once you upload art here, it's part of your professional record. Treat it like a museum display.
                """)

            with st.expander("6. IDEA GENERATOR (The Spark)"):
                st.markdown("""
                * **How it works:** It grabs 2 random people from your Vault and invents a story.
                * **The Rule:** You need at least **2 Characters** saved first.
                * **Advice:** Don't just copy what the AI says. Use it as a *spark* to start your own fire.
                """)
            
            st.markdown("---")
            st.subheader("🛡️ TRAINING DRILLS")
            test_word = st.text_input("DRILL 1: Type a 'Villain Word' to test shields:", key="drill1")
            if test_word:
                safe, msg = check_safety(test_word)
                if not safe: st.success("✅ SHIELD ACTIVE.")
                else: st.info("Try a banned word.")

        with tab_dad:
            st.markdown("### 🔒 Security Clearance Required")
            pwd = st.text_input("Enter Admin Password:", type="password", key="admin_tut")
            
            if pwd == DAD_PASSWORD:
                st.success("Access Granted.")
                st.markdown("""
                # 👨‍✈️ COMMANDER'S BRIEFING (Dad's Guide)
                
                ### 1. Dashboard & Data Entry
                * **Why specific inputs?** The AI needs structured data (Name, Role, Relations) to roleplay correctly. If Joe skips "Relationships", the chat will feel generic.
                * **New Feature:** The dashboard now supports 18 different data points (Origin, Costume, etc.) to act as a full "Wiki" for his world.
                
                ### 2. Chat Safety Features
                * **Hard-Coded Ethics:** The code actively scans for PII (Phone numbers) and Profanity *before* sending data to Google.
                * **Copyright Check:** Forces creativity by banning major IP names.
                
                ### 3. Timeline & Logic Cop
                * **Educational Value:** The "Logic Cop" isn't just a bug checker; it teaches **Critical Thinking**. It forces him to consider cause-and-effect in his storytelling.
                
                ### 4. Script Writer & Archive
                * **File Management:** Scripts are now saved as real `.txt` files in the `saved_scripts` folder. You can back these up to a USB drive if you want.
                
                ### 5. Portfolio & Permanence
                * **Pride of Work:** This section is designed to make him feel like a professional. It separates "sketches" from "published work."
                
                ---
                ### ⚠️ COMMANDER'S DUTY:
                **Check the `security_log.csv` file weekly.** This code blocks bad inputs, but it doesn't parent him. The logs will tell you if he's trying to push boundaries.
                """)
                
                if os.path.exists(LOG_FILE):
                    st.dataframe(pd.read_csv(LOG_FILE).tail(5))
                else:
                    st.write("No logs yet.")