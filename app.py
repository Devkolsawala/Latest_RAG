import streamlit as st
import os
from rag_engine import get_documents_text, get_text_chunks, get_vector_store, user_input
from chat_utils import load_chat_history, group_chat_history, save_chat_session, get_new_session_id, delete_chat_session
from datetime import datetime, timedelta
import uuid
import extra_streamlit_components as stx

# --- Page Configuration ---
st.set_page_config(
    page_title="DocChat AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "session_id" not in st.session_state:
    st.session_state.session_id = get_new_session_id()
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# --- Device ID Management ---
cookie_manager = stx.CookieManager(key="cookie_manager")
cookies = cookie_manager.get_all()
device_id = cookies.get("device_id") if cookies else None

if not device_id:
    device_id = str(uuid.uuid4())
    cookie_manager.set("device_id", device_id, expires_at=datetime.now() + timedelta(days=365))

# --- CSS & Theming Logic (Gemini Style) ---
def inject_custom_css():
    """Injects CSS for a clean, Gemini-like aesthetic."""
    
    bg_color = "#ffffff"
    sidebar_bg = "#f0f4f9"
    text_color = "#1f1f1f"
    secondary_text = "#444746"
    accent_color = "#0b57d0"
    hover_color = "#0842a0"
    
    user_bg = "#f0f4f9"
    user_text = "#1f1f1f"
    ai_bg = "#ffffff"
    ai_text = "#1f1f1f"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Google Sans', 'Roboto', sans-serif;
            color: {text_color};
            background-color: {bg_color};
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: none;
        }}

        header {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        h1, h2, h3 {{
            color: {text_color};
            font-weight: 500;
        }}
        
        .stButton > button {{
            background-color: #ffffff;
            color: {accent_color};
            border: 1px solid transparent;
            border-radius: 24px;
            transition: all 0.2s ease;
            font-weight: 500;
            padding: 0.5rem 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .stButton > button:hover {{
            background-color: #e8f0fe;
            color: {hover_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }}

        .primary-btn button {{
            background-color: {accent_color} !important;
            color: #ffffff !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        .primary-btn button:hover {{
            background-color: {hover_color} !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        .history-date {{
            font-size: 0.75rem;
            color: {secondary_text};
            margin-top: 15px;
            margin-bottom: 8px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding-left: 10px;
        }}
        
        [data-testid="stChatMessage"] {{
            padding: 1rem 0;
            background: transparent;
        }}
        
        [data-testid="stChatMessage"] .stChatMessageAvatar {{
            background-color: transparent;
        }}

        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
            padding: 10px 15px;
            border-radius: 18px;
            line-height: 1.6;
            max-width: 100%;
        }}
        
        [data-testid="stChatMessage"]:nth-child(odd) {{
            flex-direction: row-reverse; 
        }}
        [data-testid="stChatMessage"]:nth-child(odd) [data-testid="stMarkdownContainer"] {{
            background-color: {user_bg};
            color: {user_text};
            border-top-right-radius: 4px;
        }}
        
        [data-testid="stChatMessage"]:nth-child(even) [data-testid="stMarkdownContainer"] {{
            background-color: {ai_bg};
            color: {ai_text};
            padding-left: 0;
        }}
        
        [data-testid="stFileUploader"] {{
            background-color: #ffffff;
            border: 1px dashed #c4c7c5;
            border-radius: 12px;
            padding: 20px;
        }}
        
        .stChatInputContainer {{
            padding-bottom: 20px;
        }}
        
        .streamlit-expanderHeader {{
            background-color: transparent;
            color: {secondary_text};
            font-weight: 500;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- Sidebar UI ---
def render_sidebar():
    with st.sidebar:
        st.markdown("### ✨ DocChat")
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # New Chat Button (Primary)
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = get_new_session_id()
            st.session_state.processing_complete = False  # Reset processing state
            st.session_state.confirm_delete = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # File Upload
        st.markdown("#### 📄 Documents")
        pdf_docs = st.file_uploader(
            "Upload PDF/DOCX/TXT",
            accept_multiple_files=True,
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed"
        )
        
        if pdf_docs:
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("⚡ Process Files", use_container_width=True):
                with st.spinner("Analyzing documents..."):
                    raw_text = get_documents_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    # Pass session_id to create isolated vector store
                    get_vector_store(text_chunks, st.session_state.session_id)
                    st.session_state.processing_complete = True
                    st.toast("Documents processed successfully!", icon="✅")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()

        # Chat History
        st.markdown("#### 🕒 Recent")
        history = load_chat_history(user_id=device_id)
        
        if not history:
            st.caption("No recent chats found.")
        else:
            grouped_history = group_chat_history(history)
            
            for group_name, sessions in grouped_history.items():
                if sessions:
                    st.markdown(f'<div class="history-date">{group_name}</div>', unsafe_allow_html=True)
                    
                    for session in sessions:
                        is_active = st.session_state.session_id == session["id"]
                        
                        col_text, col_del = st.columns([0.85, 0.15])
                        
                        with col_text:
                            btn_label = f"📝 {session['title']}"
                            if is_active:
                                btn_label = f"🔵 {session['title']}"

                            if st.button(
                                btn_label, 
                                key=f"open_{session['id']}", 
                                use_container_width=True,
                                help=session['timestamp']
                            ):
                                st.session_state.messages = session["messages"]
                                st.session_state.session_id = session["id"]
                                st.session_state.confirm_delete = None
                                
                                # Check if vector store exists for this session
                                index_path = f"faiss_indexes/{session['id']}"
                                if os.path.exists(index_path):
                                    st.session_state.processing_complete = True
                                else:
                                    st.session_state.processing_complete = False
                                
                                st.rerun()
                                
                        with col_del:
                            if st.session_state.confirm_delete == session["id"]:
                                if st.button("✓", key=f"confirm_{session['id']}", type="primary"):
                                    delete_chat_session(session["id"])
                                    if st.session_state.session_id == session["id"]:
                                        st.session_state.messages = []
                                        st.session_state.session_id = get_new_session_id()
                                        st.session_state.processing_complete = False
                                    st.session_state.confirm_delete = None
                                    st.rerun()
                            else:
                                if st.button("✕", key=f"del_{session['id']}", help="Delete Chat"):
                                    st.session_state.confirm_delete = session["id"]
                                    st.rerun()

        st.divider()
        
        with st.expander("⚙️ Settings"):
            model_mapping = {
                "GPT-OSS": "openai/gpt-oss-20b:free",
                "Qwen 3": "qwen/qwen3-coder:free"
            }
            selected_model_name = st.radio(
                "Model",
                list(model_mapping.keys()),
                horizontal=True
            )
            st.session_state.selected_model = model_mapping[selected_model_name]

# --- Main Content ---
def main():
    inject_custom_css()
    render_sidebar()

    st.title("Chat with Documents")
    
    if not st.session_state.processing_complete:
        st.info("👈 Upload your documents in the sidebar to begin.")
        st.markdown("""
            <div style='text-align: center; padding: 50px; color: #444746; background-color: #f8f9fa; border-radius: 24px; margin-top: 20px;'>
                <h2 style='color: #1f1f1f; font-weight: 400;'>Hello, Human.</h2>
                <p style='font-size: 1.1rem;'>Upload a PDF or DOCX to get started.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                avatar = "✨" if message["role"] == "assistant" else "👤"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Ask anything about your documents..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)
            
            save_chat_session(st.session_state.session_id, st.session_state.messages, user_id=device_id)

            with st.chat_message("assistant", avatar="✨"):
                with st.spinner("Thinking..."):
                    # Pass session_id to use the correct vector store
                    response = user_input(
                        prompt, 
                        st.session_state.get("selected_model", "openai/gpt-oss-20b:free"),
                        st.session_state.session_id
                    )
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_chat_session(st.session_state.session_id, st.session_state.messages, user_id=device_id, title=None)

if __name__ == "__main__":
    main()