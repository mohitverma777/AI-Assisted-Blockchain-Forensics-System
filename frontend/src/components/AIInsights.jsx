import React from 'react';
import { getReportUrl } from '../services/api';

function AIInsights({ insights, address }) {
    if (!insights) return null;

    const { summary, riskFactors = [], recommendations = [], confidence = 0, ai_model } = insights;

    return (
        <div className="card">
            <div className="card-header">
                <div className="card-title"><span className="icon">🤖</span> AI Forensic Insights</div>
                {ai_model && (
                    <span style={{
                        fontSize: '10px', padding: '3px 10px', borderRadius: '20px',
                        background: 'var(--accent-glow)', color: 'var(--accent)', fontWeight: '600'
                    }}>
                        {ai_model}
                    </span>
                )}
            </div>

            {/* Summary */}
            <div className="ai-summary">{summary}</div>

            {/* Risk Factors */}
            {riskFactors.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px', fontWeight: '600' }}>
                        Risk Factor Analysis
                    </h4>
                    {riskFactors.slice(0, 4).map((factor, i) => (
                        <div key={i} className={`ai-factor-card ${factor.severity}`}>
                            <div className="ai-factor-title">
                                {factor.title}
                                <span className={`severity-badge ${factor.severity}`}>{factor.severity}</span>
                                {factor.score !== undefined && (
                                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                        {factor.score}/{factor.maxScore || '?'}
                                    </span>
                                )}
                            </div>
                            <div className="ai-factor-desc">{factor.description}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                    <h4 style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px', fontWeight: '600' }}>
                        Recommendations
                    </h4>
                    {recommendations.map((rec, i) => (
                        <div key={i} className="recommendation-item">{rec}</div>
                    ))}
                </div>
            )}

            {/* Confidence Bar */}
            <div className="confidence-bar">
                <span className="confidence-label">Analysis Confidence</span>
                <div className="confidence-track">
                    <div className="confidence-fill" style={{ width: `${confidence}%` }} />
                </div>
                <span className="confidence-value">{confidence}%</span>
            </div>

            {/* Report Download */}
            {address && (
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                    <a
                        href={getReportUrl(address)}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                            display: 'inline-flex', alignItems: 'center', gap: '8px',
                            background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)', padding: '10px 20px',
                            color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '500',
                            textDecoration: 'none', transition: 'all 0.2s', cursor: 'pointer',
                            fontFamily: 'var(--font-sans)'
                        }}
                        onMouseEnter={e => {
                            e.target.style.borderColor = 'var(--accent)';
                            e.target.style.color = 'var(--accent)';
                        }}
                        onMouseLeave={e => {
                            e.target.style.borderColor = 'var(--border)';
                            e.target.style.color = 'var(--text-secondary)';
                        }}
                    >
                        📄 Download Full Report
                    </a>
                </div>
            )}
        </div>
    );
}

export default AIInsights;
