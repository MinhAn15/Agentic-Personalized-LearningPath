from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events in the system"""
    # Agent Communication
    AGENT_MESSAGE = "agent.message"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"
    
    # Learning Path Events
    PATH_CREATED = "path.created"
    PATH_UPDATED = "path.updated"
    PATH_COMPLETED = "path.completed"
    
    # User Events
    USER_PROGRESS = "user.progress"
    USER_ASSESSMENT = "user.assessment"
    USER_FEEDBACK = "user.feedback"
    
    # Knowledge Events
    KNOWLEDGE_EXTRACTED = "knowledge.extracted"
    KNOWLEDGE_UPDATED = "knowledge.updated"
    
    # System Events
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"


@dataclass
class Event:
    """Event structure for the Event Bus"""
    event_type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }


# Type alias for event handlers
EventHandler = Callable[[Event], asyncio.coroutine]


class EventBus:
    """
    Central Event Bus for inter-agent communication.
    
    Features:
    - Publish/Subscribe pattern
    - Async event handling
    - Event filtering by type
    - Event history for debugging
    
    Usage:
        bus = EventBus()
        
        # Subscribe to events
        async def handler(event: Event):
            print(f"Received: {event.payload}")
        
        bus.subscribe(EventType.AGENT_MESSAGE, handler)
        
        # Publish events
        await bus.publish(Event(
            event_type=EventType.AGENT_MESSAGE,
            source="agent_1",
            payload={"message": "Hello"}
        ))
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        self._history: List[Event] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("EventBus")
        self.logger.info("📡 Event Bus initialized")
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Subscribe to a specific event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self.logger.debug(f"📌 Subscribed to {event_type.value}")
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events"""
        self._global_subscribers.append(handler)
        self.logger.debug("📌 Subscribed to all events")
    
    def unsubscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Unsubscribe from a specific event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        async with self._lock:
            # Add to history
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)
        
        self.logger.debug(
            f"📤 Publishing {event.event_type.value} from {event.source}"
        )
        
        # Get all handlers for this event type
        handlers = self._subscribers.get(event.event_type, [])
        all_handlers = handlers + self._global_subscribers
        
        # Execute all handlers concurrently
        if all_handlers:
            tasks = [handler(event) for handler in all_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish_message(
        self,
        source: str,
        target: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Convenience method for agent-to-agent messages"""
        event = Event(
            event_type=EventType.AGENT_MESSAGE,
            source=source,
            payload={
                "target": target,
                "message_type": message_type,
                "data": payload
            }
        )
        await self.publish(event)
    
    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history, optionally filtered by type"""
        if event_type:
            filtered = [e for e in self._history if e.event_type == event_type]
            return filtered[-limit:]
        return self._history[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._history.clear()
        self.logger.info("🗑️ Event history cleared")
    
    async def wait_for_event(
        self, 
        event_type: EventType, 
        timeout: float = 30.0
    ) -> Optional[Event]:
        """Wait for a specific event type (useful for testing)"""
        future: asyncio.Future = asyncio.Future()
        
        async def capture_handler(event: Event):
            if not future.done():
                future.set_result(event)
        
        self.subscribe(event_type, capture_handler)
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ Timeout waiting for {event_type.value}")
            return None
        finally:
            self.unsubscribe(event_type, capture_handler)


# Singleton instance for the application
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the singleton Event Bus instance"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def create_event_bus(max_history: int = 1000) -> EventBus:
    """Create a new Event Bus instance (for testing)"""
    return EventBus(max_history=max_history)
