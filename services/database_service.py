"""
Database Service Layer for Munch AI Dating Assistant
Provides CRUD operations for User, Conversation, Message, and Analytics models
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.models import (
    User, Conversation, Message, Analytics,
    ConversationStatus, ResponseType, MessageRole
)
from database.database import get_db_session, SessionLocal


class DatabaseService:
    """Service class for all database operations"""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize with optional session.
        If no session provided, creates new session for each operation.
        """
        self._db = db
        self._owns_session = db is None

    def _get_session(self) -> Session:
        """Get the current session or create a new one"""
        if self._db is not None:
            return self._db
        return SessionLocal()

    def _close_session(self, session: Session):
        """Close session if we created it"""
        if self._owns_session and session is not self._db:
            session.close()

    # ===================== USER OPERATIONS =====================

    def create_user(
        self,
        email: str,
        username: Optional[str] = None,
        subscription_tier: str = "free"
    ) -> User:
        """
        Create a new user.

        Args:
            email: User's email (must be unique)
            username: Optional username
            subscription_tier: Subscription level (default: 'free')

        Returns:
            Created User object

        Raises:
            IntegrityError: If email already exists
        """
        session = self._get_session()
        try:
            user = User(
                email=email,
                username=username,
                subscription_tier=subscription_tier
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            raise ValueError(f"User with email '{email}' already exists")
        finally:
            self._close_session(session)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        session = self._get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            self._close_session(session)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        session = self._get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            self._close_session(session)

    def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        subscription_tier: Optional[str] = None
    ) -> Optional[User]:
        """
        Update user fields.

        Args:
            user_id: ID of user to update
            username: New username (if provided)
            subscription_tier: New subscription tier (if provided)

        Returns:
            Updated User object or None if not found
        """
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            if username is not None:
                user.username = username
            if subscription_tier is not None:
                user.subscription_tier = subscription_tier

            session.commit()
            session.refresh(user)
            return user
        finally:
            self._close_session(session)

    def delete_user(self, user_id: int) -> bool:
        """
        Delete user and all associated data (cascades).

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            session.delete(user)
            session.commit()
            return True
        finally:
            self._close_session(session)

    def get_or_create_user(
        self,
        email: str,
        username: Optional[str] = None,
        subscription_tier: str = "free"
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.

        Returns:
            Tuple of (User, created) where created is True if new user
        """
        user = self.get_user_by_email(email)
        if user:
            return user, False

        user = self.create_user(email, username, subscription_tier)
        return user, True

    def create_user_with_password(
        self,
        email: str,
        password_hash: str,
        username: Optional[str] = None,
        subscription_tier: str = "free"
    ) -> User:
        """
        Create a new user with password hash.

        Args:
            email: User's email (must be unique)
            password_hash: Bcrypt hashed password
            username: Optional username
            subscription_tier: Subscription level (default: 'free')

        Returns:
            Created User object

        Raises:
            ValueError: If email already exists
        """
        session = self._get_session()
        try:
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                subscription_tier=subscription_tier
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            raise ValueError(f"User with email '{email}' already exists")
        finally:
            self._close_session(session)

    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """
        Update user's password hash.

        Args:
            user_id: ID of user to update
            password_hash: New bcrypt hashed password

        Returns:
            True if updated, False if user not found
        """
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.password_hash = password_hash
            session.commit()
            return True
        finally:
            self._close_session(session)

    # ===================== CONVERSATION OPERATIONS =====================

    def create_conversation(
        self,
        user_id: int,
        name: str,
        response_type: ResponseType,
        status: ConversationStatus = ConversationStatus.ACTIVE
    ) -> Conversation:
        """
        Create a new conversation for a user.

        Args:
            user_id: ID of the user
            name: Name/label for the conversation
            response_type: Type of response context
            status: Initial status (default: ACTIVE)

        Returns:
            Created Conversation object
        """
        session = self._get_session()
        try:
            conversation = Conversation(
                user_id=user_id,
                name=name,
                response_type=response_type,
                status=status
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation
        finally:
            self._close_session(session)

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        session = self._get_session()
        try:
            return session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
        finally:
            self._close_session(session)

    def get_conversations_by_user(
        self,
        user_id: int,
        status: Optional[ConversationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get conversations for a user.

        Args:
            user_id: ID of the user
            status: Filter by status (optional)
            limit: Maximum number to return
            offset: Number to skip for pagination

        Returns:
            List of Conversation objects
        """
        session = self._get_session()
        try:
            query = session.query(Conversation).filter(
                Conversation.user_id == user_id
            )

            if status:
                query = query.filter(Conversation.status == status)

            return query.order_by(
                Conversation.updated_at.desc()
            ).offset(offset).limit(limit).all()
        finally:
            self._close_session(session)

    def update_conversation(
        self,
        conversation_id: int,
        name: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        chemistry_score: Optional[int] = None,
        success_rate: Optional[float] = None,
        failure_rate: Optional[float] = None
    ) -> Optional[Conversation]:
        """
        Update conversation fields.

        Returns:
            Updated Conversation or None if not found
        """
        session = self._get_session()
        try:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                return None

            if name is not None:
                conversation.name = name
            if status is not None:
                conversation.status = status
            if chemistry_score is not None:
                conversation.chemistry_score = chemistry_score
            if success_rate is not None:
                conversation.success_rate = success_rate
            if failure_rate is not None:
                conversation.failure_rate = failure_rate

            session.commit()
            session.refresh(conversation)
            return conversation
        finally:
            self._close_session(session)

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete conversation and all messages/analytics (cascades).

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                return False

            session.delete(conversation)
            session.commit()
            return True
        finally:
            self._close_session(session)

    # ===================== MESSAGE OPERATIONS =====================

    def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        image_url: Optional[str] = None
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            role: Message role (USER, ASSISTANT, SYSTEM)
            content: Message text content
            image_url: Optional URL to image attachment

        Returns:
            Created Message object
        """
        session = self._get_session()
        try:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                image_url=image_url
            )
            session.add(message)

            # Update conversation message count and last_message_at
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                conversation.total_messages += 1
                conversation.last_message_at = datetime.utcnow()

            session.commit()
            session.refresh(message)
            return message
        finally:
            self._close_session(session)

    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 100,
        offset: int = 0,
        order_desc: bool = False
    ) -> List[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: ID of the conversation
            limit: Maximum messages to return
            offset: Number to skip for pagination
            order_desc: If True, newest first; otherwise oldest first

        Returns:
            List of Message objects
        """
        session = self._get_session()
        try:
            query = session.query(Message).filter(
                Message.conversation_id == conversation_id
            )

            if order_desc:
                query = query.order_by(Message.created_at.desc())
            else:
                query = query.order_by(Message.created_at.asc())

            return query.offset(offset).limit(limit).all()
        finally:
            self._close_session(session)

    def get_last_n_messages(
        self,
        conversation_id: int,
        n: int = 10
    ) -> List[Message]:
        """Get the last N messages in chronological order"""
        session = self._get_session()
        try:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(n).all()

            return list(reversed(messages))
        finally:
            self._close_session(session)

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a single message.

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            message = session.query(Message).filter(
                Message.id == message_id
            ).first()

            if not message:
                return False

            # Update conversation message count
            conversation = session.query(Conversation).filter(
                Conversation.id == message.conversation_id
            ).first()
            if conversation and conversation.total_messages > 0:
                conversation.total_messages -= 1

            session.delete(message)
            session.commit()
            return True
        finally:
            self._close_session(session)

    # ===================== ANALYTICS OPERATIONS =====================

    def save_analytics(
        self,
        conversation_id: int,
        chemistry_score: int,
        success_rate: float,
        failure_rate: float,
        ai_tip: Optional[str] = None
    ) -> Analytics:
        """
        Save analytics snapshot for a conversation.

        Args:
            conversation_id: ID of the conversation
            chemistry_score: Chemistry score (0-100)
            success_rate: Success rate (0-100)
            failure_rate: Failure rate (0-100)
            ai_tip: Optional AI-generated tip

        Returns:
            Created Analytics object
        """
        session = self._get_session()
        try:
            analytics = Analytics(
                conversation_id=conversation_id,
                chemistry_score=chemistry_score,
                success_rate=success_rate,
                failure_rate=failure_rate,
                ai_tip=ai_tip
            )
            session.add(analytics)

            # Also update the conversation's current scores
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                conversation.chemistry_score = chemistry_score
                conversation.success_rate = success_rate
                conversation.failure_rate = failure_rate

            session.commit()
            session.refresh(analytics)
            return analytics
        finally:
            self._close_session(session)

    def get_latest_analytics(
        self,
        conversation_id: int
    ) -> Optional[Analytics]:
        """Get the most recent analytics for a conversation"""
        session = self._get_session()
        try:
            return session.query(Analytics).filter(
                Analytics.conversation_id == conversation_id
            ).order_by(Analytics.analyzed_at.desc()).first()
        finally:
            self._close_session(session)

    def get_analytics_history(
        self,
        conversation_id: int,
        limit: int = 20
    ) -> List[Analytics]:
        """Get analytics history for a conversation"""
        session = self._get_session()
        try:
            return session.query(Analytics).filter(
                Analytics.conversation_id == conversation_id
            ).order_by(Analytics.analyzed_at.desc()).limit(limit).all()
        finally:
            self._close_session(session)

    # ===================== AGGREGATE QUERIES =====================

    def get_user_stats(self, user_id: int) -> dict:
        """
        Get aggregate statistics for a user.

        Returns:
            Dict with total_conversations, active, stalled, ghosted, success counts
        """
        session = self._get_session()
        try:
            conversations = session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).all()

            stats = {
                "total_conversations": len(conversations),
                "active": 0,
                "stalled": 0,
                "ghosted": 0,
                "success": 0,
                "total_messages": 0,
                "avg_chemistry_score": 0
            }

            total_chemistry = 0
            for conv in conversations:
                stats["total_messages"] += conv.total_messages
                total_chemistry += conv.chemistry_score

                if conv.status == ConversationStatus.ACTIVE:
                    stats["active"] += 1
                elif conv.status == ConversationStatus.STALLED:
                    stats["stalled"] += 1
                elif conv.status == ConversationStatus.GHOSTED:
                    stats["ghosted"] += 1
                elif conv.status == ConversationStatus.SUCCESS:
                    stats["success"] += 1

            if stats["total_conversations"] > 0:
                stats["avg_chemistry_score"] = round(
                    total_chemistry / stats["total_conversations"], 1
                )

            return stats
        finally:
            self._close_session(session)

    def get_conversation_with_messages(
        self,
        conversation_id: int
    ) -> Optional[dict]:
        """
        Get conversation with all its messages.

        Returns:
            Dict with conversation and messages, or None if not found
        """
        session = self._get_session()
        try:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

            if not conversation:
                return None

            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()

            return {
                "conversation": conversation,
                "messages": messages
            }
        finally:
            self._close_session(session)

    # ===================== ANALYTICS TRENDS =====================

    def get_analytics_trends(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = "daily"
    ) -> dict:
        """
        Get aggregated analytics trends for a user over time.

        Args:
            user_id: ID of the user
            start_date: Start of date range (default: 30 days ago)
            end_date: End of date range (default: now)
            granularity: "daily" or "weekly"

        Returns:
            Dict with trend data including dates and aggregated scores
        """
        from sqlalchemy import func, cast, Date
        from datetime import timedelta

        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        session = self._get_session()
        try:
            # Get all conversations for user
            conv_ids = session.query(Conversation.id).filter(
                Conversation.user_id == user_id
            ).all()
            conv_ids = [c[0] for c in conv_ids]

            if not conv_ids:
                return {
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "granularity": granularity,
                    "data_points": [],
                    "summary": {
                        "avg_chemistry": 0,
                        "avg_success_rate": 0,
                        "total_analyses": 0,
                        "trend_direction": "neutral"
                    }
                }

            # Get analytics in date range
            analytics = session.query(Analytics).filter(
                Analytics.conversation_id.in_(conv_ids),
                Analytics.analyzed_at >= start_date,
                Analytics.analyzed_at <= end_date
            ).order_by(Analytics.analyzed_at.asc()).all()

            if not analytics:
                return {
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "granularity": granularity,
                    "data_points": [],
                    "summary": {
                        "avg_chemistry": 0,
                        "avg_success_rate": 0,
                        "total_analyses": 0,
                        "trend_direction": "neutral"
                    }
                }

            # Group by date
            from collections import defaultdict
            grouped = defaultdict(list)

            for a in analytics:
                if granularity == "weekly":
                    # Group by week start (Monday)
                    week_start = a.analyzed_at - timedelta(days=a.analyzed_at.weekday())
                    key = week_start.date().isoformat()
                else:
                    key = a.analyzed_at.date().isoformat()
                grouped[key].append(a)

            # Calculate aggregates per period
            data_points = []
            for date_key in sorted(grouped.keys()):
                items = grouped[date_key]
                data_points.append({
                    "date": date_key,
                    "avg_chemistry_score": round(sum(a.chemistry_score for a in items) / len(items), 1),
                    "avg_success_rate": round(sum(a.success_rate for a in items) / len(items), 1),
                    "avg_failure_rate": round(sum(a.failure_rate for a in items) / len(items), 1),
                    "analysis_count": len(items)
                })

            # Calculate overall summary
            all_chemistry = [a.chemistry_score for a in analytics]
            all_success = [a.success_rate for a in analytics]

            # Determine trend direction
            trend = "neutral"
            if len(data_points) >= 2:
                first_half = data_points[:len(data_points)//2]
                second_half = data_points[len(data_points)//2:]
                first_avg = sum(p["avg_chemistry_score"] for p in first_half) / len(first_half)
                second_avg = sum(p["avg_chemistry_score"] for p in second_half) / len(second_half)
                if second_avg > first_avg + 5:
                    trend = "improving"
                elif second_avg < first_avg - 5:
                    trend = "declining"

            return {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": granularity,
                "data_points": data_points,
                "summary": {
                    "avg_chemistry": round(sum(all_chemistry) / len(all_chemistry), 1),
                    "avg_success_rate": round(sum(all_success) / len(all_success), 1),
                    "total_analyses": len(analytics),
                    "trend_direction": trend
                }
            }
        finally:
            self._close_session(session)

    def get_conversation_progression(
        self,
        conversation_id: int
    ) -> dict:
        """
        Get chemistry score progression for a single conversation.

        Returns:
            Dict with timestamps and scores showing progression
        """
        session = self._get_session()
        try:
            analytics = session.query(Analytics).filter(
                Analytics.conversation_id == conversation_id
            ).order_by(Analytics.analyzed_at.asc()).all()

            if not analytics:
                return {
                    "conversation_id": conversation_id,
                    "data_points": [],
                    "summary": {
                        "start_score": 0,
                        "end_score": 0,
                        "peak_score": 0,
                        "total_change": 0
                    }
                }

            data_points = [
                {
                    "timestamp": a.analyzed_at.isoformat(),
                    "chemistry_score": a.chemistry_score,
                    "success_rate": a.success_rate,
                    "failure_rate": a.failure_rate,
                    "ai_tip": a.ai_tip
                }
                for a in analytics
            ]

            scores = [a.chemistry_score for a in analytics]
            return {
                "conversation_id": conversation_id,
                "data_points": data_points,
                "summary": {
                    "start_score": scores[0],
                    "end_score": scores[-1],
                    "peak_score": max(scores),
                    "low_score": min(scores),
                    "total_change": scores[-1] - scores[0],
                    "analysis_count": len(analytics)
                }
            }
        finally:
            self._close_session(session)


# Singleton instance for convenience
_service_instance: Optional[DatabaseService] = None


def get_database_service(db: Optional[Session] = None) -> DatabaseService:
    """
    Get a DatabaseService instance.

    Args:
        db: Optional session to use. If None, uses singleton.

    Returns:
        DatabaseService instance
    """
    global _service_instance

    if db is not None:
        return DatabaseService(db)

    if _service_instance is None:
        _service_instance = DatabaseService()

    return _service_instance
