"""
tests/test_feed.py — Mixtape

Tests for the "Friends Listening Now" feed logic.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app import create_app, db
from models import User, Song, ListeningEvent
from services.feed_service import get_friends_listening_now


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def seed_friends(app):
    """Create a user with one friend, and a song the friend can listen to."""
    with app.app_context():
        user = User(username="me", email="me@example.com")
        friend = User(username="friend", email="friend@example.com")
        db.session.add_all([user, friend])
        db.session.flush()

        user.friends.append(friend)

        song = Song(title="Test Track", artist="Various", shared_by=user.id)
        db.session.add(song)
        db.session.commit()

        yield {"user": user, "friend": friend, "song": song}


def test_friend_listening_yesterday_not_shown_today(app, seed_friends):
    """
    A friend's listen from yesterday should not appear in
    "Friends Listening Now" once it's a new calendar day, even if
    it's still within the last 24 real-time hours.

    Note: this test only exercises the bug when run early enough in the
    day that "1 hour after yesterday's midnight" is still in the past.
    """
    with app.app_context():
        user_id = seed_friends["user"].id
        friend_id = seed_friends["friend"].id
        song_id = seed_friends["song"].id

        now = datetime.now(timezone.utc)
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Listened 1 hour before today started (i.e. yesterday, but < 24h ago)
        listened_at = today_midnight - timedelta(hours=1)
        event = ListeningEvent(user_id=friend_id, song_id=song_id, listened_at=listened_at)
        db.session.add(event)
        db.session.commit()

        results = get_friends_listening_now(user_id)

        assert results == []  # Bug: rolling 24h window still includes yesterday's listen


def test_friend_listening_earlier_today_is_shown(app, seed_friends):
    """A friend's listen from earlier today should appear."""
    with app.app_context():
        user_id = seed_friends["user"].id
        friend_id = seed_friends["friend"].id
        song_id = seed_friends["song"].id

        now = datetime.now(timezone.utc)
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Listened 1 minute after today started
        listened_at = today_midnight + timedelta(minutes=1)
        event = ListeningEvent(user_id=friend_id, song_id=song_id, listened_at=listened_at)
        db.session.add(event)
        db.session.commit()

        results = get_friends_listening_now(user_id)

        assert len(results) == 1
        assert results[0]["friend"]["id"] == friend_id
