try:
    from langchain.chains.question_answering import load_qa_chain
    print("Import successful: langchain.chains.question_answering.load_qa_chain")
except ImportError as e:
    print(f"Import failed: {e}")

try:
    from langchain.chains import load_qa_chain
    print("Import successful: langchain.chains.load_qa_chain")
except ImportError as e:
    print(f"Import failed: {e}")

import langchain
print(f"LangChain version: {langchain.__version__}")
print(f"LangChain dir: {dir(langchain)}")
