"""
Durable storage for collaborative workspaces and custom tools (Plugin SDK).

Uses its own metadata (create-only, never dropped) on the shared async engine,
so these tables survive restarts independently of the auth `Base`.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, String, Text, DateTime, select, delete, func
from sqlalchemy.orm import declarative_base

from .connection import engine, async_session

ExtrasBase = declarative_base()


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class WorkspaceModel(ExtrasBase):
    __tablename__ = "workspaces"
    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    owner_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now)


class WorkspaceMemberModel(ExtrasBase):
    __tablename__ = "workspace_members"
    id = Column(String(36), primary_key=True, default=_uuid)
    workspace_id = Column(String(36), index=True, nullable=False)
    user_id = Column(String(36), index=True, nullable=False)
    username = Column(String(80))
    role = Column(String(20), default="member")  # owner | member
    added_at = Column(DateTime(timezone=True), default=_now)


class CustomToolModel(ExtrasBase):
    __tablename__ = "custom_tools"
    id = Column(String(36), primary_key=True, default=_uuid)
    owner_id = Column(String(36), index=True)
    name = Column(String(64), nullable=False)
    description = Column(Text)
    endpoint_url = Column(Text, nullable=False)
    method = Column(String(8), default="POST")
    params_schema = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), default=_now)


async def init_extras():
    async with engine.begin() as conn:
        await conn.run_sync(ExtrasBase.metadata.create_all)


# ── Workspaces ───────────────────────────────────────────────────────────────
async def create_workspace(name: str, owner_id: str, owner_username: str = "") -> Dict[str, Any]:
    async with async_session() as s:
        ws = WorkspaceModel(name=name, owner_id=owner_id)
        s.add(ws)
        await s.flush()
        s.add(WorkspaceMemberModel(workspace_id=ws.id, user_id=owner_id, username=owner_username, role="owner"))
        await s.commit()
        return {"id": ws.id, "name": ws.name, "owner_id": owner_id, "role": "owner"}


async def list_workspaces(user_id: str) -> List[Dict[str, Any]]:
    async with async_session() as s:
        rows = (await s.execute(
            select(WorkspaceModel, WorkspaceMemberModel.role)
            .join(WorkspaceMemberModel, WorkspaceMemberModel.workspace_id == WorkspaceModel.id)
            .where(WorkspaceMemberModel.user_id == user_id)
        )).all()
        out = []
        for ws, role in rows:
            n = (await s.execute(
                select(func.count(WorkspaceMemberModel.id)).where(WorkspaceMemberModel.workspace_id == ws.id)
            )).scalar() or 0
            out.append({"id": ws.id, "name": ws.name, "owner_id": ws.owner_id,
                        "role": role, "members": int(n),
                        "created_at": ws.created_at.isoformat() if ws.created_at else None})
        return out


async def add_member(workspace_id: str, user_id: str, username: str) -> bool:
    async with async_session() as s:
        exists = (await s.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id)
        )).scalar_one_or_none()
        if exists:
            return False
        s.add(WorkspaceMemberModel(workspace_id=workspace_id, user_id=user_id, username=username, role="member"))
        await s.commit()
        return True


async def list_members(workspace_id: str) -> List[Dict[str, Any]]:
    async with async_session() as s:
        rows = (await s.execute(
            select(WorkspaceMemberModel).where(WorkspaceMemberModel.workspace_id == workspace_id)
        )).scalars().all()
        return [{"user_id": m.user_id, "username": m.username, "role": m.role} for m in rows]


async def is_member(workspace_id: str, user_id: str) -> bool:
    async with async_session() as s:
        m = (await s.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id)
        )).scalar_one_or_none()
        return m is not None


# ── Custom tools (Plugin SDK) ────────────────────────────────────────────────
async def create_custom_tool(owner_id: str, name: str, description: str, endpoint_url: str,
                             method: str, params_schema: dict) -> Dict[str, Any]:
    async with async_session() as s:
        t = CustomToolModel(owner_id=owner_id, name=name, description=description,
                            endpoint_url=endpoint_url, method=method,
                            params_schema=json.dumps(params_schema or {}))
        s.add(t)
        await s.commit()
        return {"id": t.id, "name": name}


async def list_custom_tools() -> List[Dict[str, Any]]:
    async with async_session() as s:
        rows = (await s.execute(select(CustomToolModel))).scalars().all()
        out = []
        for t in rows:
            try:
                schema = json.loads(t.params_schema) if t.params_schema else {}
            except Exception:
                schema = {}
            out.append({"id": t.id, "name": t.name, "description": t.description,
                        "endpoint_url": t.endpoint_url, "method": t.method,
                        "params_schema": schema})
        return out


async def delete_custom_tool(tool_id: str) -> bool:
    async with async_session() as s:
        res = await s.execute(delete(CustomToolModel).where(CustomToolModel.id == tool_id))
        await s.commit()
        return res.rowcount > 0
