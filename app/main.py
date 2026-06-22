from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class WorkflowState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Workflow(BaseModel):
    id: int
    title: str
    state: WorkflowState


workflows = {}
next_id = 1


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/workflow")
def create_workflow(title: str):
    global next_id

    workflow = Workflow(
        id=next_id,
        title=title,
        state=WorkflowState.PENDING
    )

    workflows[next_id] = workflow
    next_id += 1

    return workflow


@app.post("/approve/{workflow_id}")
def approve_workflow(workflow_id: int):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows[workflow_id]

    if workflow.state != WorkflowState.PENDING:
        raise HTTPException(status_code=400, detail="Invalid transition")

    workflow.state = WorkflowState.APPROVED

    return workflow


@app.post("/reject/{workflow_id}")
def reject_workflow(workflow_id: int):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows[workflow_id]

    if workflow.state != WorkflowState.PENDING:
        raise HTTPException(status_code=400, detail="Invalid transition")

    workflow.state = WorkflowState.REJECTED

    return workflow


@app.get("/workflow/{workflow_id}")
def get_workflow(workflow_id: int):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflows[workflow_id]


