import React from 'react';

function RiskAnalysis({ riskScore = 0, riskLevel = 'MEDIUM', riskBreakdown, aiInsights }) {
    const score = Math.round(riskScore);
    const factors = aiInsights?.riskFactors || [];

    const getColor = (level) => {
        const colors = {
            LOW: 'var(--risk-low)',
            MEDIUM: 'var(--risk-medium)',
            HIGH: 'var(--risk-high)',
            CRITICAL: 'var(--risk-critical)'
        };
        return colors[level] || colors.MEDIUM;
    };

    const color = getColor(riskLevel);

    // SVG gauge parameters
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    return (
        <div className="card">
            <div className="card-header">
                <div className="card-title"><span className="icon">⚠️</span> Risk Analysis</div>
                <span className="severity-badge" style={{
                    background: `${color}20`, color,
                    padding: '4px 12px', borderRadius: '20px',
                    fontSize: '11px', fontWeight: '700'
                }}>
                    {riskLevel}
                </span>
            </div>

            <div className="risk-gauge">
                <svg width="180" height="180" viewBox="0 0 180 180">
                    {/* Background circle */}
                    <circle
                        cx="90" cy="90" r={radius}
                        fill="none" stroke="var(--border)" strokeWidth="8"
                    />
                    {/* Score arc */}
                    <circle
                        cx="90" cy="90" r={radius}
                        fill="none" stroke={color} strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        transform="rotate(-90 90 90)"
                        style={{ transition: 'stroke-dashoffset 1.5s ease-out' }}
                    />
                    {/* Score text */}
                    <text x="90" y="82" textAnchor="middle" fill={color}
                        fontSize="42" fontWeight="900" fontFamily="var(--font-mono)">
                        {score}
                    </text>
                    <text x="90" y="105" textAnchor="middle" fill="var(--text-muted)"
                        fontSize="11" fontWeight="600" letterSpacing="2">
                        {riskLevel} RISK
                    </text>
                </svg>
            </div>

            {factors.length > 0 && (
                <div className="risk-factors-list">
                    {factors.slice(0, 10).map((factor, i) => {
                        const pct = factor.maxScore > 0 ? (factor.score / factor.maxScore * 100) : 0;
                        const barColor = factor.severity === 'high' ? 'var(--risk-critical)'
                            : factor.severity === 'medium' ? 'var(--risk-medium)' : 'var(--risk-low)';
                        return (
                            <div key={i} className="risk-factor-item">
                                <span className="factor-name">{factor.title}</span>
                                <span className="factor-score" style={{ color: barColor }}>
                                    {factor.score}/{factor.maxScore}
                                </span>
                                <div className="factor-bar">
                                    <div className="factor-bar-fill" style={{
                                        width: `${Math.min(pct, 100)}%`,
                                        background: barColor
                                    }} />
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default RiskAnalysis;
