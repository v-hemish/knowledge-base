from pydantic import BaseModel, Field
from enum import Enum

class TaskCreate(BaseModel):
    text: str = Field(min_length = 1, max_length = 200)

class TaskStatus(str, Enum): 
    ICEBOX = "icebox"
    TASKS = "tasks"
    DOING = "doing"
    DONE = "done"
    BLOCKED = "blocked"

class TaskUpdate(BaseModel): 
    text: str | None = None
    status: TaskStatus | None = None

class Task(BaseModel): 
    task_id: str
    text: str
    status: TaskStatus
