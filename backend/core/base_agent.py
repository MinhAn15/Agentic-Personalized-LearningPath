from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any
import logging

class AgentType(str, Enum):
    """Types of agents in the system"""
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    PROFILER = "profiler"
    PATH_PLANNER = "path_planner"
    TUTOR = "tutor"
    EVALUATOR = "evaluator"
    KAG = "kag"

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Responsibilities:
    - Execute agent-specific tasks
    - Manage agent state
    - Communicate with other agents via event bus
    - Log activities
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, state_manager, event_bus):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type of agent (from AgentType enum)
            state_manager: CentralStateManager instance for shared state
            event_bus: EventBus instance for inter-agent communication
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state_manager = state_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(f"{agent_type.value}.{agent_id}")
        self.logger.info(f"Initialized {agent_type.value} agent: {agent_id}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute agent's main task.
        
        This must be implemented by each agent subclass.
        
        Args:
            **kwargs: Agent-specific parameters
            
        Returns:
            Dict with execution results (must include 'success' key)
        """
        pass
    
    async def save_state(self, key: str, value: Any) -> None:
        """
        Save state to central state manager.
        
        Args:
            key: State key
            value: State value
        """
        await self.state_manager.set(key, value)
    
    async def get_state(self, key: str) -> Any:
        """
        Get state from central state manager.
        
        Args:
            key: State key
            
        Returns:
            State value or None if not found
        """
        return await self.state_manager.get(key)
    
    async def send_message(self, receiver: str, message_type: str, payload: Dict[str, Any]) -> None:
        """
        Send message to another agent via event bus.
        
        Args:
            receiver: Receiver agent ID or type
            message_type: Type of message
            payload: Message payload
        """
        await self.event_bus.publish(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            payload=payload
        )
    
    async def subscribe(self, message_type: str, handler) -> None:
        """
        Subscribe to messages of a specific type.
        
        Args:
            message_type: Type of message to subscribe to
            handler: Async function to handle message
        """
        await self.event_bus.subscribe(message_type, handler)
