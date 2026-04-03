"""
Voice Message Processor — Arabic Speech-to-Text
PDPL Compliant: Voice data is sensitive biometric data.

Architecture:
1. Voice arrives from WhatsApp (OGG/OPUS format)
2. Check customer has voice_processing consent
3. Process LOCALLY using Whisper (no data leaves Saudi Arabia)
4. Convert speech to text
5. Delete voice file immediately after transcription
6. Feed text into normal agent pipeline
7. Log the transcription event (but NOT the audio) in audit trail

Why local processing matters:
- Voice = biometric data under PDPL Article 1
- Sending to Google STT / OpenAI Whisper API = data export violation
- Local Whisper model runs on your server = data stays in Kingdom
"""

import os
import uuid
import time
import tempfile
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class VoiceTranscription:
    """Result of voice-to-text conversion."""
    text: str
    language: str                    # Detected language: "ar" or "en"
    confidence: float                # 0.0 to 1.0
    duration_seconds: float          # Length of the audio
    processing_time_ms: int          # How long transcription took
    dialect: Optional[str] = None    # "najdi", "hijazi", "khaleeji" if detected
    was_processed_locally: bool = True  # Always True for compliance


class VoiceProcessor:
    """
    Processes WhatsApp voice messages using local Whisper model.
    
    Setup requirement: 
    The Ollama container or a local Whisper server must be running.
    We use faster-whisper for Arabic which runs locally.
    
    For production at scale, deploy whisper on GPU instance
    within Saudi data center.
    """

    def __init__(self):
        # Local Whisper endpoint (runs alongside Ollama)
        self.whisper_endpoint = os.getenv(
            "WHISPER_ENDPOINT", 
            "http://localhost:9000/asr"
        )
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.temp_dir = Path(tempfile.gettempdir()) / "raseel_voice"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Maximum voice message length (WhatsApp allows up to 15 min)
        self.max_duration_seconds = 300  # 5 minutes max for processing
        
    async def process_voice_message(
        self,
        audio_data: bytes,
        file_format: str = "ogg",
        customer_id: str = None,
        business_id: str = None,
    ) -> VoiceTranscription:
        """
        Convert voice message to text.
        
        Flow:
        1. Save audio to temp file
        2. Send to local Whisper for transcription
        3. Delete audio file immediately
        4. Return text for agent processing
        """
        start_time = time.time()
        temp_file = None
        
        try:
            # 1. Save to temporary file (never to permanent storage)
            temp_file = self.temp_dir / f"{uuid.uuid4().hex}.{file_format}"
            temp_file.write_bytes(audio_data)
            
            logger.info(
                "voice_processing_started",
                business_id=business_id,
                file_size_kb=len(audio_data) / 1024,
                format=file_format,
            )
            
            # 2. Send to local Whisper model
            transcription = await self._transcribe_local(temp_file)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # 3. Detect Arabic dialect from transcribed text
            dialect = self._detect_dialect(transcription["text"])
            
            result = VoiceTranscription(
                text=transcription["text"],
                language=transcription.get("language", "ar"),
                confidence=transcription.get("confidence", 0.85),
                duration_seconds=transcription.get("duration", 0.0),
                processing_time_ms=processing_time,
                dialect=dialect,
                was_processed_locally=True,
            )
            
            logger.info(
                "voice_processing_completed",
                business_id=business_id,
                language=result.language,
                dialect=result.dialect,
                duration_s=result.duration_seconds,
                processing_ms=result.processing_time_ms,
                text_length=len(result.text),
            )
            
            return result
            
        finally:
            # 4. ALWAYS delete the audio file — no voice data retention
            if temp_file and temp_file.exists():
                temp_file.unlink()
                logger.info("voice_file_deleted", file=str(temp_file))
    
    async def _transcribe_local(self, audio_path: Path) -> Dict:
        """
        Send audio to local Whisper server for transcription.
        
        This uses faster-whisper running as a local service.
        The audio NEVER leaves the server.
        """
        try:
            # Try local Whisper HTTP service first
            with open(audio_path, "rb") as f:
                response = await self.http_client.post(
                    self.whisper_endpoint,
                    files={"audio_file": (audio_path.name, f, "audio/ogg")},
                    data={
                        "task": "transcribe",
                        "language": "ar",        # Optimize for Arabic
                        "output": "json",
                        "word_timestamps": "false",
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", "ar"),
                    "confidence": data.get("confidence", 0.85),
                    "duration": data.get("duration", 0.0),
                }
                
        except httpx.ConnectError:
            logger.warning("local_whisper_unavailable, trying Ollama")
            return await self._transcribe_via_ollama(audio_path)
            
        except Exception as e:
            logger.error("transcription_failed", error=str(e))
            raise RuntimeError(
                f"Voice transcription failed: {str(e)}. "
                f"Ensure local Whisper service is running."
            )
    
    async def _transcribe_via_ollama(self, audio_path: Path) -> Dict:
        """
        Fallback: Use Ollama's whisper model if available.
        Still local — data stays on the server.
        """
        # Ollama doesn't natively support audio yet (as of early 2026)
        # This is a placeholder for when it does, or for a custom setup
        raise RuntimeError(
            "Local Whisper service unavailable. "
            "Voice messages cannot be processed without local STT. "
            "External STT services are blocked for PDPL compliance."
        )
    
    def _detect_dialect(self, arabic_text: str) -> Optional[str]:
        """
        Basic Saudi dialect detection from transcribed text.
        
        This is simplified — a production system would use a 
        fine-tuned classifier. But these keyword patterns catch
        the most common dialect markers.
        """
        if not arabic_text:
            return None
            
        text = arabic_text.lower()
        
        # Najdi (Riyadh, Central) markers
        najdi_markers = [
            "وش", "ليش", "كذا", "ذا", "هالحين", "يبغى",
            "زين", "مو", "كيذا", "ابغى", "وشلون",
        ]
        
        # Hijazi (Jeddah, Makkah, Western) markers  
        hijazi_markers = [
            "كده", "دحين", "لسه", "ايوه", "طيب",
            "يلا", "أيش", "كمان", "برضو",
        ]
        
        # Khaleeji (Eastern Province, shared with Gulf) markers
        khaleeji_markers = [
            "شلونك", "هالشي", "يالله", "شقول",
            "جي", "يعني", "شلون",
        ]
        
        najdi_score = sum(1 for m in najdi_markers if m in text)
        hijazi_score = sum(1 for m in hijazi_markers if m in text)
        khaleeji_score = sum(1 for m in khaleeji_markers if m in text)
        
        max_score = max(najdi_score, hijazi_score, khaleeji_score)
        
        if max_score == 0:
            return "msa"  # Modern Standard Arabic
        elif najdi_score == max_score:
            return "najdi"
        elif hijazi_score == max_score:
            return "hijazi"
        else:
            return "khaleeji"
    
    async def check_voice_consent(
        self,
        db,
        business_id: str,
        customer_id: str,
    ) -> bool:
        """
        Check if customer has consented to voice processing.
        Voice = biometric data = requires SEPARATE explicit consent.
        """
        from app.compliance.consent_manager import (
            consent_manager, ConsentType,
        )
        return await consent_manager.check_consent(
            db, business_id, customer_id, ConsentType.VOICE_PROCESSING,
        )
    
    def get_voice_consent_message(self, language: str = "ar") -> str:
        """Generate the voice processing consent request."""
        if language == "ar":
            return (
                "🎤 لقد أرسلت رسالة صوتية.\n\n"
                "لمعالجة الرسائل الصوتية، نحتاج موافقتك على تحويل "
                "الصوت إلى نص. تتم المعالجة بالكامل داخل المملكة "
                "العربية السعودية ويتم حذف الملف الصوتي فوراً بعد "
                "التحويل.\n\n"
                "لا يتم تخزين أو مشاركة صوتك مع أي جهة خارجية.\n\n"
                "للموافقة أرسل: موافق_صوت\n"
                "لرفض أرسل: رفض_صوت\n"
                "(سنرد على رسائلك النصية فقط في هذه الحالة)"
            )
        else:
            return (
                "🎤 You sent a voice message.\n\n"
                "To process voice messages, we need your consent to "
                "convert audio to text. Processing happens entirely "
                "within Saudi Arabia and the audio file is deleted "
                "immediately after conversion.\n\n"
                "Your voice is never stored or shared with third parties.\n\n"
                "To agree, send: AGREE_VOICE\n"
                "To decline, send: DECLINE_VOICE\n"
                "(We will only respond to your text messages in that case)"
            )

    async def close(self):
        await self.http_client.aclose()


# Singleton
voice_processor = VoiceProcessor()

