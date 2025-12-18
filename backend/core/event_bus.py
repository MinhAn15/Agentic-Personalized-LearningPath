from typing import Dict, List, Callable, Any
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventBus:
    """
    Event bus for inter-agent communication.
    
    Enables agents to:
    - Publish events/messages
    - Subscribe to specific event types
    - React to events asynchronously
    """
    
    def __init__(self):
        """Initialize event bus"""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.logger.info(f"Handler subscribed to {event_type}")
    
    async def publish(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """
        Publish an event to all interested subscribers.
        
        Args:
            sender: Agent ID of sender
            receiver: Agent ID or type of receiver
            message_type: Type of message
            payload: Message payload
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "receiver": receiver,
            "message_type": message_type,
            "payload": payload
        }
        
        # Log event
        self.event_log.append(event)
        self.logger.info(f"Event published: {sender} → {receiver} ({message_type})")
        
        # Call all subscribers for this event type
        if message_type in self.subscribers:
            handlers = self.subscribers[message_type]
            tasks = [handler(event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_event_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent events from log.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        return self.event_log[-limit:]
    
    async def clear_log(self) -> None:
        """Clear event log"""
        self.event_log.clear()
