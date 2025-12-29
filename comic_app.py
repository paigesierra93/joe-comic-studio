import streamlit as st
import pandas as pd
import random
import os
import shutil
import time  # Added for the cool-down timer
from datetime import datetime
import google.generativeai as genai 

# --- CONFIGURATION ---
try:
    # This tells Python to look inside the .streamlit/secrets.toml file
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except FileNotFoundError:
    st.error("🚨 Secrets file not found! Please create a .streamlit/secrets.toml file.")
    st.stop()
except KeyError:
    st.error("🚨 Key missing! Make sure your secrets.toml file says: GOOGLE_API_KEY = 'your-key'")
    st.stop()

# --- FILE & FOLDER SETUP ---
CHAR_FILE = "characters.csv"
PORTFOLIO_FILE = "portfolio.csv"
TIMELINE_FILE = "timeline.csv"

# This matches your file name exactly
ROSTER_FILES = ["roster_completed.csv"]

IMAGE_DIR = "character_images"
PORTFOLIO_DIR = "portfolio_images"

for folder in [IMAGE_DIR, PORTFOLIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- BACKEND FUNCTIONS ---

def load_data(file_path, columns):
    """
    Robust data loader that handles missing files, empty files,
    and missing columns automatically.
    """
    # 1. If file doesn't exist, create an empty one with the right headers
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    
    try:
        # 2. Read the file
        df = pd.read_csv(file_path)
        
        # 3. Auto-repair: Add any missing columns 
        # (This prevents crashes if you add new features like 'Relationships' later)
        missing_cols = set(columns) - set(df.columns)
        if missing_cols:
            for col in missing_cols:
                df[col] = None
        
        # 4. Return only the columns we want
        return df[columns]
        
    except pd.errors.EmptyDataError:
        # Handle case where file exists but is perfectly empty
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

def save_character(name, alias, universe, role, age, origin, personality, strength, magic, power, weakness, costume, relationships, speaking_style, allies, enemies, catchphrase, image_path):
    columns = [
        "Name", "Alias", "Universe", "Role", "Age", 
        "Origin", "Personality", "Strength", "Magic",
        "Power", "Weakness", "Costume", 
        "Relationships", "Speaking Style", "Allies", "Enemies", "Catchphrase",
        "Image_Path"
    ]
    df = load_data(CHAR_FILE, columns)
    
    # Avoid creating duplicates if the character is already there
    # (Simple check: if Alias exists, drop it and add the new version)
    if not df.empty:
        df = df[df['Alias'] != alias]

    new_entry = pd.DataFrame([{
        "Name": name, "Alias": alias, "Universe": universe, "Role": role, "Age": age,
        "Origin": origin, "Personality": personality, "Strength": strength, "Magic": magic,
        "Power": power, "Weakness": weakness, "Costume": costume, 
        "Relationships": relationships, "Speaking Style": speaking_style,
        "Allies": allies, "Enemies": enemies, "Catchphrase": catchphrase,
        "Image_Path": image_path
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(CHAR_FILE, index=False)

def save_portfolio_entry(title, issue_num, description, image_file):
    image_path = save_image(image_file, PORTFOLIO_DIR, title)
    df = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
    new_entry = pd.DataFrame([{
        "Title": title, "Issue": issue_num, "Description": description, "Image_Path": image_path
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(PORTFOLIO_FILE, index=False)

def save_timeline_event(year, event, type):
    df = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])
    new_entry = pd.DataFrame([{ "Year": year, "Event": event, "Type": type }])
    df = pd.concat([df, new_entry], ignore_index=True)
    try:
        df["Year"] = df["Year"].astype(int)
        df = df.sort_values(by="Year")
    except:
        pass 
    df.to_csv(TIMELINE_FILE, index=False)

def initialize_roster():
    # Find the correct file
    target_file = None
    for f in ROSTER_FILES:
        if os.path.exists(f):
            target_file = f
            break
            
    # Only run if we found a file AND the database is empty/missing
    if target_file and (not os.path.exists(CHAR_FILE) or os.stat(CHAR_FILE).st_size < 10):
        try:
            ex_df = pd.read_csv(target_file)
            
            # --- CRITICAL FIXES ---
            # 1. Strip whitespace from column names (Fixes "Enemies ")
            ex_df.columns = ex_df.columns.str.strip()
            
            # 2. Drop rows where 'Hero Name' is missing (Fixes the extra catchphrase rows)
            if 'Hero Name' in ex_df.columns:
                ex_df = ex_df.dropna(subset=['Hero Name'])

            for index, row in ex_df.iterrows():
                # Image Handling
                img_filename = row.get('Picture Link', None)
                if pd.isna(img_filename) or str(img_filename).strip() == "":
                        img_filename = row.get('Uploaded Sketch', None)
                final_img_path = None
                if pd.notna(img_filename) and str(img_filename).lower() != 'nan':
                    img_filename = str(img_filename).strip()
                    target_path = os.path.join(IMAGE_DIR, img_filename)
                    if os.path.exists(img_filename): 
                        shutil.copy(img_filename, target_path)
                        final_img_path = target_path
                    elif os.path.exists(target_path):
                        final_img_path = target_path
                
                # Power Text
                power_text = str(row.get('Super Powers', ''))
                sig_move = row.get('Signature Move', '')
                if pd.notna(sig_move) and sig_move:
                    power_text += f"\n\n💥 Signature Move: {sig_move}"
                
                # Save Character
                save_character(
                    name=row.get('Real Name', 'Unknown'),
                    alias=row.get('Hero Name', 'Unknown'),
                    universe=row.get('Universe', 'Unsorted'),
                    role=row.get('Role / Archetype', 'Hero'),
                    age=row.get('Age', 'Unknown'),
                    origin=row.get('Origin', ''),
                    personality=row.get('Personality', ''),
                    strength=row.get('Strength', '0/10'),
                    magic=row.get('Magic', '0/10'),
                    power=power_text,
                    weakness=row.get('Weaknesses', ''),
                    costume=row.get('Costume / Visuals', ''),
                    relationships=row.get('Relationships', ''),
                    speaking_style=row.get('Speaking Style', ''),
                    allies=row.get('Allies', ''),
                    enemies=row.get('Enemies', ''),
                    catchphrase=row.get('Catchphrase', ''),
                    image_path=final_img_path
                )
            return True 
        except Exception as e:
            print(f"Error loading : {e}")
            return False
    return False

# --- CREATIVE GENERATORS ---
def generate_plot(category):
    heroes = ["A retired ninja", "A radioactive hamster", "A time-traveling teen", "A cyborg detective", "A slime knight"]
    villains = ["an evil AI", "a sludge monster", "a corrupted politician", "an alien warlord", "a shadow demon"]
    if category == "Action 💥":
        conflicts = ["plants a bomb in the city", "kidnaps the president", "starts a robot uprising", "steals a nuclear code"]
    elif category == "Mystery 🕵️‍♂️":
        conflicts = ["frames the hero for a crime", "vanishes from a locked room", "replaces people with clones", "steals a famous artifact"]
    elif category == "Sci-Fi 👽":
        conflicts = ["rewrites the timeline", "opens a portal to a dark dimension", "turns off the sun", "hacks gravity"]
    else:
        conflicts = ["steals all the candy", "paints the moon red", "turns dogs into cats"]
    settings = ["in a neon city", "under the ocean", "on Mars", "inside a video game", "in a floating castle"]
    return f"{random.choice(heroes)} must fight {random.choice(villains)} who {random.choice(conflicts)} {random.choice(settings)}."

def get_daily_challenge():
    challenges = [
        "Draw a hero's secret hideout.", "Sketch a villain's main weapon.", 
        "Design a logo for a superhero team.", "Draw a character eating their favorite food.",
        "Create a sidekick based on a household appliance.", "Draw a scene from the villain's childhood."
    ]
    day_num = datetime.now().timetuple().tm_yday
    return challenges[day_num % len(challenges)]

# --- PAGE CONFIG & STYLE ---
st.set_page_config(page_title="Joe's Comic Studio", page_icon="🦇", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@300;400;700&display=swap');
    .stApp, .stMarkdown, .stText, p, div, input, textarea, button {
        font-family: 'Comic Neue', cursive !important;
        font-weight: 400;
        font-size: 18px;
    }
    h1, h2, h3 { 
        font-family: 'Bangers', cursive !important; 
        color: #00adb5 !important; 
        letter-spacing: 2px;
        text-shadow: 2px 2px #000;
    }
    .intro-card {
        background-color: #262730; padding: 40px; border-radius: 15px;
        border: 4px solid #00adb5; text-align: center;
        box-shadow: 5px 5px 0px #00adb5;
    }
    .stat-box {
        background-color: #333; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;
    }
    .user-msg { background-color: #2b313e; padding: 10px; border-radius: 10px; text-align: right; margin-bottom: 10px; }
    .ai-msg { background-color: #00adb5; color: black; padding: 10px; border-radius: 10px; text-align: left; margin-bottom: 10px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'script_text' not in st.session_state:
    st.session_state['script_text'] = "TITLE: \nISSUE: \n\n[PAGE 1]\n"

if 'roster_loaded' not in st.session_state:
    # Try to load. If successful, toast.
    if initialize_roster():
        st.toast("🚀 Auto-loaded Full Roster!", icon="🦸")
    st.session_state['roster_loaded'] = True

def insert_text(text_to_add):
    st.session_state['script_text'] += f"\n\n{text_to_add}"

# ==========================================
# PART 1: THE WELCOME SCREEN
# ==========================================
if 'intro_seen' not in st.session_state:
    st.session_state['intro_seen'] = False

if not st.session_state['intro_seen']:
    st.balloons()
    st.markdown('<div class="intro-card">', unsafe_allow_html=True)
    st.title("🎄 Merry Christmas, Joe! 🎄")
    st.write("### Welcome to your Secret Headquarters.")
    st.markdown("""
    <div style="text-align: left; font-size: 20px;">
    <p>We know you have a universe of characters in your head. We built this software 
    so you can finally organize them like a professional Comic Book Creator.</p>
    <p>The world is waiting for your stories. Start creating.</p>
    <br>
    <p><strong>Love,<br>Paige and Uncle</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("🚀 ACCESS THE STUDIO", type="primary"):
        st.session_state['intro_seen'] = True
        st.rerun()

# ==========================================
# PART 2: THE STUDIO
# ==========================================
else:
    st.sidebar.title("🦇 Studio Tools")
    st.sidebar.markdown("---")
    
    # --- AUTO-DISCOVERY MODEL DEBUGGER ---
    if "valid_models" not in st.session_state:
        st.session_state.valid_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.session_state.valid_models.append(m.name)
        except Exception as e:
            st.sidebar.error(f"API Error: {e}")

    with st.sidebar.expander("🔑 API Status"):
        if st.session_state.valid_models:
            st.success(f"Connected! Found {len(st.session_state.valid_models)} models.")
        else:
            st.error("Could not find any models. Check API Key.")
    
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio("Go to:", [
        "💬 Chat with Hero", 
        "🦸 Character Vault", 
        "⏳ Universe Timeline", 
        "📝 Script Writer", 
        "📚 Portfolio", 
        "🎲 Idea Generator"
    ])

    # ----------------------------------------------------
    # CHAT WITH HERO
    # ----------------------------------------------------
    if mode == "💬 Chat with Hero":
        st.title("💬 Chat with your Characters")
        st.caption("Talk to them to flesh out their personality!")

        # UPDATED: Load all the new columns including Relationships
        cols_needed = ["Alias", "Name", "Role", "Origin", "Personality", "Power", "Image_Path", "Relationships", "Speaking Style", "Allies", "Enemies", "Catchphrase"]
        df = load_data(CHAR_FILE, cols_needed)
        
        if df.empty:
            st.warning("No characters found! Go to the Vault to create one.")
        else:
            char_list = df['Alias'].unique().tolist()
            selected_alias = st.selectbox("Who do you want to talk to?", char_list)
            char_data = df[df['Alias'] == selected_alias].iloc[0]

            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "current_char" not in st.session_state:
                st.session_state.current_char = ""
            
            if st.session_state.current_char != selected_alias:
                st.session_state.messages = []
                st.session_state.current_char = selected_alias

            c1, c2 = st.columns([1, 3])
            with c1:
                if char_data['Image_Path'] and os.path.exists(str(char_data['Image_Path'])):
                    st.image(str(char_data['Image_Path']), use_container_width=True)
                st.markdown(f"**{char_data['Role']}**")
                
                with st.expander("Cheat Sheet"):
                    st.caption(f"**Talks like:** {char_data['Speaking Style']}")
                    st.caption(f"**Likes/Hates:** {char_data['Relationships']}")
            
            with c2:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        st.markdown(f"<div class='user-msg'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='ai-msg'>🦸‍♂️ {msg['content']}</div>", unsafe_allow_html=True)

                if prompt := st.chat_input(f"Say something to {selected_alias}..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with c2:
                    with st.spinner(f"{selected_alias} is thinking..."):
                        # --- SMART MODEL SELECTION ---
                        chosen_model = "gemini-1.5-flash-latest" 
                        if st.session_state.valid_models:
                            # Prefer 1.5 flash over 2.5/experimental for stability
                            flash_options = [m for m in st.session_state.valid_models if "gemini-1.5-flash" in m]
                            if flash_options:
                                chosen_model = flash_options[0]
                            else:
                                chosen_model = st.session_state.valid_models[0]
                        
                        model = genai.GenerativeModel(chosen_model)
                        
                        system_prompt = f"""
                        You are playing the role of a character in a story.
                        
                        CHARACTER PROFILE:
                        - Name: {char_data['Name']} (Alias: {char_data['Alias']})
                        - Role: {char_data['Role']}
                        - Origin: {char_data['Origin']}
                        - Personality: {char_data['Personality']}
                        - Powers: {char_data['Power']}
                        
                        DEEP DIVE DETAILS:
                        - Relationships: {char_data['Relationships']}
                        - Speaking Style: {char_data['Speaking Style']}
                        - Allies: {char_data['Allies']}
                        - Enemies: {char_data['Enemies']}
                        - Catchphrase: {char_data['Catchphrase']}
                        
                        INSTRUCTIONS:
                        1. STAY IN CHARACTER. Use the "Speaking Style" described above.
                        2. Use your knowledge of "Relationships" to react to names mentioned.
                        3. Use your "Catchphrase" only if it fits naturally.
                        4. Keep responses conversational (2-4 sentences).
                        5. Do NOT act like an AI assistant. You ARE the character.
                        """
                        
                        full_prompt = system_prompt + "\n\nConversation History:\n"
                        for m in st.session_state.messages:
                            role = "User" if m["role"] == "user" else "You"
                            full_prompt += f"{role}: {m['content']}\n"
                        full_prompt += "You:"
                        
                        # --- TRY/EXCEPT WITH AUTO-RETRY ---
                        try:
                            response = model.generate_content(full_prompt)
                            ai_reply = response.text
                            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                            st.rerun()
                            
                        except Exception as e:
                            # CHECK FOR QUOTA ERROR (429)
                            if "429" in str(e):
                                st.warning(f"⚡ {selected_alias} needs a breather (Speed Limit hit). Waiting 35 seconds...")
                                time.sleep(35) # Wait for the quota to reset
                                try:
                                    # Retry once
                                    response = model.generate_content(full_prompt)
                                    ai_reply = response.text
                                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                                    st.rerun()
                                except Exception as e2:
                                     st.error("Still busy. Please try again in a minute.")
                            else:
                                st.error(f"Error connecting to AI: {e}")

    # 1. CHARACTER VAULT
    elif mode == "🦸 Character Vault":
        st.title("The Universe Database 🦸‍♂️")
        col_input, col_roster = st.columns([1, 2])
        
        with col_input:
            st.subheader("Create New Character")
            with st.container(border=True):
                name = st.text_input("Real Name")
                alias = st.text_input("Hero/Villain Name")
                universe = st.selectbox("Universe", ["Home", "Sci-Fi", "Fantasy", "Other"])
                role = st.text_input("Role / Archetype")
                age = st.text_input("Age")
                s1, s2 = st.columns(2)
                with s1: strength = st.text_input("Strength (1-10)")
                with s2: magic = st.text_input("Magic (1-10)")
                
                # New Fields Inputs
                relationships = st.text_area("Relationships (Friends/Rivals)")
                speaking_style = st.text_input("Speaking Style (Slang, Formal, etc)")
                
                origin = st.text_area("Origin Story", height=100)
                personality = st.text_area("Personality", height=80)
                power = st.text_area("Super Powers & Signature Moves", height=100)
                weakness = st.text_area("Weaknesses", height=60)
                costume = st.text_area("Costume Visuals", height=60)
                
                allies = st.text_input("Allies")
                enemies = st.text_input("Enemies")
                catchphrase = st.text_input("Catchphrase")
                
                uploaded_file = st.file_uploader("Upload Sketch", type=['png', 'jpg'])
                
                if st.button("Save to Vault", type="primary"):
                    if alias:
                        img_path = None
                        if uploaded_file:
                            img_path = save_image(uploaded_file, IMAGE_DIR, alias)
                        save_character(name, alias, universe, role, age, origin, personality, strength, magic, power, weakness, costume, relationships, speaking_style, allies, enemies, catchphrase, img_path)
                        st.success(f"Saved {alias}!")
                        st.rerun()
        
        with col_roster:
            cols_needed = ["Name", "Alias", "Universe", "Role", "Age", "Origin", "Personality", "Strength", "Magic", "Power", "Weakness", "Costume", "Image_Path", "Relationships"]
            df = load_data(CHAR_FILE, cols_needed)
            all_universes = ["All"] + list(df['Universe'].unique()) if not df.empty else ["All"]
            selected_universe = st.selectbox("Filter by Universe:", all_universes)
            if not df.empty:
                if selected_universe != "All":
                    df = df[df['Universe'] == selected_universe]
                df = df.iloc[::-1].reset_index(drop=True)
                for i in range(0, len(df), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df):
                            row = df.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                                        st.image(str(row['Image_Path']), use_container_width=True)
                                    st.markdown(f"### {row['Alias']}")
                                    st.caption(f"**{row['Name']}** | Age: {row['Age']} | {row['Role']}")
                                    s1, s2 = st.columns(2)
                                    s1.markdown(f"<div class='stat-box'>💪 STR: {row['Strength']}</div>", unsafe_allow_html=True)
                                    s2.markdown(f"<div class='stat-box'>✨ MAG: {row['Magic']}</div>", unsafe_allow_html=True)
                                    with st.expander("⚡ Powers & Weaknesses"):
                                        st.write(f"**Powers:**\n{row['Power']}")
                                        st.markdown("---")
                                        st.write(f"**Weakness:**\n{row['Weakness']}")
                                    with st.expander("📜 Origin & Personality"):
                                        st.write(f"**Origin:** {row['Origin']}")
                                        st.markdown("---")
                                        st.write(f"**Personality:** {row['Personality']}")
                                    with st.expander("❤️ Relationships"):
                                        st.write(row['Relationships'])
            else:
                st.info("Vault is empty. Add your first character on the left!")

    # 2. UNIVERSE TIMELINE
    elif mode == "⏳ Universe Timeline":
        st.title("⏳ Universe History")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("### Add Event")
            t_year = st.text_input("Year / Era", value="2024")
            t_event = st.text_area("What happened?")
            t_type = st.selectbox("Type", ["Origin Story", "Battle", "Alliance", "Catastrophe"])
            if st.button("Record Event"):
                save_timeline_event(t_year, t_event, t_type)
                st.success("Event Recorded.")
                st.rerun()
        with c2:
            st.write("### Chronology")
            df_t = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])
            if not df_t.empty:
                for index, row in df_t.iterrows():
                    st.markdown(f"""
                    <div style="border-left: 4px solid #00adb5; padding-left: 15px; margin-bottom: 15px;">
                        <h3 style="margin:0; color: #fff !important;">{row['Year']}</h3>
                        <span style="background-color: #333; padding: 2px 8px; border-radius: 4px; font-size: 14px;">{row['Type']}</span>
                        <p style="margin-top: 5px; font-size: 18px;">{row['Event']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No history recorded yet.")

    # 3. SCRIPT WRITER
    elif mode == "📝 Script Writer":
        st.title("Script Editor 💬")
        st.write("Quick Insert:")
        b1, b2, b3, b4 = st.columns(4)
        b1.button("[PANEL]", on_click=insert_text, args=("[PANEL X]",))
        b2.button("CAPTION", on_click=insert_text, args=("CAPTION: ",))
        b3.button("DIALOGUE", on_click=insert_text, args=("CHARACTER: \"(Dialogue)\"",))
        b4.button("SFX 💥", on_click=insert_text, args=("(SFX: BOOM!)",))
        text_area = st.text_area("Write your script here...", height=500, key="script_text")
        st.download_button("Download Script", text_area, file_name="comic_script.txt")

    # 4. PORTFOLIO
    elif mode == "📚 Portfolio":
        st.title("Professional Portfolio 🎨")
        tab1, tab2 = st.tabs(["📤 Upload", "🖼️ Gallery"])
        with tab1:
            p_title = st.text_input("Title")
            p_issue = st.text_input("Issue #")
            p_desc = st.text_area("Description")
            p_file = st.file_uploader("Upload Art", type=['png', 'jpg'])
            if st.button("Add to Portfolio", type="primary"):
                if p_title and p_file:
                    save_portfolio_entry(p_title, p_issue, p_desc, p_file)
                    st.success("Uploaded!")
                    st.rerun()
        with tab2:
            df_p = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
            if not df_p.empty:
                cols = st.columns(3)
                for index, row in df_p.iterrows():
                    with cols[index % 3]:
                        if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                            st.image(str(row['Image_Path']), use_container_width=True)
                        st.markdown(f"**{row['Title']}** #{row['Issue']}")
                        st.caption(row['Description'])
            else:
                st.info("No art uploaded yet.")

    # 5. IDEA GENERATOR
    elif mode == "🎲 Idea Generator":
        st.title("The Idea Machine 💡")
        cat = st.selectbox("Choose Genre:", ["Action 💥", "Mystery 🕵️‍♂️", "Sci-Fi 👽", "Random 🎲"])
        if st.button("Generate Plot", type="primary"):
            st.success(generate_plot(cat))import streamlit as st
import pandas as pd
import random
import os
import shutil
import time
import warnings # Added to control warnings
from datetime import datetime
import google.generativeai as genai 

# --- SUPPRESS WARNINGS ---
# This hides the "FutureWarning" from Google and other libraries to keep the app clean
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIGURATION ---
# Note: For production, move this to st.secrets
GOOGLE_API_KEY = "AIzaSyCr9K-vEUEk16cYuzFQYAjJVLwMppTS8WA"
genai.configure(api_key=GOOGLE_API_KEY)

# --- FILE & FOLDER SETUP ---
CHAR_FILE = "characters.csv"
PORTFOLIO_FILE = "portfolio.csv"
TIMELINE_FILE = "timeline.csv"

ROSTER_FILES = ["roster_completed.csv"]

IMAGE_DIR = "character_images"
PORTFOLIO_DIR = "portfolio_images"

for folder in [IMAGE_DIR, PORTFOLIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- BACKEND FUNCTIONS ---

def load_data(file_path, columns):
    """
    Robust data loader that handles missing files, empty files,
    and missing columns automatically.
    """
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    
    try:
        df = pd.read_csv(file_path)
        
        # Auto-repair: Add any missing columns 
        missing_cols = set(columns) - set(df.columns)
        if missing_cols:
            for col in missing_cols:
                df[col] = None
        
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

def save_character(name, alias, universe, role, age, origin, personality, strength, magic, power, weakness, costume, relationships, speaking_style, allies, enemies, catchphrase, image_path):
    columns = [
        "Name", "Alias", "Universe", "Role", "Age", 
        "Origin", "Personality", "Strength", "Magic",
        "Power", "Weakness", "Costume", 
        "Relationships", "Speaking Style", "Allies", "Enemies", "Catchphrase",
        "Image_Path"
    ]
    df = load_data(CHAR_FILE, columns)
    
    if not df.empty:
        df = df[df['Alias'] != alias]

    new_entry = pd.DataFrame([{
        "Name": name, "Alias": alias, "Universe": universe, "Role": role, "Age": age,
        "Origin": origin, "Personality": personality, "Strength": strength, "Magic": magic,
        "Power": power, "Weakness": weakness, "Costume": costume, 
        "Relationships": relationships, "Speaking Style": speaking_style,
        "Allies": allies, "Enemies": enemies, "Catchphrase": catchphrase,
        "Image_Path": image_path
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(CHAR_FILE, index=False)

def save_portfolio_entry(title, issue_num, description, image_file):
    image_path = save_image(image_file, PORTFOLIO_DIR, title)
    df = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
    new_entry = pd.DataFrame([{
        "Title": title, "Issue": issue_num, "Description": description, "Image_Path": image_path
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(PORTFOLIO_FILE, index=False)

def save_timeline_event(year, event, type):
    df = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])
    new_entry = pd.DataFrame([{ "Year": year, "Event": event, "Type": type }])
    df = pd.concat([df, new_entry], ignore_index=True)
    try:
        df["Year"] = df["Year"].astype(int)
        df = df.sort_values(by="Year")
    except:
        pass 
    df.to_csv(TIMELINE_FILE, index=False)

def initialize_roster():
    target_file = None
    for f in ROSTER_FILES:
        if os.path.exists(f):
            target_file = f
            break
            
    if target_file and (not os.path.exists(CHAR_FILE) or os.stat(CHAR_FILE).st_size < 10):
        try:
            ex_df = pd.read_csv(target_file)
            
            ex_df.columns = ex_df.columns.str.strip()
            
            if 'Hero Name' in ex_df.columns:
                ex_df = ex_df.dropna(subset=['Hero Name'])

            for index, row in ex_df.iterrows():
                # Image Handling
                img_filename = row.get('Picture Link', None)
                if pd.isna(img_filename) or str(img_filename).strip() == "":
                        img_filename = row.get('Uploaded Sketch', None)
                final_img_path = None
                if pd.notna(img_filename) and str(img_filename).lower() != 'nan':
                    img_filename = str(img_filename).strip()
                    target_path = os.path.join(IMAGE_DIR, img_filename)
                    if os.path.exists(img_filename): 
                        shutil.copy(img_filename, target_path)
                        final_img_path = target_path
                    elif os.path.exists(target_path):
                        final_img_path = target_path
                
                # Power Text
                power_text = str(row.get('Super Powers', ''))
                sig_move = row.get('Signature Move', '')
                if pd.notna(sig_move) and sig_move:
                    power_text += f"\n\n💥 Signature Move: {sig_move}"
                
                # Save Character
                save_character(
                    name=row.get('Real Name', 'Unknown'),
                    alias=row.get('Hero Name', 'Unknown'),
                    universe=row.get('Universe', 'Unsorted'),
                    role=row.get('Role / Archetype', 'Hero'),
                    age=row.get('Age', 'Unknown'),
                    origin=row.get('Origin', ''),
                    personality=row.get('Personality', ''),
                    strength=row.get('Strength', '0/10'),
                    magic=row.get('Magic', '0/10'),
                    power=power_text,
                    weakness=row.get('Weaknesses', ''),
                    costume=row.get('Costume / Visuals', ''),
                    relationships=row.get('Relationships', ''),
                    speaking_style=row.get('Speaking Style', ''),
                    allies=row.get('Allies', ''),
                    enemies=row.get('Enemies', ''),
                    catchphrase=row.get('Catchphrase', ''),
                    image_path=final_img_path
                )
            return True 
        except Exception as e:
            print(f"Error loading : {e}")
            return False
    return False

# --- CREATIVE GENERATORS ---
def generate_plot(category):
    heroes = ["A retired ninja", "A radioactive hamster", "A time-traveling teen", "A cyborg detective", "A slime knight"]
    villains = ["an evil AI", "a sludge monster", "a corrupted politician", "an alien warlord", "a shadow demon"]
    if category == "Action 💥":
        conflicts = ["plants a bomb in the city", "kidnaps the president", "starts a robot uprising", "steals a nuclear code"]
    elif category == "Mystery 🕵️‍♂️":
        conflicts = ["frames the hero for a crime", "vanishes from a locked room", "replaces people with clones", "steals a famous artifact"]
    elif category == "Sci-Fi 👽":
        conflicts = ["rewrites the timeline", "opens a portal to a dark dimension", "turns off the sun", "hacks gravity"]
    else:
        conflicts = ["steals all the candy", "paints the moon red", "turns dogs into cats"]
    settings = ["in a neon city", "under the ocean", "on Mars", "inside a video game", "in a floating castle"]
    return f"{random.choice(heroes)} must fight {random.choice(villains)} who {random.choice(conflicts)} {random.choice(settings)}."

def get_daily_challenge():
    challenges = [
        "Draw a hero's secret hideout.", "Sketch a villain's main weapon.", 
        "Design a logo for a superhero team.", "Draw a character eating their favorite food.",
        "Create a sidekick based on a household appliance.", "Draw a scene from the villain's childhood."
    ]
    day_num = datetime.now().timetuple().tm_yday
    return challenges[day_num % len(challenges)]

# --- PAGE CONFIG & STYLE ---
st.set_page_config(page_title="Joe's Comic Studio", page_icon="🦇", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@300;400;700&display=swap');
    .stApp, .stMarkdown, .stText, p, div, input, textarea, button {
        font-family: 'Comic Neue', cursive !important;
        font-weight: 400;
        font-size: 18px;
    }
    h1, h2, h3 { 
        font-family: 'Bangers', cursive !important; 
        color: #00adb5 !important; 
        letter-spacing: 2px;
        text-shadow: 2px 2px #000;
    }
    .intro-card {
        background-color: #262730; padding: 40px; border-radius: 15px;
        border: 4px solid #00adb5; text-align: center;
        box-shadow: 5px 5px 0px #00adb5;
    }
    .stat-box {
        background-color: #333; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;
    }
    .user-msg { background-color: #2b313e; padding: 10px; border-radius: 10px; text-align: right; margin-bottom: 10px; }
    .ai-msg { background-color: #00adb5; color: black; padding: 10px; border-radius: 10px; text-align: left; margin-bottom: 10px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'script_text' not in st.session_state:
    st.session_state['script_text'] = "TITLE: \nISSUE: \n\n[PAGE 1]\n"

if 'roster_loaded' not in st.session_state:
    if initialize_roster():
        st.toast("🚀 Auto-loaded Full Roster!", icon="🦸")
    st.session_state['roster_loaded'] = True

def insert_text(text_to_add):
    st.session_state['script_text'] += f"\n\n{text_to_add}"

# ==========================================
# PART 1: THE WELCOME SCREEN
# ==========================================
if 'intro_seen' not in st.session_state:
    st.session_state['intro_seen'] = False

if not st.session_state['intro_seen']:
    st.balloons()
    st.markdown('<div class="intro-card">', unsafe_allow_html=True)
    st.title("🎄 Merry Christmas, Joe! 🎄")
    st.write("### Welcome to your Secret Headquarters.")
    st.markdown("""
    <div style="text-align: left; font-size: 20px;">
    <p>We know you have a universe of characters in your head. We built this software 
    so you can finally organize them like a professional Comic Book Creator.</p>
    <p>The world is waiting for your stories. Start creating.</p>
    <br>
    <p><strong>Love,<br>Paige and Uncle</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("🚀 ACCESS THE STUDIO", type="primary"):
        st.session_state['intro_seen'] = True
        st.rerun()

# ==========================================
# PART 2: THE STUDIO
# ==========================================
else:
    st.sidebar.title("🦇 Studio Tools")
    st.sidebar.markdown("---")
    
    # --- AUTO-DISCOVERY MODEL DEBUGGER ---
    if "valid_models" not in st.session_state:
        st.session_state.valid_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.session_state.valid_models.append(m.name)
        except Exception as e:
            st.sidebar.error(f"API Error: {e}")

    with st.sidebar.expander("🔑 API Status"):
        if st.session_state.valid_models:
            st.success(f"Connected! Found {len(st.session_state.valid_models)} models.")
        else:
            st.error("Could not find any models. Check API Key.")
    
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio("Go to:", [
        "💬 Chat with Hero", 
        "🦸 Character Vault", 
        "⏳ Universe Timeline", 
        "📝 Script Writer", 
        "📚 Portfolio", 
        "🎲 Idea Generator"
    ])

    # ----------------------------------------------------
    # CHAT WITH HERO
    # ----------------------------------------------------
    if mode == "💬 Chat with Hero":
        st.title("💬 Chat with your Characters")
        st.caption("Talk to them to flesh out their personality!")

        # Load all columns
        cols_needed = ["Alias", "Name", "Role", "Origin", "Personality", "Power", "Image_Path", "Relationships", "Speaking Style", "Allies", "Enemies", "Catchphrase"]
        df = load_data(CHAR_FILE, cols_needed)
        
        if df.empty:
            st.warning("No characters found! Go to the Vault to create one.")
        else:
            char_list = df['Alias'].unique().tolist()
            selected_alias = st.selectbox("Who do you want to talk to?", char_list)
            char_data = df[df['Alias'] == selected_alias].iloc[0]

            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "current_char" not in st.session_state:
                st.session_state.current_char = ""
            
            if st.session_state.current_char != selected_alias:
                st.session_state.messages = []
                st.session_state.current_char = selected_alias

            c1, c2 = st.columns([1, 3])
            with c1:
                # FIXED: replaced use_container_width=True with width="stretch"
                if char_data['Image_Path'] and os.path.exists(str(char_data['Image_Path'])):
                    st.image(str(char_data['Image_Path']), width="stretch")
                st.markdown(f"**{char_data['Role']}**")
                
                with st.expander("Cheat Sheet"):
                    st.caption(f"**Talks like:** {char_data['Speaking Style']}")
                    st.caption(f"**Likes/Hates:** {char_data['Relationships']}")
            
            with c2:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        st.markdown(f"<div class='user-msg'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='ai-msg'>🦸‍♂️ {msg['content']}</div>", unsafe_allow_html=True)

                if prompt := st.chat_input(f"Say something to {selected_alias}..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with c2:
                    with st.spinner(f"{selected_alias} is thinking..."):
                        chosen_model = "gemini-1.5-flash-latest" 
                        if st.session_state.valid_models:
                            flash_options = [m for m in st.session_state.valid_models if "gemini-1.5-flash" in m]
                            if flash_options:
                                chosen_model = flash_options[0]
                            else:
                                chosen_model = st.session_state.valid_models[0]
                        
                        model = genai.GenerativeModel(chosen_model)
                        
                        system_prompt = f"""
                        You are playing the role of a character in a story.
                        
                        CHARACTER PROFILE:
                        - Name: {char_data['Name']} (Alias: {char_data['Alias']})
                        - Role: {char_data['Role']}
                        - Origin: {char_data['Origin']}
                        - Personality: {char_data['Personality']}
                        - Powers: {char_data['Power']}
                        
                        DEEP DIVE DETAILS:
                        - Relationships: {char_data['Relationships']}
                        - Speaking Style: {char_data['Speaking Style']}
                        - Allies: {char_data['Allies']}
                        - Enemies: {char_data['Enemies']}
                        - Catchphrase: {char_data['Catchphrase']}
                        
                        INSTRUCTIONS:
                        1. STAY IN CHARACTER. Use the "Speaking Style" described above.
                        2. Use your knowledge of "Relationships" to react to names mentioned.
                        3. Use your "Catchphrase" only if it fits naturally.
                        4. Keep responses conversational (2-4 sentences).
                        5. Do NOT act like an AI assistant. You ARE the character.
                        """
                        
                        full_prompt = system_prompt + "\n\nConversation History:\n"
                        for m in st.session_state.messages:
                            role = "User" if m["role"] == "user" else "You"
                            full_prompt += f"{role}: {m['content']}\n"
                        full_prompt += "You:"
                        
                        try:
                            response = model.generate_content(full_prompt)
                            ai_reply = response.text
                            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                            st.rerun()
                            
                        except Exception as e:
                            # CHECK FOR QUOTA ERROR (429)
                            if "429" in str(e):
                                st.warning(f"⚡ {selected_alias} needs a breather (Speed Limit hit). Waiting 35 seconds...")
                                time.sleep(35)
                                try:
                                    response = model.generate_content(full_prompt)
                                    ai_reply = response.text
                                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                                    st.rerun()
                                except Exception as e2:
                                     st.error("Still busy. Please try again in a minute.")
                            else:
                                st.error(f"Error connecting to AI: {e}")

    # 1. CHARACTER VAULT
    elif mode == "🦸 Character Vault":
        st.title("The Universe Database 🦸‍♂️")
        col_input, col_roster = st.columns([1, 2])
        
        with col_input:
            st.subheader("Create New Character")
            with st.container(border=True):
                name = st.text_input("Real Name")
                alias = st.text_input("Hero/Villain Name")
                universe = st.selectbox("Universe", ["Home", "Sci-Fi", "Fantasy", "Other"])
                role = st.text_input("Role / Archetype")
                age = st.text_input("Age")
                s1, s2 = st.columns(2)
                with s1: strength = st.text_input("Strength (1-10)")
                with s2: magic = st.text_input("Magic (1-10)")
                
                relationships = st.text_area("Relationships (Friends/Rivals)")
                speaking_style = st.text_input("Speaking Style (Slang, Formal, etc)")
                
                origin = st.text_area("Origin Story", height=100)
                personality = st.text_area("Personality", height=80)
                power = st.text_area("Super Powers & Signature Moves", height=100)
                weakness = st.text_area("Weaknesses", height=60)
                costume = st.text_area("Costume Visuals", height=60)
                
                allies = st.text_input("Allies")
                enemies = st.text_input("Enemies")
                catchphrase = st.text_input("Catchphrase")
                
                uploaded_file = st.file_uploader("Upload Sketch", type=['png', 'jpg'])
                
                if st.button("Save to Vault", type="primary"):
                    if alias:
                        img_path = None
                        if uploaded_file:
                            img_path = save_image(uploaded_file, IMAGE_DIR, alias)
                        save_character(name, alias, universe, role, age, origin, personality, strength, magic, power, weakness, costume, relationships, speaking_style, allies, enemies, catchphrase, img_path)
                        st.success(f"Saved {alias}!")
                        st.rerun()
        
        with col_roster:
            cols_needed = ["Name", "Alias", "Universe", "Role", "Age", "Origin", "Personality", "Strength", "Magic", "Power", "Weakness", "Costume", "Image_Path", "Relationships"]
            df = load_data(CHAR_FILE, cols_needed)
            all_universes = ["All"] + list(df['Universe'].unique()) if not df.empty else ["All"]
            selected_universe = st.selectbox("Filter by Universe:", all_universes)
            if not df.empty:
                if selected_universe != "All":
                    df = df[df['Universe'] == selected_universe]
                df = df.iloc[::-1].reset_index(drop=True)
                for i in range(0, len(df), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(df):
                            row = df.iloc[i + j]
                            with cols[j]:
                                with st.container(border=True):
                                    # FIXED: replaced use_container_width=True with width="stretch"
                                    if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                                        st.image(str(row['Image_Path']), width="stretch")
                                    st.markdown(f"### {row['Alias']}")
                                    st.caption(f"**{row['Name']}** | Age: {row['Age']} | {row['Role']}")
                                    s1, s2 = st.columns(2)
                                    s1.markdown(f"<div class='stat-box'>💪 STR: {row['Strength']}</div>", unsafe_allow_html=True)
                                    s2.markdown(f"<div class='stat-box'>✨ MAG: {row['Magic']}</div>", unsafe_allow_html=True)
                                    with st.expander("⚡ Powers & Weaknesses"):
                                        st.write(f"**Powers:**\n{row['Power']}")
                                        st.markdown("---")
                                        st.write(f"**Weakness:**\n{row['Weakness']}")
                                    with st.expander("📜 Origin & Personality"):
                                        st.write(f"**Origin:** {row['Origin']}")
                                        st.markdown("---")
                                        st.write(f"**Personality:** {row['Personality']}")
                                    with st.expander("❤️ Relationships"):
                                        st.write(row['Relationships'])
            else:
                st.info("Vault is empty. Add your first character on the left!")

    # 2. UNIVERSE TIMELINE
    elif mode == "⏳ Universe Timeline":
        st.title("⏳ Universe History")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("### Add Event")
            t_year = st.text_input("Year / Era", value="2024")
            t_event = st.text_area("What happened?")
            t_type = st.selectbox("Type", ["Origin Story", "Battle", "Alliance", "Catastrophe"])
            if st.button("Record Event"):
                save_timeline_event(t_year, t_event, t_type)
                st.success("Event Recorded.")
                st.rerun()
        with c2:
            st.write("### Chronology")
            df_t = load_data(TIMELINE_FILE, ["Year", "Event", "Type"])
            if not df_t.empty:
                for index, row in df_t.iterrows():
                    st.markdown(f"""
                    <div style="border-left: 4px solid #00adb5; padding-left: 15px; margin-bottom: 15px;">
                        <h3 style="margin:0; color: #fff !important;">{row['Year']}</h3>
                        <span style="background-color: #333; padding: 2px 8px; border-radius: 4px; font-size: 14px;">{row['Type']}</span>
                        <p style="margin-top: 5px; font-size: 18px;">{row['Event']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No history recorded yet.")

    # 3. SCRIPT WRITER
    elif mode == "📝 Script Writer":
        st.title("Script Editor 💬")
        st.write("Quick Insert:")
        b1, b2, b3, b4 = st.columns(4)
        b1.button("[PANEL]", on_click=insert_text, args=("[PANEL X]",))
        b2.button("CAPTION", on_click=insert_text, args=("CAPTION: ",))
        b3.button("DIALOGUE", on_click=insert_text, args=("CHARACTER: \"(Dialogue)\"",))
        b4.button("SFX 💥", on_click=insert_text, args=("(SFX: BOOM!)",))
        text_area = st.text_area("Write your script here...", height=500, key="script_text")
        st.download_button("Download Script", text_area, file_name="comic_script.txt")

    # 4. PORTFOLIO
    elif mode == "📚 Portfolio":
        st.title("Professional Portfolio 🎨")
        tab1, tab2 = st.tabs(["📤 Upload", "🖼️ Gallery"])
        with tab1:
            p_title = st.text_input("Title")
            p_issue = st.text_input("Issue #")
            p_desc = st.text_area("Description")
            p_file = st.file_uploader("Upload Art", type=['png', 'jpg'])
            if st.button("Add to Portfolio", type="primary"):
                if p_title and p_file:
                    save_portfolio_entry(p_title, p_issue, p_desc, p_file)
                    st.success("Uploaded!")
                    st.rerun()
        with tab2:
            df_p = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
            if not df_p.empty:
                cols = st.columns(3)
                for index, row in df_p.iterrows():
                    with cols[index % 3]:
                        # FIXED: replaced use_container_width=True with width="stretch"
                        if row['Image_Path'] and os.path.exists(str(row['Image_Path'])):
                            st.image(str(row['Image_Path']), width="stretch")
                        st.markdown(f"**{row['Title']}** #{row['Issue']}")
                        st.caption(row['Description'])
            else:
                st.info("No art uploaded yet.")

    # 5. IDEA GENERATOR
    elif mode == "🎲 Idea Generator":
        st.title("The Idea Machine 💡")
        cat = st.selectbox("Choose Genre:", ["Action 💥", "Mystery 🕵️‍♂️", "Sci-Fi 👽", "Random 🎲"])
        if st.button("Generate Plot", type="primary"):
            st.success(generate_plot(cat))