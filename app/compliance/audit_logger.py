import uuid
from datetime import datetime
from app.models.audit import AuditLog


class AuditLogger:
    def log(self, db, business_id, category, action, description, description_ar="",
            actor_type="system", actor_id=None, resource_type=None, resource_id=None,
            metadata=None, risk_level="low", **kwargs):
        entry = AuditLog(
            id=str(uuid.uuid4()), business_id=business_id, category=category,
            action=action, description=description, description_ar=description_ar or description,
            actor_type=actor_type, actor_id=actor_id, resource_type=resource_type,
            resource_id=resource_id, metadata_extra=metadata or {}, risk_level=risk_level,
        )
        db.add(entry)
        return entry

    def log_ai_decision(self, db, business_id, agent_name, conversation_id,
                         decision, confidence, model_used, was_escalated=False):
        return self.log(
            db=db, business_id=business_id, category="ai_decision",
            action=f"ai.{agent_name}.decision",
            description=f"Agent {agent_name}: {decision} (conf: {confidence:.2f})",
            actor_type="ai_agent", actor_id=agent_name,
            resource_type="conversation", resource_id=conversation_id,
            metadata={"confidence": confidence, "model": model_used},
            risk_level="high" if was_escalated else "low",
        )


audit_logger = AuditLogger()