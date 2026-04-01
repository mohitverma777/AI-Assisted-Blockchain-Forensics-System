import React from 'react';

function GraphExplanation({ graphExplanation }) {
    if (!graphExplanation) return null;

    const { overview, key_findings = [], ai_model } = graphExplanation;

    return (
        <div className="card">
            <div className="card-header">
                <div className="card-title"><span className="icon">🧠</span> Graph Analysis</div>
                {ai_model && (
                    <span style={{
                        fontSize: '10px', padding: '3px 10px', borderRadius: '20px',
                        background: 'var(--accent-glow)', color: 'var(--accent)', fontWeight: '600'
                    }}>
                        {ai_model}
                    </span>
                )}
            </div>

            {/* Overview */}
            <div className="graph-explanation-overview">
                {overview}
            </div>

            {/* Key Findings */}
            {key_findings.length > 0 && (
                <div style={{ marginTop: '16px' }}>
                    <h4 style={{
                        fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px',
                        fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px'
                    }}>
                        Key Findings
                    </h4>
                    {key_findings.map((finding, i) => (
                        <div key={i} className="graph-finding-item">
                            <span className="finding-number">{i + 1}</span>
                            <span className="finding-text">{finding}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default GraphExplanation;
