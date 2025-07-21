import streamlit as st
import base64
from io import BytesIO
import os

# --- Custom CSS for UI Styling ---
def load_css():
    st.markdown("""
    <style>
        .stApp {
            background-color: #1E1E1E;
            color: white;
        }
        .stButton>button {
            background-color: #4ECDC4;
            color: white;
            border-radius: 10px;
            padding: 8px 16px;
            margin: 2px;
        }
        .metadata-card {
            background-color: #2E2E2E;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session State ---
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'playlist' not in st.session_state:
    st.session_state.playlist = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

# --- Simplified Metadata Extraction ---
def get_metadata(file):
    return {
        'title': file.name if hasattr(file, 'name') else "Unknown Track",
        'artist': "Unknown Artist",
        'album': "Unknown Album",
        'duration': "0:00"
    }

# --- Audio Player Component ---
def audio_player():
    if st.session_state.current_song:
        audio_bytes = st.session_state.current_song.read()
        audio_str = f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}"
        
        autoplay = "autoplay" if st.session_state.is_playing else ""
        st.markdown(f"""
        <audio id="audio_player" controls {autoplay}>
            <source src="{audio_str}" type="audio/mp3">
        </audio>
        """, unsafe_allow_html=True)

# --- Main App ---
def main():
    load_css()
    st.title("🎧 Pure Python Music Player")
    
    # --- File Upload ---
    uploaded_files = st.file_uploader(
        "Upload music files (MP3, WAV, OGG)",
        type=["mp3", "wav", "ogg"],
        accept_multiple_files=True
    )
    
    if uploaded_files and not st.session_state.playlist:
        st.session_state.playlist = uploaded_files

    # --- Playlist Display ---
    if st.session_state.playlist:
        st.subheader("🎶 Playlist")
        for i, song in enumerate(st.session_state.playlist):
            cols = st.columns([1, 4])
            with cols[0]:
                if st.button("▶", key=f"play_{i}"):
                    st.session_state.current_index = i
                    st.session_state.current_song = song
                    st.session_state.is_playing = True
            with cols[1]:
                metadata = get_metadata(song)
                st.write(f"{i+1}. {metadata['title']}")

    # --- Current Song Display ---
    if st.session_state.current_song:
        metadata = get_metadata(st.session_state.current_song)
        
        st.markdown(f"""
        <div class="metadata-card">
            <h3>{metadata['title']}</h3>
            <p>👨‍🎤 Artist: {metadata['artist']}</p>
            <p>💿 Album: {metadata['album']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        audio_player()
        
        # Player Controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏮ Previous") and len(st.session_state.playlist) > 1:
                st.session_state.current_index = (st.session_state.current_index - 1) % len(st.session_state.playlist)
                st.session_state.current_song = st.session_state.playlist[st.session_state.current_index]
                st.session_state.is_playing = True
                st.experimental_rerun()
        with col2:
            if st.button("⏭ Next") and len(st.session_state.playlist) > 1:
                st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.playlist)
                st.session_state.current_song = st.session_state.playlist[st.session_state.current_index]
                st.session_state.is_playing = True
                st.experimental_rerun()

if __name__ == "__main__":
    main()
