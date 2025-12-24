import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# --- FILE & FOLDER SETUP ---
CHAR_FILE = "characters.csv"
PORTFOLIO_FILE = "portfolio.csv"
TIMELINE_FILE = "timeline.csv"
IMAGE_DIR = "character_images"
PORTFOLIO_DIR = "portfolio_images"

# Make sure the folders exist
for folder in [IMAGE_DIR, PORTFOLIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- BACKEND FUNCTIONS ---
def load_data(file_path, columns):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(file_path)
    # Ensure all columns exist (adds new columns like 'Background' if missing)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

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

# UPDATED: Added 'background' to save function
def save_character(name, alias, background, power, weakness, allies, enemies, costume, image_file):
    image_path = save_image(image_file, IMAGE_DIR, alias)
    # Load with new Background column
    df = load_data(CHAR_FILE, ["Name", "Alias", "Background", "Power", "Weakness", "Allies", "Enemies", "Costume", "Image_Path"])
    new_entry = pd.DataFrame([{
        "Name": name, "Alias": alias, "Background": background, 
        "Power": power, "Weakness": weakness,
        "Allies": allies, "Enemies": enemies, "Costume": costume, "Image_Path": image_path
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
</style>
""", unsafe_allow_html=True)

# --- SCRIPT HELPERS ---
if 'script_text' not in st.session_state:
    st.session_state['script_text'] = "TITLE: \nISSUE: \n\n[PAGE 1]\n"

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
    st.sidebar.markdown("**🔥 Daily Art Challenge**")
    st.sidebar.info(get_daily_challenge())
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio("Go to:", [
        "🦸 Character Vault", 
        "⏳ Universe Timeline", 
        "📝 Script Writer", 
        "📚 Portfolio", 
        "🎲 Idea Generator"
    ])

    # 1. CHARACTER VAULT
    if mode == "🦸 Character Vault":
        st.title("The Universe Database 🦸‍♂️")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Create New Character")
            name = st.text_input("Real Name")
            alias = st.text_input("Hero/Villain Name")
            
            # UPDATED: Background Field
            background = st.text_area("Origin Story / Background", height=150, help="How did they get their powers? Where are they from?")

            # UPDATED: Power & Weakness larger
            st.write("---")
            c1, c2 = st.columns(2)
            with c1: 
                power = st.text_area("Super Powers", height=100)
            with c2: 
                weakness = st.text_area("Weaknesses", height=100)
            
            allies = st.text_input("Allies")
            enemies = st.text_input("Enemies")
            costume = st.text_area("Costume Description")
            uploaded_file = st.file_uploader("Upload Sketch", type=['png', 'jpg'])
            
            if st.button("Save to Vault", type="primary"):
                if alias:
                    save_character(name, alias, background, power, weakness, allies, enemies, costume, uploaded_file)
                    st.success(f"Saved {alias}!")
                    st.rerun()
        
        with col2:
            st.subheader("Roster")
            # UPDATED: Loading Background column
            df = load_data(CHAR_FILE, ["Alias", "Background", "Power", "Image_Path", "Weakness", "Allies", "Enemies"])
            if not df.empty:
                for index, row in df.iloc[::-1].iterrows():
                    with st.expander(f"**{row['Alias']}**"):
                        if row['Image_Path'] and os.path.exists(row['Image_Path']):
                            st.image(row['Image_Path'])
                        
                        # UPDATED: Displaying Background
                        if row['Background']:
                            st.write(f"**📜 Origin:** {row['Background']}")
                            st.markdown("---")
                            
                        st.write(f"**⚡ Power:** {row['Power']}")
                        st.write(f"**⚠️ Weakness:** {row['Weakness']}")
                        st.info(f"Allies: {row['Allies']}")
                        st.error(f"Enemies: {row['Enemies']}")
            else:
                st.info("Vault is empty.")

    # 2. UNIVERSE TIMELINE
    elif mode == "⏳ Universe Timeline":
        st.title("⏳ Universe History")
        st.caption("Track the major events, wars, and origins of your world.")
        
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
                        if row['Image_Path'] and os.path.exists(row['Image_Path']):
                            st.image(row['Image_Path'], use_container_width=True)
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