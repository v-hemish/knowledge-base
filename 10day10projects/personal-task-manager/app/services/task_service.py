from app.schemas import Task, TaskCreate, TaskUpdate, TaskStatus
from app.store.store import TaskStore
import uuid
from typing import List

class TaskService: 

    def __init__(self, store): 
        self.store = store

    def create_task(self, payload: TaskCreate) -> Task: 
        task = Task(
            task_id = str(uuid.uuid4()),
            text = payload.text, 
            status = TaskStatus.TASKS.value
        )
        return self.store.create_task(task)

    def get_all_tasks(self) -> List[Task]: 
        self.store.get_all_tasks()

    def update_task(self, task_id: str, payload: TaskUpdate) -> Task: 
        task = self.store.update_task(task_id, payload)
        if task is None: 
            raise HTTPException(status_code = 404, detail = "Task not found to update")
        return task

    def get_task(self, task_id:str) -> Task: 
        task = self.store.get_task(task_id)
        if task is None: 
            raise HTTPException(status_code = 404, detail = "Task not found to retrieve")
        return task

        
