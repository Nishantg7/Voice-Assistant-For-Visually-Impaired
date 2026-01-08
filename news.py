import feedparser
import requests
from datetime import datetime, timedelta

class NewsService:
    def __init__(self):
        # Popular news RSS feeds
        self.feeds = {
            'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
            'cnn': 'http://rss.cnn.com/rss/edition.rss',
            'reuters': 'https://feeds.reuters.com/reuters/topNews',
            'general': 'https://news.google.com/rss'
        }

    def get_headlines(self, source='bbc', limit=3):
        """Get latest headlines from a news source"""
        try:
            if source not in self.feeds:
                source = 'bbc'  # Default fallback

            feed_url = self.feeds[source]
            feed = feedparser.parse(feed_url)

            if feed.bozo:  # Check for parsing errors
                return f"Sorry, couldn't fetch news from {source}."

            headlines = []
            for entry in feed.entries[:limit]:
                # Clean up the title
                title = entry.title.replace('&', 'and')
                headlines.append(title)

            if not headlines:
                return f"No headlines found from {source}."

            response = f"Here are the latest headlines from {source.upper()}:\n"
            for i, headline in enumerate(headlines, 1):
                response += f"{i}. {headline}\n"

            return response

        except Exception as e:
            return f"Sorry, I couldn't fetch news. Error: {str(e)}"

    def get_news_summary(self, topic='general'):
        """Get a brief news summary"""
        return self.get_headlines(topic, 2)

def get_latest_news(source='bbc'):
    """Simple function to get latest news"""
    news_service = NewsService()
    return news_service.get_headlines(source)

def get_news_headlines():
    """Get general news headlines"""
    news_service = NewsService()
    return news_service.get_headlines('general')

if __name__ == "__main__":
    # Test the news functions
    print(get_latest_news('bbc'))
    print(get_news_headlines())
