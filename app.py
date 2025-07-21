import streamlit as st
import base64
from io import BytesIO
import time
from pydub import AudioSegment  # Pure Python audio processing
import wave
import json

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
        .album-art {
            border-radius: 10px;
            width: 200px;
            height: 200px;
            object-fit: cover;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session State ---
if 'player_state' not in st.session_state:
    st.session_state.player_state = {
        'current_song': None,
        'playlist': [],
        'current_index': 0,
        'is_playing': False,
        'volume': 80,
        'duration': 0,
        'position': 0,
        'last_update': time.time()
    }

# --- Audio Processing (Pure Python) ---
def get_audio_duration(file):
    """Get duration using pure Python (wave module)"""
    try:
        if file.name.endswith('.wav'):
            with wave.open(file) as wf:
                return wf.getnframes() / float(wf.getframerate())
        else:
            # Fallback for MP3/OGG using pydub
            audio = AudioSegment.from_file(BytesIO(file.read()))
            return len(audio) / 1000  # Convert to seconds
    except:
        return 0

# --- Audio Player Component ---
def audio_player():
    if st.session_state.player_state['current_song']:
        audio_bytes = st.session_state.player_state['current_song'].read()
        audio_str = f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}"
        
        st.markdown(f"""
        <audio id="audio_player" 
               {'autoplay' if st.session_state.player_state['is_playing'] else ''}
               ontimeupdate="updateProgress()"
               onended="songEnded()">
            <source src="{audio_str}" type="audio/mp3">
        </audio>
        
        <script>
            let lastVolume = {st.session_state.player_state['volume'] / 100};
            const audio = document.getElementById('audio_player');
            audio.volume = lastVolume;
            
            function updateProgress() {{
                const progress = audio.currentTime / audio.duration * 100;
                window.parent.postMessage({{
                    type: 'progressUpdate',
                    progress: progress,
                    currentTime: audio.currentTime
                }}, '*');
            }}
            
            function songEnded() {{
                window.parent.postMessage({{
                    type: 'songEnded'
                }}, '*');
            }}
            
            // Volume control
            function setVolume(vol) {{
                audio.volume = vol / 100;
                lastVolume = vol / 100;
            }}
            
            // Sync play/pause from Python
            function syncPlayState(shouldPlay) {{
                if (shouldPlay && audio.paused) audio.play();
                if (!shouldPlay && !audio.paused) audio.pause();
            }}
        </script>
        """, unsafe_allow_html=True)

# --- Main App ---
def main():
    load_css()
    st.title("🎧 Enhanced Music Player")
    
    # JavaScript communication
    st.components.v1.html("""
    <script>
        window.addEventListener('message', function(event) {
            if (event.data.type === 'progressUpdate') {
                Streamlit.setComponentValue({
                    type: "progress",
                    progress: event.data.progress,
                    currentTime: event.data.currentTime
                });
            }
            if (event.data.type === 'songEnded') {
                Streamlit.setComponentValue({
                    type: "songEnded"
                });
            }
        });
    </script>
    """, height=0)
    
    # Handle JS events
    if 'player_state' in st.session_state:
        if st.experimental_get_query_params().get('type') == ["progress"]:
            st.session_state.player_state['position'] = st.experimental_get_query_params().get('currentTime', [0])[0]
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.subheader("🔊 Volume Control")
        new_volume = st.slider("Volume", 0, 100, st.session_state.player_state['volume'])
        if new_volume != st.session_state.player_state['volume']:
            st.session_state.player_state['volume'] = new_volume
            st.markdown(f"""
            <script>
                setVolume({new_volume});
            </script>
            """, unsafe_allow_html=True)
        
        # Progress display
        if st.session_state.player_state['duration'] > 0:
            mins, secs = divmod(int(st.session_state.player_state['position']), 60)
            total_mins, total_secs = divmod(int(st.session_state.player_state['duration']), 60)
            st.write(f"⏱ {mins}:{secs:02d} / {total_mins}:{total_secs:02d}")
    
    # --- File Upload ---
    uploaded_files = st.file_uploader(
        "Upload music files (MP3, WAV, OGG)",
        type=["mp3", "wav", "ogg"],
        accept_multiple_files=True
    )
    
    if uploaded_files and not st.session_state.player_state['playlist']:
        st.session_state.player_state['playlist'] = uploaded_files
        for file in uploaded_files:
            file.seek(0)  # Reset file pointer after checking duration
    
    # --- Playlist Display ---
    if st.session_state.player_state['playlist']:
        st.subheader("🎶 Playlist")
        for i, song in enumerate(st.session_state.player_state['playlist']):
            cols = st.columns([1, 4])
            with cols[0]:
                if st.button("▶", key=f"play_{i}"):
                    st.session_state.player_state['current_index'] = i
                    st.session_state.player_state['current_song'] = song
                    st.session_state.player_state['is_playing'] = True
                    st.session_state.player_state['duration'] = get_audio_duration(song)
                    song.seek(0)
            with cols[1]:
                st.write(f"{i+1}. {song.name}")
    
    # --- Current Song Display ---
    if st.session_state.player_state['current_song']:
        current_song = st.session_state.player_state['current_song']
        
        # Album art placeholder
        st.image("https://via.placeholder.com/200x200/4ECDC4/FFFFFF?text=No+Album+Art", 
                width=200, caption="Album Art Placeholder", use_column_width=False)
        
        # Metadata
        duration = st.session_state.player_state['duration']
        mins, secs = divmod(int(duration), 60)
        
        st.markdown(f"""
        <div class="metadata-card">
            <h3>{current_song.name}</h3>
            <p>👨‍🎤 Artist: Unknown Artist</p>
            <p>💿 Album: Unknown Album</p>
            <p>⏱ Duration: {mins}:{secs:02d}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio Player
        audio_player()
        
        # Player Controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏮ Previous") and len(st.session_state.player_state['playlist']) > 1:
                st.session_state.player_state['current_index'] = (
                    st.session_state.player_state['current_index'] - 1) % len(st.session_state.player_state['playlist'])
                st.session_state.player_state['current_song'] = st.session_state.player_state['playlist'][
                    st.session_state.player_state['current_index']]
                st.session_state.player_state['is_playing'] = True
                st.session_state.player_state['duration'] = get_audio_duration(
                    st.session_state.player_state['current_song'])
                st.experimental_rerun()
        with col2:
            play_pause_text = "⏸ Pause" if st.session_state.player_state['is_playing'] else "▶ Play"
            if st.button(play_pause_text):
                st.session_state.player_state['is_playing'] = not st.session_state.player_state['is_playing']
                st.markdown(f"""
                <script>
                    syncPlayState({str(st.session_state.player_state['is_playing']).lower()});
                </script>
                """, unsafe_allow_html=True)
        with col3:
            if st.button("⏭ Next") and len(st.session_state.player_state['playlist']) > 1:
                st.session_state.player_state['current_index'] = (
                    st.session_state.player_state['current_index'] + 1) % len(st.session_state.player_state['playlist'])
                st.session_state.player_state['current_song'] = st.session_state.player_state['playlist'][
                    st.session_state.player_state['current_index']]
                st.session_state.player_state['is_playing'] = True
                st.session_state.player_state['duration'] = get_audio_duration(
                    st.session_state.player_state['current_song'])
                st.experimental_rerun()

if __name__ == "__main__":
    main()
