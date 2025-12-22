import streamlit as st
import pandas as pd
import random
import os

# --- FILE & FOLDER SETUP ---
CHAR_FILE = "characters.csv"
PORTFOLIO_FILE = "portfolio.csv"
IMAGE_DIR = "character_images"
PORTFOLIO_DIR = "portfolio_images"

# Make sure the image folders exist
for folder in [IMAGE_DIR, PORTFOLIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- BACKEND FUNCTIONS ---
def load_data(file_path, columns):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(file_path)
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

def save_character(name, alias, power, weakness, allies, enemies, costume, image_file):
    image_path = save_image(image_file, IMAGE_DIR, alias)
    df = load_data(CHAR_FILE, ["Name", "Alias", "Power", "Weakness", "Allies", "Enemies", "Costume", "Image_Path"])
    new_entry = pd.DataFrame([{
        "Name": name, "Alias": alias, "Power": power, "Weakness": weakness,
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

# --- PLOT GENERATOR ---
def generate_plot():
    heroes = ["A retired ninja", "A radioactive hamster", "A time-traveling teen", "A cyborg detective", "A wizard", "A ghost", "A deep-sea diver", "A slime knight"]
    villains = ["an evil AI", "a sludge monster", "a corrupted politician", "an alien warlord", "a shadow demon", "a vampire", "a mad scientist"]
    conflicts = ["steals the Earth's gravity", "deletes the internet", "poisons the water", "rewrites history", "opens a portal to hell", "turns dogs to stone"]
    settings = ["in a neon city", "under the ocean", "on Mars", "inside a video game", "in a floating castle", "in a wild west town"]
    return f"{random.choice(heroes)} must fight {random.choice(villains)} who {random.choice(conflicts)} {random.choice(settings)}."

# --- PAGE CONFIG ---
st.set_page_config(page_title="Comic Creator Studio", page_icon="🦇", layout="wide")

# --- DARK THEME INJECTION (CSS) ---
st.markdown("""
<style>
    /* Force dark background */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    /* Style the Intro Card */
    .intro-card {
        background-color: #262730;
        padding: 40px;
        border-radius: 15px;
        border: 2px solid #00adb5; /* Cool Cyan Border */
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    h1, h2, h3 {
        color: #00adb5 !important; /* Cyan Headings */
    }
</style>
""", unsafe_allow_html=True)

# --- INTRO LOGIC ---
if 'intro_seen' not in st.session_state:
    st.session_state['intro_seen'] = False

# ==========================================
# PART 1: THE WELCOME SCREEN FOR JOE
# ==========================================
if not st.session_state['intro_seen']:
    st.balloons()
    
    # Custom HTML Card
    st.markdown('<div class="intro-card">', unsafe_allow_html=True)
    st.title("🎄 Merry Christmas, Joe! 🎄")
    st.write("### Welcome to your Secret Headquarters.")
    st.markdown("""
    <div style="text-align: left; font-size: 18px;">
    <p>We know you have a universe of characters in your head. We built this software 
    so you can finally organize them like a professional Comic Book Creator.</p>
    
    <p><strong>This Studio Includes:</strong></p>
    <ul>
    <li>🦸 <strong>Character Vault:</strong> Track powers, allies, and enemies.</li>
    <li>🎨 <strong>Portfolio:</strong> A gallery for your finished masterpieces.</li>
    <li>🎲 <strong>Idea Engine:</strong> Never get writer's block again.</li>
    </ul>
    
    <p>The world is waiting for your stories. Start creating.</p>
    <br>
    <p><strong>Love,<br>Paige and Uncle</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    if st.button("🚀 ACCESS THE STUDIO", type="primary"):
        st.session_state['intro_seen'] = True
        st.rerun()

# ==========================================
# PART 2: THE MAIN APP
# ==========================================
else:
    st.sidebar.title("🦇 Studio Tools")
    mode = st.sidebar.radio("Menu:", ["🦸 Character Vault", "📚 Portfolio (Finished Work)", "🎲 Idea Generator", "📝 Script Writer"])

    # 1. CHARACTER VAULT
    if mode == "🦸 Character Vault":
        st.title("The Universe Database 🦸‍♂️")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Create New Character")
            name = st.text_input("Real Name")
            alias = st.text_input("Hero/Villain Name")
            
            c1, c2 = st.columns(2)
            with c1: power = st.text_input("Power")
            with c2: weakness = st.text_input("Weakness")
            
            st.markdown("---")
            st.write("**Relationship Tracker**")
            allies = st.text_input("Allies (Friends)")
            enemies = st.text_input("Enemies (Rivals)")
            
            st.markdown("---")
            costume = st.text_area("Costume Visuals")
            uploaded_file = st.file_uploader("Upload Sketch", type=['png', 'jpg'])
            
            if st.button("Save Character", type="primary"):
                if alias:
                    save_character(name, alias, power, weakness, allies, enemies, costume, uploaded_file)
                    st.success(f"Saved {alias}!")
                    st.rerun()
        
        with col2:
            st.subheader("Character Roster")
            df = load_data(CHAR_FILE, ["Alias", "Name", "Power", "Image_Path", "Allies", "Enemies", "Weakness"])
            
            if not df.empty:
                for index, row in df.iloc[::-1].iterrows():
                    with st.expander(f"**{row['Alias']}**"):
                        if row['Image_Path'] and os.path.exists(row['Image_Path']):
                            st.image(row['Image_Path'])
                        
                        st.write(f"**Power:** {row['Power']}")
                        st.write(f"**Weakness:** {row['Weakness']}")
                        st.info(f"**🤝 Allies:** {row['Allies']}")
                        st.error(f"**⚔️ Enemies:** {row['Enemies']}")
            else:
                st.info("No characters yet.")

    # 2. PORTFOLIO
    elif mode == "📚 Portfolio (Finished Work)":
        st.title("My Professional Portfolio 🎨")
        st.write("Upload your FINISHED comic covers or pages here.")
        
        tab1, tab2 = st.tabs(["📤 Upload New Work", "🖼️ View Gallery"])
        
        with tab1:
            st.subheader("Add to Portfolio")
            p_title = st.text_input("Comic Title")
            p_issue = st.text_input("Issue Number / Page Number")
            p_desc = st.text_area("Description / Plot Summary")
            p_file = st.file_uploader("Upload Finished Art", type=['png', 'jpg'])
            
            if st.button("Add to Portfolio", type="primary"):
                if p_title and p_file:
                    save_portfolio_entry(p_title, p_issue, p_desc, p_file)
                    st.success("Added to portfolio!")
                else:
                    st.error("Title and Image required.")
                    
        with tab2:
            df_p = load_data(PORTFOLIO_FILE, ["Title", "Issue", "Description", "Image_Path"])
            if not df_p.empty:
                st.write("### The Collection")
                cols = st.columns(3)
                for index, row in df_p.iterrows():
                    col_idx = index % 3
                    with cols[col_idx]:
                        if row['Image_Path'] and os.path.exists(row['Image_Path']):
                            st.image(row['Image_Path'], use_container_width=True)
                        st.markdown(f"**{row['Title']}** (Issue {row['Issue']})")
                        st.caption(row['Description'])
            else:
                st.info("Your portfolio is empty. Time to draw!")

    # 3. IDEA GENERATOR
    elif mode == "🎲 Idea Generator":
        st.title("The Idea Machine 💡")
        if st.button("Generate Prompt", type="primary"):
            st.success(generate_plot())

    # 4. SCRIPT WRITER
    elif mode == "📝 Script Writer":
        st.title("Script Editor 💬")
        st.text_area("Write script...", height=400)