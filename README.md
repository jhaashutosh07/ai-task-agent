# AI Task Automation Agent v2.0

An advanced multi-agent AI system for complex task automation with workflow orchestration, long-term memory, and scheduled execution.

## Key Features

### Multi-Agent Architecture
- **Orchestrator Agent** - Coordinates and delegates tasks to specialized agents
- **Researcher Agent** - Web search and information gathering
- **Coder Agent** - Code generation, execution, and debugging
- **Analyst Agent** - Data analysis and visualization
- **Executor Agent** - System operations and automation

### 10+ Specialized Tools
| Tool | Description |
|------|-------------|
| `web_search` | Search the internet using DuckDuckGo |
| `web_browser` | Fetch and read web page content |
| `code_executor` | Write and execute Python code |
| `file_manager` | Read, write, and manage files |
| `shell_execute` | Run shell commands safely |
| `api_caller` | Make HTTP API requests |
| `pdf_reader` | Extract text from PDFs |
| `screenshot` | Capture web page screenshots |
| `database` | Execute SQL queries (SQLite) |
| `send_email` | Send emails via SMTP |

### Advanced Features
- **Vector Memory** - Long-term memory with ChromaDB for semantic search
- **Knowledge Base** - Store and retrieve learned information
- **Workflow Engine** - Create and run multi-step automations
- **Task Scheduler** - Schedule workflows with cron, interval, or date triggers
- **Parallel Execution** - Run independent tasks simultaneously
- **Human-in-the-Loop** - Confirmation for dangerous operations

## Project Structure

```
ai-task-agent/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration
│   ├── agents/                 # Multi-agent system
│   │   ├── orchestrator.py     # Main coordinator
│   │   ├── researcher.py       # Research specialist
│   │   ├── coder.py            # Code specialist
│   │   ├── analyst.py          # Analysis specialist
│   │   └── executor.py         # System operations
│   ├── tools/                  # 10+ specialized tools
│   ├── memory/                 # Memory systems
│   │   ├── vector_memory.py    # ChromaDB integration
│   │   ├── conversation_memory.py
│   │   └── knowledge_base.py
│   ├── workflows/              # Workflow automation
│   │   ├── workflow_engine.py
│   │   ├── workflow_manager.py
│   │   └── scheduler.py
│   ├── llm/                    # LLM providers
│   └── api/                    # REST + WebSocket
├── frontend/
│   ├── app/                    # Next.js app
│   ├── components/
│   │   ├── ChatInterface.tsx   # Chat UI
│   │   ├── Dashboard.tsx       # System dashboard
│   │   ├── WorkflowBuilder.tsx # Visual workflow editor
│   │   └── ToolsExplorer.tsx   # Tool testing UI
│   └── lib/                    # Utilities
├── workspace/                  # Agent working directory
└── data/                       # Persistent storage
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key OR Ollama installed

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your settings
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Access the App
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Configuration

### Environment Variables (.env)

```env
# LLM Provider: "openai" or "ollama"
LLM_PROVIDER=openai

# OpenAI (if using)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Ollama (if using)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Agent Settings
MAX_ITERATIONS=15
WORKSPACE_PATH=./workspace

# Memory
VECTOR_DB_PATH=./data/vectordb
MEMORY_DB_PATH=./data/agent.db

# Optional: Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
```

## API Endpoints

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/info` | GET | System information |
| `/api/chat` | POST | Send message to agent |

### Memory
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/memory/search` | GET | Search vector memory |
| `/api/memory/stats` | GET | Memory statistics |
| `/api/knowledge` | POST | Add knowledge entry |
| `/api/knowledge/search` | GET | Search knowledge base |

### Workflows
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workflows` | GET/POST | List/Create workflows |
| `/api/workflows/{id}` | GET/DELETE | Get/Delete workflow |
| `/api/workflows/{id}/run` | POST | Execute workflow |
| `/api/workflows/templates` | GET | Get workflow templates |

### Scheduling
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schedule` | GET/POST | List/Create scheduled tasks |
| `/api/schedule/{id}/pause` | POST | Pause task |
| `/api/schedule/{id}/resume` | POST | Resume task |

### Tools
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tools` | GET | List available tools |
| `/api/tools/{name}/execute` | POST | Execute a tool |

## Usage Examples

### Complex Research Task
```
"Research the latest developments in quantum computing,
summarize the top 3 breakthroughs, and create a report file"
```
The orchestrator will:
1. Delegate web search to Researcher Agent
2. Have Researcher browse and extract information
3. Ask Analyst to synthesize findings
4. Have Executor create the report file

### Data Analysis
```
"Analyze the sales data in sales.csv, create visualizations,
and generate insights"
```
The orchestrator will:
1. Use file_manager to read the CSV
2. Delegate to Analyst Agent for analysis
3. Generate charts using matplotlib
4. Save visualizations to workspace

### Workflow Automation
Create a workflow to:
1. Search for news every morning
2. Summarize key articles
3. Send email digest

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Request                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Task Decomposition                        │  │
│  │         (Break into subtasks, assign agents)           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │              │               │              │
         ▼              ▼               ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Researcher │ │    Coder    │ │   Analyst   │ │  Executor   │
│    Agent    │ │    Agent    │ │    Agent    │ │    Agent    │
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│ web_search  │ │code_executor│ │code_executor│ │shell_execute│
│ web_browser │ │file_manager │ │file_manager │ │file_manager │
│ pdf_reader  │ │             │ │ web_browser │ │ api_caller  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Memory Systems                           │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │
│  │ Vector Memory  │ │ Conversation   │ │ Knowledge Base │   │
│  │   (ChromaDB)   │ │    Memory      │ │                │   │
│  └────────────────┘ └────────────────┘ └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - Async web framework
- **OpenAI/Ollama** - LLM providers
- **ChromaDB** - Vector database
- **SQLite** - Persistent storage
- **APScheduler** - Task scheduling

### Frontend
- **Next.js 14** - React framework
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Lucide React** - Icons

## License

MIT License - Use freely for your final year project!

## Contributing

This is a final year project demonstrating advanced AI agent capabilities including:
- Multi-agent orchestration
- Tool use and function calling
- Long-term memory with vector search
- Workflow automation
- Scheduled task execution

Built with modern AI/ML techniques for autonomous task execution.
