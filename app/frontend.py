import streamlit as st
import requests
import os
import plotly.graph_objects as go
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE
# ============================================
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []
if 'doc_chunks' not in st.session_state:
    st.session_state.doc_chunks = {}
if 'show_chunks' not in st.session_state:
    st.session_state.show_chunks = False
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = "test_token"

API_BASE = "https://enterprise-rag-backend-pzgr.onrender.com"

# ============================================
# ENTERPRISE CSS
# ============================================
st.markdown("""
<style>
    .stApp { background: #0a0a1a; }
    .stMarkdown, p, h1, h2, h3, h4, div, span, label {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0E1117 !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span {
        color: #ffffff !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #6c63ff, #5a52d5) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #7b73ff, #6a62e5) !important;
        transform: scale(1.02);
    }
    .stTextInput input {
        color: #ffffff !important;
        background: #1a1a35 !important;
        border: 1px solid #2d2d5a !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #6c63ff !important;
        box-shadow: 0 0 20px rgba(108,99,255,0.1) !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888 !important;
        background: #1a1a35 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        border: 1px solid #2d2d5a !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: linear-gradient(135deg, #6c63ff, #5a52d5) !important;
        border-color: #6c63ff !important;
    }
    .stAlert { color: #ffffff !important; }
    .stSelectbox label { color: #ffffff !important; }
    .stFileUploader { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div style="background:linear-gradient(135deg,#1a1a3e,#2d1b69);padding:20px;border-radius:15px;border:1px solid #3d2a8a;margin-bottom:20px;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
        <div>
            <h1 style="color:#fff;margin:0;">🧠 Enterprise RAG System</h1>
            <p style="color:#8b83ff;margin:5px 0 0 0;">Intelligent Document Assistant • Enterprise Grade</p>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
            <span style="background:rgba(76,175,80,0.15);padding:4px 14px;border-radius:20px;font-size:11px;color:#4CAF50;border:1px solid rgba(76,175,80,0.2);">● ONLINE</span>
            <span style="background:rgba(108,99,255,0.12);padding:4px 14px;border-radius:20px;font-size:11px;color:#8b83ff;border:1px solid rgba(108,99,255,0.1);">⚡ v3.0.0</span>
            <span style="background:rgba(108,99,255,0.12);padding:4px 14px;border-radius:20px;font-size:11px;color:#8b83ff;border:1px solid rgba(108,99,255,0.1);">🔒 SECURE</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 🔐 Authentication")
    token_input = st.text_input("API Token", type="password", placeholder="Enter your API token", value=st.session_state.auth_token)
    if token_input:
        st.session_state.auth_token = token_input
        st.success("✅ Authenticated")
    
    st.markdown("---")
    st.markdown("### 📂 Document Management")
    
    uploaded_files = st.file_uploader("📤 Upload PDF Files", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files and st.session_state.auth_token:
        if st.button("🚀 Process Documents"):
            with st.spinner("Processing..."):
                for file in uploaded_files:
                    try:
                        os.makedirs("uploads", exist_ok=True)
                        temp_path = f"uploads/{file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        
                        with open(temp_path, "rb") as f:
                            files = {"files": (file.name, f, "application/pdf")}
                            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                            response = requests.post(
                                f"{API_BASE}/api/upload",
                                files=files,
                                headers=headers,
                                timeout=60
                            )
                        
                        if response.status_code == 200:
                            data = response.json()
                            if file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(file.name)
                            for result in data.get("results", []):
                                if result.get("status") == "completed":
                                    st.session_state.doc_chunks[file.name] = {
                                        "doc_id": result.get("document_id"),
                                        "total_chunks": result.get("total_chunks", 0)
                                    }
                            st.success(f"✅ {file.name} processed!")
                            st.balloons()
                        else:
                            st.error(f"❌ Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    elif uploaded_files and not st.session_state.auth_token:
        st.warning("⚠️ Please enter API token first")
    
    st.markdown("---")
    
    if st.session_state.uploaded_docs:
        st.markdown("### 📄 Processed Documents")
        for doc in st.session_state.uploaded_docs:
            chunk_info = st.session_state.doc_chunks.get(doc, {})
            chunks = chunk_info.get("total_chunks", 0)
            st.markdown(f"📄 {doc[:20]}... `{chunks} chunks`")
    else:
        st.info("📂 No documents uploaded")
    
    st.markdown("---")
    
    total_docs = len(st.session_state.uploaded_docs)
    total_chunks = sum(info.get("total_chunks", 0) for info in st.session_state.doc_chunks.values())
    st.markdown("### 📊 System Stats")
    st.markdown(f"**Documents:** {total_docs}")
    st.markdown(f"**Chunks:** {total_chunks}")
    st.markdown(f"**Status:** 🟢 Active")

# ============================================
# TABS
# ============================================
tab1, tab2, tab3 = st.tabs(["💬 Chat Assistant", "📄 Document Chunks", "📊 Analytics"])

# ============================================
# TAB 1: CHAT
# ============================================
with tab1:
    st.markdown("### 💬 AI Chat Assistant")
    st.markdown("Ask questions about your uploaded documents")
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.last_question = ""
            st.rerun()
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div style="background:linear-gradient(135deg,#6c63ff,#5a52d5);border-radius:18px 18px 4px 18px;padding:12px 20px;margin:8px 0;color:white;max-width:75%;float:right;clear:both;">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#1e1e45;border-radius:18px 18px 18px 4px;padding:12px 20px;margin:8px 0;color:#e0e0e0;max-width:75%;float:left;clear:both;border:1px solid #2d2d5a;">{msg["content"]}</div>', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.info("📤 Upload a PDF and ask a question!")
    
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Ask a question...", key="chat_input")
    with col2:
        if st.button("🚀 Send", use_container_width=True):
            if user_input:
                if not st.session_state.uploaded_docs:
                    st.warning("⚠️ Upload documents first!")
                elif not st.session_state.auth_token:
                    st.warning("⚠️ Enter API token in sidebar!")
                else:
                    if user_input.strip() == st.session_state.last_question:
                        st.warning("⚠️ Same question already asked!")
                    else:
                        st.session_state.last_question = user_input.strip()
                        st.session_state.messages.append({"role": "user", "content": user_input})
                        
                        with st.spinner("🤔 Analyzing..."):
                            try:
                                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                                response = requests.post(
                                    f"{API_BASE}/api/query",
                                    json={"query": user_input, "top_k": 3},
                                    headers=headers,
                                    timeout=30
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": data.get("answer", "No answer")
                                    })
                                else:
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ Error: {response.status_code}"
                                    })
                            except Exception as e:
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"❌ Error: {str(e)}"
                                })
                        st.rerun()

# ============================================
# TAB 2: DOCUMENT CHUNKS - CLEAR CARD DISPLAY
# ============================================
with tab2:
    st.markdown("### 📄 Document Chunks")
    st.markdown("View all chunks and their summaries")
    st.markdown("---")
    
    if not st.session_state.uploaded_docs:
        st.info("📂 No documents uploaded")
    else:
        selected_doc = st.selectbox("Select Document", st.session_state.uploaded_docs)
        
        if selected_doc:
            try:
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                response = requests.get(f"{API_BASE}/api/documents", headers=headers)
                
                if response.status_code == 200:
                    docs_data = response.json().get("documents", [])
                    
                    doc_info = None
                    for doc in docs_data:
                        if doc.get("filename") == selected_doc:
                            doc_info = doc
                            break
                    
                    if doc_info:
                        total_chunks = doc_info.get("total_chunks", 0)
                        summaries = doc_info.get("summaries", [])
                        chunks = doc_info.get("chunks", [])
                        
                        # Stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"""
                            <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
                                <div style="font-size:32px;font-weight:700;background:linear-gradient(135deg,#6c63ff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_chunks}</div>
                                <div style="color:#888;font-size:13px;">Total Chunks</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                            <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
                                <div style="font-size:32px;font-weight:700;color:#4CAF50;">✅</div>
                                <div style="color:#888;font-size:13px;">Status: {doc_info.get('status', 'unknown')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"""
                            <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
                                <div style="font-size:32px;font-weight:700;color:#fff;">📄</div>
                                <div style="color:#888;font-size:13px;">{doc_info.get('filename', 'Unknown')[:20]}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Show/Hide button
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            btn_label = "📚 Hide All Chunks" if st.session_state.show_chunks else f"📚 Show All {total_chunks} Chunks"
                            if st.button(btn_label, use_container_width=True):
                                st.session_state.show_chunks = not st.session_state.show_chunks
                                st.rerun()
                        
                        st.markdown("---")
                        
                        if st.session_state.show_chunks:
                            st.markdown("### 🧩 All Chunks")
                            
                            if chunks and summaries:
                                for i, (chunk, summary) in enumerate(zip(chunks, summaries)):
                                    st.markdown(f"""
                                    <div style="background:rgba(26,26,62,0.6);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.12);border-radius:12px;padding:20px 24px;margin:16px 0;">
                                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                                            <div style="color:#6c63ff;font-size:14px;font-weight:600;">📄 CHUNK {i+1} OF {total_chunks}</div>
                                            <div style="background:rgba(108,99,255,0.12);padding:2px 14px;border-radius:12px;font-size:11px;color:#8b83ff;">{len(chunk)} chars</div>
                                        </div>
                                        <div style="background:rgba(13,13,34,0.5);border-radius:8px;padding:14px 18px;margin:8px 0;border-left:3px solid #6c63ff;">
                                            <div style="color:#a78bfa;font-size:12px;font-weight:500;margin-bottom:4px;">📝 SUMMARY</div>
                                            <div style="color:#e8e8e8;font-size:14px;line-height:1.7;">{summary}</div>
                                        </div>
                                        <div style="background:rgba(13,13,34,0.3);border-radius:8px;padding:14px 18px;margin:8px 0;">
                                            <div style="color:#8b83ff;font-size:12px;font-weight:500;margin-bottom:4px;">📄 CONTENT</div>
                                            <div style="color:#c8c8c8;font-size:13px;line-height:1.7;">{chunk[:500]}...</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.warning("⚠️ No chunks found. Please re-upload the PDF.")
                        else:
                            if chunks and summaries:
                                st.markdown("### 📌 Preview (First 3 Chunks)")
                                st.markdown("👆 Click 'Show All Chunks' button above to view all chunks")
                                st.markdown("---")
                                
                                for i, (chunk, summary) in enumerate(zip(chunks[:3], summaries[:3])):
                                    st.markdown(f"""
                                    <div style="background:rgba(26,26,62,0.4);backdrop-filter:blur(8px);border:1px solid rgba(108,99,255,0.08);border-radius:10px;padding:16px 20px;margin:10px 0;border-left:3px solid #6c63ff;">
                                        <div style="display:flex;justify-content:space-between;align-items:center;">
                                            <span style="color:#6c63ff;font-size:12px;font-weight:600;">CHUNK {i+1}</span>
                                            <span style="color:#888;font-size:11px;">{len(chunk)} chars</span>
                                        </div>
                                        <div style="color:#e0e0e0;font-size:14px;margin-top:6px;line-height:1.6;">{summary[:200]}...</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if total_chunks > 3:
                                    st.info(f"📌 + {total_chunks - 3} more chunks. Click 'Show All Chunks' button above.")
                            else:
                                st.info("No chunks available")
                    else:
                        st.info("Document not found")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================
# TAB 3: ANALYTICS
# ============================================
with tab3:
    st.markdown("### 📊 Analytics Dashboard")
    st.markdown("---")
    
    total_docs = len(st.session_state.uploaded_docs)
    total_chunks = sum(info.get("total_chunks", 0) for info in st.session_state.doc_chunks.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;background:linear-gradient(135deg,#6c63ff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_docs}</div>
            <div style="color:#888;font-size:13px;">Documents</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;background:linear-gradient(135deg,#6c63ff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{total_chunks}</div>
            <div style="color:#888;font-size:13px;">Total Chunks</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background:rgba(26,26,62,0.5);backdrop-filter:blur(10px);border:1px solid rgba(108,99,255,0.1);border-radius:12px;padding:20px;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#4CAF50;">🟢</div>
            <div style="color:#888;font-size:13px;">System Active</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.uploaded_docs:
        st.markdown("---")
        st.markdown("### 📊 Chunk Distribution")
        
        doc_names = []
        chunk_counts = []
        for doc in st.session_state.uploaded_docs:
            chunk_info = st.session_state.doc_chunks.get(doc, {})
            chunk_count = chunk_info.get("total_chunks", 0)
            doc_names.append(doc[:15] + "...")
            chunk_counts.append(chunk_count)
        
        fig = go.Figure(data=[
            go.Bar(x=doc_names, y=chunk_counts, marker_color='#6c63ff', text=chunk_counts, textposition='outside', textfont=dict(color='#ffffff'))
        ])
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#888')
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div style="text-align:center;color:#444;font-size:12px;padding:20px 0;border-top:1px solid #1a1a3e;margin-top:30px;">
    Enterprise RAG System v3.0.0 • Built for MNC Deployments • © 2026
</div>
""", unsafe_allow_html=True)