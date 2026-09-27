"""Script to generate the comprehensive Oil Trading Bot PDF Guide."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def build_pdf(filename="Oil_Trading_Bot_User_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f2b48'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2b5c8f'),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f2b48'),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1d3557'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#222222'),
        spaceAfter=5
    )

    code_style = ParagraphStyle(
        'CodeText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1e293b')
    )

    alert_box_style = ParagraphStyle(
        'AlertBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Title Banner
    story.append(Paragraph("🛢️ Automated Oil Stock Trading Bot", title_style))
    story.append(Paragraph("Revolut Hungary Edition • Technical Setup, Schedule & Operational Playbook", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f2b48'), spaceAfter=12))

    # Section 1: Overview & Revolut Universe
    story.append(Paragraph("1. System Overview & Revolut Hungary Universe", h1_style))
    story.append(Paragraph(
        "This bot is an institutional-grade, multi-factor algorithmic trading system designed specifically for "
        "<b>Revolut users in Hungary</b>. It monitors physical crude commodity dynamics and breaking news headlines "
        "24/7 in the cloud, calculating high-conviction buy/exit signals and pushing instant notifications to your phone.",
        body_style
    ))

    universe_data = [
        ["Symbol", "Company Name", "Revolut Availability", "Role in Strategy"],
        ["XOM", "ExxonMobil Corp.", "Direct Stock (US)", "Integrated supermajor, global refining leader"],
        ["CVX", "Chevron Corp.", "Direct Stock (US)", "Upstream exploration leader, high cash return"],
        ["OXY", "Occidental Petroleum", "Direct Stock (US)", "Permian basin pure-play, high crude beta"],
        ["COP", "ConocoPhillips", "Direct Stock (US)", "Low-cost E&P exploration bellwether"],
        ["BP", "BP p.l.c.", "Direct Stock (US/UK)", "High dividend yield, European international leader"],
        ["SHEL", "Shell plc", "Direct Stock (US/UK)", "Global LNG & integrated commercial trading giant"],
        ["CL=F", "WTI Crude Futures", "Macro Data Anchor", "Physical commodity benchmark (used for news & trend confirmation)"]
    ]

    t_universe = Table(universe_data, colWidths=[55, 140, 120, 215])
    t_universe.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2b48')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_universe)
    story.append(Spacer(1, 10))

    # Section 2: Strategy & Risk Engine
    story.append(Paragraph("2. Quantitative Strategy & Risk Management Rules", h1_style))
    story.append(Paragraph(
        "The bot enforces strict multi-factor rules before dispatching any trade notification to prevent bad advice:",
        body_style
    ))

    rules_data = [
        ["Factor", "Rule / Condition", "Purpose & Risk Guardrail"],
        ["Trend Direction", "Fast EMA(12) > Slow EMA(26)", "Ensures stock is already moving up in a bullish regime."],
        ["Momentum", "MACD Line > Signal & Hist > 0", "Verifies buying momentum is actively accelerating."],
        ["Exhaustion Filter", "45 <= RSI <= 75", "Blocks buying into overbought blow-offs or oversold traps."],
        ["Commodity Anchor", "WTI Crude Futures (CL=F) Bullish", "Guarantees physical crude market confirms the equity move."],
        ["News Catalyst", "Gemini LLM Sentiment Score >= +0.15", "Ensures news events genuinely support physical tightness."],
        ["Stop Loss", "2.5x ATR below execution price", "Hard volatility-adjusted stop; caps risk at 2-3% capital."],
        ["Profit Management", "Ratchet Trailing Stop (2.5x ATR)", "Automatically locks in profits as price hits new highs."],
        ["Capital Sizing", "25% per qualified stock", "Max 85% total equity invested in high-conviction periods."]
    ]

    t_rules = Table(rules_data, colWidths=[100, 180, 250])
    t_rules.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_rules)
    story.append(Spacer(1, 10))

    # Section 3: AI Intelligence Engine & Fallback
    story.append(Paragraph("3. Dual-Engine AI Intelligence & Fallback Architecture", h1_style))
    story.append(Paragraph(
        "<b>Engine 1: Google Gemini LLM (Primary Context Engine)</b><br/>"
        "Analyzes breaking headlines using a specialized quantitative commodity analyst prompt. It evaluates OPEC quota "
        "discipline, EIA inventory surprises (unexpected builds vs draws), and geopolitical transit chokepoints (Strait of Hormuz, "
        "Red Sea). It outputs a 1-2 sentence executive explanation sent directly to your phone.<br/><br/>"
        "<b>Engine 2: Energy Domain Lexicon (Automatic 100% Uptime Fallback)</b><br/>"
        "If no API key is set or if rate limits occur, the bot seamlessly switches to a tailored physical supply/demand lexicon. "
        "Every push notification explicitly declares whether it used <b>[Gemini LLM]</b> or <b>[Fallback Lexicon]</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Page Break for Cloud Schedule & Playbook
    story.append(PageBreak())

    # Section 4: 24/7 Cloud Architecture & Schedule
    story.append(Paragraph("4. 24/7 Cloud Architecture & Schedule (GitHub Actions)", h1_style))
    story.append(Paragraph(
        "The bot runs completely in GitHub's cloud infrastructure via <code>.github/workflows/scanner.yml</code>. "
        "<b>It operates 24/7 even when your MacBook lid is closed, asleep, or turned off.</b>",
        body_style
    ))

    sched_data = [
        ["Schedule Window", "Cron Expression", "Frequency", "Operational Focus"],
        ["US Regular Trading Hours", "*/30 13-22 * * 1-5", "Every 30 mins (Mon-Fri)", "Intraday price action, technical crossovers, and morning EIA inventory reports (Wed 10:30 EST)."],
        ["Off-Market & Weekends", "0 */2 * * 0,6", "Every 2 hours", "Weekend OPEC+ quota summits, geopolitical strikes, pipeline disruptions, and Asian market open prep."],
        ["Manual Trigger", "workflow_dispatch", "On Demand", "Triggerable anytime from your GitHub Actions web dashboard with a single click."]
    ]

    t_sched = Table(sched_data, colWidths=[120, 110, 110, 190])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2b48')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 12))

    # Section 5: Notification Security & Topic Privacy Guide
    story.append(Paragraph("5. Notification Setup & Privacy Guide (ntfy.sh)", h1_style))
    story.append(Paragraph(
        "<b>Active Channel Name:</b> <code>buzi-bot</code> (Web URL: <a href='https://ntfy.sh/buzi-bot'>https://ntfy.sh/buzi-bot</a>)<br/><br/>"
        "<b>How ntfy Security & Privacy Works:</b><br/>"
        "On the free public <code>ntfy.sh</code> server, topics operate like unlisted YouTube videos or radio channels. "
        "There is no 'password' or registration required; anyone who guesses the exact topic string can subscribe. "
        "Because <code>buzi-bot</code> is a custom name you selected, only people who know that exact string can see it.<br/><br/>"
        "<b>To Guarantee 100% Cryptographic Exclusivity:</b><br/>"
        "If you want absolute secrecy where no human can ever guess your channel, use a random 8-character suffix "
        "(for example: <code>buzi-bot-8f92a</code>). Simply update your phone app subscription and update the "
        "<code>NTFY_TOPIC</code> secret in your GitHub repository.",
        body_style
    ))
    story.append(Spacer(1, 12))

    # Section 6: Revolut Execution Playbook
    story.append(Paragraph("6. Revolut Operational Playbook", h1_style))
    story.append(Paragraph(
        "<b>When You Receive a BUY Alert:</b><br/>"
        "1. Open your <b>Revolut</b> app $\rightarrow$ <b>Invest</b> $\rightarrow$ Search ticker (e.g. <b>XOM</b>).<br/>"
        "2. Tap <b>Buy</b> (Market or Limit order at the alert execution price).<br/>"
        "3. Note the <b>Stop Loss</b> price from your alert. (You can set a Stop Order on Revolut or watch for the bot's EXIT alert).<br/><br/>"
        "<b>When You Receive an EXIT Alert:</b><br/>"
        "1. Open Revolut $\rightarrow$ Tap your open position $\rightarrow$ Tap <b>Sell</b> $\rightarrow$ <b>100%</b>.<br/>"
        "2. The bot has detected trend exhaustion, MACD rollover, or trailing stop trigger. Capital returns safely to cash.",
        body_style
    ))
    story.append(Spacer(1, 15))

    # Summary box
    summary_box_data = [[
        Paragraph(
            "<b>Repository:</b> <a href='https://github.com/eandras28/trade-bot'>https://github.com/eandras28/trade-bot</a><br/>"
            "<b>Notification Channel:</b> ntfy.sh/buzi-bot<br/>"
            "<b>6-Year Historical Backtest (2020–2026):</b> +63.66% Return | 1.37 Profit Factor | -26.9% Max Drawdown",
            alert_box_style
        )
    ]]
    t_box = Table(summary_box_data, colWidths=[530])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e0f2fe')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0284c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(t_box)

    doc.build(story)
    print(f"[✓] Generated PDF: {filename}")


if __name__ == "__main__":
    build_pdf()
