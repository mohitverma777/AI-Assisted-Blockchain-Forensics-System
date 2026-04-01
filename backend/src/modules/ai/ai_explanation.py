"""
AI Explanation Generator - Module E
Converts risk scores and forensic metrics into human-readable explanations.
Uses rule-based NLP templates with optional local Ollama LLM integration.

Authors: Shreya (Primary), Mohit (Backup)
"""

import os
import json
import random
from typing import Dict, List, Optional
from datetime import datetime

# Optional: Local Ollama LLM integration
try:
    import requests as http_requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AIExplanationGenerator:
    """
    Generates natural language explanations for blockchain forensic analysis.
    
    Two modes:
    1. Rule-based (default) — deterministic, no API dependency, always works
    2. LLM-powered (optional) — uses local Ollama server when available
    """

    # Default Ollama configuration
    DEFAULT_OLLAMA_URL = 'http://127.0.0.1:11434'
    DEFAULT_MODEL = 'gemma3:4b'

    def __init__(self, ollama_url: Optional[str] = None, model: Optional[str] = None):
        self.ollama_url = ollama_url or os.getenv('OLLAMA_URL', self.DEFAULT_OLLAMA_URL)
        self.model = model or os.getenv('OLLAMA_MODEL', self.DEFAULT_MODEL)
        self.use_llm = HAS_REQUESTS and self._check_ollama_health()

    # ================================================================
    # MAIN PUBLIC METHOD
    # ================================================================

    def generate_explanation(
        self,
        risk_score: float,
        risk_band: str,
        factor_breakdown: Dict,
        wallet_stats: Dict,
        cluster_info: Optional[Dict] = None,
        blockchain: str = "ethereum"
    ) -> Dict:
        """
        Generate a complete AI explanation for a wallet analysis.
        
        Args:
            risk_score: Overall risk score (0-100)
            risk_band: Risk band label (LOW/MEDIUM/HIGH/CRITICAL)
            factor_breakdown: Per-factor scores and reasons
            wallet_stats: Transaction statistics (count, volume, etc.)
            cluster_info: Cluster membership info (optional)
            blockchain: "ethereum" or "bitcoin"
        
        Returns:
            Dict with summary, riskFactors, recommendations, confidence
        """
        # Always use rule-based for reliability
        explanation = self._generate_rule_based(
            risk_score, risk_band, factor_breakdown,
            wallet_stats, cluster_info, blockchain
        )

        # Optionally enhance with local Ollama LLM
        if self.use_llm:
            try:
                llm_summary = self._generate_llm_summary(
                    risk_score, risk_band, factor_breakdown,
                    wallet_stats, blockchain
                )
                if llm_summary:
                    explanation['summary'] = llm_summary
                    explanation['ai_model'] = f'ollama/{self.model}'
            except Exception as e:
                explanation['ai_model'] = 'rule-based (LLM fallback)'
                explanation['llm_error'] = str(e)
        else:
            explanation['ai_model'] = 'rule-based'

        explanation['generated_at'] = datetime.utcnow().isoformat()
        return explanation

    # ================================================================
    # RULE-BASED EXPLANATION ENGINE
    # ================================================================

    def _generate_rule_based(
        self, risk_score, risk_band, factor_breakdown,
        wallet_stats, cluster_info, blockchain
    ) -> Dict:
        """Generate comprehensive explanation using rule-based templates."""
        
        summary = self._build_summary(risk_score, risk_band, wallet_stats, blockchain)
        risk_factors = self._build_risk_factors(factor_breakdown)
        recommendations = self._build_recommendations(risk_score, risk_band, factor_breakdown)
        confidence = self._calculate_confidence(factor_breakdown, wallet_stats)

        return {
            'summary': summary,
            'riskFactors': risk_factors,
            'recommendations': recommendations,
            'confidence': confidence,
            'riskLevel': risk_band.lower(),
            'overallScore': round(risk_score)
        }

    def _build_summary(self, risk_score, risk_band, wallet_stats, blockchain) -> str:
        """Build a natural language summary paragraph."""
        
        chain_name = "Ethereum" if blockchain == "ethereum" else "Bitcoin"
        tx_count = wallet_stats.get('total_transactions', 0)
        volume = wallet_stats.get('total_volume', 0)
        connected = wallet_stats.get('connected_wallets', 0)

        # Opening sentence based on risk level
        openers = {
            'LOW': [
                f"This {chain_name} wallet demonstrates normal transaction behavior with a low risk score of {risk_score}/100.",
                f"Analysis of this {chain_name} address indicates standard usage patterns with minimal risk indicators.",
                f"The forensic scan of this {chain_name} wallet reveals typical blockchain activity with low risk (score: {risk_score}/100)."
            ],
            'MEDIUM': [
                f"This {chain_name} wallet shows moderate risk indicators with an overall score of {risk_score}/100, warranting closer examination.",
                f"The analysis of this {chain_name} address reveals some behavioral patterns that deviate from typical usage (risk score: {risk_score}/100).",
                f"Our forensic assessment assigns a moderate risk rating of {risk_score}/100 to this {chain_name} wallet based on several contributing factors."
            ],
            'HIGH': [
                f"This {chain_name} wallet exhibits multiple high-risk behavioral patterns with a concerning score of {risk_score}/100.",
                f"Forensic analysis of this {chain_name} address has identified significant risk indicators, resulting in a high score of {risk_score}/100.",
                f"Several concerning patterns have been detected in this {chain_name} wallet, yielding a high-risk score of {risk_score}/100."
            ],
            'CRITICAL': [
                f"CRITICAL ALERT: This {chain_name} wallet shows extreme risk indicators with a score of {risk_score}/100, suggesting potential illicit activity.",
                f"This {chain_name} address has triggered critical risk thresholds with a score of {risk_score}/100. Multiple forensic indicators point to highly suspicious behavior.",
                f"Forensic analysis has flagged this {chain_name} wallet as critical risk ({risk_score}/100). The combination of detected patterns strongly suggests involvement in suspicious operations."
            ]
        }
        
        opener = random.choice(openers.get(risk_band, openers['MEDIUM']))
        
        # Activity details
        details = ""
        if tx_count > 0:
            details += f" The wallet has processed {tx_count:,} transactions"
            if volume > 0:
                if blockchain == "ethereum":
                    details += f" totaling approximately {volume:.4f} ETH in volume"
                else:
                    details += f" totaling approximately {volume:.8f} BTC in volume"
            details += "."
        
        if connected > 0:
            details += f" It is directly connected to {connected} other wallet addresses in the transaction network."

        # Closing assessment
        closings = {
            'LOW': " No immediate flags require attention, but periodic monitoring is recommended as standard practice.",
            'MEDIUM': " While not conclusively suspicious, these patterns merit further investigation to rule out potential misuse.",
            'HIGH': " These combined indicators suggest possible involvement in mixing services, exchange tumbling, or structured transactions designed to obscure fund origins.",
            'CRITICAL': " Immediate attention is recommended. The pattern combination is consistent with known money laundering typologies or exchange hack-related fund movements."
        }
        
        closing = closings.get(risk_band, closings['MEDIUM'])
        
        return opener + details + closing

    def _build_risk_factors(self, factor_breakdown: Dict) -> List[Dict]:
        """Convert factor scores into human-readable risk factor cards."""
        
        factor_templates = {
            'transaction_velocity': {
                'title': 'Transaction Velocity Analysis',
                'high': 'This wallet processes transactions at an unusually high frequency, {score}/15 points. Rapid-fire transactions are commonly associated with automated trading bots, mixing services, or wash trading operations.',
                'medium': 'Transaction frequency shows moderate activity ({score}/15 points). The pace is higher than typical personal wallets but within range of active traders or small business operations.',
                'low': 'Transaction velocity is within normal ranges ({score}/15 points), consistent with regular personal or business wallet usage patterns.'
            },
            'amount_anomaly': {
                'title': 'Amount Pattern Anomaly',
                'high': 'Significant amount anomalies detected ({score}/15 points). The distribution of transaction values shows irregular patterns — disproportionate incoming vs. outgoing amounts may indicate fund structuring or smurfing techniques.',
                'medium': 'Some amount irregularities observed ({score}/15 points). Transaction values show mild deviations from typical distribution patterns, possibly indicating occasional large transfers or consolidation.',
                'low': 'Transaction amounts follow normal distribution patterns ({score}/15 points). No significant anomalies detected in value distributions.'
            },
            'behavioral_pattern': {
                'title': 'Behavioral Pattern Detection',
                'high': 'Strong behavioral anomalies detected ({score}/10 points). The wallet exhibits patterns inconsistent with normal usage — potential indicators include automated behavior, rapid fund cycling, or coordinated multi-wallet operations.',
                'medium': 'Moderate behavioral deviations noted ({score}/10 points). Some transaction patterns differ from typical wallet behavior but may have legitimate explanations.',
                'low': 'Behavioral patterns appear normal ({score}/10 points). Activity is consistent with standard wallet usage.'
            },
            'connection_density': {
                'title': 'Network Connection Density',
                'high': 'High connection density detected ({score}/10 points). This wallet interacts with an unusually large number of unique addresses, which may indicate hub behavior associated with exchanges, mixers, or distribution networks.',
                'medium': 'Moderate network connections ({score}/10 points). The wallet interacts with a reasonable number of counterparties, suggesting diversified but not suspicious activity.',
                'low': 'Connection density is normal ({score}/10 points). The wallet interacts with a limited number of addresses, typical of personal wallets.'
            },
            'dormancy_risk': {
                'title': 'Dormancy & Reactivation Analysis',
                'high': 'Suspicious dormancy pattern detected ({score}/10 points). This wallet was inactive for an extended period and then suddenly reactivated with high transaction volume — a pattern often seen in compromised wallets or planned exit scams.',
                'medium': 'Some dormancy noted ({score}/10 points). The wallet had periods of inactivity followed by resumed usage, which may have benign explanations.',
                'low': 'No significant dormancy issues ({score}/10 points). The wallet shows consistent activity over time.'
            },
            'mixing_entropy': {
                'title': 'Mixing Entropy Score',
                'high': 'High entropy in transaction graph ({score}/15 points). The branching and recombination patterns of funds are consistent with cryptocurrency mixing or tumbling services designed to obscure transaction trails.',
                'medium': 'Moderate entropy detected ({score}/15 points). Some branching patterns exist but are not definitively indicative of mixing services.',
                'low': 'Low entropy in transaction patterns ({score}/15 points). Fund flows are straightforward with minimal obfuscation.'
            },
            'exposure_risk': {
                'title': 'Exposure to Flagged Entities',
                'high': 'Direct exposure to flagged addresses detected ({score}/5 points). This wallet has transacted with addresses known to be associated with scams, hacks, or sanctioned entities in public databases.',
                'medium': 'Indirect exposure detected ({score}/5 points). The wallet has second-degree connections to flagged entities through intermediary wallets.',
                'low': 'No known exposure ({score}/5 points). The wallet has no detected connections to flagged addresses in public databases.'
            },
            'chain_hopping': {
                'title': 'Cross-Chain Activity Indicator',
                'high': 'Chain-hopping patterns detected ({score}/5 points). Evidence suggests funds are being moved across blockchain networks, a technique used to complicate forensic tracing.',
                'medium': 'Some cross-chain indicators ({score}/5 points). Limited evidence of multi-chain activity detected.',
                'low': 'No cross-chain indicators ({score}/5 points). Activity appears confined to a single blockchain network.'
            },
            'peeling_chain': {
                'title': 'Peeling Chain Detection',
                'high': 'Peeling chain patterns identified ({score}/10 points). The wallet shows a classic peeling pattern where small amounts are successively peeled off to different addresses — a known money laundering technique.',
                'medium': 'Possible peeling behavior ({score}/10 points). Some transactions show characteristics of peeling chains but patterns are not conclusive.',
                'low': 'No peeling chain patterns ({score}/10 points). Transaction outputs do not show the sequential reduction pattern associated with peeling.'
            },
            'round_number_risk': {
                'title': 'Round Number Transaction Analysis',
                'high': 'High proportion of round-number transactions ({score}/5 points). Frequent use of round amounts (e.g., 1.0, 5.0, 10.0) is a common indicator of manual transfers, OTC deals, or structured transactions.',
                'medium': 'Some round-number transactions detected ({score}/5 points). A moderate number of transactions use clean amounts.',
                'low': 'Normal amount granularity ({score}/5 points). Transaction amounts show typical decimal variation.'
            }
        }

        risk_factors = []
        
        for factor_name, factor_data in factor_breakdown.items():
            score = factor_data.get('score', 0) if isinstance(factor_data, dict) else factor_data[0] if isinstance(factor_data, (list, tuple)) else 0
            reason = factor_data.get('reason', '') if isinstance(factor_data, dict) else factor_data[1] if isinstance(factor_data, (list, tuple)) and len(factor_data) > 1 else ''
            
            template = factor_templates.get(factor_name, {
                'title': factor_name.replace('_', ' ').title(),
                'high': f'Elevated score detected ({score} points). This factor contributes to the overall risk assessment.',
                'medium': f'Moderate score ({score} points). This factor shows some deviation from baseline.',
                'low': f'Low score ({score} points). This factor is within normal parameters.'
            })
            
            # Determine severity
            max_scores = {
                'transaction_velocity': 15, 'amount_anomaly': 15,
                'behavioral_pattern': 10, 'connection_density': 10,
                'dormancy_risk': 10, 'mixing_entropy': 15,
                'exposure_risk': 5, 'chain_hopping': 5,
                'peeling_chain': 10, 'round_number_risk': 5
            }
            max_score = max_scores.get(factor_name, 10)
            ratio = score / max_score if max_score > 0 else 0
            
            if ratio >= 0.6:
                severity = 'high'
                description = template['high'].format(score=score)
            elif ratio >= 0.3:
                severity = 'medium'
                description = template['medium'].format(score=score)
            else:
                severity = 'low'
                description = template['low'].format(score=score)

            risk_factors.append({
                'title': template['title'],
                'description': description,
                'severity': severity,
                'score': round(score, 1),
                'maxScore': max_score,
                'impact': round(score / 100 * 100, 1) if score > 0 else 0,
                'rawReason': reason
            })
        
        # Sort by score descending (most significant first)
        risk_factors.sort(key=lambda x: x['score'], reverse=True)
        return risk_factors

    def _build_recommendations(self, risk_score, risk_band, factor_breakdown) -> List[str]:
        """Generate actionable recommendations based on risk level."""
        
        recs = []
        
        if risk_band == 'CRITICAL':
            recs.extend([
                "🔴 Immediate enhanced monitoring recommended — flag for compliance review",
                "🔴 Cross-reference with OFAC/SDN sanctions lists and known darknet markets",
                "🔴 File Suspicious Transaction Report (STR) with FIU-IND if applicable",
                "🔴 Preserve all transaction evidence for potential law enforcement request"
            ])
        elif risk_band == 'HIGH':
            recs.extend([
                "🟠 Place wallet under enhanced monitoring for the next 30 days",
                "🟠 Review cluster members for additional risk indicators",
                "🟠 Cross-reference with exchange KYC databases if applicable",
                "🟠 Monitor for sudden fund consolidation or distribution patterns"
            ])
        elif risk_band == 'MEDIUM':
            recs.extend([
                "🟡 Periodic monitoring recommended — reassess in 14 days",
                "🟡 Review connected wallet addresses for known entity matches",
                "🟡 Check for unusual pattern changes in upcoming transactions"
            ])
        else:
            recs.extend([
                "🟢 Standard monitoring sufficient — no immediate action required",
                "🟢 Include in routine periodic blockchain compliance reviews"
            ])
        
        # Factor-specific recommendations
        scores = {}
        for k, v in factor_breakdown.items():
            if isinstance(v, dict):
                scores[k] = v.get('score', 0)
            elif isinstance(v, (list, tuple)):
                scores[k] = v[0]
            else:
                scores[k] = 0
        
        if scores.get('mixing_entropy', 0) >= 10:
            recs.append("📊 Conduct deep-dive mixing analysis with extended transaction hop tracing")
        if scores.get('peeling_chain', 0) >= 5:
            recs.append("🔗 Track peeling chain endpoints for potential cashout addresses")
        if scores.get('exposure_risk', 0) >= 3:
            recs.append("⚠️ Investigate direct connections to flagged entities in detail")
        if scores.get('dormancy_risk', 0) >= 7:
            recs.append("🕐 Investigate cause of reactivation after dormancy period")
        
        return recs[:6]  # Cap at 6 recommendations

    def _calculate_confidence(self, factor_breakdown, wallet_stats) -> int:
        """Calculate confidence score for the analysis (0-100)."""
        
        tx_count = wallet_stats.get('total_transactions', 0)
        
        # More transactions = higher confidence
        if tx_count >= 100:
            data_confidence = 95
        elif tx_count >= 50:
            data_confidence = 85
        elif tx_count >= 20:
            data_confidence = 75
        elif tx_count >= 5:
            data_confidence = 60
        else:
            data_confidence = 40
        
        # Number of factors analyzed adds confidence
        num_factors = len(factor_breakdown)
        factor_confidence = min(95, 50 + num_factors * 5)
        
        return round((data_confidence + factor_confidence) / 2)

    # ================================================================
    # OPTIONAL: LOCAL OLLAMA LLM-POWERED EXPLANATION
    # ================================================================

    def _check_ollama_health(self) -> bool:
        """Check if Ollama server is running and reachable."""
        try:
            resp = http_requests.get(f'{self.ollama_url}/api/tags', timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def _generate_llm_summary(
        self, risk_score, risk_band, factor_breakdown,
        wallet_stats, blockchain
    ) -> Optional[str]:
        """Generate summary using local Ollama LLM (optional enhancement)."""
        
        if not self.use_llm or not HAS_REQUESTS:
            return None

        prompt = self._build_llm_prompt(
            risk_score, risk_band, factor_breakdown,
            wallet_stats, blockchain
        )

        try:
            response = http_requests.post(
                f'{self.ollama_url}/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': (
                                'You are a blockchain forensics analyst. Generate a concise, '
                                'professional 2-3 sentence summary of a wallet risk analysis. '
                                'Be factual and avoid speculation. Only describe what the data shows.'
                            )
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 200,
                    'temperature': 0.3
                },
                timeout=60  # Local inference can be slower
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            return None
            
        except Exception:
            return None

    def _build_llm_prompt(self, risk_score, risk_band, factor_breakdown, wallet_stats, blockchain):
        """Build a structured prompt for the LLM."""
        
        factors_text = ""
        for name, data in factor_breakdown.items():
            score = data.get('score', 0) if isinstance(data, dict) else data[0] if isinstance(data, (list, tuple)) else 0
            reason = data.get('reason', '') if isinstance(data, dict) else data[1] if isinstance(data, (list, tuple)) and len(data) > 1 else ''
            factors_text += f"  - {name.replace('_', ' ').title()}: {score} points — {reason}\n"
        
        return f"""Analyze this {blockchain} wallet forensic report:

Risk Score: {risk_score}/100 ({risk_band})
Transactions: {wallet_stats.get('total_transactions', 'Unknown')}
Connected Wallets: {wallet_stats.get('connected_wallets', 'Unknown')}

Risk Factor Breakdown:
{factors_text}

Generate a professional forensic summary in 2-3 sentences. Focus on the most significant findings."""


    # ================================================================
    # GRAPH EXPLANATION GENERATOR
    # ================================================================

    def generate_graph_explanation(
        self,
        graph_data: Dict,
        risk_score: float = 0,
        risk_band: str = 'MEDIUM',
        blockchain: str = 'ethereum'
    ) -> Dict:
        """
        Generate an easy-to-understand explanation of the transaction graph.

        Args:
            graph_data: Dict with 'nodes' and 'edges' lists
            risk_score: Overall risk score (0-100)
            risk_band: Risk band label
            blockchain: "ethereum" or "bitcoin"

        Returns:
            Dict with overview, key_findings, and ai_model
        """
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        if not nodes:
            return {
                'overview': 'No graph data available for this wallet.',
                'key_findings': [],
                'ai_model': 'rule-based'
            }

        # Classify nodes by risk
        high_risk = [n for n in nodes if n.get('type') == 'high-risk' or n.get('risk', 0) >= 70]
        medium_risk = [n for n in nodes if n.get('type') == 'medium-risk' or (40 <= n.get('risk', 0) < 70)]
        low_risk = [n for n in nodes if n.get('type') == 'low-risk' or n.get('risk', 0) < 40]
        target_nodes = [n for n in nodes if n.get('type') == 'target']
        connected_count = len(nodes) - len(target_nodes)

        # Build rule-based explanation
        chain_name = "Ethereum" if blockchain == "ethereum" else "Bitcoin"
        overview = self._build_graph_overview(
            chain_name, connected_count, len(edges),
            len(high_risk), len(medium_risk), len(low_risk),
            risk_score, risk_band
        )
        key_findings = self._build_graph_findings(
            nodes, edges, high_risk, medium_risk,
            connected_count, risk_band
        )

        result = {
            'overview': overview,
            'key_findings': key_findings,
            'ai_model': 'rule-based'
        }

        # Try LLM enhancement
        if self.use_llm:
            try:
                llm_explanation = self._generate_graph_llm(
                    nodes, edges, chain_name,
                    risk_score, risk_band
                )
                if llm_explanation:
                    result['overview'] = llm_explanation
                    result['ai_model'] = f'ollama/{self.model}'
            except Exception:
                result['ai_model'] = 'rule-based (LLM fallback)'

        return result

    def _build_graph_overview(
        self, chain_name, connected, edges_count,
        high_count, medium_count, low_count,
        risk_score, risk_band
    ) -> str:
        """Build a simple overview paragraph of the graph."""

        overview = f"This {chain_name} wallet is connected to {connected} other wallet addresses through {edges_count} transaction links."

        if high_count > 0:
            overview += f" Notably, {high_count} of these connected wallets are flagged as high-risk, which means they have exhibited suspicious patterns like mixing, rapid fund cycling, or connections to known flagged entities."
        elif medium_count > 0 and medium_count >= connected // 2:
            overview += f" About {medium_count} connected wallets show moderate risk indicators, suggesting some unusual but not conclusively suspicious activity in the network."
        else:
            overview += " The connected wallets generally show normal activity patterns with low risk indicators."

        if connected >= 10:
            overview += " The high number of connections could indicate this wallet is used as a hub — possibly an exchange wallet, OTC desk, or a mixing intermediary."
        elif connected <= 3:
            overview += " The small number of connections suggests this is a personal wallet with limited transaction activity."

        return overview

    def _build_graph_findings(
        self, nodes, edges, high_risk, medium_risk,
        connected_count, risk_band
    ) -> List[str]:
        """Generate key findings from graph structure."""

        findings = []

        # Connection density
        if connected_count >= 10:
            findings.append(f"High connectivity detected — this wallet interacts with {connected_count} unique addresses, which is above average and may indicate hub-like behavior.")
        elif connected_count >= 5:
            findings.append(f"Moderate connectivity — the wallet is linked to {connected_count} addresses, showing diversified transaction activity.")
        else:
            findings.append(f"Low connectivity — only {connected_count} connected addresses, typical of personal or low-activity wallets.")

        # High risk neighbors
        if len(high_risk) > 0:
            pct = round(len(high_risk) / max(connected_count, 1) * 100)
            findings.append(f"{len(high_risk)} high-risk wallet(s) detected in the network ({pct}% of connections). These wallets exhibit patterns associated with mixing services, fraud, or laundering.")

        # Transaction volume from edge labels
        large_txs = [e for e in edges if e.get('value', 0) > 5]
        if large_txs:
            findings.append(f"{len(large_txs)} large-value transaction link(s) found in the graph, which could indicate significant fund movements worth investigating.")

        # Medium risk concentration
        if len(medium_risk) >= 3:
            findings.append(f"{len(medium_risk)} wallets with moderate risk scores are connected, suggesting a cluster of addresses with some behavioral deviations from normal patterns.")

        # Overall assessment
        if risk_band in ('HIGH', 'CRITICAL'):
            findings.append("The overall network structure shows patterns consistent with organized fund movement. Further investigation of the high-risk connections is recommended.")
        elif risk_band == 'MEDIUM':
            findings.append("The network shows some concerning patterns but nothing conclusive. Periodic monitoring of this wallet's connections is advised.")
        else:
            findings.append("The transaction network appears typical and does not raise immediate red flags. Standard monitoring is sufficient.")

        return findings[:5]

    def _generate_graph_llm(
        self, nodes, edges, chain_name, risk_score, risk_band
    ) -> Optional[str]:
        """Use Ollama to generate a simple graph explanation."""

        if not self.use_llm or not HAS_REQUESTS:
            return None

        high_risk = [n for n in nodes if n.get('risk', 0) >= 70]
        medium_risk = [n for n in nodes if 40 <= n.get('risk', 0) < 70]
        connected = len(nodes) - 1

        prompt = f"""Explain this {chain_name} wallet transaction graph in simple terms that anyone can understand:

- Target wallet risk score: {risk_score}/100 ({risk_band})
- Connected to {connected} other wallets
- {len(high_risk)} high-risk wallets in the network
- {len(medium_risk)} medium-risk wallets
- {len(edges)} transaction links between wallets

Write a clear 3-4 sentence paragraph explaining what this graph shows about the wallet's activity. Use simple language — avoid technical jargon. Focus on what the connections mean and whether the pattern looks normal or suspicious."""

        try:
            response = http_requests.post(
                f'{self.ollama_url}/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': (
                                'You are a helpful assistant who explains blockchain forensic data '
                                'in simple, everyday language. Write concise explanations that a '
                                'non-technical person can easily understand. Do not use bullet points.'
                            )
                        },
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 250,
                    'temperature': 0.4
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            return None
        except Exception:
            return None


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

def generate_ai_explanation(
    risk_data: Dict,
    wallet_stats: Dict,
    cluster_info: Optional[Dict] = None,
    blockchain: str = "ethereum"
) -> Dict:
    """
    Convenience function for generating AI explanations.
    
    Args:
        risk_data: Output from risk_engine() containing overall_risk, risk_band, factor_breakdown
        wallet_stats: Transaction statistics dict
        cluster_info: Optional cluster membership info
        blockchain: "ethereum" or "bitcoin"
    
    Returns:
        Complete explanation dict
    """
    generator = AIExplanationGenerator()
    return generator.generate_explanation(
        risk_score=risk_data.get('overall_risk', 0),
        risk_band=risk_data.get('risk_band', 'MEDIUM'),
        factor_breakdown=risk_data.get('factor_breakdown', {}),
        wallet_stats=wallet_stats,
        cluster_info=cluster_info,
        blockchain=blockchain
    )


def generate_graph_explanation(
    graph_data: Dict,
    risk_data: Dict,
    blockchain: str = "ethereum"
) -> Dict:
    """
    Convenience function for generating graph explanations.

    Args:
        graph_data: Dict with 'nodes' and 'edges'
        risk_data: Output from risk_engine()
        blockchain: "ethereum" or "bitcoin"

    Returns:
        Dict with overview, key_findings, ai_model
    """
    generator = AIExplanationGenerator()
    return generator.generate_graph_explanation(
        graph_data=graph_data,
        risk_score=risk_data.get('overall_risk', 0),
        risk_band=risk_data.get('risk_band', 'MEDIUM'),
        blockchain=blockchain
    )


if __name__ == '__main__':
    # Demo with sample data
    sample_risk = {
        'overall_risk': 72,
        'risk_band': 'HIGH',
        'factor_breakdown': {
            'transaction_velocity': {'score': 12, 'reason': 'High frequency detected'},
            'amount_anomaly': {'score': 10, 'reason': 'Significant amount disparity'},
            'behavioral_pattern': {'score': 7, 'reason': 'Automated behavior suspected'},
            'connection_density': {'score': 6, 'reason': 'Connected to 45 wallets'},
            'dormancy_risk': {'score': 2, 'reason': 'Recently active'},
            'mixing_entropy': {'score': 13, 'reason': 'High branching factor'},
            'exposure_risk': {'score': 4, 'reason': 'Connected to flagged address'},
            'chain_hopping': {'score': 3, 'reason': 'Cross-chain indicators'},
            'peeling_chain': {'score': 8, 'reason': 'Sequential peeling detected'},
            'round_number_risk': {'score': 3, 'reason': '40% round numbers'}
        }
    }
    
    sample_stats = {
        'total_transactions': 156,
        'total_volume': 45.67,
        'connected_wallets': 45
    }
    
    result = generate_ai_explanation(sample_risk, sample_stats, blockchain='ethereum')
    
    print("=" * 60)
    print("🤖 AI EXPLANATION GENERATOR - DEMO")
    print("=" * 60)
    print(f"\n📝 Summary:\n{result['summary']}")
    print(f"\n🎯 Confidence: {result['confidence']}%")
    print(f"🔧 AI Model: {result['ai_model']}")
    print(f"\n📊 Risk Factors ({len(result['riskFactors'])}):")
    for f in result['riskFactors'][:3]:
        print(f"  [{f['severity'].upper()}] {f['title']}: {f['score']}/{f['maxScore']}")
    print(f"\n💡 Recommendations ({len(result['recommendations'])}):")
    for r in result['recommendations']:
        print(f"  {r}")
