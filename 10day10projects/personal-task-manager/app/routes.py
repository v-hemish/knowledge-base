
from fastapi import APIRouter, HTTPException
from app.schemas import TaskCreate, TaskUpdate, TaskStatus

from app.store.store import TaskStore
from app.services.task_service import TaskService

router = APIRouter()
store = TaskStore()
service = TaskService(store)

@router.get("/")
def whats_in_root(): 
    return {
        "message": "Backend is running"
    }

@router.get("/tasks")
def get_tasks(): 
    return service.get_all_tasks()

@router.post("/tasks")
def create_task(payload:TaskCreate): 
    return service.create_task(payload)

@router.patch("/tasks/{task_id}")
def update_tasks(task_id: str, update: TaskUpdate):
    return service.update_task(task_id, update)
    
@router.get("/tasks/{task_id}")
def get_task(task_id: str): 
    return service.get_task(task_id)

