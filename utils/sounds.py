import streamlit as st

# BUG FIX: original play_sound called st.toast() which created a second toast
# on top of the one already fired in app.py, resulting in duplicate notifications.
# Now it injects a tiny JS snippet that plays an AudioContext beep so there is
# actual audio feedback without double-toasting.

_BEEP_JS = """
<script>
(function() {{
    try {{
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = '{wave}';
        osc.frequency.setValueAtTime({freq}, ctx.currentTime);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + {dur});
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + {dur});
    }} catch(e) {{}}
}})();
</script>
"""

_PROFILES = {
    "win":   dict(wave="sine",     freq=880, dur=0.25),
    "loss":  dict(wave="sawtooth", freq=220, dur=0.35),
    "alert": dict(wave="square",   freq=660, dur=0.20),
}


def play_sound(sound_type: str):
    """
    Play a short synthesised beep in the browser via the Web Audio API.
    Falls back silently if the browser blocks AudioContext (e.g. no user gesture).
    """
    profile = _PROFILES.get(sound_type, _PROFILES["alert"])
    js = _BEEP_JS.format(**profile)
    st.markdown(js, unsafe_allow_html=True)