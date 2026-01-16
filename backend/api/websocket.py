import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, List


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_event(self, websocket: WebSocket, event_type: str, data: Dict[str, Any]):
        try:
            await websocket.send_json({
                "type": event_type,
                "data": data
            })
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        for connection in self.active_connections:
            await self.send_event(connection, event_type, data)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, components: Dict[str, Any]):
    """WebSocket endpoint for real-time agent communication"""
    await manager.connect(websocket)

    # Get components
    orchestrator = components.get("orchestrator")
    workflow_engine = components.get("workflow_engine")
    scheduler = components.get("scheduler")
    vector_memory = components.get("vector_memory")

    # Set up event handlers
    async def handle_agent_event(event):
        await manager.send_event(websocket, event.type, event.data)

    if orchestrator:
        orchestrator.add_event_handler(lambda e: asyncio.create_task(
            manager.send_event(websocket, e.type, e.data)
        ))

    if workflow_engine:
        workflow_engine.add_event_handler(lambda e: asyncio.create_task(
            manager.send_event(websocket, e["type"], e["data"])
        ))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            if msg_type == "chat":
                # Handle chat message
                user_message = message.get("message", "")

                await manager.send_event(websocket, "ack", {
                    "message": "Processing your request..."
                })

                if orchestrator:
                    try:
                        result = await orchestrator.execute(user_message)

                        # Store in memory
                        if vector_memory:
                            await vector_memory.add(
                                content=f"Task: {user_message}\nResult: {result.output[:500]}",
                                memory_type="conversation"
                            )

                        await manager.send_event(websocket, "response", {
                            "message": result.output,
                            "success": result.success,
                            "execution_time": result.execution_time
                        })

                    except Exception as e:
                        await manager.send_event(websocket, "error", {
                            "message": str(e)
                        })

            elif msg_type == "run_workflow":
                # Run a workflow
                workflow_id = message.get("workflow_id")
                variables = message.get("variables", {})

                workflow_manager = components.get("workflow_manager")
                if workflow_manager and workflow_engine:
                    workflow = await workflow_manager.get(workflow_id)
                    if workflow:
                        await manager.send_event(websocket, "workflow_started", {
                            "workflow_id": workflow_id,
                            "name": workflow.name
                        })

                        execution = await workflow_engine.execute(workflow, variables)

                        await manager.send_event(websocket, "workflow_complete", {
                            "execution_id": execution.id,
                            "status": execution.status,
                            "results": execution.step_results
                        })

            elif msg_type == "search_memory":
                # Search vector memory
                query = message.get("query", "")
                if vector_memory:
                    results = await vector_memory.search(query, n_results=5)
                    await manager.send_event(websocket, "memory_results", {
                        "results": [
                            {
                                "id": r.id,
                                "content": r.content,
                                "relevance": r.relevance_score
                            }
                            for r in results
                        ]
                    })

            elif msg_type == "get_tools":
                # List available tools
                tools = components.get("tools", {})
                await manager.send_event(websocket, "tools_list", {
                    "tools": [
                        {
                            "name": name,
                            "description": tool.description
                        }
                        for name, tool in tools.items()
                    ]
                })

            elif msg_type == "execute_tool":
                # Execute a specific tool
                tool_name = message.get("tool")
                params = message.get("params", {})

                tools = components.get("tools", {})
                if tool_name in tools:
                    result = await tools[tool_name].execute(**params)
                    await manager.send_event(websocket, "tool_result", {
                        "tool": tool_name,
                        "success": result.success,
                        "output": result.output,
                        "error": result.error
                    })

            elif msg_type == "clear":
                # Clear conversation
                conv_memory = components.get("conversation_memory")
                if conv_memory:
                    conv_memory.clear()
                await manager.send_event(websocket, "cleared", {
                    "message": "Conversation cleared"
                })

            elif msg_type == "ping":
                # Heartbeat
                await manager.send_event(websocket, "pong", {})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
