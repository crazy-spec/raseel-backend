from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class AgentContext:
    business_id: str
    customer_id: str
    conversation_id: str
    message_text: str
    message_language: str = "ar"
    customer_history: List[Dict] = field(default_factory=list)
    products: List[Dict] = field(default_factory=list)
    sector: str = "general"
    customer_sentiment: float = 0.0
    customer_lead_score: str = "cold"
    is_vip: bool = False
    business_config: Dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    agent_name: str
    response_text: str
    confidence: float
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    detected_intent: str = "unknown"
    selected_action: str = "respond"
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    suggested_products: List[Dict] = field(default_factory=list)
    model_used: str = "unknown"
    processing_time_ms: int = 0
    tokens_used: int = 0
    metadata: Dict = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.85


class BaseAgent(ABC):
    def __init__(self, name: str, capabilities: list = None,
                 sector: str = None, confidence_threshold: float = 0.85):
        self.name = name
        self.capabilities = capabilities or []
        self.sector = sector
        self.confidence_threshold = confidence_threshold
        self.version = "1.0"

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        pass