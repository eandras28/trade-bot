"""News Scraper and Energy-Domain Sentiment Analyzer for Oil Markets."""
from typing import Dict, List, Any, Optional
import feedparser
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer


# Specialized domain dictionary for oil & commodities
# Positive values indicate upward pressure on crude/oil equities (tight supply, high demand)
# Negative values indicate downward pressure (oversupply, demand destruction)
ENERGY_LEXICON = {
    # Supply contraction & geopolitical disruptions (BULLISH for oil price)
    "production cut": 2.5,
    "output cut": 2.5,
    "quota cut": 2.0,
    "inventory draw": 2.2,
    "stockpile draw": 2.0,
    "drawdown": 1.5,
    "supply disruption": 2.4,
    "pipeline outage": 2.0,
    "refinery outage": 1.8,
    "drone strike": 2.2,
    "tanker seized": 2.0,
    "sanctions": 1.8,
    "embargo": 2.0,
    "tight supply": 2.0,
    "backwardation": 1.5,
    "spr refill": 1.5,
    "record demand": 2.0,
    "strong demand": 1.8,
    "upgrade": 1.5,
    "outperform": 1.5,
    "dividend hike": 1.5,
    "buyback": 1.5,

    # Supply expansion & demand slump (BEARISH for oil price)
    "inventory build": -2.2,
    "stockpile build": -2.2,
    "production increase": -2.2,
    "output hike": -2.2,
    "supply glut": -2.8,
    "oil glut": -2.8,
    "oversupply": -2.5,
    "surplus": -2.0,
    "quota breach": -2.0,
    "cheating on quotas": -2.2,
    "ceasefire": -2.0,
    "peace talks": -1.8,
    "de-escalation": -1.8,
    "demand destruction": -2.5,
    "demand slump": -2.2,
    "recession": -2.2,
    "economic slowdown": -2.0,
    "downgrade": -1.8,
    "contango": -1.5,
    "windfall tax": -1.8,
    "spill": -1.5,
}


class OilSentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        # Update VADER lexicon with energy specific weights
        self.vader.lexicon.update(ENERGY_LEXICON)

    def analyze_text(self, text: str) -> float:
        """Return compound score between -1.0 (bearish) and +1.0 (bullish)."""
        if not text:
            return 0.0
        scores = self.vader.polarity_scores(text)
        return scores['compound']

    def fetch_ticker_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch latest news articles for a specific stock/ETF from yfinance."""
        articles = []
        try:
            ticker = yf.Ticker(symbol)
            items = ticker.news or []
            for item in items[:limit]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title") or ""
                summary = content.get("summary") or item.get("summary") or ""
                pub_date = content.get("pubDate") or item.get("pubDate") or ""
                provider = content.get("provider", {}).get("displayName") or item.get("publisher") or "Yahoo Finance"
                link = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""

                if not title:
                    continue

                full_text = f"{title}. {summary}"
                score = self.analyze_text(full_text)

                articles.append({
                    "title": title,
                    "summary": summary,
                    "score": round(score, 3),
                    "publisher": provider,
                    "pubDate": pub_date,
                    "url": link,
                    "type": f"{symbol} Company/Fund News"
                })
        except Exception as e:
            print(f"Error fetching ticker news for {symbol}: {e}")

        return articles

    def fetch_macro_crude_news(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch macro crude oil, OPEC, and geopolitical news via Google News RSS."""
        articles = []
        try:
            query = "crude+oil+OR+OPEC+OR+petroleum+inventory"
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                published = entry.get("published", "")
                link = entry.get("link", "")
                source = entry.get("source", {}).get("title", "Google News")

                score = self.analyze_text(title)
                articles.append({
                    "title": title,
                    "summary": "",
                    "score": round(score, 3),
                    "publisher": source,
                    "pubDate": published,
                    "url": link,
                    "type": "Macro Crude / OPEC"
                })
        except Exception as e:
            print(f"Error fetching macro news: {e}")

        return articles

    def get_market_sentiment_report(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Aggregate sentiment for macro crude oil plus each individual symbol.
        """
        macro_news = self.fetch_macro_crude_news(limit=15)
        macro_scores = [a["score"] for a in macro_news if a["score"] != 0]
        avg_macro_score = sum(macro_scores) / len(macro_scores) if macro_scores else 0.0

        symbol_reports = {}
        for sym in symbols:
            sym_news = self.fetch_ticker_news(sym, limit=8)
            scores = [a["score"] for a in sym_news if a["score"] != 0]
            avg_sym_score = sum(scores) / len(scores) if scores else 0.0

            # Composite sentiment: 50% ticker specific, 50% macro crude
            composite = 0.5 * avg_sym_score + 0.5 * avg_macro_score

            if composite >= 0.25:
                regime = "🟢 STRONG BULLISH CATALYST"
            elif composite >= 0.08:
                regime = "🌱 MILD BULLISH"
            elif composite <= -0.25:
                regime = "🛑 STRONG BEARISH / SHORT"
            elif composite <= -0.08:
                regime = "🔻 MILD BEARISH"
            else:
                regime = "⚪ NEUTRAL"

            symbol_reports[sym] = {
                "composite_score": round(composite, 3),
                "ticker_score": round(avg_sym_score, 3),
                "macro_score": round(avg_macro_score, 3),
                "sentiment_regime": regime,
                "news_count": len(sym_news),
                "top_articles": sorted(sym_news, key=lambda x: abs(x["score"]), reverse=True)[:3]
            }

        return {
            "macro_score": round(avg_macro_score, 3),
            "macro_news_count": len(macro_news),
            "top_macro_news": sorted(macro_news, key=lambda x: abs(x["score"]), reverse=True)[:5],
            "symbols": symbol_reports
        }
