# 🧠 Research Assistant using OpenAI Agents SDK & Real-Time Streaming

Welcome to the **Research Assistant**, an intelligent, multi-source literature review and research synthesis tool powered by OpenAI's latest LLMs, integrated with real-time streaming via Chainlit, and built using the OpenAI **Agents SDK**.

> 📁 Repository:(https://github.com/ahadnaeem785/Research_Assitant-openai-agents-sdk-)  
> 📄 Core File: `research.py`

---

## 🚀 Features

### 🔍 Query Refinement
Refines user input into a more specific and research-oriented query using GPT-4o.

### 📚 Multi-Source Paper Retrieval
Automatically searches and aggregates research papers from:
- **Semantic Scholar**
- **PubMed**
- **ArXiv** 

### 📊 Structured Summarization
Generates structured output including:
- Key insights
- Short summary
- Final conclusion

### 📄 Markdown Report Generation
Produces a well-formatted report including:
- Query
- Short summary
- Insights with clickable URLs
- Conclusion
- List of source links

### ⚡ Real-Time Streaming
Uses **Chainlit** for real-time streaming of the final report — token-by-token — for enhanced user interactivity and responsiveness.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenAI GPT-4o**
- **Chainlit** (frontend + streaming)
- **LangChain** (for research insights)
- **Pydantic** (data validation)
- **Asyncio** (for concurrency)
- **Requests** (for PubMed & Semantic Scholar APIs)
- **uv** (package manager for reproducible environments)

---

## 📁 Project Structure

```
📦 Research_Assitant-openai-agents-sdk-
 ┣ 📂 .chainlit
 ┣ 📂 __pycache__
 ┣ 📄 .gitignore
 ┣ 📄 .python-version
 ┣ 📄 README.md
 ┣ 📄 chainlit.md
 ┣ 📄 example.env
 ┣ 📄 hello_agent.py
 ┣ 📄 pyproject.toml
 ┣ 📄 research.py         # Main Chainlit app and workflow logic
 ┣ 📄 uv.lock
```

---

## ▶️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ahadnaeem785/Research_Assitant-openai-agents-sdk-.git
cd Research_Assitant-openai-agents-sdk-
```

### 2. Set Up a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
```

### 3. Install Dependencies with `uv`

This project uses [**uv**](https://github.com/astral-sh/uv) as the package manager. Ensure it's installed:

```bash
pip install uv
```

Then sync the environment:

```bash
uv sync
```

### 4. Set Your OpenAI API Key

Update the `.env` or `example.env` file or export your API key:

```bash
export OPENAI_API_KEY=your-api-key
```

### 5. Run the Chainlit App

```bash
chainlit run research.py
```

Then open the provided localhost URL in your browser to interact with the assistant.

---

## ✅ Use Cases

- Academic Literature Reviews  
- Scientific Paper Summarization  
- Research Topic Analysis  
- AI-Assisted Writing & Decision Support  
- Domain-Specific Insight Generation  

---

## 📌 Credits

- Built by [Muhammad Ahad](https://github.com/ahadnaeem785)
- Powered by OpenAI GPT-4o, Chainlit, LangChain, Openai Agents SDK.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributions & Feedback

Contributions, bug reports, and feedback are welcome! Feel free to open an issue or submit a pull request.

---

## 🌐 Connect
- 📬 Email: muhammadahad764@gmail.com
