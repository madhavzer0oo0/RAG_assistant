from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_splitter(chunk_size=800, overlap=80):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )
