## 🤖 Chatbot Assignment: Flow and RAG Chatbot

This project implements a web-based chatbot system with two distinct modes: a **Flow Chatbot** for guided data collection and a **RAG Chatbot** (Retrieval-Augmented Generation) for answering questions based on an uploaded document (a company handbook). The application is built using **Flask** for the backend and **JavaScript/HTML/CSS** for the frontend, leveraging **OpenAI** and **LangChain** for the RAG functionality.

### ✨ Features

  * **Dual Chat Modes:**
      * **Flow Chat:** A structured, multi-step conversational flow for collecting specific information (e.g., name, email, service interest, budget, timeline).
      * **RAG Chat:** An open-ended chat interface that searches a company document (`sample_documents.txt`) to provide context-aware answers using LLMs.
  * **Vector Store Integration:** Uses **Chroma** and **OpenAI Embeddings** via **LangChain** to create and query a vector store for the RAG functionality.
  * **Persistent RAG System:** The RAG system is initialized on application startup and uses a persisted vector store directory (`vector_store/`).
  * **Progressive Flow:** The Flow Chat includes front-end logic to track and display progress through the steps.
  * **Responsive UI:** A clean, modern, and mobile-friendly user interface.

-----

### 📂 File Structure

The project follows a standard Flask application structure:

```
FLOW-CHATBOT/
│
├── data/
│   └── sample_documents.txt      # Company handbook for RAG system
│
├── static/
│   ├── css/
│   │   └── style.css             # Stylesheet for the application
│   └── js/
│   │   └── script.js             # Frontend logic for chat interface
│
├── templates/
│   ├── base.html                 # Base template for all pages
│   ├── flow_chat.html            # Template for the Flow Chat interface
│   ├── index.html                # Home page with mode selection
│   └── rag_chat.html             # Template for the RAG Chat interface
│
├── vector_store/                 # Directory for Chroma vector database (created at runtime)
│
├── venv/                         # Python virtual environment (not committed to Git)
│
├── .env                          # Environment variables (e.g., OPENAI_API_KEY, SECRET_KEY)
├── .gitignore                    # Specifies files/directories to ignore in Git (e.g., venv, vector_store)
├── app.py                        # Main Flask application and chatbot logic
├── README.md                     # This file
└── requirements.txt              # Project dependencies
```

-----

### 🚀 Getting Started

#### Prerequisites

  * Python 3.8+
  * An OpenAI API Key

#### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd FLOW-CHATBOT
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    *(Note: `requirements.txt` should contain dependencies like `flask`, `openai`, `langchain`, `chromadb`, `python-dotenv`.)*

4.  **Configure environment variables:**
    Create a file named `.env` in the root directory and add your keys:

    ```env
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
    SECRET_KEY="A_STRONG_RANDOM_SECRET_KEY"
    ```

#### Running the Application

1.  **Ensure your virtual environment is active.**

2.  **Run the Flask application:**

    ```bash
    python app.py
    ```

3.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000/`.

-----

### 💻 Code Overview

#### `app.py`

This is the core of the backend.

  * **Initialization:** Loads environment variables and initializes the global `rag_bot` and `flow_bot`.
  * **`initialize_rag_system()`:** Responsible for reading `sample_documents.txt`, splitting it into chunks, generating embeddings using `OpenAIEmbeddings`, and storing them in the `Chroma` vector store. It re-initializes and clears the `vector_store` directory on each run for development simplicity.
  * **`FlowChatbot` Class:**
      * Defines the conversational structure (`flow_steps`), including a question, a validation function, and an error message for each step.
      * Handles progression and generates a final summary.
  * **`RAGChatbot` Class:**
      * Initializes a connection to the `Chroma` vector store.
      * **`get_response()`:** Performs a similarity search on the vector store to retrieve relevant document chunks, constructs a prompt with the context, and sends it to the OpenAI `gpt-3.5-turbo` model for a final, context-grounded answer.
  * **Routing:** Defines routes for the homepage (`/`), the chat pages (`/flow-chat`, `/rag-chat`), and the API endpoints (`/api/flow/next-question`, `/api/rag/chat`).

#### `script.js`

This file contains the frontend logic for handling user interaction and API communication.

  * **`ChatInterface` Class:**
      * Manages event listeners for button clicks and input submissions.
      * **`sendFlowMessage()`/`sendRagMessage()`:** Functions to handle user input and send messages to the respective backend APIs (`/api/flow/next-question` and `/api/rag/chat`).
      * **`getNextFlowQuestion()`:** Handles the flow state, sending the previous answer and receiving the next question or the final summary.
      * **UI Helpers:** Includes functions for adding messages to the chat view (`addMessage`), clearing the chat, updating the progress bar (`updateProgress`), and managing the loading state (`setLoading`).

-----

### ⚠️ Note on RAG Initialization

The `app.py` is configured to **recreate and populate** the `vector_store/` directory every time the application starts. This ensures the RAG system is always initialized with the latest document content but may cause a slight delay at startup. In a production environment, this initialization would typically be a separate, one-time process.