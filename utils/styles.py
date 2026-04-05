CHIP_DEFS = [
    {"coin": 10,   "label": "₹10"},
    {"coin": 50,   "label": "₹50"},
    {"coin": 100,  "label": "₹100"},
    {"coin": 500,  "label": "₹500"},
    {"coin": 1000, "label": "₹1K"},
]

def get_css():
    return """
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
    }

    /* Hide default elements */
    #MainMenu, footer, header {
        display: none !important;
    }

    /* Main container - clean spacing */
    .block-container {
        padding: 0.5rem 1rem 0.5rem !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }

    /* Button styling - clean and consistent */
    .stButton > button {
        padding: 0.35rem 0.5rem !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }

    .stButton > button:hover:not(:disabled) {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102,126,234,0.4) !important;
    }

    .stButton > button:active:not(:disabled) {
        transform: translateY(0) !important;
    }

    .stButton > button:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }

    /* Number input styling */
    .stNumberInput > div > div > input {
        padding: 0.35rem 0.5rem !important;
        font-size: 0.8rem !important;
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(102,126,234,0.3) !important;
        border-radius: 6px !important;
        color: white !important;
    }

    .stNumberInput > div > div > input:focus {
        border-color: #667eea !important;
        outline: none !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        height: 6px !important;
        border-radius: 3px !important;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        padding: 0.3rem 0.5rem !important;
        font-size: 0.8rem !important;
        background: rgba(255,255,255,0.05) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(255,255,255,0.1) !important;
    }

    /* Expander content */
    .streamlit-expanderContent {
        background: rgba(0,0,0,0.2) !important;
        border-radius: 8px !important;
        margin-top: 0.3rem !important;
        padding: 0.5rem !important;
    }

    /* Column spacing fix - prevent overlap */
    div[data-testid="column"] {
        padding: 0 0.25rem !important;
        margin: 0 !important;
    }

    /* Row containers */
    .row-widget {
        margin: 0 !important;
    }

    /* Fix for st.columns overlap */
    .stColumns {
        gap: 0.5rem !important;
    }

    /* Remove extra spacing */
    .element-container {
        margin: 0 !important;
    }

    /* Text area */
    .stTextArea > div > div > textarea {
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(102,126,234,0.3) !important;
        border-radius: 6px !important;
        color: white !important;
        font-size: 0.8rem !important;
        padding: 0.3rem !important;
    }

    /* Labels */
    .stNumberInput label, .stTextArea label {
        font-size: 0.7rem !important;
        color: #aaa !important;
        margin-bottom: 0.2rem !important;
    }

    /* Alert banner */
    .alert-banner {
        animation: fadeIn 0.5s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Responsive */
    @media (max-width: 768px) {
        .block-container {
            padding: 0.3rem 0.5rem 0.3rem !important;
        }

        .stButton > button {
            font-size: 0.7rem !important;
            padding: 0.25rem 0.3rem !important;
        }

        div[data-testid="column"] {
            padding: 0 0.15rem !important;
        }
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }

    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    </style>
    """