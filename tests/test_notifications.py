"""
tests/test_notifications.py - Mixtape

Tests for user's notification
"""

import pytest
from app import create_app, db
from models import User, Song, Playlist
from services.notification_service import rate_song, add_to_playlist, get_notifications


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def seed_song(app):
    """Create a sharer who owns a song, and a separate rater."""
    with app.app_context():
        sharer = User(username="sharer", email="sharer@example.com")
        rater = User(username="rater", email="rater@example.com")
        db.session.add_all([sharer, rater])
        db.session.flush()

        song = Song(title="Test Track", artist="Various", shared_by=sharer.id)
        db.session.add(song)
        db.session.flush()

        playlist = Playlist(name="Test Playlist", created_by=rater.id)
        db.session.add(playlist)
        db.session.commit()

        yield {"sharer": sharer, "rater": rater, "song": song, "playlist": playlist}


def test_adding_song_to_playlist_notifies_the_sharer(app, seed_song):
    """
    Control case: adding someone else's song to a playlist should
    notify the original sharer.

    Note: this currently fails for an unrelated reason — add_to_playlist()
    appends to playlist.songs directly, which never sets the required
    playlist_entries.position column, causing a NOT NULL IntegrityError
    before the notification logic is even reached. Separate bug from #4.
    """
    with app.app_context():
        sharer_id = seed_song["sharer"].id
        rater_id = seed_song["rater"].id
        song_id = seed_song["song"].id
        playlist_id = seed_song["playlist"].id

        notifications_before = get_notifications(sharer_id)
        assert notifications_before == []

        add_to_playlist(playlist_id, song_id, rater_id)

        notifications_after = get_notifications(sharer_id)
        assert len(notifications_after) == 1
        

def test_rating_a_song_notifies_the_sharer(app, seed_song):
    """
    Rating someone else's song should notify the original sharer,
    the same way adding their song to a playlist does.
    """
    with app.app_context():
        sharer_id = seed_song["sharer"].id
        rater_id = seed_song["rater"].id
        song_id = seed_song["song"].id

        notifications_before = get_notifications(sharer_id)
        assert notifications_before == []

        rate_song(rater_id, song_id, 5)

        notifications_after = get_notifications(sharer_id)
        assert len(notifications_after) == 1  # Bug: rate_song never notifies the sharer

