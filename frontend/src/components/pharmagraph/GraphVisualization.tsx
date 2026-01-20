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

  // Custom node rendering
  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const isSelected = selectedNode?.id === node.id;
      const isHighlighted = highlightedPath.includes(node.id);
      const isComparator = node.metadata?.isComparator === true;
      const isEvidence = node.type === 'evidence' || node.type === 'trial';

      // PRIORITY 4: De-emphasize comparator drugs
      const fontSize = 12 / globalScale;
      let nodeSize = isSelected ? 8 : isHighlighted ? 6 : 5;

      // PRIORITY 6: Emphasize evidence nodes
      if (isEvidence && !isComparator) {
        nodeSize = isSelected ? 9 : isHighlighted ? 7 : 6;
      }

      // Comparators are smaller and greyed
      if (isComparator) {
        nodeSize = isSelected ? 5 : 3.5;
      }

      // Draw node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);

      // PRIORITY 4: Reduce opacity for comparators
      const baseColor = (nodeColors as any)[node.type] || '#64748B';
      if (isComparator) {
        ctx.globalAlpha = 0.35; // Greyed out comparators
        ctx.fillStyle = '#94A3B8'; // Slate-400 (neutral grey)
      } else {
        ctx.globalAlpha = 1.0;
        ctx.fillStyle = baseColor;
      }

      ctx.fill();
      ctx.globalAlpha = 1.0;

      // Highlight border for selected/highlighted nodes
      if (isSelected || isHighlighted) {
        ctx.strokeStyle = isSelected ? '#1E293B' : '#64748B';
        ctx.lineWidth = isSelected ? 2 : 1;
        ctx.stroke();
      }

      // PRIORITY 6: Add visual indicator for evidence nodes
      if (isEvidence && !isComparator) {
        ctx.strokeStyle = '#059669'; // Emerald border for evidence
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Draw label
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // PRIORITY 4: Lighter text for comparators
      if (isComparator) {
        ctx.fillStyle = '#94A3B8';
        ctx.globalAlpha = 0.5;
      } else {
        ctx.fillStyle = '#1E293B';
        ctx.globalAlpha = 1.0;
      }

      ctx.fillText(label, node.x, node.y + nodeSize + fontSize);
      ctx.globalAlpha = 1.0;
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

  // Zoom to fit on mount
  useEffect(() => {
    if (graphRef.current && nodes.length > 0) {
      setTimeout(() => {
        graphRef.current.zoomToFit(400, 50);
      }, 100);
    }
  }, [nodes.length]);

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
        onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
        backgroundColor="#F8FAFC"
        linkColor={() => '#CBD5E1'}
        d3VelocityDecay={0.3}
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
