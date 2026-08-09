---
title: Physical AI Book
emoji: 🏆
colorFrom: gray
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Physical AI Book Project

This project consists of a **Physical AI & Humanoid Robotics textbook (Frontend)** and a **RAG-powered Chatbot API (Backend)**.

---

## 📁 Project Structure

- `backend/`: FastAPI server with local Qdrant Vector Database, FastEmbed (`BAAI/bge-small-en-v1.5`), and Groq LLM API.
- `book/`: Docusaurus-based Frontend for the interactive textbook.

---

## 🚀 How to Run Frontend & Backend

### 1. ⚙️ Running the Backend (FastAPI)

1. Open Terminal/PowerShell and navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Activate the Virtual Environment:
   - **PowerShell:**
     ```powershell
     .\venv\Scripts\activate
     ```
   - **Command Prompt (CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **Bash / Mac / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Run the Backend server using `uvicorn`:
   ```powershell
   uvicorn main:app --reload --port 8000
   ```
   > 📍 **Backend API URL:** `http://localhost:8000`

---

### 2. 💻 Running the Frontend (Docusaurus)

1. Open a **new Terminal window** and navigate to the `book` directory:
   ```powershell
   cd book
   ```

2. Start the Frontend development server:
   ```powershell
   npm start
   ```
   *(Alternative command: `npm run start`)*

   > 📍 **Frontend Website URL:** `http://localhost:3000`

---

## 🛠️ Tech Stack & Requirements

- **Backend:** Python 3.10+, FastAPI, Uvicorn, FastEmbed, Qdrant Client, Groq API (`llama-3.3-70b-versatile`).
- **Frontend:** Node.js 20+, React, Docusaurus 3.