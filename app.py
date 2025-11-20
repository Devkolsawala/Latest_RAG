import streamlit as st
from rag_engine import get_pdf_text, get_text_chunks, get_vector_store, user_input

def main():
    st.set_page_config("Chat PDF")
    st.header("Chat with PDF ")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        with st.spinner("Thinking..."):
            # We need to access the selected model from the sidebar, but since sidebar renders after main content in script flow,
            # we rely on Streamlit's rerun behavior or session state. 
            # However, for simplicity in this structure, we can assume the user selects first.
            # Better approach: Move sidebar to top or use session state.
            # Actually, st.sidebar can be defined anywhere. But `selected_model` variable scope is issue.
            # Let's move sidebar definition to the top of main() or use st.session_state.
            pass 
            
    # Initialize processing state
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False

    # Refactoring main to define sidebar first to capture model selection
    with st.sidebar:
        st.title("Menu:")
        model_mapping = {
            "GPT-OSS": "openai/gpt-oss-20b:free",
            "Deepseek": "deepseek/deepseek-chat-v3-0324:free",
            "Quen - 3": "qwen/qwen3-coder:free"
        }
        selected_model_name = st.selectbox("Select Model", list(model_mapping.keys()))
        selected_model = model_mapping[selected_model_name]
        
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        
        if not pdf_docs:
            st.session_state.processing_complete = False
            
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                if not pdf_docs:
                    st.error("Please upload at least one PDF file.")
                else:
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    get_vector_store(text_chunks)
                    st.session_state.processing_complete = True
                    st.success("Done")

    # React to user input (Main area)
    if st.session_state.processing_complete:
        if prompt := st.chat_input("Ask a Question from the PDF Files"):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.spinner("Thinking..."):
                response = user_input(prompt, selected_model)
                
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("Please upload and process PDF files to start chatting.")

if __name__ == "__main__":
    main()
