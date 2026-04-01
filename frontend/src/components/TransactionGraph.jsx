import React, { useRef, useEffect, useState } from 'react';

function TransactionGraph({ graphData }) {
    const canvasRef = useRef(null);
    const [hoveredNode, setHoveredNode] = useState(null);
    const [positions, setPositions] = useState([]);

    const nodes = graphData?.nodes || [];
    const edges = graphData?.edges || [];

    useEffect(() => {
        if (!canvasRef.current || nodes.length === 0) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;

        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;

        // Position nodes in a radial layout
        const nodePositions = nodes.map((node, i) => {
            if (i === 0) {
                return { ...node, x: cx, y: cy, radius: 22 };
            }
            const angle = ((i - 1) / (nodes.length - 1)) * Math.PI * 2 - Math.PI / 2;
            const dist = Math.min(w, h) * 0.32;
            return {
                ...node,
                x: cx + Math.cos(angle) * dist,
                y: cy + Math.sin(angle) * dist,
                radius: 14
            };
        });

        setPositions(nodePositions);

        const getNodeColor = (type, risk) => {
            if (type === 'target') return '#6366f1';
            if (type === 'high-risk' || risk >= 70) return '#ef4444';
            if (type === 'medium-risk' || risk >= 40) return '#eab308';
            return '#22c55e';
        };

        // Animation
        let frame;
        let progress = 0;

        const draw = () => {
            progress = Math.min(progress + 0.02, 1);
            ctx.clearRect(0, 0, w, h);

            // Draw edges
            ctx.lineWidth = 1.5;
            edges.forEach(edge => {
                const fromNode = nodePositions.find(n => n.id === edge.from);
                const toNode = nodePositions.find(n => n.id === edge.to);
                if (!fromNode || !toNode) return;

                const ex = fromNode.x + (toNode.x - fromNode.x) * progress;
                const ey = fromNode.y + (toNode.y - fromNode.y) * progress;

                ctx.beginPath();
                ctx.moveTo(fromNode.x, fromNode.y);
                ctx.lineTo(ex, ey);
                ctx.strokeStyle = 'rgba(99, 102, 241, 0.25)';
                ctx.stroke();

                // Edge label
                if (progress >= 1 && edge.label) {
                    const mx = (fromNode.x + toNode.x) / 2;
                    const my = (fromNode.y + toNode.y) / 2;
                    ctx.font = '10px Inter';
                    ctx.fillStyle = 'rgba(148, 163, 184, 0.6)';
                    ctx.textAlign = 'center';
                    ctx.fillText(edge.label, mx, my - 4);
                }
            });

            // Draw nodes
            nodePositions.forEach((node, i) => {
                if (i > 0 && progress < i / nodes.length) return;

                const color = getNodeColor(node.type, node.risk);

                // Glow effect
                if (node.type === 'target') {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 35, 0, Math.PI * 2);
                    const glow = ctx.createRadialGradient(node.x, node.y, 15, node.x, node.y, 35);
                    glow.addColorStop(0, `${color}30`);
                    glow.addColorStop(1, 'transparent');
                    ctx.fillStyle = glow;
                    ctx.fill();
                }

                // Node circle
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = `${color}60`;
                ctx.lineWidth = 2;
                ctx.stroke();

                // Node label
                ctx.font = `${node.type === 'target' ? '11px' : '9px'} Inter`;
                ctx.fillStyle = '#f1f5f9';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(node.label?.substring(0, 10) || '', node.x, node.y + node.radius + 14);
            });

            if (progress < 1) {
                frame = requestAnimationFrame(draw);
            }
        };

        draw();
        return () => cancelAnimationFrame(frame);
    }, [nodes, edges]);

    // Handle mouse hover for tooltips
    const handleMouse = (e) => {
        if (!positions.length) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        const hovered = positions.find(p => {
            const dx = mx - p.x;
            const dy = my - p.y;
            return Math.sqrt(dx * dx + dy * dy) < p.radius + 4;
        });
        setHoveredNode(hovered || null);
    };

    return (
        <div className="card">
            <div className="card-header">
                <div className="card-title"><span className="icon">🕸️</span> Transaction Graph</div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {nodes.length} nodes • {edges.length} connections
                </span>
            </div>

            <div className="graph-container" onMouseMove={handleMouse} onMouseLeave={() => setHoveredNode(null)}>
                <canvas ref={canvasRef} className="graph-canvas" />

                {hoveredNode && (
                    <div style={{
                        position: 'absolute', bottom: '12px', left: '12px',
                        background: 'var(--bg-card)', border: '1px solid var(--border)',
                        borderRadius: '8px', padding: '10px 14px', fontSize: '12px',
                        pointerEvents: 'none', zIndex: 10
                    }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{hoveredNode.label}</strong>
                        <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>
                            Risk: {hoveredNode.risk}/100 • Type: {hoveredNode.type}
                        </div>
                        {hoveredNode.fullAddress && (
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--accent)', marginTop: '4px' }}>
                                {hoveredNode.fullAddress.substring(0, 20)}...
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="graph-legend">
                <div className="legend-item"><div className="legend-dot" style={{ background: '#6366f1' }} /> Target</div>
                <div className="legend-item"><div className="legend-dot" style={{ background: '#ef4444' }} /> High Risk</div>
                <div className="legend-item"><div className="legend-dot" style={{ background: '#eab308' }} /> Medium Risk</div>
                <div className="legend-item"><div className="legend-dot" style={{ background: '#22c55e' }} /> Low Risk</div>
            </div>
        </div>
    );
}

export default TransactionGraph;
