import streamlit as st
import requests
import json
from datetime import datetime
import os

# ============================================================================
# Configuration and Setup
# ============================================================================
# Use environment variable for production, fallback to localhost for development
API_URL = "http://localhost:8000"

if not API_URL:
    st.error("API_URL environment variable is not set!")
    st.stop()

st.set_page_config(
    page_title="DocKeeper - Passport Scanner",
    page_icon="📄",
    layout="wide"
)

# Add authentication states
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# ============================================================================
# UI Styles
# ============================================================================

CUSTOM_CSS = """
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .card {
        background-color: var(--background-color);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .copyable-field {
        cursor: pointer;
        padding: 8px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 4px;
        background-color: var(--background-color);
        margin: 4px 0;
        color: var(--text-color);
    }
    .copyable-field:hover {
        background-color: rgba(128, 128, 128, 0.1);
    }
    .field-group {
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    .search-results {
        margin-top: 1rem;
    }
    .search-result-row {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr;
        gap: 1rem;
        padding: 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        align-items: center;
    }
    .search-result-row:hover {
        background-color: rgba(128, 128, 128, 0.1);
    }
    .field-name {
        font-weight: bold;
    }
    .document-link {
        text-align: right;
        color: #4CAF50;
    }
    .document-link a {
        text-decoration: none;
    }
    .document-link a:hover {
        text-decoration: underline;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# API Client Functions
# ============================================================================

def api_login(email: str, password: str) -> bool:
    """Handle user login through API."""
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.user = data["user_id"]
            st.session_state.access_token = data["access_token"]
            return True
        return False
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False

def api_signup(email: str, password: str) -> bool:
    """Handle user signup through API."""
    try:
        response = requests.post(
            f"{API_URL}/auth/signup",
            json={"email": email, "password": password}
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return False

def api_process_document(file) -> dict:
    """Process document through API."""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.post(
            f"{API_URL}/documents/process",
            files=files,
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error processing document: {response.json()['detail']}")
            return None
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
        return None

def api_get_documents() -> list:
    """Fetch documents through API."""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.get(
            f"{API_URL}/documents",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Please log in to view documents")
            st.session_state.authenticated = False
            st.rerun()
        return []
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")
        return []

def api_search_documents(query: str, min_score: int = 60) -> list:
    """Search documents through API."""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.get(
            f"{API_URL}/documents/search",
            params={"query": query, "min_score": min_score},
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Please log in to search documents")
            st.session_state.authenticated = False
            st.rerun()
        return []
    except Exception as e:
        st.error(f"Error searching documents: {str(e)}")
        return []

# ============================================================================
# UI Components
# ============================================================================

def display_data_card(data):
    """Display extracted data in a modern card layout."""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    for key, value in data.items():
        if key != 'processed_at':
            st.markdown('<div class="field-group">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f'<div class="field-title"><strong>{key.replace("_", " ").title()}</strong></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f'<div class="copyable-field field-value" onclick="navigator.clipboard.writeText(\'{value}\')">{value}</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_search_tab():
    """Render the Search Data tab."""
    st.markdown("### Search Documents")
    
    search_term = st.text_input("Enter search term", 
                               help="Search through your documents. The search is smart and will find partial matches.")
    
    if search_term:
        with st.spinner("Searching..."):
            results = api_search_documents(search_term)
            
            if not results:
                st.info("No matches found. Try using different search terms.")
            else:
                st.success(f"Found {len(results)} matches")
                
                st.markdown('<div class="search-results">', unsafe_allow_html=True)
                
                # Header
                st.markdown(
                    '<div class="search-result-row">'
                    '<div class="field-name">Field</div>'
                    '<div>Value</div>'
                    '<div class="document-link">Source Document</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                
                # Results
                for result in results:
                    doc_link = f'<a href="{result["pdf_url"]}" target="_blank">{result["document_name"]}</a>' if result["pdf_url"] else result["document_name"]
                    
                    st.markdown(
                        f'<div class="search-result-row">'
                        f'<div class="field-name">{result["field_name"].replace("_", " ").title()}</div>'
                        f'<div class="copyable-field">{result["field_value"]}</div>'
                        f'<div class="document-link">{doc_link}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)

def render_upload_tab():
    """Render the Upload Document tab."""
    st.markdown("### Upload your passport document for AI-powered data extraction")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                result = api_process_document(uploaded_file)
                
                if result:
                    st.success("Document processed successfully!")
                    display_data_card(result["fields"])
                    
                    json_str = json.dumps(result["fields"], indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name="passport_data.json",
                        mime="application/json"
                    )

def render_view_tab():
    """Render the View Documents tab."""
    st.markdown("### View Processed Documents")
    
    with st.spinner("Fetching documents..."):
        documents = api_get_documents()
        
        if not documents:
            st.info("No documents found.")
            return
            
        for doc in documents:
            with st.expander(f"Document: {doc['file_name']}"):
                # Document info
                st.markdown("### Document Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Type:** {doc['document_type']}")
                with col2:
                    processed_at = datetime.fromisoformat(doc['processed_at'])
                    st.markdown(f"**Processed:** {processed_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # PDF viewer/download link
                if doc.get('pdf_url'):
                    st.markdown("### Original Document")
                    st.markdown(f'<a href="{doc["pdf_url"]}" target="_blank" class="pdf-link">View Original PDF</a>', unsafe_allow_html=True)
                
                # Extracted Fields
                st.markdown("### Extracted Fields")
                if doc['fields']:
                    display_data_card(doc['fields'])
                    json_str = json.dumps(doc['fields'], indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"document_{doc['id']}_data.json",
                        mime="application/json",
                        key=f"download_{doc['id']}"
                    )
                else:
                    st.info("No fields extracted for this document.")

def handle_login():
    """Handle user login."""
    st.markdown("### Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if api_login(email, password):
                st.success("Successfully logged in!")
                st.rerun()

def handle_signup():
    """Handle user signup."""
    st.markdown("### Sign Up")
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords do not match!")
                return
                
            if api_signup(email, password):
                st.success("Account created successfully! Please log in.")

def handle_logout():
    """Handle user logout."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.success("Successfully logged out!")
    st.rerun()

def main():
    """Main application entry point."""
    st.title("📄 DocKeeper - Passport Scanner")
    
    # Authentication UI
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            handle_login()
        with tab2:
            handle_signup()
        return
    
    # Show logout button in sidebar when authenticated
    with st.sidebar:
        st.button("Logout", on_click=handle_logout)
    
    # Main application tabs
    tab1, tab2, tab3 = st.tabs(["Upload Document", "View Documents", "Search Data"])
    
    with tab1:
        render_upload_tab()
    
    with tab2:
        render_view_tab()
        
    with tab3:
        render_search_tab()

if __name__ == "__main__":
    main() 