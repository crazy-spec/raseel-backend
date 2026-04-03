"""
Voice Message Handler — integrates voice processing into the agent pipeline.
Sits between WhatsApp webhook and the Agent Orchestrator.
"""

from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.voice.processor import voice_processor, VoiceTranscription
from app.agents.orchestrator import orchestrator, AgentResponse
from app.compliance.consent_manager import (
    consent_manager, ConsentType, ConsentAction, ConsentChannel,
)
from app.compliance.audit_logger import audit_logger, AuditCategory
from app.whatsapp.bsp_client import WhatsAppMessage
import structlog
import uuid

logger = structlog.get_logger()


class VoiceMessageHandler:
    """
    Handles the complete voice message flow:
    1. Receive audio from WhatsApp
    2. Check voice consent
    3. Transcribe locally
    4. Feed text to agent orchestrator
    5. Respond to customer
    """
    
    async def handle_voice_message(
        self,
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        conversation_id: str,
        audio_data: bytes,
        audio_format: str = "ogg",
        customer_language: str = "ar",
    ) -> AgentResponse:
        """
        Process a voice message end-to-end.
        """
        
        # ── STEP 1: Check voice processing consent ──
        has_voice_consent = await voice_processor.check_voice_consent(
            db, business_id, customer_id,
        )
        
        if not has_voice_consent:
            # Send consent request — don't process the audio
            consent_msg = voice_processor.get_voice_consent_message(
                customer_language
            )
            
            # Log that we received but couldn't process
            await audit_logger.log(
                db=db,
                business_id=business_id,
                category=AuditCategory.COMPLIANCE_EVENT,
                action="voice.consent_required",
                description="Voice message received but not processed — "
                           "awaiting voice processing consent",
                description_ar="تم استلام رسالة صوتية ولكن لم تتم معالجتها — "
                              "في انتظار موافقة معالجة الصوت",
                actor_type="system",
                resource_type="customer",
                resource_id=customer_id,
                risk_level="medium",
            )
            await db.commit()
            
            return AgentResponse(
                agent_name="system",
                response_text=consent_msg,
                confidence=1.0,
                detected_intent="voice_consent_request",
                selected_action="request_voice_consent",
            )
        
        # ── STEP 2: Transcribe voice locally ──
        try:
            transcription = await voice_processor.process_voice_message(
                audio_data=audio_data,
                file_format=audio_format,
                customer_id=customer_id,
                business_id=business_id,
            )
        except RuntimeError as e:
            logger.error("voice_transcription_failed", error=str(e))
            
            # Fallback message — tell customer to type instead
            fallback = (
                "عذراً، لم نتمكن من معالجة الرسالة الصوتية حالياً. "
                "يرجى إرسال رسالة نصية وسنساعدك فوراً. 🙏"
                if customer_language == "ar" else
                "Sorry, we couldn't process your voice message right now. "
                "Please send a text message and we'll help you right away. 🙏"
            )
            
            return AgentResponse(
                agent_name="system",
                response_text=fallback,
                confidence=1.0,
                detected_intent="voice_processing_error",
                selected_action="request_text_fallback",
            )
        
        # ── STEP 3: Log transcription event (NOT the audio) ──
        await audit_logger.log(
            db=db,
            business_id=business_id,
            category=AuditCategory.AI_DECISION,
            action="voice.transcribed",
            description=f"Voice message transcribed locally. "
                       f"Duration: {transcription.duration_seconds:.1f}s, "
                       f"Language: {transcription.language}, "
                       f"Dialect: {transcription.dialect}, "
                       f"Confidence: {transcription.confidence:.2f}",
            description_ar=f"تم تحويل الرسالة الصوتية محلياً. "
                          f"المدة: {transcription.duration_seconds:.1f} ثانية، "
                          f"اللغة: {transcription.language}، "
                          f"اللهجة: {transcription.dialect}، "
                          f"الثقة: {transcription.confidence:.2f}",
            actor_type="ai_agent",
            actor_id="voice_processor",
            resource_type="conversation",
            resource_id=conversation_id,
            metadata={
                "duration_seconds": transcription.duration_seconds,
                "language": transcription.language,
                "dialect": transcription.dialect,
                "confidence": transcription.confidence,
                "processing_time_ms": transcription.processing_time_ms,
                "processed_locally": True,
                "audio_retained": False,  # PDPL: audio deleted immediately
            },
            risk_level="low",
        )
        
        # ── STEP 4: If transcription confidence too low ──
        if transcription.confidence < 0.6:
            low_conf_msg = (
                f"سمعت رسالتك الصوتية ولكن لم أفهمها بوضوح. "
                f"هل يمكنك إعادة إرسالها أو كتابة رسالة نصية؟ 🎤"
                if customer_language == "ar" else
                f"I heard your voice message but couldn't understand it clearly. "
                f"Could you resend it or type a text message? 🎤"
            )
            
            return AgentResponse(
                agent_name="system",
                response_text=low_conf_msg,
                confidence=transcription.confidence,
                detected_intent="voice_unclear",
                selected_action="request_retry",
            )
        
        # ── STEP 5: Feed transcribed text into agent orchestrator ──
        logger.info(
            "voice_to_agent_pipeline",
            business_id=business_id,
            transcribed_text_length=len(transcription.text),
            language=transcription.language,
            dialect=transcription.dialect,
        )
        
        # Process the transcribed text as if it were a regular text message
        response = await orchestrator.process_message(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            message_text=transcription.text,
            message_language=transcription.language,
            sector="general",  # Will be determined by orchestrator
        )
        
        # Add voice metadata to response
        response.metadata["voice_message"] = True
        response.metadata["voice_duration"] = transcription.duration_seconds
        response.metadata["voice_dialect"] = transcription.dialect
        response.metadata["transcribed_text"] = transcription.text
        
        return response
    
    async def handle_voice_consent_response(
        self,
        db: AsyncSession,
        business_id: str,
        customer_id: str,
        message_text: str,
    ) -> Optional[AgentResponse]:
        """
        Handle customer's response to voice consent request.
        Returns None if message is not a consent response.
        """
        text_lower = message_text.lower().strip()
        
        # Check for Arabic/English consent keywords
        agree_words = ["موافق_صوت", "agree_voice", "موافق صوت"]
        decline_words = ["رفض_صوت", "decline_voice", "رفض صوت"]
        
        if any(word in text_lower for word in agree_words):
            await consent_manager.record_consent(
                db=db,
                business_id=business_id,
                customer_id=customer_id,
                consent_type=ConsentType.VOICE_PROCESSING,
                action=ConsentAction.GRANTED,
                channel=ConsentChannel.WHATSAPP,
            )
            
            return AgentResponse(
                agent_name="system",
                response_text=(
                    "✅ شكراً لموافقتك. يمكنك الآن إرسال رسائل صوتية "
                    "وسنقوم بمعالجتها.\n\n"
                    "✅ Thank you for your consent. You can now send "
                    "voice messages and we'll process them."
                ),
                confidence=1.0,
                detected_intent="voice_consent_granted",
                selected_action="consent_confirmed",
            )
        
        elif any(word in text_lower for word in decline_words):
            await consent_manager.record_consent(
                db=db,
                business_id=business_id,
                customer_id=customer_id,
                consent_type=ConsentType.VOICE_PROCESSING,
                action=ConsentAction.REVOKED,
                channel=ConsentChannel.WHATSAPP,
            )
            
            return AgentResponse(
                agent_name="system",
                response_text=(
                    "تم تسجيل رفضك. لن نعالج الرسائل الصوتية. "
                    "يمكنك إرسال رسائل نصية وسنساعدك بكل سرور. ✍️\n\n"
                    "Your preference has been recorded. We won't process "
                    "voice messages. You can send text messages and "
                    "we'll be happy to help. ✍️"
                ),
                confidence=1.0,
                detected_intent="voice_consent_declined",
                selected_action="consent_declined",
            )
        
        # Not a consent response
        return None


# Singleton
voice_handler = VoiceMessageHandler()
