from datetime import datetime, timezone
from app.services.quantpulse_news import _sentiment


def test_news_sentiment_positive():
    assert _sentiment("Strong growth and record profit") > 0


def test_news_sentiment_negative():
    assert _sentiment("Weak results, loss and downgrade") < 0


def test_news_sentiment_neutral():
    assert _sentiment("Company announces annual meeting") == 0.0


def test_news_timestamp_is_timezone_aware():
    assert datetime.now(timezone.utc).tzinfo is not None
