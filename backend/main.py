import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from llm import (
    OpenAIProvider, OllamaProvider, AnthropicProvider, GeminiProvider,
    init_provider_manager, get_provider_manager,
    init_cost_tracker, get_cost_tracker
)
from tools import (
    WebSearchTool, WebBrowserTool, CodeExecutorTool, FileManagerTool,
    ShellExecutorTool, APICallerTool, PDFReaderTool, ScreenshotTool,
    DatabaseTool, EmailSenderTool, GitOperationsTool, CalendarIntegrationTool
)
from agents import (
    OrchestratorAgent, ResearcherAgent, CoderAgent,
    AnalystAgent, ExecutorAgent, AgentRole,
    PlannerAgent, SummarizerAgent
)
from memory import VectorMemory, ConversationMemory, KnowledgeBase
from workflows import WorkflowEngine, WorkflowManager, WorkflowScheduler
from api.routes import router, set_components
from api.websocket import websocket_endpoint
from auth import auth_router
from database.connection import init_db
from middleware.rate_limiter import RateLimitMiddleware

# Create FastAPI app
app = FastAPI(
    title="AI Task Automation Agent",
    description="Advanced multi-agent AI system for complex task automation with authentication",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Global components
components = {
    "llm": None,
    "provider_manager": None,
    "cost_tracker": None,
    "tools": {},
    "agents": {},
    "orchestrator": None,
    "memory": None,
    "vector_memory": None,
    "knowledge_base": None,
    "workflow_engine": None,
    "workflow_manager": None,
    "scheduler": None,
    "conversation_memory": None
}


def initialize_llm():
    # Initialize cost tracker
    components["cost_tracker"] = init_cost_tracker()
    print("Initialized cost tracker")

    # Initialize provider manager with all available providers
    provider_manager = init_provider_manager(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        google_api_key=settings.google_api_key,
        ollama_base_url=settings.ollama_base_url,
        default_provider=settings.llm_provider,
        fallback_chain=settings.fallback_chain
    )
    components["provider_manager"] = provider_manager

    # Get the default provider's LLM for backward compatibility
    components["llm"] = provider_manager.get_provider()

    available = provider_manager.list_providers()
    print(f"Initialized LLM providers: {', '.join(available)}")
    print(f"Default provider: {settings.llm_provider}")
    print(f"Fallback chain: {' -> '.join(settings.fallback_chain)}")


def initialize_tools():
    workspace = Path(settings.workspace_path).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    data_path = Path("./data").resolve()
    data_path.mkdir(parents=True, exist_ok=True)

    components["tools"] = {
        "web_search": WebSearchTool(),
        "web_browser": WebBrowserTool(),
        "code_executor": CodeExecutorTool(str(workspace)),
        "file_manager": FileManagerTool(str(workspace)),
        "shell_execute": ShellExecutorTool(str(workspace)),
        "api_caller": APICallerTool(),
        "pdf_reader": PDFReaderTool(str(workspace)),
        "screenshot": ScreenshotTool(str(workspace)),
        "database": DatabaseTool(settings.memory_db_path),
        "send_email": EmailSenderTool(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password
        ),
        "git": GitOperationsTool(str(workspace)),
        "calendar": CalendarIntegrationTool(str(data_path))
    }
    print(f"Initialized {len(components['tools'])} tools")


def initialize_agents():
    llm = components["llm"]
    tools = components["tools"]

    researcher = ResearcherAgent(llm, {
        "web_search": tools["web_search"],
        "web_browser": tools["web_browser"],
        "pdf_reader": tools["pdf_reader"]
    })

    coder = CoderAgent(llm, {
        "code_executor": tools["code_executor"],
        "file_manager": tools["file_manager"]
    })

    analyst = AnalystAgent(llm, {
        "code_executor": tools["code_executor"],
        "file_manager": tools["file_manager"],
        "web_browser": tools["web_browser"]
    })

    executor = ExecutorAgent(llm, {
        "shell_execute": tools["shell_execute"],
        "file_manager": tools["file_manager"],
        "api_caller": tools["api_caller"],
        "send_email": tools["send_email"]
    })

    components["agents"] = {
        AgentRole.RESEARCHER: researcher,
        AgentRole.CODER: coder,
        AgentRole.ANALYST: analyst,
        AgentRole.EXECUTOR: executor
    }

    components["orchestrator"] = OrchestratorAgent(
        llm=llm,
        agents=components["agents"],
        tools=tools
    )
    agents_count = len(components["agents"])
    print(f"Initialized {agents_count} specialized agents + orchestrator")


def initialize_memory():
    components["conversation_memory"] = ConversationMemory()
    components["vector_memory"] = VectorMemory(settings.vector_db_path)
    components["knowledge_base"] = KnowledgeBase()
    print("Initialized memory systems")


def initialize_workflows():
    components["workflow_manager"] = WorkflowManager(settings.workflows_path)
    components["workflow_engine"] = WorkflowEngine(
        tools=components["tools"],
        agents=components["agents"]
    )
    components["scheduler"] = WorkflowScheduler(
        workflow_engine=components["workflow_engine"],
        workflow_manager=components["workflow_manager"]
    )
    print("Initialized workflow system")


async def initialize_all():
    print("\n" + "=" * 50)
    print("Initializing AI Task Automation Agent v2.0")
    print("=" * 50)

    await init_db()
    print("Initialized authentication database")

    initialize_llm()
    initialize_tools()
    initialize_agents()
    initialize_memory()
    initialize_workflows()

    set_components(components)

    print("\n" + "=" * 50)
    print("AI Task Automation Agent is ready!")
    print(f"API: http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    print("=" * 50 + "\n")


# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    try:
        await initialize_all()
    except Exception as e:
        print(f"Error during initialization: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    if components["scheduler"]:
        components["scheduler"].shutdown()


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket, components)


@app.get("/")
async def root():
    return {
        "name": "AI Task Automation Agent",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Multi-agent orchestration",
            "User authentication",
            "Multi-provider LLM",
            "15+ tools",
            "Vector memory",
            "Workflow automation"
        ],
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "tools_count": len(components.get("tools", {})),
        "agents_count": len(components.get("agents", {}))
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
