from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """Types of agents in the system"""
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    PROFILER = "profiler"
    PLANNER = "planner"
    TUTOR = "tutor"
    EVALUATOR = "evaluator"
    KAG = "kag"  # Knowledge Artifact Generation

class AgentMessage:
    """Message structure for inter-agent communication"""
    def __init__(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        payload: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.payload = payload
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Architecture:
    - Each agent is responsible for ONE task
    - Agents communicate via Event Bus
    - Agents manage their own state
    - Agents use LLM via LlamaIndex
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        state_manager: Any,  # Central State Manager
        event_bus: Any       # Event Bus
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state_manager = state_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(f"Agent.{agent_id}")
        
        self.logger.info(f"🤖 Initializing {agent_type.value} agent: {agent_id}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method that subclasses must implement.
        
        Args:
            **kwargs: Agent-specific parameters
        
        Returns:
            Dict containing execution results
        """
        pass
    
    async def send_message(self, receiver: str, message_type: str, payload: Dict):
        """Send message to another agent via Event Bus"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            payload=payload
        )
        await self.event_bus.publish(message)
        self.logger.debug(f"📤 Sent message to {receiver}: {message_type}")
    
    async def receive_message(self, message: AgentMessage) -> None:
        """
        Receive and handle message from another agent.
        Subclasses can override for custom handling.
        """
        self.logger.debug(f"📥 Received message from {message.sender}: {message.message_type}")
    
    async def save_state(self, key: str, value: Any) -> None:
        """Save agent state to Central State Manager"""
        await self.state_manager.set(f"{self.agent_id}:{key}", value)
    
    async def load_state(self, key: str) -> Optional[Any]:
        """Load agent state from Central State Manager"""
        return await self.state_manager.get(f"{self.agent_id}:{key}")
    
    async def health_check(self) -> bool:
        """Check if agent is healthy"""
        try:
            self.logger.info(f"✅ Health check passed for {self.agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return False

# Example usage in subclass:
# 
# class KnowledgeExtractionAgent(BaseAgent):
#     def __init__(self, agent_id, state_manager, event_bus, llm):
#         super().__init__(agent_id, AgentType.KNOWLEDGE_EXTRACTION, 
#                         state_manager, event_bus)
#         self.llm = llm
#     
#     async def execute(self, document_path: str, **kwargs):
#         # Custom implementation
#         return {"status": "success", "nodes": [...], "relationships": [...]}
