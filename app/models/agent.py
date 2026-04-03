import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, ForeignKey, Boolean, Integer
from app.database import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    message_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent_name = Column(String(50), nullable=False)
    agent_version = Column(String(20), default="1.0")
    input_text = Column(Text)
    detected_intent = Column(String(100))
    selected_action = Column(String(100))
    output_text = Column(Text)
    confidence_score = Column(Float, nullable=False)
    confidence_breakdown = Column(JSON)
    was_escalated = Column(Boolean, default=False)
    escalation_reason = Column(String(50))
    model_used = Column(String(50))
    processing_time_ms = Column(Integer)
    token_count_input = Column(Integer)
    token_count_output = Column(Integer)
    was_sent_to_customer = Column(Boolean, default=False)
    was_modified_by_human = Column(Boolean, default=False)
    human_modified_text = Column(Text)


class AgentFeedback(Base):
    __tablename__ = "agent_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False)
    agent_action_id = Column(String(36), ForeignKey("agent_actions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    admin_id = Column(String(36), nullable=False)
    rating = Column(Integer)
    feedback_type = Column(String(30))
    original_response = Column(Text)
    corrected_response = Column(Text)
    correction_reason = Column(Text)
    error_category = Column(String(50))
    tags = Column(JSON, default=list)
    used_for_training = Column(Boolean, default=False)