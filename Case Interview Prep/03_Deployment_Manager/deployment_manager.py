"""
Deployment Manager - Skeleton Implementation

This module manages deployments across different environments with varying policies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple
from datetime import datetime, time
from enum import Enum


class DeploymentStatus(Enum):
    """
    TODO: Define deployment statuses
    Examples: PENDING, IN_PROGRESS, SUCCESS, FAILED, ROLLED_BACK
    """
    pass


class HealthCheckResult(Enum):
    """
    TODO: Define health check results
    Examples: PASS, FAIL, TIMEOUT
    """
    pass


class Environment(ABC):
    """
    Base class for deployment environments.
    
    Each environment has different deployment policies.
    """
    
    def __init__(self, name: str):
        """
        TODO: Store environment name
        """
        pass
    
    @abstractmethod
    def requires_approval(self) -> bool:
        """
        TODO: Return whether this environment requires manual approval
        """
        pass
    
    @abstractmethod
    def is_deploy_allowed(self, deploy_time: datetime) -> Tuple[bool, str]:
        """
        Check if deployment is allowed at the given time.
        
        TODO:
        - Check if time falls within allowed windows
        - Check for blackout periods
        - Return (allowed: bool, reason: str)
        
        Args:
            deploy_time: The time of the proposed deployment
            
        Returns:
            Tuple of (is_allowed, reason_message)
        """
        pass
    
    @abstractmethod
    def auto_rollback_on_failure(self) -> bool:
        """
        TODO: Return whether this environment auto-rolls back on failure
        """
        pass
    
    @abstractmethod
    def get_health_checks(self) -> List[str]:
        """
        TODO: Return list of health check names to run after deployment
        """
        pass


class DevEnvironment(Environment):
    """
    Development environment - most permissive.
    
    TODO: Implement policies:
    - No approval required
    - Deployments allowed 24/7
    - No automatic rollback (devs fix forward)
    - Minimal health checks
    """
    
    def __init__(self):
        pass
    
    def requires_approval(self) -> bool:
        pass
    
    def is_deploy_allowed(self, deploy_time: datetime) -> Tuple[bool, str]:
        pass
    
    def auto_rollback_on_failure(self) -> bool:
        pass
    
    def get_health_checks(self) -> List[str]:
        pass


class StagingEnvironment(Environment):
    """
    Staging environment - moderate restrictions.
    
    TODO: Implement policies:
    - No approval required (or optional)
    - Deployments allowed during business hours
    - Automatic rollback on health check failure
    - Standard health checks
    """
    
    def __init__(self):
        pass
    
    def requires_approval(self) -> bool:
        pass
    
    def is_deploy_allowed(self, deploy_time: datetime) -> Tuple[bool, str]:
        """
        TODO: Check if time is during business hours (e.g., 8am-6pm on weekdays)
        """
        pass
    
    def auto_rollback_on_failure(self) -> bool:
        pass
    
    def get_health_checks(self) -> List[str]:
        pass


class ProductionEnvironment(Environment):
    """
    Production environment - most restrictive.
    
    TODO: Implement policies:
    - Requires manual approval
    - Deployments only during approved windows (e.g., Tue/Thu 2am-4am)
    - Automatic rollback on any failure
    - Comprehensive health checks
    - No deployments on Fridays or before holidays
    """
    
    def __init__(self):
        pass
    
    def requires_approval(self) -> bool:
        pass
    
    def is_deploy_allowed(self, deploy_time: datetime) -> Tuple[bool, str]:
        """
        TODO: 
        - Check day of week and time
        - Verify it's in an approved deployment window
        - Return detailed reason if not allowed
        """
        pass
    
    def auto_rollback_on_failure(self) -> bool:
        pass
    
    def get_health_checks(self) -> List[str]:
        pass


class Deployment:
    """
    Represents a single deployment.
    
    TODO: Track:
    - deployment_id
    - environment
    - version/artifact being deployed
    - status
    - start_time, end_time
    - approval (if required)
    - health check results
    """
    
    def __init__(self, deployment_id: str, environment: Environment, version: str):
        """
        TODO: Initialize deployment object
        """
        pass


class DeploymentManager:
    """
    Manages the deployment process across environments.
    """
    
    def __init__(self):
        """
        TODO:
        - Store available environments (dev, staging, prod)
        - Track deployment history
        - Track pending approvals
        """
        pass
    
    def validate_deployment(self, environment_name: str, 
                          deploy_time: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Validate if deployment can proceed.
        
        TODO:
        - Get the environment
        - Check if deploy is allowed at the given time
        - Check if approval exists (if required)
        - Return (can_deploy, reason)
        
        Args:
            environment_name: Name of target environment
            deploy_time: Proposed deployment time (default: now)
            
        Returns:
            Tuple of (is_valid, reason_message)
        """
        pass
    
    def request_approval(self, deployment_id: str) -> str:
        """
        Request approval for a deployment.
        
        TODO:
        - Store approval request
        - Return approval_request_id
        - In real system, this would notify approvers
        """
        pass
    
    def approve_deployment(self, approval_request_id: str, approver: str) -> None:
        """
        Approve a pending deployment.
        
        TODO:
        - Find the approval request
        - Mark as approved with approver name
        - Store timestamp
        """
        pass
    
    def deploy(self, environment_name: str, version: str, 
               approval_id: Optional[str] = None) -> Deployment:
        """
        Execute a deployment.
        
        TODO:
        - Validate deployment is allowed
        - Create Deployment object
        - Simulate deployment steps:
            1. Pre-deployment health check
            2. Deploy artifacts
            3. Post-deployment health checks
            4. Update status
        - If health checks fail and auto_rollback is enabled, rollback
        - Return the Deployment object with final status
        
        Args:
            environment_name: Target environment
            version: Version/artifact to deploy
            approval_id: Approval ID if required
            
        Returns:
            Deployment object with results
        """
        pass
    
    def _simulate_deployment(self, deployment: Deployment) -> bool:
        """
        Simulate the actual deployment process.
        
        TODO:
        - In real implementation, this would deploy actual artifacts
        - For this exercise, simulate success/failure
        - Could use random chance or check version format
        - Return True for success, False for failure
        """
        pass
    
    def _run_health_checks(self, deployment: Deployment) -> bool:
        """
        Run health checks for the deployment.
        
        TODO:
        - Get health checks from environment
        - Simulate running each check
        - Return True if all pass, False if any fail
        - Store results in deployment object
        """
        pass
    
    def rollback(self, deployment: Deployment) -> bool:
        """
        Rollback a failed deployment.
        
        TODO:
        - Simulate rollback process
        - Update deployment status to ROLLED_BACK
        - Run health checks after rollback
        - Return success status
        """
        pass
    
    def get_deployment_history(self, environment_name: Optional[str] = None) -> List[Dict]:
        """
        Get deployment history.
        
        TODO:
        - Return list of past deployments
        - Filter by environment if specified
        - Include key details (id, env, version, status, time)
        """
        pass


# Example usage and testing
if __name__ == "__main__":
    """
    TODO: Test your implementation
    
    Test scenarios:
    1. Deploy to dev (should always work)
    2. Deploy to staging during business hours (should work)
    3. Deploy to staging at midnight (should fail)
    4. Deploy to prod without approval (should fail)
    5. Request approval and then deploy to prod
    6. Simulate failed deployment with auto-rollback
    7. Check deployment history
    """
    pass
