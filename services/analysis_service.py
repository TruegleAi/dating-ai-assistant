"""
AI Analysis Service for Munch AI Dating Assistant
Provides advanced conversation analysis, chemistry scoring, and AI-powered tips
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import re
import requests

from database.models import Message, MessageRole, ConversationStatus, ResponseType


class AnalysisService:
    """Advanced AI analysis for dating conversations"""

    def __init__(
        self,
        ollama_model: str,
        api_key: str = "",
        base_url: str = "http://localhost:11434",
        fallback_models: List[str] = None
    ):
        self.primary_model = ollama_model
        self.active_model = ollama_model
        self.api_key = api_key
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        self.fallback_models = fallback_models or []

        # Scoring weights
        self.weights = {
            "message_length": 0.15,
            "question_asking": 0.20,
            "emoji_usage": 0.10,
            "response_enthusiasm": 0.15,
            "engagement_signals": 0.20,
            "reciprocity": 0.20
        }

        # Positive signals
        self.positive_signals = [
            "haha", "lol", "lmao", "hehe", "omg", "wow", "amazing", "love",
            "cute", "funny", "sweet", "adorable", "definitely", "absolutely",
            "yes!", "can't wait", "excited", "miss you", "thinking of you"
        ]

        # Negative signals
        self.negative_signals = [
            "k", "ok", "sure", "whatever", "idk", "maybe", "busy",
            "we'll see", "i guess", "fine", "mhm", "yea"
        ]

        # Meetup indicators
        self.meetup_indicators = [
            "meet", "date", "coffee", "drinks", "dinner", "hang out",
            "get together", "see you", "this weekend", "tomorrow",
            "free on", "available", "let's go", "pick you up"
        ]

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call local Ollama API with fallback support"""
        payload = {
            "model": self.active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.7}
        }

        # Try active model first, then fallbacks
        models_to_try = [self.active_model] + [m for m in self.fallback_models if m != self.active_model]

        for model in models_to_try:
            try:
                payload["model"] = model
                response = requests.post(self.api_url, json=payload, timeout=60)
                response.raise_for_status()

                # Update active model if fallback succeeded
                if model != self.active_model:
                    self.active_model = model

                return response.json()['message']['content']
            except Exception:
                continue

        return "Analysis unavailable: Could not connect to Ollama. Please ensure Ollama is running."

    def analyze_conversation(
        self,
        messages: List[Message],
        response_type: ResponseType
    ) -> Dict[str, Any]:
        """
        Comprehensive conversation analysis.

        Returns:
            Dict with chemistry_score, success_rate, failure_rate, status, ai_tip
        """
        if not messages:
            return {
                "chemistry_score": 50,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "status": ConversationStatus.ACTIVE,
                "ai_tip": "Start the conversation to get analysis!",
                "interest_level": "neutral",
                "signals": []
            }

        # Calculate component scores
        length_score = self._analyze_message_lengths(messages)
        question_score = self._analyze_questions(messages)
        emoji_score = self._analyze_emojis(messages)
        enthusiasm_score = self._analyze_enthusiasm(messages)
        engagement_score = self._analyze_engagement(messages)
        reciprocity_score = self._analyze_reciprocity(messages)

        # Weighted chemistry score
        chemistry_score = int(
            length_score * self.weights["message_length"] +
            question_score * self.weights["question_asking"] +
            emoji_score * self.weights["emoji_usage"] +
            enthusiasm_score * self.weights["response_enthusiasm"] +
            engagement_score * self.weights["engagement_signals"] +
            reciprocity_score * self.weights["reciprocity"]
        )

        # Clamp to 0-100
        chemistry_score = max(0, min(100, chemistry_score))

        # Calculate rates
        success_rate = self._calculate_success_rate(chemistry_score, messages)
        failure_rate = self._calculate_failure_rate(chemistry_score, messages)

        # Determine status
        status = self._determine_status(chemistry_score, messages)

        # Detect signals
        signals = self._detect_signals(messages)

        # Generate AI tip based on context
        ai_tip = self._generate_contextual_tip(
            messages, chemistry_score, response_type, signals
        )

        # Interest level
        if chemistry_score >= 75:
            interest_level = "high"
        elif chemistry_score >= 50:
            interest_level = "medium"
        elif chemistry_score >= 30:
            interest_level = "low"
        else:
            interest_level = "very_low"

        return {
            "chemistry_score": chemistry_score,
            "success_rate": round(success_rate, 1),
            "failure_rate": round(failure_rate, 1),
            "status": status,
            "interest_level": interest_level,
            "ai_tip": ai_tip,
            "signals": signals,
            "component_scores": {
                "message_length": length_score,
                "questions": question_score,
                "emojis": emoji_score,
                "enthusiasm": enthusiasm_score,
                "engagement": engagement_score,
                "reciprocity": reciprocity_score
            }
        }

    def _analyze_message_lengths(self, messages: List[Message]) -> int:
        """Analyze message length patterns (longer = more interested)"""
        her_messages = [m for m in messages if m.role == MessageRole.USER]
        if not her_messages:
            return 50

        avg_length = sum(len(m.content) for m in her_messages) / len(her_messages)

        if avg_length > 100:
            return 95
        elif avg_length > 50:
            return 80
        elif avg_length > 25:
            return 60
        elif avg_length > 10:
            return 40
        else:
            return 20

    def _analyze_questions(self, messages: List[Message]) -> int:
        """Analyze question-asking (asking questions = curious/interested)"""
        her_messages = [m for m in messages if m.role == MessageRole.USER]
        if not her_messages:
            return 50

        question_count = sum(1 for m in her_messages if '?' in m.content)
        question_ratio = question_count / len(her_messages)

        if question_ratio > 0.5:
            return 95
        elif question_ratio > 0.3:
            return 80
        elif question_ratio > 0.15:
            return 60
        else:
            return 40

    def _analyze_emojis(self, messages: List[Message]) -> int:
        """Analyze emoji usage (positive emojis = warmth)"""
        her_messages = [m for m in messages if m.role == MessageRole.USER]
        if not her_messages:
            return 50

        positive_emojis = ['😊', '😂', '🥰', '😍', '💕', '❤️', '😘', '🥺', '✨', '💖', '😁', '🙈']
        neutral_emojis = ['😅', '🙂', '👍', '👌', '😌']

        positive_count = 0
        neutral_count = 0

        for m in her_messages:
            for e in positive_emojis:
                positive_count += m.content.count(e)
            for e in neutral_emojis:
                neutral_count += m.content.count(e)

        total = positive_count + neutral_count
        if total == 0:
            return 50

        positivity_ratio = positive_count / total if total > 0 else 0

        if positive_count >= 5 and positivity_ratio > 0.7:
            return 95
        elif positive_count >= 3:
            return 80
        elif positive_count >= 1:
            return 65
        else:
            return 45

    def _analyze_enthusiasm(self, messages: List[Message]) -> int:
        """Analyze enthusiasm markers"""
        her_messages = [m for m in messages if m.role == MessageRole.USER]
        if not her_messages:
            return 50

        enthusiasm_count = 0
        for m in her_messages:
            text = m.content.lower()
            # Exclamation marks
            enthusiasm_count += text.count('!')
            # Positive words
            for signal in self.positive_signals:
                if signal in text:
                    enthusiasm_count += 2
            # Negative signals subtract
            for signal in self.negative_signals:
                if text.strip() == signal or text.startswith(signal + ' '):
                    enthusiasm_count -= 3

        avg_enthusiasm = enthusiasm_count / len(her_messages)

        if avg_enthusiasm > 3:
            return 95
        elif avg_enthusiasm > 1.5:
            return 75
        elif avg_enthusiasm > 0.5:
            return 55
        elif avg_enthusiasm > 0:
            return 40
        else:
            return 25

    def _analyze_engagement(self, messages: List[Message]) -> int:
        """Analyze engagement patterns"""
        her_messages = [m for m in messages if m.role == MessageRole.USER]
        if not her_messages:
            return 50

        engagement_score = 50

        for m in her_messages:
            text = m.content.lower()

            # Topic continuation
            if any(word in text for word in ['tell me more', 'what about', 'and you', 'how about']):
                engagement_score += 10

            # Personal sharing
            if any(word in text for word in ['i love', 'i really', 'my favorite', 'i always']):
                engagement_score += 8

            # Future references
            if any(word in text for word in ['we should', 'we could', 'next time', 'sometime']):
                engagement_score += 12

            # Meetup indicators
            for indicator in self.meetup_indicators:
                if indicator in text:
                    engagement_score += 15
                    break

        return min(100, engagement_score)

    def _analyze_reciprocity(self, messages: List[Message]) -> int:
        """Analyze conversation balance"""
        her_messages = len([m for m in messages if m.role == MessageRole.USER])
        his_messages = len([m for m in messages if m.role == MessageRole.ASSISTANT])

        if his_messages == 0:
            return 50

        ratio = her_messages / his_messages

        if 0.8 <= ratio <= 1.2:
            return 90  # Balanced
        elif 0.6 <= ratio <= 1.5:
            return 70  # Slightly unbalanced
        elif ratio > 1.5:
            return 85  # She's messaging more
        else:
            return 40  # He's chasing

    def _calculate_success_rate(self, chemistry: int, messages: List[Message]) -> float:
        """Calculate success probability"""
        base_rate = chemistry * 0.8

        # Bonus for meetup mentions
        for m in messages:
            if any(ind in m.content.lower() for ind in self.meetup_indicators):
                base_rate += 10
                break

        return min(100, base_rate)

    def _calculate_failure_rate(self, chemistry: int, messages: List[Message]) -> float:
        """Calculate failure/ghosting probability"""
        if chemistry >= 70:
            return max(0, 20 - (chemistry - 70))
        elif chemistry >= 50:
            return 30
        elif chemistry >= 30:
            return 50
        else:
            return 70

    def _determine_status(
        self,
        chemistry: int,
        messages: List[Message]
    ) -> ConversationStatus:
        """Determine conversation status"""
        # Check for meetup planning
        has_meetup = any(
            any(ind in m.content.lower() for ind in self.meetup_indicators)
            for m in messages
        )

        if chemistry >= 75 and has_meetup:
            return ConversationStatus.SUCCESS
        elif chemistry >= 50:
            return ConversationStatus.ACTIVE
        elif chemistry >= 30:
            return ConversationStatus.STALLED
        else:
            return ConversationStatus.GHOSTED

    def _detect_signals(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Detect positive and negative signals"""
        signals = []

        for m in messages[-5:]:  # Last 5 messages
            if m.role != MessageRole.USER:
                continue

            text = m.content.lower()

            # Positive signals
            for signal in self.positive_signals:
                if signal in text:
                    signals.append({
                        "type": "positive",
                        "signal": signal,
                        "message_preview": m.content[:50]
                    })
                    break

            # Negative signals
            for signal in self.negative_signals:
                if text.strip() == signal or text.startswith(signal + ' '):
                    signals.append({
                        "type": "negative",
                        "signal": signal,
                        "message_preview": m.content[:50]
                    })
                    break

            # Meetup signals
            for indicator in self.meetup_indicators:
                if indicator in text:
                    signals.append({
                        "type": "meetup",
                        "signal": indicator,
                        "message_preview": m.content[:50]
                    })
                    break

        return signals

    def _generate_contextual_tip(
        self,
        messages: List[Message],
        chemistry: int,
        response_type: ResponseType,
        signals: List[Dict]
    ) -> str:
        """Generate context-aware tip"""
        # Context-specific tips - direct and commanding
        context_tips = {
            ResponseType.DATING_APP: {
                "high": "Close now. 'Drinks Thursday 8pm' - get her number and get off the app.",
                "medium": "Don't interview her. Make a statement. Tease. Create tension.",
                "low": "She's not interested. Send one more low-investment message or unmatch."
            },
            ResponseType.TEXT: {
                "high": "Close it. '[Day] at [time], [place].' Lead with specifics, not questions.",
                "medium": "Less is more. Short reply. Make her invest more.",
                "low": "Radio silence. Wait 48+ hours minimum. Don't chase."
            },
            ResponseType.DMS: {
                "high": "Get her number or set the date now. '[Day] [time] [place]' - lead it.",
                "medium": "Reply to her story with something specific. No generic fire emojis.",
                "low": "Stop DMing. Post better content. Let her come to you."
            },
            ResponseType.COLD_APPROACH: {
                "high": "Strike now. 'Let's grab drinks Thursday 7pm' - propose, don't ask.",
                "medium": "One callback to when you met, then push for plans.",
                "low": "She gave her number to get rid of you. One text, then delete if no response."
            },
            ResponseType.LIVE_DATING: {
                "high": "Lead. Change venues. Escalate kino. Go for the kiss.",
                "medium": "Create an emotional spike. Tell a story. Use push-pull.",
                "low": "Change the energy. Move locations or end it early on a high."
            },
            ResponseType.OPENERS: {
                "high": "Good hook. Now make her qualify herself to you.",
                "medium": "Opener landed. Don't ruin it with interview questions.",
                "low": "Weak opener. Be more specific or more bold next time."
            },
            ResponseType.PRACTICE: {
                "high": "Solid. Keep this frame in real conversations.",
                "medium": "Getting there. Work on being less reactive.",
                "low": "Too try-hard or too passive. Find the balance."
            }
        }

        # Determine interest level
        if chemistry >= 70:
            level = "high"
        elif chemistry >= 45:
            level = "medium"
        else:
            level = "low"

        base_tip = context_tips.get(response_type, context_tips[ResponseType.TEXT]).get(level, "")

        # Add signal-specific advice
        has_meetup_signal = any(s["type"] == "meetup" for s in signals)
        has_negative_signal = any(s["type"] == "negative" for s in signals)

        if has_meetup_signal and chemistry >= 60:
            base_tip += " She mentioned meeting. Close it NOW - propose the exact time and place, don't ask."
        elif has_negative_signal:
            base_tip += " Low effort from her. Match her energy or go lower."

        return base_tip

    def generate_ai_response_suggestion(
        self,
        messages: List[Message],
        response_type: ResponseType,
        chemistry_score: int
    ) -> str:
        """Generate AI-powered response suggestion"""
        # Build conversation context
        context_lines = []
        for m in messages[-8:]:
            role = "Her" if m.role == MessageRole.USER else "You"
            context_lines.append(f"{role}: {m.content}")

        context = "\n".join(context_lines)

        # Core style rules applied to all responses
        style_rules = """
YOUR VIBE:
- MATCH THE ENERGY. If it's playful banter, stay playful. If it's flirty, be flirty.
- Confident but not try-hard. You're fun to talk to.
- Mysterious - don't over-explain, leave some intrigue.
- Playful teasing > serious conversation. Keep it light.
- Humor is your weapon. Make her laugh, make her wonder.
- Lead with charm, not force. You're the prize but you're not a dick about it.

WHEN TO BE DIRECT:
- She's clearly into it and giving green lights = strike, set the plan
- Logistics are being discussed = be clear and decisive
- She asks a direct question = answer confidently

CLOSING THE DEAL - CRITICAL:
- NEVER ask questions about time, place, or logistics. YOU decide. YOU propose.
- WRONG: "What time works?" / "When should I come?" / "What's a good time?"
- WRONG: "8-ish?" / "Around 8?" / "Does 8 work?"
- RIGHT: "I'll be there at 8." / "See you at 8." / "Coming over at 8. Sound good?"
- The ONLY acceptable question is "Sound good?" AFTER stating the complete plan.
- Lead. Decide. State it as fact. She'll adjust if needed.

WHEN TO BE PLAYFUL:
- Banter is flowing = keep the fun going, riff on what she said
- She's teasing you = tease back, escalate slightly
- Inside jokes developing = build on them

AVOID:
- Killing the vibe with overly serious responses
- Being robotic when she's being fun
- Over-explaining jokes or being try-hard
- Generic responses that could be sent to anyone
- ANY questions about time/logistics when closing ("What time?" "When?" "Does X work?")"""

        # Build system prompt based on context type
        system_prompts = {
            ResponseType.DATING_APP: f"""You write dating app replies that spark attraction and keep her engaged.
{style_rules}
Dating apps = stand out from boring guys. Be the fun option.""",

            ResponseType.TEXT: f"""You write texts that keep the spark alive and move things forward.
{style_rules}
Texting = maintain attraction between seeing each other. Don't be her pen pal.""",

            ResponseType.DMS: f"""You write DMs that are intriguing and different.
{style_rules}
DMs = you're competing with 50 other guys. Be memorable.""",

            ResponseType.COLD_APPROACH: f"""You write follow-ups that build on real-life chemistry.
{style_rules}
Cold approach follow-up = reference the vibe you had, keep it going.""",

            ResponseType.LIVE_DATING: f"""You give advice for in-person dates.
{style_rules}
Live dating = be present, lead, create moments.""",

            ResponseType.OPENERS: f"""You write openers that demand a response.
{style_rules}
Openers = pattern interrupt, make her curious.""",

            ResponseType.PRACTICE: f"""You help practice conversational game.
{style_rules}
Give feedback on what's working and what's not."""
        }

        system_prompt = system_prompts.get(response_type, system_prompts[ResponseType.TEXT])

        # Adjust based on chemistry
        if chemistry_score >= 70:
            system_prompt += "\n\nVIBE CHECK: HIGH chemistry. She's into it. When closing, STATE the plan as fact: 'I'll be there at 8' or 'See you at 8. Sound good?' NEVER ask what time or when - YOU decide. Only question allowed: 'Sound good?' after the plan."
        elif chemistry_score >= 45:
            system_prompt += "\n\nVIBE CHECK: Building chemistry. Keep the playful push-pull going. Make her laugh, make her curious."
        else:
            system_prompt += "\n\nVIBE CHECK: Chemistry is low. Either spark something interesting or gracefully pull back."

        user_prompt = f"""Conversation:
{context}

Read the vibe. Write a reply that fits the flow of THIS conversation.
CLOSING RULE: If setting up a meet, STATE the time/place as fact - NEVER ask "what time?" or "when?" The only allowed question is "Sound good?" after the full plan.
Just the message, nothing else."""

        return self._call_ollama(system_prompt, user_prompt)


def get_analysis_service(
    ollama_model: str,
    api_key: str = "",
    base_url: str = "http://localhost:11434",
    fallback_models: List[str] = None
) -> AnalysisService:
    """Factory function to create AnalysisService"""
    return AnalysisService(
        ollama_model=ollama_model,
        api_key=api_key,
        base_url=base_url,
        fallback_models=fallback_models
    )
