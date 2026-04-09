
from app.schemas import TaskCreate, Task
from typing import List, Optional


class TaskStore: 
    def __init__(self): 
        self.tasks = {}

    def create_task(self, task:Task) -> Task: 
        self.tasks[task.task_id] = task
        return task

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def get_task(self, task_id:str) -> Optional[Task]: 
        if task_id not in self.tasks: 
            return None

        return self.tasks[task_id]
    
    def update_task(self, task_id: str, update: TaskUpdate) -> Optional[Task]: 
        
        task = self.tasks.get(task_id)
        
        if task is None: 
            return None

        if update.text is not None: 
            task.text = update.text

        if update.status is not None: 
            task.status = update.status

        self.tasks[task_id] = task

        return task
