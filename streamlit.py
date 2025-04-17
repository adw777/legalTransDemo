import streamlit as st
import requests
import json
import time
import platform
import base64
import os
import io

# Set backend API URL (change this to your Ngrok URL when deployed)
# Local development
# API_URL = "http://localhost:8000"
# Remote via Ngrok (replace with your actual Ngrok URL)
API_URL = "https://e5e7-2401-4900-8843-57cc-a8fa-cf2c-9639-37a9.ngrok-free.app"  # ← Change this to your Ngrok URL

# Set page configuration
st.set_page_config(
    page_title="Legal English to Hindi Translator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
SRC_LANG = "eng_Latn"
TGT_LANG = "hin_Deva"

def check_api_health():
    """Check if the backend API is available"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        return False, {"error": "API returned non-200 status code"}
    except Exception as e:
        return False, {"error": str(e)}

def translate_legal_text(input_text, max_length=512, do_sample=False, temperature=0.7, num_beams=5):
    """Send translation request to the backend API"""
    if not input_text.strip():
        return "कृपया अनुवाद के लिए कुछ टेक्स्ट दर्ज करें।", None
    
    try:
        with st.spinner("Connecting to translation server..."):
            payload = {
                "text": input_text,
                "max_length": max_length,
                "do_sample": do_sample,
                "temperature": temperature,
                "num_beams": num_beams
            }
            
            response = requests.post(
                f"{API_URL}/translate", 
                json=payload,
                timeout=300  # 5-minute timeout for long translations
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["translation"], result["model_info"]
            else:
                st.error(f"API Error: {response.status_code}")
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    return f"अनुवाद में त्रुटि: {error_detail}", None
                except:
                    return "अनुवाद में त्रुटि: API से कनेक्ट नहीं हो सका।", None
    
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the translation server.")
        return "अनुवाद में त्रुटि: अनुवाद सर्वर से कनेक्शन विफल हुआ।", None
    except requests.exceptions.Timeout:
        st.error("Timeout Error: The translation request took too long.")
        return "अनुवाद में त्रुटि: अनुवाद अनुरोध का समय समाप्त हो गया।", None
    except Exception as e:
        st.error(f"Error during translation: {str(e)}")
        return f"अनुवाद में त्रुटि: {str(e)}\nकृपया छोटे इनपुट के साथ प्रयास करें।", None

def translate_file(file, max_length=512, do_sample=False, temperature=0.7, num_beams=5):
    """Send file to the backend API for translation"""
    try:
        with st.spinner("Uploading and translating file..."):
            # Prepare the files for upload
            files = {"file": (file.name, file.getvalue(), file.type)}
            
            # Prepare the form data
            form_data = {
                "max_length": str(max_length),
                "do_sample": str(do_sample).lower(),
                "temperature": str(temperature),
                "num_beams": str(num_beams)
            }
            
            # Send the request
            response = requests.post(
                f"{API_URL}/translate/file",
                files=files,
                data=form_data,
                timeout=600  # 5-minute timeout for long translations
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["translation"], result["original_text"], result["model_info"]
            else:
                st.error(f"API Error: {response.status_code}")
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    return f"अनुवाद में त्रुटि: {error_detail}", None, None
                except:
                    return "अनुवाद में त्रुटि: API से कनेक्ट नहीं हो सका।", None, None
    
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the translation server.")
        return "अनुवाद में त्रुटि: अनुवाद सर्वर से कनेक्शन विफल हुआ।", None, None
    except requests.exceptions.Timeout:
        st.error("Timeout Error: The translation request took too long.")
        return "अनुवाद में त्रुटि: अनुवाद अनुरोध का समय समाप्त हो गया।", None, None
    except Exception as e:
        st.error(f"Error during file translation: {str(e)}")
        return f"अनुवाद में त्रुटि: {str(e)}", None, None

def main():
    global API_URL
    # Check API connection
    api_available, health_data = check_api_health()
    
    # Header section
    st.title("🏛️ Legal English to Hindi Translator")
    st.markdown("""
    Translate legal English text to Hindi using a specialized model fine-tuned for legal domain translation.
    
    **Model details:** [Legal-IndicTrans2-en_indic](https://huggingface.co/axondendriteplus/Legal-IndicTrans2-en_indic) - 
    A PEFT/LoRA adaptation of [AI4Bharat's IndicTrans2](https://huggingface.co/ai4bharat/indictrans2-en-indic-1B) for legal domain.
    """)
    
    # Backend connection status
    backend_status = st.empty()
    if api_available:
        backend_status.success(f"✅ Connected to translation server: {API_URL}")
        device = health_data.get("device", "Unknown")
    else:
        backend_status.error(f"❌ Cannot connect to translation server: {API_URL}")
        device = "Not available"
    
    # Device and platform information
    st.sidebar.title("System Info")
    st.sidebar.info(f"Client platform: {platform.system()}")
    st.sidebar.info(f"Backend device: {device}")
    st.sidebar.info(f"Server status: {'Online' if api_available else 'Offline'}")
    
    # Advanced options in sidebar
    st.sidebar.title("Advanced Options")
    max_length = st.sidebar.slider("Maximum Length", 100, 1024, 512, 32, 
                                 help="Maximum length of generated translation")
    do_sample = st.sidebar.checkbox("Use Sampling", False, 
                                  help="Enable for more creative translations")
    temperature = st.sidebar.slider("Temperature", 0.1, 1.5, 0.7, 0.1, 
                                  help="Higher = more creative, only used if sampling is enabled")
    num_beams = st.sidebar.slider("Number of Beams", 1, 10, 5, 1, 
                                help="Higher = more diverse candidates considered")
    
    # About section in sidebar
    st.sidebar.title("About")
    st.sidebar.markdown("""
    This app translates English legal text to Hindi using a specialized model.
    
    **Features:**
    - Optimized for legal terminology
    - Handles complex legal sentences
    - Processes long documents in chunks
    - Supports PDF and text files
    - Remote processing via API
    
    **Limitations:**
    - Requires internet connection
    - Translation speed depends on server load
    - Maximum input length is limited
    """)
    
    # Connection settings (collapsible)
    with st.sidebar.expander("Connection Settings"):
        api_url_input = st.text_input("API URL", value=API_URL)
        if api_url_input != API_URL and st.button("Update API URL"):
            # Now you can modify the global variable
            API_URL = api_url_input
            st.experimental_rerun()
    
    # Input tabs
    tab1, tab2 = st.tabs(["Text Input", "File Upload"])
    
    with tab1:
        # Example selector
        examples = {
            "Select an example": "",
            "Court Order": "The court held that the order was arbitrary and unconstitutional.",
            "Constitutional Petition": "The petitioner seeks relief under Article 32 of the Constitution.",
            "Judgment Status": "The judgment is reserved until further notice.",
            "Jurisdiction": "The High Court has jurisdiction over this matter as per Section 5.",
            "Prima Facie": "The plaintiff failed to establish a prima facie case.",
            "Arbitration Case": "Arbitration and Conciliation Act, 1996 – Ex-parte arbitral awards – Enforcement by employee, when denial of the authenticity of the arbitration agreement by employer – Service dispute by the employee against the State Government.",
        }
        example_choice = st.selectbox("Try with an example:", options=list(examples.keys()))
        
        # Text input area
        if example_choice != "Select an example":
            default_text = examples[example_choice]
        else:
            default_text = ""
            
        input_text = st.text_area("Enter English legal text:", value=default_text, height=200, label_visibility="visible")
        
        col1, col2 = st.columns([1, 5])
        with col1:
            translate_button = st.button("Translate", type="primary", disabled=not api_available)
        with col2:
            st.write("")  # Placeholder for layout
            
        # Translation result
        if translate_button and input_text:
            start_time = time.time()
            
            with st.spinner("Translating..."):
                translation, model_info = translate_legal_text(
                    input_text, 
                    max_length=max_length,
                    do_sample=do_sample,
                    temperature=temperature,
                    num_beams=num_beams
                )
            
            elapsed_time = time.time() - start_time
            
            st.subheader("Hindi Translation:")
            st.text_area("Hindi Translation", value=translation, height=300, label_visibility="collapsed")
            
            # Show translation metadata
            if model_info:
                st.caption(f"Translation completed in {elapsed_time:.2f} seconds using {model_info.get('device', 'unknown')} device.")
            
            # Provide download button for translation
            st.download_button(
                label="Download Translation",
                data=translation.encode('utf-8'),
                file_name="translation.txt",
                mime="text/plain"
            )
    
    with tab2:
        st.write("Upload an English legal document to translate:")
        
        # Updated file uploader with explicit PDF support
        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf'], disabled=not api_available)
        
        if uploaded_file is not None:
            # Display file details
            file_details = {"Filename": uploaded_file.name, "Filetype": uploaded_file.type, "Filesize": f"{uploaded_file.size / 1024:.2f} KB"}
            st.write(file_details)
            
            # Show appropriate messages based on file type
            if uploaded_file.type == "application/pdf":
                st.info("PDF files are now supported! The text will be extracted and translated.")
            
            # Add a button to start translation
            if st.button("Translate File", type="primary", disabled=not api_available):
                start_time = time.time()
                
                # Call the new file translation function
                translation, original_text, model_info = translate_file(
                    uploaded_file,
                    max_length=max_length,
                    do_sample=do_sample,
                    temperature=temperature,
                    num_beams=num_beams
                )
                
                elapsed_time = time.time() - start_time
                
                if translation and original_text:
                    # Display original text
                    st.subheader("Original Text:")
                    with st.expander("View Original Text", expanded=False):
                        st.text_area("Original Content", value=original_text, height=200, label_visibility="collapsed")
                    
                    # Display translation
                    st.subheader("Hindi Translation:")
                    st.text_area("File Translation", value=translation, height=300, label_visibility="collapsed")
                    
                    # Show translation metadata
                    if model_info:
                        st.caption(f"Translation completed in {elapsed_time:.2f} seconds using {model_info.get('device', 'unknown')} device.")
                    
                    # Provide download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="Download Translation",
                            data=translation.encode('utf-8'),
                            file_name=f"translated_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="Download Original Text",
                            data=original_text.encode('utf-8'),
                            file_name=f"original_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain"
                        )

if __name__ == "__main__":
    main()