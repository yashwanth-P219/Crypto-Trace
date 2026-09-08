import React, { useState, useEffect, useMemo } from 'react';
import {
  Network, Search, ZoomIn, ZoomOut, Maximize2, ArrowRight,
  ExternalLink, Copy, Check, AlertTriangle, ArrowDownLeft, ArrowUpRight,
  RefreshCw, Layers, GitFork, Users, Filter, Compass, ChevronRight, Shield
} from 'lucide-react';
import { api } from '../services/api';
import {
  Phase4GraphResponse,
  Phase4GraphNode,
  Phase4GraphEdge,
  Phase4CounterpartiesResponse,
  Phase4PathDiscoveryResponse
} from '../types';

interface GraphExplorerProps {
  initialAddress?: string;
  onInspectWallet?: (address: string) => void;
}

const SAMPLE_WALLETS = [
  { address: '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97', label: 'Suspect Intake (Wallet A)' },
  { address: '0x1db3439a222c519ab44bb1144fc23cc742106cf2', label: 'Peeling Hub (Wallet B)' },
  { address: '0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852', label: 'Money Mule (Wallet F)' },
  { address: '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', label: 'Consolidator (Wallet G)' },
  { address: '0x28c6c06298d514db089934071355e5743bf21d60', label: 'Binance 14 Hot Wallet (VASP)' },
  { address: '0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5', label: 'Victim (Rahul Sharma)' }
];

export const getNodeVisuals = (node: Phase4GraphNode) => {
  const isRoot = node.is_root;
  const etype = (node.entity_type || '').toUpperCase();
  const ename = (node.entity_name || node.label || '').toLowerCase();
  const rawAddr = (node.address || '').toLowerCase();

  if (isRoot || ename.includes('suspect') || etype === 'SCAM' || rawAddr === '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97') {
    return {
      category: 'SUSPECT INTAKE',
      title: node.entity_name || 'Suspect Intake (Wallet A)',
      circleFill: 'fill-red-100',
      circleStroke: 'stroke-red-600',
      textColor: '#dc2626',
      badgeBg: 'bg-red-50 border-red-200 text-red-700',
      dotColor: 'bg-red-600',
      tag: 'SUSPECT',
      emoji: '🎯'
    };
  }
  if (etype === 'VASP' || ename.includes('binance') || ename.includes('exchange') || ename.includes('vasp') || ename.includes('hot wallet') || rawAddr === '0x28c6c06298d514db089934071355e5743bf21d60') {
    return {
      category: 'IDENTIFIED VASP / EXCHANGE',
      title: node.entity_name || 'Binance 14 (Hot Wallet)',
      circleFill: 'fill-emerald-100',
      circleStroke: 'stroke-emerald-600',
      textColor: '#16a34a',
      badgeBg: 'bg-emerald-50 border-emerald-200 text-emerald-700',
      dotColor: 'bg-emerald-600',
      tag: 'VASP / EXCHANGE',
      emoji: '🏦'
    };
  }
  if (ename.includes('victim') || ename.includes('rahul') || rawAddr === '0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5') {
    return {
      category: 'VICTIM / COMPLAINANT',
      title: node.entity_name || 'Rahul Sharma (Victim Wallet)',
      circleFill: 'fill-blue-100',
      circleStroke: 'stroke-blue-600',
      textColor: '#2563eb',
      badgeBg: 'bg-blue-50 border-blue-200 text-blue-700',
      dotColor: 'bg-blue-600',
      tag: 'VICTIM',
      emoji: '👤'
    };
  }
  if (ename.includes('mule') || ename.includes('split') || ename.includes('layering') || ename.includes('transit') || rawAddr === '0x1db3439a222c519ab44bb1144fc23cc742106cf2' || rawAddr === '0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852' || rawAddr === '0x7a250d5630b4cf539739df2c5dacb4c659f2488d') {
    return {
      category: 'MONEY MULE / LAYERING',
      title: node.entity_name || (rawAddr === '0x1db3439a222c519ab44bb1144fc23cc742106cf2' ? 'Fund Splitting Hub (Wallet B)' : rawAddr === '0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852' ? 'Money Mule Transit (Wallet F)' : 'Suspect Layering Hub (Wallet G)'),
      circleFill: 'fill-amber-100',
      circleStroke: 'stroke-amber-600',
      textColor: '#d97706',
      badgeBg: 'bg-amber-50 border-amber-200 text-amber-800',
      dotColor: 'bg-amber-600',
      tag: 'MULE / TRANSIT',
      emoji: '🔄'
    };
  }
  return {
    category: 'INTERMEDIARY TRANSIT',
    title: node.entity_name || (node.hops_from_root ? `Hop ${node.hops_from_root} Address` : 'Counterparty'),
    circleFill: 'fill-slate-100',
    circleStroke: 'stroke-slate-400',
    textColor: '#475569',
    badgeBg: 'bg-slate-100 border-slate-200 text-slate-700',
    dotColor: 'bg-slate-500',
    tag: `H${node.hops_from_root ?? 1}`,
    emoji: `H${node.hops_from_root ?? 1}`
  };
};

