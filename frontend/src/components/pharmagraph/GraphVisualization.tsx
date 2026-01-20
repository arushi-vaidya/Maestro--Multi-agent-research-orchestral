/**
 * Graph Visualization Component
 * Interactive force-directed graph using react-force-graph-2d
 *
 * Library choice: react-force-graph-2d
 * Rationale:
 * - Lightweight and performant for medium-sized graphs (<1000 nodes)
 * - Built-in zoom/pan controls
 * - Easy node/edge customization
 * - Good TypeScript support
 * - Force-directed layout out of the box
 */

import React, { useRef, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface GraphNode {
  id: string;
  label: string;
  type: 'drug' | 'disease' | 'evidence' | 'target' | 'pathway' | 'adverse' | 'trial' | 'patent' | 'market_signal';
  metadata?: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
  type?: string;
}

interface GraphVisualizationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode?: GraphNode | null;
  highlightedPath?: string[];
  onNodeClick?: (node: GraphNode) => void;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  nodes,
  edges,
  selectedNode,
  highlightedPath = [],
  onNodeClick,
}) => {
  const graphRef = useRef<any>(null);

  // Node type colors (memoized to avoid recreating on every render)
  const nodeColors = useMemo(() => ({
    drug: '#3B82F6',        // blue
    disease: '#EF4444',     // red
    target: '#A855F7',      // purple
    pathway: '#10B981',     // green
    adverse: '#F59E0B',     // amber
    evidence: '#64748B',    // slate
    trial: '#14B8A6',       // teal
    patent: '#6366F1',      // indigo
    market_signal: '#059669', // emerald
  }), []);

  // Edge type colors (memoized to avoid recreating on every render)
  const edgeColors = useMemo(() => ({
    activates: '#10B981',   // green
    inhibits: '#EF4444',    // red
    regulates: '#6366F1',   // indigo
    promotes: '#F59E0B',    // amber
    risk: '#DC2626',        // red
    TREATS: '#10B981',
    SUGGESTS: '#6366F1',
    CONTRADICTS: '#EF4444',
    INVESTIGATED_FOR: '#F59E0B',
    SUPPORTS: '#14B8A6',
  }), []);

  // Custom node rendering (Card Style)
  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const isSelected = selectedNode?.id === node.id;
      const isHighlighted = highlightedPath.includes(node.id);
      const isEvidence = node.type === 'evidence' || node.type === 'trial';
      
      // Card dimensions
      const width = 140;
      const height = 50;
      const radius = 6;
      const x = node.x - width / 2;
      const y = node.y - height / 2;

      // Colors
      const typeColor = (nodeColors as any)[node.type] || '#64748B';
      const bgColor = isSelected ? '#FFFFFF' : '#F8FAFC'; // White if selected, slate-50 if not
      const borderColor = isSelected ? '#1E293B' : (isHighlighted ? typeColor : '#E2E8F0');
      
      // Shadow for selected nodes
      if (isSelected) {
        ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
        ctx.shadowBlur = 15;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 4;
      } else {
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
      }

      // Draw Card Background (Rounded Rect)
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + width - radius, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
      ctx.lineTo(x + width, y + height - radius);
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      
      ctx.fillStyle = bgColor;
      ctx.fill();
      
      // Draw Border
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = isSelected || isHighlighted ? 2 : 1;
      ctx.stroke();
      
      // Reset Shadow
      ctx.shadowColor = 'transparent';

      // Draw Left Color Strip (Type Indicator)
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + 4, y);
      ctx.lineTo(x + 4, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      ctx.fillStyle = typeColor;
      ctx.fill();

      // Text Formatting
      // 1. Label
      const fontSizeLabel = 14;
      ctx.font = `600 ${fontSizeLabel}px Inter, system-ui, sans-serif`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#1E293B'; // Slate-800
      
      // Truncate label if too long
      let displayLabel = label;
      const maxLabelWidth = width - 20;
      if (ctx.measureText(displayLabel).width > maxLabelWidth) {
        while (ctx.measureText(displayLabel + '...').width > maxLabelWidth && displayLabel.length > 0) {
          displayLabel = displayLabel.slice(0, -1);
        }
        displayLabel += '...';
      }
      ctx.fillText(displayLabel, x + 12, y + 20);

      // 2. Type (Subtitle)
      const fontSizeType = 10;
      ctx.font = `400 ${fontSizeType}px Inter, system-ui, sans-serif`;
      ctx.fillStyle = typeColor; // Use type color for text
      ctx.fillText(node.type.toUpperCase(), x + 12, y + 38);
      
      // Evidence Indicator (Badge)
      if (isEvidence) {
         ctx.beginPath();
         ctx.arc(x + width - 12, y + 12, 4, 0, 2 * Math.PI);
         ctx.fillStyle = '#10B981'; // Emerald
         ctx.fill();
      }
    },
    [selectedNode, highlightedPath, nodeColors]
  );

  // PRIORITY 5: Custom edge rendering with polarity-based styling
  const linkCanvasObject = useCallback(
    (link: any, ctx: CanvasRenderingContext2D) => {
      const isHighlighted =
        highlightedPath.includes(link.source.id) && highlightedPath.includes(link.target.id);

      // PRIORITY 5: Thickness based on evidence strength (polarity)
      let lineWidth = 1;
      if (link.type === 'SUPPORTS' || link.type === 'TREATS') {
        lineWidth = 2.5; // Strong evidence
      } else if (link.type === 'SUGGESTS') {
        lineWidth = 1.5; // Moderate evidence
      } else if (link.type === 'CONTRADICTS') {
        lineWidth = 2; // Strong negative evidence
      }

      if (isHighlighted) {
        lineWidth += 1;
      }

      // Draw edge line
      ctx.beginPath();
      ctx.moveTo(link.source.x, link.source.y);
      ctx.lineTo(link.target.x, link.target.y);
      ctx.strokeStyle = isHighlighted
        ? '#1E293B'
        : (edgeColors as any)[link.type] || '#CBD5E1';
      ctx.lineWidth = lineWidth;
      ctx.stroke();

      // Draw arrow
      const arrowLength = 10;
      const arrowWidth = 4;
      const angle = Math.atan2(
        link.target.y - link.source.y,
        link.target.x - link.source.x
      );

      ctx.save();
      ctx.translate(link.target.x, link.target.y);
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(-arrowLength, arrowWidth);
      ctx.lineTo(-arrowLength, -arrowWidth);
      ctx.closePath();
      ctx.fillStyle = isHighlighted
        ? '#1E293B'
        : (edgeColors as any)[link.type] || '#CBD5E1';
      ctx.fill();
      ctx.restore();
    },
    [highlightedPath, edgeColors]
  );

  // Handle node click
  const handleNodeClick = useCallback(
    (node: any) => {
      if (onNodeClick) {
        onNodeClick(node as GraphNode);
      }
    },
    [onNodeClick]
  );

  // Zoom to fit on mount and configure forces
  useEffect(() => {
    if (graphRef.current) {
      // Configure forces for card layout
      // Stronger repulsion to prevent card overlap
      graphRef.current.d3Force('charge').strength(-800);
      // Longer links to accommodate card width
      graphRef.current.d3Force('link').distance(200);
      // Gentle centering
      graphRef.current.d3Force('center').strength(0.05);

      if (nodes.length > 0) {
        setTimeout(() => {
          if (graphRef.current && graphRef.current.zoomToFit) {
            graphRef.current.zoomToFit(400, 50);
          }
        }, 500); // Wait for simulation to settle a bit
      }
    }
  }, [nodes.length, edges.length]);

  return (
    <div className="w-full h-[600px] bg-slate-50 relative">
      <ForceGraph2D
        ref={graphRef}
        graphData={{ nodes, links: edges }}
        nodeId="id"
        nodeLabel="label"
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        onNodeClick={handleNodeClick}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        enableNodeDrag={true}
        cooldownTicks={100}
        d3AlphaDecay={0.02} // Slower decay for better settling
        d3VelocityDecay={0.3}
        onEngineStop={() => {
          if (graphRef.current && graphRef.current.zoomToFit) {
            graphRef.current.zoomToFit(400, 50);
          }
        }}
        backgroundColor="#F8FAFC"
        linkColor={() => '#CBD5E1'}
      />

      {/* PRIORITY 5: Edge Semantics Legend */}
      <div className="absolute bottom-4 left-4 bg-white/95 border border-slate-200 rounded-lg p-3 shadow-sm">
        <div className="text-xs font-medium text-slate-700 mb-2 uppercase tracking-wider">
          Edge Polarity
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#10B981]"></div>
            <span className="text-xs text-slate-600">SUPPORTS</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#14B8A6]"></div>
            <span className="text-xs text-slate-600">TREATS</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#6366F1]"></div>
            <span className="text-xs text-slate-600">SUGGESTS</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#F59E0B]"></div>
            <span className="text-xs text-slate-600">INVESTIGATED</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[#EF4444]"></div>
            <span className="text-xs text-slate-600">CONTRADICTS</span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-slate-100">
          <div className="text-xs text-slate-500 italic">
            Thickness = Evidence strength
          </div>
        </div>
      </div>

      {/* Evidence Mediation Indicator */}
      <div className="absolute top-4 left-4 bg-emerald-50/95 border border-emerald-200 rounded-lg px-3 py-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          <span className="text-xs text-emerald-800 font-medium">
            Evidence nodes (green border)
          </span>
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
