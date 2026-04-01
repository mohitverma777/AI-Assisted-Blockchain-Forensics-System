"""
Report Generator - Module G
Generates HTML forensic analysis reports suitable for PDF export.

Authors: Shubham (Primary), Shreya (Backup)
"""

from datetime import datetime
from typing import Dict, List, Optional
import html


class ReportGenerator:
    """Generate HTML-based forensic analysis reports."""

    def generate_report(
        self,
        address: str,
        blockchain: str,
        risk_data: Dict,
        wallet_stats: Dict,
        transactions: List[Dict],
        ai_explanation: Dict,
        cluster_info: Optional[Dict] = None
    ) -> str:
        """
        Generate a complete HTML forensic report.
        
        Returns: HTML string
        """
        risk_score = risk_data.get('overall_risk', 0)
        risk_band = risk_data.get('risk_band', 'UNKNOWN')
        factor_breakdown = risk_data.get('factor_breakdown', {})
        
        risk_color = self._get_risk_color(risk_band)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forensic Report — {html.escape(address[:12])}...</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f1419; color: #e7e9ea; line-height: 1.6;
            padding: 40px; max-width: 900px; margin: 0 auto;
        }}
        .header {{
            text-align: center; padding: 30px;
            background: linear-gradient(135deg, #1a1f2e, #0d1117);
            border: 1px solid #30363d; border-radius: 16px; margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 24px; color: #58a6ff; margin-bottom: 8px; }}
        .header .subtitle {{ color: #8b949e; font-size: 14px; }}
        .address {{ 
            font-family: 'Courier New', monospace; font-size: 13px;
            background: #161b22; padding: 8px 16px; border-radius: 8px;
            display: inline-block; margin-top: 12px; color: #79c0ff;
            word-break: break-all;
        }}
        .risk-gauge {{
            text-align: center; padding: 30px;
            background: linear-gradient(135deg, #1a1f2e, #0d1117);
            border: 1px solid #30363d; border-radius: 16px; margin-bottom: 30px;
        }}
        .risk-score {{
            font-size: 64px; font-weight: 800; color: {risk_color};
            text-shadow: 0 0 20px {risk_color}40;
        }}
        .risk-band {{
            font-size: 18px; font-weight: 600; color: {risk_color};
            text-transform: uppercase; letter-spacing: 2px; margin-top: 8px;
        }}
        .section {{
            background: #161b22; border: 1px solid #30363d;
            border-radius: 16px; padding: 24px; margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 18px; color: #58a6ff; margin-bottom: 16px;
            padding-bottom: 8px; border-bottom: 1px solid #30363d;
        }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
        }}
        .stat-card {{
            background: #0d1117; border: 1px solid #30363d;
            border-radius: 12px; padding: 16px; text-align: center;
        }}
        .stat-value {{ font-size: 24px; font-weight: 700; color: #f0f6fc; }}
        .stat-label {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
        .factor {{
            display: flex; align-items: center; gap: 16px;
            padding: 12px; background: #0d1117; border-radius: 10px;
            margin-bottom: 10px; border-left: 4px solid #30363d;
        }}
        .factor.high {{ border-left-color: #f85149; }}
        .factor.medium {{ border-left-color: #d29922; }}
        .factor.low {{ border-left-color: #3fb950; }}
        .factor-score {{ 
            min-width: 45px; text-align: center; font-weight: 700;
            font-size: 16px;
        }}
        .factor-name {{ font-weight: 600; font-size: 14px; }}
        .factor-desc {{ font-size: 12px; color: #8b949e; margin-top: 2px; }}
        .bar-bg {{ 
            flex: 1; height: 8px; background: #21262d; border-radius: 4px;
            overflow: hidden;
        }}
        .bar-fill {{ height: 100%; border-radius: 4px; }}
        .bar-fill.high {{ background: #f85149; }}
        .bar-fill.medium {{ background: #d29922; }}
        .bar-fill.low {{ background: #3fb950; }}
        .summary-text {{ color: #c9d1d9; line-height: 1.8; }}
        .recommendation {{
            padding: 10px 16px; background: #0d1117;
            border-radius: 8px; margin-bottom: 8px;
            font-size: 14px; border-left: 3px solid #58a6ff;
        }}
        table {{
            width: 100%; border-collapse: collapse; font-size: 13px;
        }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #21262d; }}
        th {{ color: #8b949e; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        .footer {{
            text-align: center; padding: 20px; color: #484f58; font-size: 12px;
            border-top: 1px solid #30363d; margin-top: 40px;
        }}
        @media print {{
            body {{ background: white; color: #1f2937; padding: 20px; }}
            .section {{ border-color: #e5e7eb; }}
            .stat-card {{ border-color: #e5e7eb; background: #f9fafb; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Blockchain Forensic Analysis Report</h1>
        <div class="subtitle">AI-Assisted Blockchain Forensics System</div>
        <div class="address">{html.escape(address)}</div>
        <div class="subtitle" style="margin-top: 8px;">
            {blockchain.upper()} Network • Generated {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}
        </div>
    </div>

    <div class="risk-gauge">
        <div class="risk-score">{risk_score}</div>
        <div class="risk-band">{risk_band} RISK</div>
        <div class="subtitle" style="margin-top: 8px;">
            Confidence: {ai_explanation.get('confidence', 'N/A')}% • AI Model: {ai_explanation.get('ai_model', 'rule-based')}
        </div>
    </div>

    <div class="section">
        <h2>📊 Wallet Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{wallet_stats.get('total_transactions', 0):,}</div>
                <div class="stat-label">Transactions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{wallet_stats.get('total_volume', 0):.4f}</div>
                <div class="stat-label">Total Volume</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{wallet_stats.get('connected_wallets', 0)}</div>
                <div class="stat-label">Connected Wallets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{wallet_stats.get('suspicious_activities', 0)}</div>
                <div class="stat-label">Suspicious Activities</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🤖 AI Analysis Summary</h2>
        <p class="summary-text">{html.escape(ai_explanation.get('summary', 'No summary available.'))}</p>
    </div>

    <div class="section">
        <h2>📋 Risk Factor Breakdown</h2>
        {self._render_factors_html(ai_explanation.get('riskFactors', []))}
    </div>

    <div class="section">
        <h2>💡 Recommendations</h2>
        {''.join(f'<div class="recommendation">{html.escape(r)}</div>' for r in ai_explanation.get('recommendations', []))}
    </div>

    <div class="section">
        <h2>📜 Recent Transactions</h2>
        {self._render_transactions_html(transactions[:20])}
    </div>

    <div class="footer">
        <p>AI-Assisted Blockchain Forensics System — Academic Research Project</p>
        <p>This report is generated for educational and research purposes only.</p>
        <p>Report ID: RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')} • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>"""

    def _render_factors_html(self, risk_factors: List[Dict]) -> str:
        factors_html = ""
        for f in risk_factors:
            severity = f.get('severity', 'low')
            score = f.get('score', 0)
            max_score = f.get('maxScore', 10)
            pct = (score / max_score * 100) if max_score > 0 else 0
            
            factors_html += f"""
            <div class="factor {severity}">
                <div class="factor-score">{score}</div>
                <div style="flex: 1;">
                    <div class="factor-name">{html.escape(f.get('title', ''))}</div>
                    <div class="factor-desc">{html.escape(f.get('description', '')[:150])}</div>
                    <div class="bar-bg" style="margin-top: 6px;">
                        <div class="bar-fill {severity}" style="width: {pct}%;"></div>
                    </div>
                </div>
            </div>"""
        return factors_html

    def _render_transactions_html(self, transactions: List[Dict]) -> str:
        if not transactions:
            return '<p style="color: #8b949e;">No transactions available.</p>'
        
        rows = ""
        for tx in transactions:
            tx_hash = tx.get('hash', 'N/A')
            if len(tx_hash) > 16:
                tx_hash = tx_hash[:8] + '...' + tx_hash[-6:]
            rows += f"""
            <tr>
                <td style="font-family: monospace;">{html.escape(tx_hash)}</td>
                <td>{html.escape(str(tx.get('type', 'N/A')))}</td>
                <td>{html.escape(str(tx.get('amount', 'N/A')))}</td>
                <td>{html.escape(str(tx.get('timestamp', 'N/A'))[:19])}</td>
                <td>{html.escape(str(tx.get('status', 'N/A')))}</td>
            </tr>"""
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Transaction Hash</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Timestamp</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""

    def _get_risk_color(self, risk_band: str) -> str:
        colors = {
            'LOW': '#3fb950', 'MEDIUM': '#d29922',
            'HIGH': '#f85149', 'CRITICAL': '#ff4757'
        }
        return colors.get(risk_band, '#8b949e')


if __name__ == '__main__':
    gen = ReportGenerator()
    report = gen.generate_report(
        address='0xF977814e90dA44bFA03b6295A0616a897441aceC',
        blockchain='ethereum',
        risk_data={'overall_risk': 72, 'risk_band': 'HIGH', 'factor_breakdown': {}},
        wallet_stats={'total_transactions': 156, 'total_volume': 45.67, 'connected_wallets': 45, 'suspicious_activities': 8},
        transactions=[],
        ai_explanation={
            'summary': 'This wallet exhibits high-risk behavior.',
            'riskFactors': [], 'recommendations': ['Monitor closely'],
            'confidence': 85, 'ai_model': 'rule-based'
        }
    )
    print(f"Report generated: {len(report)} characters")
