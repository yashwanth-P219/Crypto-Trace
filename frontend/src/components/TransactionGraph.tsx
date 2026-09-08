import React, { useState, useMemo } from 'react';
import {
  Maximize2, ZoomIn, ZoomOut, Filter, ShieldAlert,
  Building2, ArrowRight, ExternalLink, Info, Copy, Check
} from 'lucide-react';
import { SubgraphData, GraphNode, GraphEdge } from '../types';
import { TruthBadge } from './TruthBadge';

interface TransactionGraphProps {
  data: SubgraphData | null;
  selectedHop: number;
  onHopChange: (hops: number) => void;
  suspiciousOnly: boolean;
  onToggleSuspiciousOnly: () => void;
  onInspectWallet?: (address: string) => void;
}

export const TransactionGraph: React.FC<TransactionGraphProps> = ({
  data,
  selectedHop,
  onHopChange,
  suspiciousOnly,
  onToggleSuspiciousOnly,
  onInspectWallet
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  // Compute node coordinates dynamically using multi-tier hierarchical layout
  const layout = useMemo(() => {
    if (!data || !data.nodes.length) return { nodes: [], edges: [], width: 900, height: 500 };

    const width = 960;
    const height = 520;
    const paddingX = 80;
    const paddingY = 60;

    // Group nodes by hops from source
    const groups: { [hop: number]: GraphNode[] } = {};
    data.nodes.forEach((n) => {
      const h = n.hops_from_source === 999 ? 1 : n.hops_from_source;
      if (!groups[h]) groups[h] = [];
      groups[h].push(n);
    });

    const maxHop = Math.max(...Object.keys(groups).map(Number), 1);
    const hopKeys = Object.keys(groups).map(Number).sort((a, b) => a - b);
    const colWidth = (width - paddingX * 2) / Math.max(hopKeys.length - 1, 1);

    const nodeCoords: { [id: string]: { x: number; y: number; node: GraphNode } } = {};

    hopKeys.forEach((hop, colIdx) => {
      const colNodes = groups[hop];
      const x = paddingX + colIdx * colWidth;
      const rowHeight = (height - paddingY * 2) / Math.max(colNodes.length, 1);

      colNodes.forEach((node, rowIdx) => {
        const y = paddingY + rowIdx * rowHeight + rowHeight / 2;
        nodeCoords[node.id] = { x, y, node };
      });
    });

    return {
      nodes: Object.values(nodeCoords),
      edges: data.edges,
      width,
      height
    };
  }, [data]);

  const getNodeColor = (node: GraphNode) => {
    if (node.is_source) return 'fill-red-100 stroke-[#DC2626] text-red-700';
    if (node.entity_type === 'VASP' || node.entity_type === 'EXCHANGE') {
      return 'fill-amber-100 stroke-[#F59E0B] text-amber-700';
    }
    if (node.entity_type === 'MIXER') {
      return 'fill-purple-100 stroke-purple-600 text-purple-700';
    }
    if (node.entity_type === 'BRIDGE') {
      return 'fill-sky-100 stroke-sky-600 text-sky-700';
    }
    return 'fill-blue-50 stroke-[#2563EB] text-blue-700';
  };

  return (
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4 relative flex flex-col">
      {/* Graph Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Hop Depth:
            </span>
            {[1, 2, 3, 5].map((hop) => (
              <button
                key={hop}
                onClick={() => onHopChange(hop)}
                className={`px-2.5 py-1 text-xs font-bold rounded-md transition-all ${
                  selectedHop === hop
                    ? 'bg-[#2563EB] text-white shadow-sm'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
                }`}
              >
                {hop} Hop{hop > 1 ? 's' : ''}
              </button>
            ))}
          </div>

          <button
            onClick={onToggleSuspiciousOnly}
            className={`flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-lg border transition-all ${
              suspiciousOnly
                ? 'bg-red-50 border-red-200 text-red-700 shadow-sm'
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
            <span>Show Suspicious Paths Only</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <TruthBadge category="BLOCKCHAIN FACT" size="sm" />
          <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 rounded-lg p-0.5">
            <button
              onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.15))}
              className="p-1 text-slate-600 hover:text-slate-900 rounded"
              title="Zoom out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[10px] font-mono font-bold text-slate-600 px-1">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={() => setZoomLevel((z) => Math.min(1.8, z + 0.15))}
              className="p-1 text-slate-600 hover:text-slate-900 rounded"
              title="Zoom in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoomLevel(1)}
              className="p-1 text-slate-600 hover:text-slate-900 rounded"
              title="Reset Zoom"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="relative overflow-hidden w-full h-[520px] bg-[#F8FAFC] rounded-xl my-3 border border-slate-200 flex items-center justify-center">
        {!data || !data.nodes.length ? (
          <div className="text-center text-slate-500">
            <Info className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No transaction graph data available for this view.</p>
          </div>
        ) : (
          <svg
            className="w-full h-full cursor-grab active:cursor-grabbing transition-transform duration-150"
            viewBox={`0 0 ${layout.width} ${layout.height}`}
            style={{ transform: `scale(${zoomLevel})` }}
          >
            <defs>
              <marker
                id="arrowhead-normal"
                markerWidth="8"
                markerHeight="6"
                refX="22"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#2563EB" opacity="0.9" />
              </marker>
              <marker
                id="arrowhead-suspicious"
                markerWidth="8"
                markerHeight="6"
                refX="22"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#DC2626" />
              </marker>
            </defs>

            {/* Render Edges */}
            {layout.edges.map((edge) => {
              const srcCoord = layout.nodes.find((n) => n.node.id === edge.source);
              const tgtCoord = layout.nodes.find((n) => n.node.id === edge.target);
              if (!srcCoord || !tgtCoord) return null;

              const isEdgeSelected = selectedEdge?.transaction_hash === edge.transaction_hash;
              const isSuspicious = edge.is_suspicious;

              return (
                <g
                  key={edge.id}
                  className="cursor-pointer group"
                  onClick={() => {
                    setSelectedEdge(edge);
                    setSelectedNode(null);
                  }}
                >
                  <line
                    x1={srcCoord.x}
                    y1={srcCoord.y}
                    x2={tgtCoord.x}
                    y2={tgtCoord.y}
                    stroke={isSuspicious ? '#DC2626' : isEdgeSelected ? '#1D4ED8' : '#64748B'}
                    strokeWidth={isEdgeSelected ? 3 : isSuspicious ? 2.5 : 1.5}
                    strokeDasharray={isSuspicious ? '5,3' : 'none'}
                    markerEnd={isSuspicious ? 'url(#arrowhead-suspicious)' : 'url(#arrowhead-normal)'}
                    className="transition-all hover:stroke-blue-600 hover:stroke-width-3"
                  />
                  {/* Midpoint amount badge */}
                  <rect
                    x={(srcCoord.x + tgtCoord.x) / 2 - 28}
                    y={(srcCoord.y + tgtCoord.y) / 2 - 10}
                    width="56"
                    height="18"
                    rx="4"
                    fill="#FFFFFF"
                    stroke={isSuspicious ? '#DC2626' : '#CBD5E1'}
                    strokeWidth="1"
                    className="shadow-sm"
                  />
                  <text
                    x={(srcCoord.x + tgtCoord.x) / 2}
                    y={(srcCoord.y + tgtCoord.y) / 2 + 3}
                    textAnchor="middle"
                    fill={isSuspicious ? '#DC2626' : '#1E293B'}
                    fontSize="9.5"
                    fontFamily="JetBrains Mono"
                    fontWeight="600"
                  >
                    {edge.amount} ETH
                  </text>
                </g>
              );
            })}

            {/* Render Nodes */}
            {layout.nodes.map(({ x, y, node }) => {
              const isNodeSelected = selectedNode?.id === node.id;
              const colorClass = getNodeColor(node);

              return (
                <g
                  key={node.id}
                  transform={`translate(${x},${y})`}
                  className="cursor-pointer group"
                  onClick={() => {
                    setSelectedNode(node);
                    setSelectedEdge(null);
                  }}
                >
                  {/* Ripple pulse for source / VASP */}
                  {(node.is_source || node.entity_type === 'VASP') && (
                    <circle
                      r="26"
                      className={`animate-ping opacity-25 ${
                        node.is_source ? 'fill-red-500' : 'fill-amber-500'
                      }`}
                    />
                  )}

                  {/* Main Node Circle */}
                  <circle
                    r={isNodeSelected ? 22 : 18}
                    className={`${colorClass} stroke-2 transition-all group-hover:scale-110 shadow-sm`}
                  />

                  {/* Node Label underneath */}
                  <text
                    y="32"
                    textAnchor="middle"
                    fill="#1E293B"
                    fontSize="11"
                    fontWeight="700"
                    className="pointer-events-none"
                  >
                    {node.is_source
                      ? '🎯 Suspect (Wallet A)'
                      : node.entity_type === 'VASP'
                      ? '🏦 ' + node.label
                      : node.label !== 'Unknown Address'
                      ? node.label
                      : `${node.address.slice(0, 6)}...${node.address.slice(-4)}`}
                  </text>

                  <text
                    y="45"
                    textAnchor="middle"
                    fill="#64748B"
                    fontSize="9"
                    fontFamily="JetBrains Mono"
                    className="pointer-events-none"
                  >
                    {node.address.slice(0, 8)}...
                  </text>
                </g>
              );
            })}
          </svg>
        )}

        {/* Legend Overlay */}
        <div className="absolute bottom-3 left-3 bg-white/95 border border-slate-200 rounded-lg p-2.5 text-[10px] space-y-1 shadow-sm backdrop-blur-md">
          <p className="font-bold text-slate-500 uppercase tracking-wider mb-1">Legend</p>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#DC2626]" />
            <span className="text-slate-700 font-medium">Suspect Intake Wallet</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
            <span className="text-slate-700 font-medium">Verified VASP / Exchange</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
            <span className="text-slate-700 font-medium">Intermediary Wallet (Peeling / Mule)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 border-t border-dashed border-red-600" />
            <span className="text-slate-700 font-medium">Flagged Suspicious Edge</span>
          </div>
        </div>
      </div>

      {/* Inspection Drawer (Node or Edge) */}
      {selectedNode && (
        <div className="mt-3 p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-4 animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${
              selectedNode.is_source
                ? 'bg-red-50 border-red-200 text-[#DC2626]'
                : selectedNode.entity_type === 'VASP'
                ? 'bg-amber-50 border-amber-200 text-[#F59E0B]'
                : 'bg-blue-50 border-blue-200 text-[#2563EB]'
            }`}>
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#1E293B]">
                  {selectedNode.label}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
                  {selectedNode.entity_type}
                </span>
                {selectedNode.is_source && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
                    SUSPECT ORIGIN
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-slate-600 mt-0.5 flex items-center gap-1.5">
                {selectedNode.address}
                <button
                  onClick={() => handleCopy(selectedNode.address)}
                  className="hover:text-slate-900"
                  title="Copy address"
                >
                  {copiedText === selectedNode.address ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </button>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono">
            <div>
              <p className="text-[10px] text-slate-500 font-sans uppercase">Total Incoming</p>
              <p className="font-bold text-[#16A34A]">+{selectedNode.total_incoming} ETH</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 font-sans uppercase">Total Outgoing</p>
              <p className="font-bold text-[#DC2626]">-{selectedNode.total_outgoing} ETH</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 font-sans uppercase">Transactions</p>
              <p className="font-bold text-slate-800">{selectedNode.tx_count} indexed</p>
            </div>
            {onInspectWallet && (
              <button
                onClick={() => onInspectWallet(selectedNode.address)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2563EB] hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition-all font-sans"
              >
                <span>Full Deep Trace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {selectedEdge && (
        <div className="mt-3 p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-4 animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-[#2563EB]">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#1E293B]">
                  Transaction: {selectedEdge.amount} ETH
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
                  {selectedEdge.blockchain}
                </span>
                {selectedEdge.is_suspicious && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
                    SUSPICIOUS FLOW
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-slate-600 mt-0.5 flex items-center gap-1.5">
                Hash: {selectedEdge.transaction_hash}
                <button
                  onClick={() => handleCopy(selectedEdge.transaction_hash)}
                  className="hover:text-slate-900"
                  title="Copy transaction hash"
                >
                  {copiedText === selectedEdge.transaction_hash ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </button>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono">
            <div>
              <p className="text-[10px] text-slate-500 font-sans uppercase">Sender</p>
              <p className="text-slate-700">{selectedEdge.source.slice(0, 10)}...</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 font-sans uppercase">Receiver</p>
              <p className="text-slate-700">{selectedEdge.target.slice(0, 10)}...</p>
            </div>
            {selectedEdge.block_number && (
              <div>
                <p className="text-[10px] text-slate-500 font-sans uppercase">Block</p>
                <p className="text-slate-800 font-semibold">#{selectedEdge.block_number}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
