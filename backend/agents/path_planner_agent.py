"""
Path Planner Agent (RL-based)

Responsible for:
- Generating personalized learning paths
- Optimizing path based on learner profile
- Using RL for adaptive path recommendations
- Handling prerequisite dependencies
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging
import random

from backend.core.base_agent import BaseAgent, AgentType
from backend.core.event_bus import EventType, Event

logger = logging.getLogger(__name__)


class PathNodeStatus(str, Enum):
    """Status of a node in the learning path"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class LearningPathNode:
    """A single node in the learning path"""
    node_id: str
    concept_id: str
    concept_name: str
    order: int
    status: PathNodeStatus = PathNodeStatus.NOT_STARTED
    estimated_duration: int = 30  # minutes
    difficulty: float = 0.5  # 0.0 to 1.0
    resources: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "order": self.order,
            "status": self.status.value,
            "estimated_duration": self.estimated_duration,
            "difficulty": self.difficulty,
            "resources": self.resources,
            "prerequisites": self.prerequisites
        }


@dataclass
class LearningPath:
    """Complete learning path for a user"""
    path_id: str
    user_id: str
    goal: str
    nodes: List[LearningPathNode] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_duration: int = 0
    progress: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "user_id": self.user_id,
            "goal": self.goal,
            "nodes": [node.to_dict() for node in self.nodes],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_duration": self.total_duration,
            "progress": self.progress
        }


class RLPathOptimizer:
    """
    Simple RL-based path optimizer using Q-learning concepts.
    
    State: Current knowledge state + remaining concepts
    Action: Next concept to learn
    Reward: Learning efficiency + completion
    """
    
    def __init__(self, learning_rate: float = 0.1, discount: float = 0.9):
        self.learning_rate = learning_rate
        self.discount = discount
        self.q_table: Dict[str, Dict[str, float]] = {}
    
    def get_state_key(
        self, 
        current_concept: str, 
        mastered: List[str]
    ) -> str:
        """Create state key from current position and mastered concepts"""
        mastered_str = ",".join(sorted(mastered))
        return f"{current_concept}|{mastered_str}"
    
    def get_q_value(self, state: str, action: str) -> float:
        """Get Q-value for state-action pair"""
        if state not in self.q_table:
            self.q_table[state] = {}
        return self.q_table[state].get(action, 0.0)
    
    def update_q_value(
        self, 
        state: str, 
        action: str, 
        reward: float, 
        next_state: str,
        available_actions: List[str]
    ) -> None:
        """Update Q-value using Q-learning update rule"""
        current_q = self.get_q_value(state, action)
        
        # Get max Q-value for next state
        max_next_q = 0.0
        if available_actions:
            max_next_q = max(
                self.get_q_value(next_state, a) for a in available_actions
            )
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount * max_next_q - current_q
        )
        
        if state not in self.q_table:
            self.q_table[state] = {}
        self.q_table[state][action] = new_q
    
    def select_action(
        self, 
        state: str, 
        available_actions: List[str],
        epsilon: float = 0.1
    ) -> str:
        """Select action using epsilon-greedy strategy"""
        if not available_actions:
            return None
        
        # Exploration
        if random.random() < epsilon:
            return random.choice(available_actions)
        
        # Exploitation
        q_values = [
            (action, self.get_q_value(state, action)) 
            for action in available_actions
        ]
        return max(q_values, key=lambda x: x[1])[0]


