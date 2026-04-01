import React, { useState } from 'react';

function WalletInput({ onAnalyze, isLoading }) {
    const [address, setAddress] = useState('');
    const [validationError, setValidationError] = useState('');

    const validateAddress = (addr) => {
        if (!addr.trim()) return 'Please enter a wallet address';
        // Ethereum: 0x followed by 40 hex chars
        if (addr.startsWith('0x') && /^0x[a-fA-F0-9]{40}$/.test(addr)) return '';
        // Bitcoin: starts with 1, 3, or bc1
        if (/^(1|3)[a-zA-HJ-NP-Z1-9]{25,34}$/.test(addr)) return '';
        if (/^bc1[a-z0-9]{25,100}$/.test(addr)) return '';
        // Partial Ethereum (allow short for testing)
        if (addr.startsWith('0x') && addr.length >= 10) return '';
        return 'Invalid format. Enter an Ethereum (0x...) or Bitcoin address.';
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const error = validateAddress(address);
        if (error) {
            setValidationError(error);
            return;
        }
        setValidationError('');
        onAnalyze(address.trim());
    };

    const sampleAddresses = [
        { label: 'Ethereum', addr: '0x0E58e8993100F1CBe45376c410F97f4893d9BfCD' },
        { label: 'Bitcoin', addr: '34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo' },
    ];

    return (
        <div className="wallet-input-section">
            <div className="wallet-hero">
                <h1>🔍 Blockchain Forensic Analysis</h1>
                <p>Enter any Ethereum or Bitcoin wallet address to analyze transaction patterns, detect risks, and generate AI-powered insights.</p>

                <form onSubmit={handleSubmit}>
                    <div className="wallet-input-wrapper">
                        <input
                            id="wallet-address-input"
                            type="text"
                            className="wallet-input"
                            placeholder="0x... or Bitcoin address"
                            value={address}
                            onChange={(e) => { setAddress(e.target.value); setValidationError(''); }}
                            disabled={isLoading}
                            autoComplete="off"
                            spellCheck={false}
                        />
                        <button
                            id="analyze-button"
                            type="submit"
                            className="analyze-btn"
                            disabled={isLoading || !address.trim()}
                        >
                            {isLoading ? '⏳ Analyzing...' : '🔍 Analyze'}
                        </button>
                    </div>
                </form>

                {validationError && (
                    <p style={{ color: 'var(--error)', fontSize: '13px', marginTop: '8px' }}>
                        {validationError}
                    </p>
                )}

                <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', alignSelf: 'center' }}>Try:</span>
                    {sampleAddresses.map(s => (
                        <button
                            key={s.addr}
                            onClick={() => { setAddress(s.addr); setValidationError(''); }}
                            style={{
                                background: 'var(--bg-card)', border: '1px solid var(--border)',
                                borderRadius: '20px', padding: '4px 12px', color: 'var(--accent)',
                                fontSize: '12px', cursor: 'pointer', fontFamily: 'var(--font-sans)',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
                            onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}
                        >
                            {s.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default WalletInput;