export const GraphExplorer: React.FC<GraphExplorerProps> = ({
  initialAddress = '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97',
  onInspectWallet
}) => {
  const [address, setAddress] = useState<string>(initialAddress);
  const [activeMode, setActiveMode] = useState<'wallet' | 'case'>('wallet');
  const [caseId, setCaseId] = useState<string>('CASE-SIH2026-001');
  const [maxHops, setMaxHops] = useState<number>(3);
  const [direction, setDirection] = useState<'both' | 'outgoing' | 'incoming'>('both');
  const [minValue, setMinValue] = useState<string>('');

  const [graphData, setGraphData] = useState<Phase4GraphResponse | null>(null);
  const [counterparties, setCounterparties] = useState<Phase4CounterpartiesResponse | null>(null);
  const [pathData, setPathData] = useState<Phase4PathDiscoveryResponse | null>(null);

  const [activeTab, setActiveTab] = useState<'graph' | 'counterparties' | 'paths'>('graph');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<Phase4GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Phase4GraphEdge | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const handleFetchGraph = async () => {
    const targetAddr = address.trim();
    if (activeMode === 'wallet' && (!targetAddr || !targetAddr.startsWith('0x'))) {
      setError('Please provide a valid Ethereum wallet address starting with 0x.');
      return;
    }
    if (activeMode === 'case' && !caseId.trim()) {
      setError('Please provide a valid Case ID.');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setSelectedEdge(null);

    const minValNum = minValue.trim() ? parseFloat(minValue) : undefined;

    try {
      if (activeMode === 'wallet') {
        const [graphRes, cpRes, pathsRes] = await Promise.all([
          api.getWalletGraph(targetAddr, {
            max_hops: maxHops,
            direction,
            min_value: minValNum
          }),
          api.getWalletCounterparties(targetAddr).catch(() => null),
          api.getWalletPaths(targetAddr, {
            max_hops: maxHops,
            direction,
            min_value: minValNum
          }).catch(() => null)
        ]);

        setGraphData(graphRes);
        setCounterparties(cpRes);
        setPathData(pathsRes);
      } else {
        const caseRes = await api.getCaseGraphPhase4(caseId.trim(), {
          max_hops: maxHops,
          direction,
          min_value: minValNum
        });
        setGraphData(caseRes);
        setCounterparties(null);
        setPathData(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate transaction graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialAddress) {
      setAddress(initialAddress);
      handleFetchGraph();
    }
  }, [initialAddress]);

  // Compute 2D node coordinates using column-based multi-hop hierarchical layout
  const layout = useMemo(() => {
    if (!graphData || !graphData.nodes.length) {
      return { nodes: [], edges: [], width: 960, height: 540 };
    }

    const width = 1020;
    const height = 560;
    const paddingX = 90;
    const paddingY = 70;

    // Group nodes by hop distance from root
    const groups: { [hop: number]: Phase4GraphNode[] } = {};
    graphData.nodes.forEach((n) => {
      const h = n.hops_from_root ?? (n.is_root ? 0 : 1);
      if (!groups[h]) groups[h] = [];
      groups[h].push(n);
    });

    const hopKeys = Object.keys(groups).map(Number).sort((a, b) => a - b);
    const colWidth = (width - paddingX * 2) / Math.max(hopKeys.length - 1, 1);

    const nodeCoords: { [id: string]: { x: number; y: number; node: Phase4GraphNode } } = {};

    hopKeys.forEach((hop, colIdx) => {
      const colNodes = groups[hop];
      const x = paddingX + colIdx * colWidth;
      const rowHeight = (height - paddingY * 2) / Math.max(colNodes.length, 1);

      colNodes.forEach((node, rowIdx) => {
        const y = paddingY + rowIdx * rowHeight + rowHeight / 2;
        nodeCoords[node.id.toLowerCase()] = { x, y, node };
      });
    });

    return {
      nodes: Object.values(nodeCoords),
      edges: graphData.edges,
      width,
      height
    };
  }, [graphData]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#1E293B] tracking-wide flex items-center gap-2">
              <Network className="w-6 h-6 text-[#2563EB]" />
              Multi-Hop Transaction Graph & Money Trail
            </h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              GRAPH ENGINE
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Trace fund flows from victim-reported suspect wallets across 1 to 5 hops with directed NetworkX graph analytics
          </p>
        </div>

        {/* Quick switch between Wallet and Case modes */}
        <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 rounded-lg p-1">
          <button
            onClick={() => setActiveMode('wallet')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeMode === 'wallet'
                ? 'bg-[#2563EB] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Wallet Focus
          </button>
          <button
            onClick={() => setActiveMode('case')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeMode === 'case'
                ? 'bg-[#2563EB] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Case Focus
          </button>
        </div>
      </div>

      {/* Control / Query Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          {activeMode === 'wallet' ? (
            <div className="md:col-span-5 space-y-1">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
                <Search className="w-3.5 h-3.5 text-[#2563EB]" />
                Root Suspect / Target Wallet Address
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="0x..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-[#1E293B] placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
              />
            </div>
          ) : (
            <div className="md:col-span-5 space-y-1">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-[#2563EB]" />
                Case Identifier
              </label>
              <input
                type="text"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                placeholder="CASE-2026-001"
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-[#1E293B] placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
              />
            </div>
          )}

          {/* Hop Depth Selector */}
          <div className="md:col-span-2 space-y-1">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-[#2563EB]" />
              Hop Depth
            </label>
            <select
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:bg-white focus:border-blue-500"
            >
              <option value={1}>1 Hop (Direct)</option>
              <option value={2}>2 Hops (Intermediary)</option>
              <option value={3}>3 Hops (Default)</option>
              <option value={5}>5 Hops (Deep Trace)</option>
            </select>
          </div>

          {/* Direction Filter */}
          <div className="md:col-span-2 space-y-1">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
              <GitFork className="w-3.5 h-3.5 text-[#2563EB]" />
              Flow Direction
            </label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as any)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:bg-white focus:border-blue-500"
            >
              <option value="both">Both Directions</option>
              <option value="outgoing">Outgoing (Forward)</option>
              <option value="incoming">Incoming (Backwards)</option>
            </select>
          </div>

          {/* Min Value (ETH) Filter */}
          <div className="md:col-span-1 space-y-1">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-[#2563EB]" />
              Min ETH
            </label>
            <input
              type="number"
              step="any"
              value={minValue}
              onChange={(e) => setMinValue(e.target.value)}
              placeholder="0.0"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-[#1E293B] placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
            />
          </div>

          {/* Trace Button */}
          <div className="md:col-span-2">
            <button
              onClick={handleFetchGraph}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-[#2563EB] hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg text-xs shadow-sm transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Tracing Funds...</span>
                </>
              ) : (
                <>
                  <Compass className="w-4 h-4" />
                  <span>Trace Funds</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick sample wallets chips */}
        {activeMode === 'wallet' && (
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-200 text-xs">
            <span className="text-slate-500 font-medium">Quick Select:</span>
            {SAMPLE_WALLETS.map((item) => (
              <button
                key={item.address}
                onClick={() => {
                  setAddress(item.address);
                }}
                className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-mono text-[11px] transition-colors"
              >
                {item.label} ({item.address.slice(0, 6)}...{item.address.slice(-4)})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700 text-xs">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Truncation Warning */}
      {graphData?.is_truncated && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center gap-3 text-amber-800 text-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>{graphData.warning || 'Graph result exceeds maximum rendering limits and was truncated for clarity.'}</span>
        </div>
      )}

      {/* Statistics Cards */}
      {graphData?.statistics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Wallets</span>
            <p className="text-lg font-extrabold text-[#1E293B] mt-1 font-mono">
              {graphData.statistics.connected_wallets_count}
            </p>
            <span className="text-[10px] text-slate-400">Nodes in graph</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Transactions</span>
            <p className="text-lg font-extrabold text-blue-600 mt-1 font-mono">
              {graphData.statistics.transaction_count}
            </p>
            <span className="text-[10px] text-slate-400">Directed edges</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Inflow</span>
            <p className="text-lg font-extrabold text-emerald-700 mt-1 font-mono">
              {graphData.statistics.total_incoming_value_eth.toFixed(4)}
            </p>
            <span className="text-[10px] text-slate-400">ETH received</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Outflow</span>
            <p className="text-lg font-extrabold text-red-700 mt-1 font-mono">
              {graphData.statistics.total_outgoing_value_eth.toFixed(4)}
            </p>
            <span className="text-[10px] text-slate-400">ETH transferred</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Max Hop</span>
            <p className="text-lg font-extrabold text-amber-700 mt-1 font-mono">
              {graphData.statistics.max_hop_reached}
            </p>
            <span className="text-[10px] text-slate-400">Of {maxHops} queried</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Counterparties</span>
            <p className="text-lg font-extrabold text-blue-700 mt-1 font-mono">
              {graphData.statistics.unique_counterparties}
            </p>
            <span className="text-[10px] text-slate-400">Unique wallets</span>
          </div>
        </div>
      )}

      {/* Main Tabs */}
      <div className="border-b border-slate-200 flex items-center gap-4">
        <button
          onClick={() => setActiveTab('graph')}
          className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'graph'
              ? 'border-[#2563EB] text-[#2563EB]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Network className="w-4 h-4" />
          <span>Interactive Graph Canvas</span>
        </button>

        {activeMode === 'wallet' && (
          <>
            <button
              onClick={() => setActiveTab('counterparties')}
              className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'counterparties'
                  ? 'border-[#2563EB] text-[#2563EB]'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Direct Counterparties ({counterparties?.total_unique_counterparties ?? 0})</span>
            </button>

            <button
              onClick={() => setActiveTab('paths')}
              className={`pb-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === 'paths'
                  ? 'border-[#2563EB] text-[#2563EB]'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <GitFork className="w-4 h-4" />
              <span>Discovered Paths ({pathData?.total_paths ?? 0})</span>
            </button>
          </>
        )}
      </div>

      {/* Tab 1: Interactive Graph Canvas */}
      {activeTab === 'graph' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col space-y-3 shadow-sm">
          {/* Canvas Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Network Visualization
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600">
                {layout.nodes.length} Nodes • {layout.edges.length} Edges
              </span>
            </div>

            {/* Interactive Visual Category Legend */}
            <div className="flex flex-wrap items-center gap-2.5 text-[11px] font-mono bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-600 shadow-xs"></span>
                <span className="text-red-700 font-bold">Suspect Intake</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shadow-xs"></span>
                <span className="text-emerald-700 font-bold">Identified VASP</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-xs"></span>
                <span className="text-amber-800 font-bold">Mule / Peeling</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600 shadow-xs"></span>
                <span className="text-blue-700 font-bold">Victim</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
                <span className="text-slate-600 font-bold">Transit Node</span>
              </div>
            </div>

            <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 rounded-lg p-0.5">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.15))}
                className="p-1 text-slate-600 hover:text-slate-900 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-[11px] font-mono font-bold text-slate-600 px-1.5">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(2.0, z + 0.15))}
                className="p-1 text-slate-600 hover:text-slate-900 rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={() => setZoomLevel(1)}
                className="p-1 text-slate-600 hover:text-slate-900 rounded"
                title="Reset Zoom"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* SVG Canvas */}
          <div className="relative overflow-hidden w-full h-[540px] bg-[#F8FAFC] rounded-xl border border-slate-200 flex items-center justify-center">
            {!graphData || !layout.nodes.length ? (
              <div className="text-center text-slate-400">
                <Network className="w-10 h-10 mx-auto mb-2 opacity-40 animate-pulse text-[#2563EB]" />
                <p className="text-sm font-medium text-slate-600">No transactions found for the specified wallet and filters.</p>
                <p className="text-xs text-slate-400 mt-1">Try synchronizing on-chain transactions or select a different wallet address.</p>
              </div>
            ) : (
              <svg
                className="w-full h-full cursor-grab active:cursor-grabbing transition-transform duration-150"
                viewBox={`0 0 ${layout.width} ${layout.height}`}
                style={{ transform: `scale(${zoomLevel})` }}
              >
                <defs>
                  <marker
                    id="arrowhead-phase4"
                    markerWidth="8"
                    markerHeight="6"
                    refX="22"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#2563eb" opacity="0.85" />
                  </marker>
                  <marker
                    id="arrowhead-phase4-selected"
                    markerWidth="8"
                    markerHeight="6"
                    refX="22"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#1d4ed8" />
                  </marker>
                </defs>

                {/* Render Edges */}
                {layout.edges.map((edge) => {
                  const srcCoord = layout.nodes.find(
                    (n) => n.node.address.toLowerCase() === edge.from_address.toLowerCase()
                  );
                  const tgtCoord = layout.nodes.find(
                    (n) => n.node.address.toLowerCase() === edge.to_address.toLowerCase()
                  );
                  if (!srcCoord || !tgtCoord) return null;

                  const isEdgeSelected = selectedEdge?.tx_hash === edge.tx_hash;

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
                        stroke={isEdgeSelected ? '#1d4ed8' : '#94a3b8'}
                        strokeWidth={isEdgeSelected ? 3 : 1.75}
                        markerEnd={isEdgeSelected ? 'url(#arrowhead-phase4-selected)' : 'url(#arrowhead-phase4)'}
                        className="transition-all hover:stroke-blue-600 hover:stroke-width-3"
                      />
                      {/* Midpoint value badge */}
                      <rect
                        x={(srcCoord.x + tgtCoord.x) / 2 - 28}
                        y={(srcCoord.y + tgtCoord.y) / 2 - 10}
                        width="56"
                        height="18"
                        rx="4"
                        fill="#ffffff"
                        stroke={isEdgeSelected ? '#2563eb' : '#cbd5e1'}
                        strokeWidth="1"
                      />
                      <text
                        x={(srcCoord.x + tgtCoord.x) / 2}
                        y={(srcCoord.y + tgtCoord.y) / 2 + 3}
                        textAnchor="middle"
                        fill="#1e293b"
                        fontSize="9.5"
                        fontFamily="JetBrains Mono"
                        fontWeight="600"
                      >
                        {edge.value_eth > 0 ? `${edge.value_eth.toFixed(3)} Ξ` : '0 Ξ'}
                      </text>
                    </g>
                  );
                })}

                {/* Render Nodes */}
                {layout.nodes.map(({ x, y, node }) => {
                  const isNodeSelected = selectedNode?.id.toLowerCase() === node.id.toLowerCase();
                  const isRoot = node.is_root;
                  const vis = getNodeVisuals(node);
                  const isVasp = vis.category.includes('VASP');

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
                      {/* Pulse effect for root node or VASP node */}
                      {(isRoot || isVasp) && (
                        <circle
                          r="28"
                          className={`animate-ping opacity-25 ${isRoot ? 'fill-red-400' : 'fill-emerald-400'}`}
                        />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r={isNodeSelected ? 24 : 20}
                        className={`${vis.circleFill} ${vis.circleStroke} ${
                          isNodeSelected ? 'stroke-[3.5px]' : 'stroke-2'
                        } transition-all group-hover:scale-110 shadow-sm`}
                      />

                      {/* Hop Badge or Emoji inside circle */}
                      <text
                        textAnchor="middle"
                        y="5"
                        fill="#1e293b"
                        fontSize="11"
                        fontWeight="700"
                        className="pointer-events-none font-mono"
                      >
                        {vis.emoji}
                      </text>

                      {/* Category Tag pill above circle */}
                      <rect
                        x="-26"
                        y="-34"
                        width="52"
                        height="14"
                        rx="3"
                        fill="#ffffff"
                        stroke={vis.textColor}
                        strokeWidth="1"
                      />
                      <text
                        y="-23"
                        textAnchor="middle"
                        fill={vis.textColor}
                        fontSize="8"
                        fontWeight="800"
                        className="pointer-events-none font-mono uppercase tracking-wider"
                      >
                        {vis.tag}
                      </text>

                      {/* Node Entity Name (if available) underneath */}
                      {node.entity_name && (
                        <text
                          y="35"
                          textAnchor="middle"
                          fill={vis.textColor}
                          fontSize="10.5"
                          fontWeight="700"
                          className="pointer-events-none font-sans"
                        >
                          {node.entity_name.length > 20 ? node.entity_name.slice(0, 18) + '...' : node.entity_name}
                        </text>
                      )}

                      {/* Short Address underneath */}
                      <text
                        y={node.entity_name ? "48" : "34"}
                        textAnchor="middle"
                        fill="#475569"
                        fontSize="9.5"
                        fontWeight="600"
                        className="pointer-events-none font-mono"
                      >
                        {node.address.slice(0, 6)}...{node.address.slice(-4)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            )}

            {/* Comprehensive Color Legend */}
            <div className="absolute bottom-3 left-3 bg-white/95 border border-slate-200 rounded-xl p-3 text-[10px] space-y-1.5 backdrop-blur-md shadow-md max-w-xs text-slate-700">
              <p className="font-extrabold text-slate-700 uppercase tracking-wider pb-1 border-b border-slate-200">
                Forensic Graph Color Legend
              </p>
              <div className="grid grid-cols-1 gap-1 font-mono">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-600 shrink-0" />
                  <span className="text-red-700 font-bold">🔴 Suspect / Scam Intake</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0" />
                  <span className="text-emerald-700 font-bold">🟢 Identified VASP / Exchange</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
                  <span className="text-amber-800 font-bold">🟡 Money Mule / Peeling Hub</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0" />
                  <span className="text-blue-700 font-bold">🔵 Victim / Complainant</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-400 shrink-0" />
                  <span className="text-slate-600">⚪ Intermediary Hop Address</span>
                </div>
                <div className="flex items-center gap-2 pt-0.5 border-t border-slate-200">
                  <span className="w-4 h-0.5 bg-blue-600 shrink-0" />
                  <span className="text-slate-500">Directed Transfer Flow (ETH)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Node Drawer */}
          {selectedNode && (() => {
            const selectedVis = getNodeVisuals(selectedNode);
            return (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-4 animate-in fade-in duration-200 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl border text-xl flex items-center justify-center ${selectedVis.badgeBg}`}>
                    {selectedVis.emoji}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-[#1E293B] font-sans">
                        {selectedVis.title}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${selectedVis.badgeBg}`}>
                        {selectedVis.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-slate-700 font-mono">
                        {selectedNode.address}
                      </span>
                      <button
                        onClick={() => handleCopy(selectedNode.address)}
                        className="text-slate-400 hover:text-slate-700 transition-colors"
                        title="Copy Address"
                      >
                        {copiedText === selectedNode.address ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                      <a
                        href={`https://sepolia.etherscan.io/address/${selectedNode.address}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-slate-400 hover:text-blue-600 transition-colors"
                        title="View on Sepolia Etherscan"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {selectedNode.is_root ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
                          ROOT SUSPECT WALLET
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                          HOP {selectedNode.hops_from_root}
                        </span>
                      )}
                      <span className="text-[10px] text-slate-500 font-mono">
                        {selectedNode.transaction_count} transactions recorded
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-5 text-xs font-mono">
                  <div>
                    <p className="text-[10px] text-slate-500 font-sans uppercase">Total Inflow</p>
                    <p className="font-bold text-emerald-700">+{selectedNode.total_incoming_value.toFixed(4)} ETH</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 font-sans uppercase">Total Outflow</p>
                    <p className="font-bold text-red-700">-{selectedNode.total_outgoing_value.toFixed(4)} ETH</p>
                  </div>
                  {onInspectWallet && (
                    <button
                      onClick={() => onInspectWallet(selectedNode.address)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2563EB] hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition-all font-sans cursor-pointer"
                    >
                      <span>Inspect Wallet</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setAddress(selectedNode.address);
                      handleFetchGraph();
                    }}
                    className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-bold transition-all font-sans cursor-pointer shadow-xs"
                  >
                    Pivot As Root
                  </button>
                </div>
              </div>
            );
          })()}

          {/* Edge Drawer */}
          {selectedEdge && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-4 animate-in fade-in duration-200 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-[#2563EB]">
                  <ExternalLink className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[#1E293B]">
                      Transfer: {selectedEdge.value_eth} ETH
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {selectedEdge.direction.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-600 mt-0.5 flex items-center gap-1.5">
                    Hash: {selectedEdge.tx_hash.slice(0, 14)}...{selectedEdge.tx_hash.slice(-8)}
                    <button
                      onClick={() => handleCopy(selectedEdge.tx_hash)}
                      className="hover:text-slate-900 transition-colors"
                      title="Copy transaction hash"
                    >
                      {copiedText === selectedEdge.tx_hash ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </button>
                    <a
                      href={`https://sepolia.etherscan.io/tx/${selectedEdge.tx_hash}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-blue-600 transition-colors"
                      title="View on Sepolia Etherscan"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6 text-xs font-mono">
                <div>
                  <p className="text-[10px] text-slate-500 font-sans uppercase">Sender</p>
                  <p className="text-slate-700">{selectedEdge.from_address.slice(0, 8)}...</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 font-sans uppercase">Receiver</p>
                  <p className="text-slate-700">{selectedEdge.to_address.slice(0, 8)}...</p>
                </div>
                {selectedEdge.block_number && (
                  <div>
                    <p className="text-[10px] text-slate-500 font-sans uppercase">Block</p>
                    <p className="text-slate-700">#{selectedEdge.block_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Direct Counterparties */}
      {activeTab === 'counterparties' && counterparties && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Incoming Counterparties */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <span className="text-xs font-bold text-emerald-700 flex items-center gap-1.5 uppercase tracking-wider">
                <ArrowDownLeft className="w-4 h-4" />
                Incoming Counterparties ({counterparties.incoming.length})
              </span>
            </div>
            {counterparties.incoming.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No incoming counterparties found.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {counterparties.incoming.map((cp) => (
                  <div
                    key={cp.address}
                    className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 hover:border-slate-300 flex items-center justify-between text-xs transition-colors"
                  >
                    <div>
                      <p className="font-mono text-slate-800 font-bold">
                        {cp.address.slice(0, 10)}...{cp.address.slice(-6)}
                      </p>
                      <p className="text-[10px] text-slate-500 font-sans">
                        {cp.transaction_count} transaction{cp.transaction_count > 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="text-right font-mono">
                      <p className="text-emerald-700 font-bold">+{cp.total_value_eth.toFixed(4)} ETH</p>
                      {cp.latest_block && (
                        <p className="text-[10px] text-slate-500 font-sans">Block #{cp.latest_block}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Outgoing Counterparties */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <span className="text-xs font-bold text-red-700 flex items-center gap-1.5 uppercase tracking-wider">
                <ArrowUpRight className="w-4 h-4" />
                Outgoing Counterparties ({counterparties.outgoing.length})
              </span>
            </div>
            {counterparties.outgoing.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No outgoing counterparties found.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {counterparties.outgoing.map((cp) => (
                  <div
                    key={cp.address}
                    className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 hover:border-slate-300 flex items-center justify-between text-xs transition-colors"
                  >
                    <div>
                      <p className="font-mono text-slate-800 font-bold">
                        {cp.address.slice(0, 10)}...{cp.address.slice(-6)}
                      </p>
                      <p className="text-[10px] text-slate-500 font-sans">
                        {cp.transaction_count} transaction{cp.transaction_count > 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="text-right font-mono">
                      <p className="text-red-700 font-bold">-{cp.total_value_eth.toFixed(4)} ETH</p>
                      {cp.latest_block && (
                        <p className="text-[10px] text-slate-500 font-sans">Block #{cp.latest_block}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Discovered Paths */}
      {activeTab === 'paths' && pathData && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
              <GitFork className="w-4 h-4 text-[#2563EB]" />
              Discovered Multi-Hop Fund Transfer Paths ({pathData.total_paths})
            </span>
          </div>

          {pathData.paths.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No multi-hop flow paths discovered within {pathData.max_hops} hops for this direction.
            </p>
          ) : (
            <div className="space-y-3">
              {pathData.paths.map((p, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2 shadow-xs"
                >
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span className="font-bold text-blue-700">Path #{idx + 1}</span>
                    <span>{p.length - 1} Hop{p.length - 1 > 1 ? 's' : ''}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
                    {p.map((nodeAddr, nIdx) => (
                      <React.Fragment key={nIdx}>
                        <span
                          className={`px-2 py-1 rounded border font-semibold ${
                            nIdx === 0
                              ? 'bg-red-50 border-red-200 text-red-700'
                              : nIdx === p.length - 1
                              ? 'bg-blue-50 border-blue-200 text-blue-700'
                              : 'bg-white border-slate-200 text-slate-700'
                          }`}
                        >
                          {nodeAddr.slice(0, 6)}...{nodeAddr.slice(-4)}
                        </span>
                        {nIdx < p.length - 1 && (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