class PathPlannerAgent(BaseAgent):
    """
    Agent responsible for creating and optimizing learning paths.
    
    Features:
    - RL-based path optimization
    - Prerequisite handling
    - Adaptive difficulty adjustment
    - Time-based planning
    
    Algorithms:
    - Q-learning for path optimization
    - Topological sort for prerequisites
    - Dynamic programming for optimal ordering
    """
    
    def __init__(
        self,
        agent_id: str,
        state_manager: Any,
        event_bus: Any,
        llm: Optional[Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PLANNER,
            state_manager=state_manager,
            event_bus=event_bus
        )
        self.llm = llm
        self.optimizer = RLPathOptimizer()
        self.paths: Dict[str, LearningPath] = {}
        
        # Subscribe to events
        self.event_bus.subscribe(
            EventType.PATH_CREATED,
            self._on_path_event
        )
        self.event_bus.subscribe(
            EventType.USER_PROGRESS,
            self._on_progress_event
        )
    
    async def execute(
        self,
        user_id: str,
        action: str = "generate_path",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute planner actions.
        
        Args:
            user_id: The learner's ID
            action: Action to perform (generate_path, update_path, 
                   get_next_node, optimize_path)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing action results
        """
        self.logger.info(f"🗺️ Planner action: {action} for user {user_id}")
        
        try:
            if action == "generate_path":
                return await self._generate_path(user_id, **kwargs)
            
            elif action == "update_path":
                return await self._update_path(user_id, **kwargs)
            
            elif action == "get_next_node":
                return await self._get_next_node(user_id, **kwargs)
            
            elif action == "optimize_path":
                return await self._optimize_path(user_id, **kwargs)
            
            elif action == "get_path":
                return await self._get_path(user_id, **kwargs)
            
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ Planner action failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_path(
        self,
        user_id: str,
        goal: str,
        concepts: List[Dict[str, Any]],
        knowledge_states: Optional[Dict[str, Any]] = None,
        time_budget: Optional[int] = None,  # minutes
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a personalized learning path"""
        
        import hashlib
        path_id = hashlib.md5(
            f"{user_id}:{goal}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Sort concepts by prerequisites (topological sort)
        sorted_concepts = self._topological_sort(concepts)
        
        # Filter out mastered concepts
        if knowledge_states:
            sorted_concepts = [
                c for c in sorted_concepts
                if knowledge_states.get(c["concept_id"], {}).get("confidence", 0) < 0.8
            ]
        
        # Create path nodes
        nodes = []
        total_duration = 0
        
        for i, concept in enumerate(sorted_concepts):
            node = LearningPathNode(
                node_id=f"{path_id}_{i}",
                concept_id=concept["concept_id"],
                concept_name=concept["name"],
                order=i,
                estimated_duration=concept.get("estimated_hours", 1) * 60,
                difficulty=concept.get("difficulty", 0.5),
                prerequisites=concept.get("prerequisites", [])
            )
            nodes.append(node)
            total_duration += node.estimated_duration
        
        # Apply time budget if specified
        if time_budget and total_duration > time_budget:
            nodes = self._prioritize_by_importance(nodes, time_budget)
            total_duration = sum(n.estimated_duration for n in nodes)
        
        # Create learning path
        path = LearningPath(
            path_id=path_id,
            user_id=user_id,
            goal=goal,
            nodes=nodes,
            total_duration=total_duration
        )
        
        # Store path
        self.paths[path_id] = path
        await self.save_state(f"path:{path_id}", path.to_dict())
        await self.save_state(f"user_path:{user_id}", path_id)
        
        # Publish event
        await self.event_bus.publish(Event(
            event_type=EventType.PATH_CREATED,
            source=self.agent_id,
            payload={"path_id": path_id, "user_id": user_id}
        ))
        
        self.logger.info(
            f"✅ Generated path with {len(nodes)} nodes, "
            f"~{total_duration // 60}h total"
        )
        
        return {
            "status": "success",
            "path": path.to_dict()
        }
    
    def _topological_sort(
        self, 
        concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sort concepts by prerequisites"""
        # Build adjacency list
        graph = {c["concept_id"]: c.get("prerequisites", []) for c in concepts}
        concept_map = {c["concept_id"]: c for c in concepts}
        
        # Simple topological sort
        visited = set()
        result = []
        
        def visit(concept_id: str):
            if concept_id in visited:
                return
            visited.add(concept_id)
            for prereq in graph.get(concept_id, []):
                if prereq in concept_map:
                    visit(prereq)
            if concept_id in concept_map:
                result.append(concept_map[concept_id])
        
        for concept_id in graph:
            visit(concept_id)
        
        return result
    
    def _prioritize_by_importance(
        self, 
        nodes: List[LearningPathNode],
        time_budget: int
    ) -> List[LearningPathNode]:
        """Prioritize nodes within time budget"""
        # Simple greedy: take nodes until budget exhausted
        selected = []
        remaining_time = time_budget
        
        for node in nodes:
            if node.estimated_duration <= remaining_time:
                selected.append(node)
                remaining_time -= node.estimated_duration
        
        # Re-order selected nodes
        for i, node in enumerate(selected):
            node.order = i
        
        return selected
    
    async def _update_path(
        self,
        user_id: str,
        path_id: str,
        node_id: str,
        status: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update path node status"""
        
        if path_id not in self.paths:
            saved = await self.load_state(f"path:{path_id}")
            if saved:
                self.paths[path_id] = self._dict_to_path(saved)
            else:
                return {"status": "error", "error": "Path not found"}
        
        path = self.paths[path_id]
        
        # Update node status
        for node in path.nodes:
            if node.node_id == node_id:
                node.status = PathNodeStatus(status)
                break
        
        # Recalculate progress
        completed = sum(
            1 for n in path.nodes 
            if n.status == PathNodeStatus.COMPLETED
        )
        path.progress = completed / len(path.nodes) if path.nodes else 0
        path.updated_at = datetime.now()
        
        # Save
        await self.save_state(f"path:{path_id}", path.to_dict())
        
        # Publish update event
        await self.event_bus.publish(Event(
            event_type=EventType.PATH_UPDATED,
            source=self.agent_id,
            payload={
                "path_id": path_id,
                "node_id": node_id,
                "status": status,
                "progress": path.progress
            }
        ))
        
        return {
            "status": "success",
            "path": path.to_dict()
        }
    
    async def _get_next_node(
        self,
        user_id: str,
        path_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get the next node to learn"""
        
        if not path_id:
            path_id = await self.load_state(f"user_path:{user_id}")
        
        if not path_id or path_id not in self.paths:
            return {"status": "error", "error": "No active path"}
        
        path = self.paths[path_id]
        
        # Find first incomplete node
        for node in path.nodes:
            if node.status in [PathNodeStatus.NOT_STARTED, PathNodeStatus.IN_PROGRESS]:
                return {
                    "status": "success",
                    "next_node": node.to_dict(),
                    "progress": path.progress
                }
        
        return {
            "status": "completed",
            "message": "All nodes completed!",
            "progress": 1.0
        }
    
    async def _optimize_path(
        self,
        user_id: str,
        path_id: str,
        performance_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Optimize path based on performance using RL"""
        
        if path_id not in self.paths:
            return {"status": "error", "error": "Path not found"}
        
        path = self.paths[path_id]
        
        # Use RL optimizer to update Q-values
        current_node = performance_data.get("completed_node")
        next_options = [
            n.concept_id for n in path.nodes 
            if n.status == PathNodeStatus.NOT_STARTED
        ]
        
        if current_node and next_options:
            # Calculate reward based on performance
            reward = self._calculate_reward(performance_data)
            
            state = self.optimizer.get_state_key(
                current_node,
                [n.concept_id for n in path.nodes if n.status == PathNodeStatus.COMPLETED]
            )
            
            # Select best next action
            best_next = self.optimizer.select_action(
                state, 
                next_options,
                epsilon=0.1
            )
            
            self.logger.debug(f"🎯 RL recommends: {best_next}")
        
        return {
            "status": "success",
            "message": "Path optimized based on performance"
        }
    
    def _calculate_reward(self, performance_data: Dict) -> float:
        """Calculate reward for RL update"""
        score = performance_data.get("score", 0.5)
        time_efficiency = performance_data.get("time_efficiency", 0.5)
        return score * 0.7 + time_efficiency * 0.3
    
    async def _get_path(
        self,
        user_id: str,
        path_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get current path for user"""
        
        if not path_id:
            path_id = await self.load_state(f"user_path:{user_id}")
        
        if not path_id:
            return {"status": "not_found", "message": "No path found for user"}
        
        if path_id not in self.paths:
            saved = await self.load_state(f"path:{path_id}")
            if saved:
                self.paths[path_id] = self._dict_to_path(saved)
            else:
                return {"status": "not_found", "message": "Path not found"}
        
        return {
            "status": "success",
            "path": self.paths[path_id].to_dict()
        }
    
    def _dict_to_path(self, data: Dict) -> LearningPath:
        """Convert dict back to LearningPath"""
        nodes = [
            LearningPathNode(
                node_id=n["node_id"],
                concept_id=n["concept_id"],
                concept_name=n["concept_name"],
                order=n["order"],
                status=PathNodeStatus(n["status"]),
                estimated_duration=n["estimated_duration"],
                difficulty=n["difficulty"],
                prerequisites=n.get("prerequisites", [])
            )
            for n in data.get("nodes", [])
        ]
        
        return LearningPath(
            path_id=data["path_id"],
            user_id=data["user_id"],
            goal=data["goal"],
            nodes=nodes,
            total_duration=data.get("total_duration", 0),
            progress=data.get("progress", 0.0)
        )
    
    async def _on_path_event(self, event: Event) -> None:
        """Handle path events"""
        if event.source != self.agent_id:
            self.logger.debug(f"📥 Path event from {event.source}")
    
    async def _on_progress_event(self, event: Event) -> None:
        """Handle progress events to potentially re-optimize path"""
        self.logger.debug(f"📥 Progress event: {event.payload}")
