"""ELO rating system and leaderboard queries."""
from db import db
from models import LeaderboardEntry, Game

K_FACTOR = 32  # ELO K-factor


def _expected_score(rating_a, rating_b):
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_ratings(winner_id, loser_id, game_id, draw=False):
    """Update ELO ratings after a game. Creates entries if they don't exist."""
    entry_w = _get_or_create(winner_id, game_id)
    entry_l = _get_or_create(loser_id, game_id)

    expected_w = _expected_score(entry_w.rating, entry_l.rating)
    expected_l = _expected_score(entry_l.rating, entry_w.rating)

    if draw:
        entry_w.draws += 1
        entry_l.draws += 1
        actual_w = 0.5
        actual_l = 0.5
    else:
        entry_w.wins += 1
        entry_l.losses += 1
        actual_w = 1.0
        actual_l = 0.0

    entry_w.rating = max(100, int(entry_w.rating + K_FACTOR * (actual_w - expected_w)))
    entry_l.rating = max(100, int(entry_l.rating + K_FACTOR * (actual_l - expected_l)))
    entry_w.score = entry_w.wins * 3 + entry_w.draws
    entry_l.score = entry_l.wins * 3 + entry_l.draws

    db.session.commit()


def _get_or_create(user_id, game_id):
    entry = LeaderboardEntry.query.filter_by(user_id=user_id, game_id=game_id).first()
    if not entry:
        entry = LeaderboardEntry(user_id=user_id, game_id=game_id)
        db.session.add(entry)
        db.session.flush()
    return entry


def get_leaderboard(game_slug, limit=50):
    """Get per-game leaderboard sorted by rating."""
    game = Game.query.filter_by(slug=game_slug).first()
    if not game:
        return []
    entries = LeaderboardEntry.query.filter_by(game_id=game.id) \
        .order_by(LeaderboardEntry.rating.desc()) \
        .limit(limit).all()
    return [{
        'rank': i + 1,
        'username': e.user.username,
        'user_id': e.user_id,
        'rating': e.rating,
        'wins': e.wins,
        'losses': e.losses,
        'draws': e.draws,
        'total': e.total_games,
        'win_rate': e.win_rate,
    } for i, e in enumerate(entries)]


def get_global_leaderboard(limit=50):
    """Aggregate leaderboard across all games, sorted by total score."""
    from sqlalchemy import func
    results = db.session.query(
        LeaderboardEntry.user_id,
        func.sum(LeaderboardEntry.score).label('total_score'),
        func.sum(LeaderboardEntry.wins).label('total_wins'),
        func.sum(LeaderboardEntry.losses).label('total_losses'),
        func.sum(LeaderboardEntry.draws).label('total_draws'),
        func.avg(LeaderboardEntry.rating).label('avg_rating'),
    ).group_by(LeaderboardEntry.user_id) \
     .order_by(func.sum(LeaderboardEntry.score).desc()) \
     .limit(limit).all()

    from auth import User
    out = []
    for i, r in enumerate(results):
        user = User.query.get(r.user_id)
        out.append({
            'rank': i + 1,
            'username': user.username if user else 'Unknown',
            'user_id': r.user_id,
            'total_score': int(r.total_score or 0),
            'total_wins': int(r.total_wins or 0),
            'total_losses': int(r.total_losses or 0),
            'total_draws': int(r.total_draws or 0),
            'avg_rating': int(r.avg_rating or 1200),
        })
    return out
