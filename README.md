# Physical AI Book Project

This project consists of a Physical AI textbook (frontend) and a RAG-powered chatbot (backend).

## Project Structure

- `backend/`: FastAPI server with Qdrant vector database and Groq LLM.
- `book/`: Docusaurus-based frontend for the textbook.

---

## Getting Started

### 1. Backend Setup (FastAPI)

1.  **Navigate to the backend directory:**
    ```powershell
    cd backend
    ```

2.  **Activate the Virtual Environment:**
    - **PowerShell:** `.\venv\Scripts\Activate.ps1`
    - **CMD:** `.\venv\Scripts\activate.bat`
    - **Bash/Mac:** `source venv/bin/activate`
     .\venv\Scripts\python.exe main.py

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Backend:**
    ```bash
    python main.py
    ```
    The backend will be available at: `http://localhost:8000`

---

### 2. Frontend Setup (Docusaurus)

1.  **Navigate to the book directory:**
    ```powershell
    cd book
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Run the Frontend:**
    ```bash
    npm start
    ```
    The textbook will be available at: `http://localhost:3000/physical-ai-book/`

---

## Development Notes

- Ensure you have a `.env` file in the `backend/` directory with your `GROQ_API_KEY`.
- The backend uses a local Qdrant instance stored in `backend/local_qdrant`.
