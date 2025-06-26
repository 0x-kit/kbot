# skill_system/execution.py
"""
Execution Engine for Visual Skills

Handles intelligent skill execution with visual verification,
smart queueing, and retry logic.
"""

import time
import queue
import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
import logging

from .skill_types import (
    VisualSkill, SkillState, ExecutionMode, QueuePriority,
    SkillExecutionResult, VisualRotation
)


@dataclass
class SkillExecutionRequest:
    """Request for skill execution"""
    skill: VisualSkill
    mode: ExecutionMode
    priority: QueuePriority
    verify_execution: bool = True
    retry_count: int = 0
    max_retries: int = 3
    requested_time: float = 0.0
    timeout: float = 5.0
    
    def __post_init__(self):
        if self.requested_time == 0.0:
            self.requested_time = time.time()


class ExecutionEngine:
    """Advanced skill execution engine with visual verification"""
    
    def __init__(self, input_controller=None, detector=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.input_controller = input_controller
        self.detector = detector
        
        # Execution queue
        self._execution_queue = queue.PriorityQueue()
        self._execution_thread: Optional[threading.Thread] = None
        self._execution_enabled = False
        
        # State tracking
        self._currently_executing: Optional[SkillExecutionRequest] = None
        self._last_execution_time = 0.0
        self._global_cooldown = 0.15
        
        # Performance metrics
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'verified_executions': 0,
            'queue_size': 0,
            'avg_execution_time': 0.0,
            'retry_count': 0
        }
        
        # Execution history for analysis
        self._execution_history: List[SkillExecutionResult] = []
        self._max_history_size = 100
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'execution_started': [],
            'execution_completed': [],
            'execution_failed': [],
            'queue_empty': []
        }
        
        # Smart execution features
        self.adaptive_timing = True
        self.auto_retry = True
        self.visual_verification = True
        
    def start(self) -> bool:
        """Start the execution engine"""
        try:
            if self._execution_enabled:
                self.logger.warning("Execution engine already running")
                return True
            
            self._execution_enabled = True
            self._execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
            self._execution_thread.start()
            
            self.logger.info("Execution engine started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start execution engine: {e}")
            return False
    
    def stop(self):
        """Stop the execution engine"""
        self._execution_enabled = False
        if self._execution_thread and self._execution_thread.is_alive():
            self._execution_thread.join(timeout=2.0)
        
        # Clear queue
        while not self._execution_queue.empty():
            try:
                self._execution_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("Execution engine stopped")
    
    def execute_skill(self, skill: VisualSkill, mode: ExecutionMode = ExecutionMode.IMMEDIATE,
                     priority: QueuePriority = QueuePriority.NORMAL,
                     verify: bool = True) -> bool:
        """Execute skill with specified mode and priority"""
        try:
            request = SkillExecutionRequest(
                skill=skill,
                mode=mode,
                priority=priority,
                verify_execution=verify and self.visual_verification
            )
            
            if mode == ExecutionMode.IMMEDIATE:
                return self._execute_immediately(request)
            elif mode == ExecutionMode.PRIORITY:
                request.priority = QueuePriority.HIGH
                return self._queue_execution(request)
            else:
                return self._queue_execution(request)
                
        except Exception as e:
            self.logger.error(f"Skill execution request failed for {skill.name}: {e}")
            return False
    
    def execute_rotation(self, rotation: VisualRotation, skills: Dict[str, VisualSkill]) -> bool:
        """Execute skills from rotation"""
        try:
            if not rotation.enabled:
                return False
            
            next_skill_name = rotation.get_next_skill(skills)
            if not next_skill_name:
                return False
            
            skill = skills.get(next_skill_name)
            if not skill:
                return False
            
            return self.execute_skill(skill, ExecutionMode.ROTATION, QueuePriority.NORMAL)
            
        except Exception as e:
            self.logger.error(f"Rotation execution failed: {e}")
            return False
    
    def _execute_immediately(self, request: SkillExecutionRequest) -> bool:
        """Execute skill immediately if possible"""
        try:
            # Check global cooldown
            current_time = time.time()
            if current_time - self._last_execution_time < self._global_cooldown:
                # Queue instead of immediate execution
                return self._queue_execution(request)
            
            # Check if skill is ready
            if not request.skill.is_ready():
                self.logger.debug(f"Skill {request.skill.name} not ready for immediate execution")
                return False
            
            return self._perform_execution(request)
            
        except Exception as e:
            self.logger.error(f"Immediate execution failed: {e}")
            return False
    
    def _queue_execution(self, request: SkillExecutionRequest) -> bool:
        """Add skill to execution queue"""
        try:
            # Priority queue uses negative priority for max-heap behavior
            priority = -request.priority.value
            self._execution_queue.put((priority, time.time(), request))
            
            self.execution_stats['queue_size'] = self._execution_queue.qsize()
            self.logger.debug(f"Queued skill {request.skill.name} with priority {request.priority.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue skill {request.skill.name}: {e}")
            return False
    
    def _execution_loop(self):
        """Main execution loop"""
        self.logger.debug("Execution loop started")
        
        while self._execution_enabled:
            try:
                # Get next execution request
                try:
                    priority, timestamp, request = self._execution_queue.get(timeout=0.1)
                    self.execution_stats['queue_size'] = self._execution_queue.qsize()
                except queue.Empty:
                    # Trigger queue empty callback
                    if self._execution_queue.empty():
                        self._trigger_callback('queue_empty')
                    continue
                
                # Check if request is still valid
                current_time = time.time()
                if current_time - request.requested_time > request.timeout:
                    self.logger.warning(f"Execution request timed out: {request.skill.name}")
                    continue
                
                # Execute the skill
                self._perform_execution(request)
                
            except Exception as e:
                self.logger.error(f"Execution loop error: {e}")
                time.sleep(0.1)
        
        self.logger.debug("Execution loop ended")
    
    def _perform_execution(self, request: SkillExecutionRequest) -> bool:
        """Perform actual skill execution"""
        start_time = time.time()
        self._currently_executing = request
        
        try:
            skill = request.skill
            
            # Check if skill is still ready
            if not skill.is_ready():
                if request.retry_count < request.max_retries and self.auto_retry:
                    request.retry_count += 1
                    self._queue_execution(request)
                    self.execution_stats['retry_count'] += 1
                    return False
                else:
                    result = SkillExecutionResult(
                        skill_name=skill.name,
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message="Skill not ready"
                    )
                    self._record_execution(result)
                    return False
            
            # Trigger execution started callback
            self._trigger_callback('execution_started', skill)
            
            # Perform input
            if not self.input_controller:
                raise Exception("No input controller available")
            
            input_start = time.time()
            success = self.input_controller.send_key(skill.key)
            input_delay = time.time() - input_start
            
            if not success:
                raise Exception("Input controller failed to send key")
            
            # Mark skill as executed
            skill.execute()
            self._last_execution_time = time.time()
            
            # Visual verification if requested
            verification_passed = True
            verification_delay = 0.0
            
            if request.verify_execution and self.detector and skill.position:
                verification_start = time.time()
                verification_passed = self._verify_execution(skill)
                verification_delay = time.time() - verification_start
            
            # Create execution result
            result = SkillExecutionResult(
                skill_name=skill.name,
                success=True,
                execution_time=time.time() - start_time,
                verification_passed=verification_passed,
                input_delay=input_delay,
                verification_delay=verification_delay
            )
            
            # Record execution
            self._record_execution(result)
            
            # Trigger completion callback
            self._trigger_callback('execution_completed', skill, result)
            
            self.logger.info(f"Skill executed successfully: {skill.name}")
            return True
            
        except Exception as e:
            # Create failed execution result
            result = SkillExecutionResult(
                skill_name=request.skill.name,
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
            
            # Record failed execution
            self._record_execution(result)
            
            # Trigger failure callback
            self._trigger_callback('execution_failed', request.skill, result)
            
            self.logger.error(f"Skill execution failed for {request.skill.name}: {e}")
            
            # Retry if enabled
            if request.retry_count < request.max_retries and self.auto_retry:
                request.retry_count += 1
                time.sleep(0.1)  # Small delay before retry
                self._queue_execution(request)
                self.execution_stats['retry_count'] += 1
            
            return False
            
        finally:
            self._currently_executing = None
    
    def _verify_execution(self, skill: VisualSkill) -> bool:
        """Verify skill execution through visual detection"""
        try:
            if not skill.position or not self.detector:
                return True  # Can't verify, assume success
            
            # Wait for visual change
            time.sleep(0.05)
            
            # Detect current state
            result = self.detector.detect_skill_in_region(
                skill, skill.position.region, skill.detection_config
            )
            
            # Check if skill went on cooldown (indicates successful execution)
            if result.state == SkillState.COOLDOWN:
                self.logger.debug(f"Execution verified for {skill.name}")
                return True
            else:
                self.logger.warning(f"Execution verification failed for {skill.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Execution verification error for {skill.name}: {e}")
            return False
    
    def _record_execution(self, result: SkillExecutionResult):
        """Record execution result for statistics"""
        try:
            # Update statistics
            self.execution_stats['total_executions'] += 1
            
            if result.success:
                self.execution_stats['successful_executions'] += 1
                if result.verification_passed:
                    self.execution_stats['verified_executions'] += 1
            else:
                self.execution_stats['failed_executions'] += 1
            
            # Update average execution time
            total_time = (self.execution_stats['avg_execution_time'] * 
                         (self.execution_stats['total_executions'] - 1) + 
                         result.execution_time)
            self.execution_stats['avg_execution_time'] = total_time / self.execution_stats['total_executions']
            
            # Add to history
            self._execution_history.append(result)
            if len(self._execution_history) > self._max_history_size:
                self._execution_history.pop(0)
            
        except Exception as e:
            self.logger.error(f"Failed to record execution result: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_size': self._execution_queue.qsize(),
            'currently_executing': self._currently_executing.skill.name if self._currently_executing else None,
            'execution_enabled': self._execution_enabled,
            'last_execution_time': self._last_execution_time,
            'global_cooldown': self._global_cooldown
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = self.execution_stats.copy()
        
        # Calculate success rate
        if stats['total_executions'] > 0:
            stats['success_rate'] = stats['successful_executions'] / stats['total_executions']
            stats['verification_rate'] = stats['verified_executions'] / stats['successful_executions'] if stats['successful_executions'] > 0 else 0
        else:
            stats['success_rate'] = 0.0
            stats['verification_rate'] = 0.0
        
        return stats
    
    def get_execution_history(self, limit: int = None) -> List[SkillExecutionResult]:
        """Get recent execution history"""
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history.copy()
    
    def clear_queue(self):
        """Clear the execution queue"""
        while not self._execution_queue.empty():
            try:
                self._execution_queue.get_nowait()
            except queue.Empty:
                break
        
        self.execution_stats['queue_size'] = 0
        self.logger.info("Execution queue cleared")
    
    def set_global_cooldown(self, cooldown: float):
        """Set global cooldown between skill executions"""
        self._global_cooldown = max(0.0, cooldown)
        self.logger.debug(f"Global cooldown set to {self._global_cooldown:.3f}s")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add execution event callback"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove execution event callback"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    def _trigger_callback(self, event_type: str, *args):
        """Trigger callbacks for execution event"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(*args)
            except Exception as e:
                self.logger.error(f"Execution callback error for {event_type}: {e}")
    
    def optimize_performance(self):
        """Optimize execution performance based on history"""
        try:
            if len(self._execution_history) < 10:
                return
            
            # Analyze recent execution times
            recent_executions = self._execution_history[-20:]
            avg_time = sum(r.execution_time for r in recent_executions) / len(recent_executions)
            
            # Adjust global cooldown based on performance
            if avg_time > 0.2:  # If executions are slow
                self._global_cooldown = min(0.3, self._global_cooldown * 1.1)
                self.logger.debug(f"Increased global cooldown to {self._global_cooldown:.3f}s")
            elif avg_time < 0.05:  # If executions are very fast
                self._global_cooldown = max(0.05, self._global_cooldown * 0.9)
                self.logger.debug(f"Decreased global cooldown to {self._global_cooldown:.3f}s")
            
            # Analyze verification success rate
            verified_rate = sum(1 for r in recent_executions if r.verification_passed) / len(recent_executions)
            if verified_rate < 0.7:  # Low verification rate
                self.logger.warning("Low verification rate detected, consider adjusting detection settings")
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
    
    def reset_stats(self):
        """Reset execution statistics"""
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'verified_executions': 0,
            'queue_size': self._execution_queue.qsize(),
            'avg_execution_time': 0.0,
            'retry_count': 0
        }
        self._execution_history.clear()
        self.logger.info("Execution statistics reset")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.stop()
        except:
            pass  # Ignore errors during cleanup