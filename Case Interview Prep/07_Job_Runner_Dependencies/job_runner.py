"""
Job Runner With Dependencies - Skeleton Implementation

This module orchestrates job execution with dependency resolution.
"""

from enum import Enum
from typing import Dict, List, Set, Callable, Any, Optional, Tuple
from dataclasses import dataclass


class JobStatus(Enum):
    """
    TODO: Define job statuses
    Examples: PENDING, RUNNING, SUCCESS, FAILED, BLOCKED, SKIPPED
    """
    pass


@dataclass
class JobResult:
    """
    Result of a job execution.
    
    TODO: Store:
    - job_id
    - status: final status
    - output: any return value from job
    - error: error message if failed
    - duration: execution time
    - retries: number of retry attempts
    """
    pass


class Job:
    """
    Represents a single job to be executed.
    """
    
    def __init__(self, job_id: str, func: Callable, 
                 dependencies: Optional[List[str]] = None):
        """
        Initialize a job.
        
        TODO:
        - Store job_id
        - Store func (the actual work to execute)
        - Store dependencies list (empty list if None)
        - Set initial status to PENDING
        """
        pass
    
    def execute(self) -> JobResult:
        """
        Execute the job function.
        
        TODO:
        - Set status to RUNNING
        - Call self.func()
        - Capture result or exception
        - Set status to SUCCESS or FAILED
        - Return JobResult with outcome
        """
        pass


class JobRunner:
    """
    Orchestrates execution of jobs with dependency resolution.
    """
    
    def __init__(self, max_retries: int = 2):
        """
        Initialize job runner.
        
        TODO:
        - Store max_retries
        - Create dict to store jobs (key: job_id)
        - Create dict to store job results
        """
        pass
    
    def add_job(self, job: Job) -> None:
        """
        Add a job to the runner.
        
        TODO:
        - Store job in jobs dict
        - Validate job_id is unique
        """
        pass
    
    def validate_dependencies(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that dependency graph is valid (no cycles, all deps exist).
        
        TODO:
        - Check that all dependency job_ids exist in jobs dict
        - Check for circular dependencies using DFS or topological sort
        - Return (is_valid, error_message)
        
        Algorithm hint: Use DFS with recursion stack to detect cycles
        """
        pass
    
    def _has_cycle(self) -> bool:
        """
        Detect if dependency graph has cycles.
        
        TODO: Implement cycle detection
        - Use DFS with three states: unvisited, visiting, visited
        - If you encounter a job that's currently "visiting", cycle exists
        - Return True if cycle found
        
        This is a classic graph algorithm - implement carefully!
        """
        pass
    
    def _get_execution_order(self) -> List[str]:
        """
        Compute valid execution order using topological sort.
        
        TODO:
        - Implement topological sort (Kahn's algorithm or DFS-based)
        - Return list of job_ids in valid execution order
        - Jobs with no dependencies should come first
        - Each job appears after all its dependencies
        
        Algorithm hint: 
        - Kahn's: Process jobs with no remaining dependencies iteratively
        - DFS: Post-order traversal, reverse the result
        """
        pass
    
    def run_all(self) -> Dict[str, JobResult]:
        """
        Execute all jobs in dependency order.
        
        TODO:
        - Validate dependencies first
        - Get execution order
        - For each job in order:
            - Check if all dependencies succeeded
            - If yes: execute the job
            - If no: mark as BLOCKED, skip execution
            - Handle retries for failures
        - Return dict of all results
        
        Returns:
            Dictionary mapping job_id to JobResult
        """
        pass
    
    def _can_execute_job(self, job_id: str) -> bool:
        """
        Check if a job's dependencies are satisfied.
        
        TODO:
        - Get the job
        - Check each dependency:
            - Has it been executed?
            - Did it succeed?
        - Return True only if all dependencies succeeded
        """
        pass
    
    def _execute_with_retry(self, job: Job) -> JobResult:
        """
        Execute a job with retry logic.
        
        TODO:
        - Attempt to execute job
        - If fails and retries < max_retries:
            - Retry execution
            - Increment retry count
        - Return final JobResult
        """
        pass
    
    def get_execution_report(self) -> Dict:
        """
        Generate summary report of execution.
        
        TODO: Return:
        - total_jobs
        - successful_jobs
        - failed_jobs
        - blocked_jobs
        - total_execution_time
        - jobs_by_status
        - dependency_graph_valid
        """
        pass


# Example usage and testing
if __name__ == "__main__":
    """
    TODO: Test your implementation
    
    Test scenarios:
    1. Create simple linear dependency: A -> B -> C
       - Verify execution order is correct
    2. Create diamond dependency: A -> B, A -> C, B -> D, C -> D
       - Verify D runs only after B and C
    3. Create circular dependency: A -> B -> C -> A
       - Verify it's detected and rejected
    4. Create job that fails
       - Verify downstream jobs are blocked
    5. Test retry logic
    6. Test jobs with no dependencies run first
    7. Generate execution report
    
    Helper: Create simple test functions that print and return values
    """
    pass
