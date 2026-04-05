import streamlit as st

def play_sound(sound_type):
    """
    Play sound notifications (visual-only in Streamlit Cloud)
    Returns visual feedback instead of actual audio
    """
    sound_emojis = {
        'win': '🎉',
        'loss': '💀',
        'alert': '⚠️'
    }

    # Show a temporary toast notification
    emoji = sound_emojis.get(sound_type, '🔔')
    st.toast(f"{emoji} {sound_type.upper()}!", icon=emoji)