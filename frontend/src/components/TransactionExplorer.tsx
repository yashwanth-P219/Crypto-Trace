import React, { useState, useEffect } from 'react';
import { 
  Search, RefreshCw, ExternalLink, Copy, Check, ArrowDownLeft, ArrowUpRight, 
  Layers, Database, ShieldAlert, CheckCircle2, XCircle, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

interface TransactionExplorerProps {
  initialAddress?: string;
}

export const TransactionExplorer: React.FC<TransactionExplorerProps> = ({ 
  initialAddress = '0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97'
}) => {
  const [address, setAddress] = useState<string>(initialAddress);
  const [activeAddress, setActiveAddress] = useState<string>(initialAddress);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);
  const [direction, setDirection] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [syncSummary, setSyncSummary] = useState<any | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const fetchTransactions = async (targetAddr: string, p: number, ps: number, dir: string) => {
    if (!targetAddr.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getWalletTransactions(targetAddr.trim(), {
        page: p,
        page_size: ps,
        direction: dir
      });
      setTransactions(data.transactions || []);
      setTotal(data.total || 0);
      setActiveAddress(targetAddr.trim());
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve transactions');
      setTransactions([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions(activeAddress, page, pageSize, direction);
  }, [page, pageSize, direction]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) return;
    setPage(1);
    fetchTransactions(address.trim(), 1, pageSize, direction);
  };

  const handleSync = async () => {
    if (!activeAddress.trim()) return;
    setSyncing(true);
    setSyncSummary(null);
    setError(null);
    try {
      const res = await api.syncWalletTransactions(activeAddress);
      setSyncSummary(res);
      // Reload current view
      await fetchTransactions(activeAddress, page, pageSize, direction);
    } catch (err: any) {
      setError(err.message || 'Failed to sync with Ethereum Sepolia RPC');
    } finally {
      setSyncing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const shortenAddress = (addr: string) => {
    if (!addr || addr.length <= 12) return addr || '—';
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  const shortenHash = (hash: string) => {
    if (!hash || hash.length <= 16) return hash || '—';
    return `${hash.slice(0, 10)}...${hash.slice(-6)}`;
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6">
      {/* Header & Overview Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Layers className="w-5 h-5 text-[#2563EB]" />
              <h2 className="text-lg font-bold text-[#1E293B]">
                On-Chain Transaction Explorer
              </h2>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                CHAIN ID: 11155111
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
                ETHEREUM SEPOLIA
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Query, synchronize, and inspect immutable on-chain transaction records stored in Supabase PostgreSQL.
            </p>
          </div>

          {/* Sync Button */}
          <button
            onClick={handleSync}
            disabled={syncing || loading}
            className="flex items-center gap-2 px-4 py-2 bg-[#2563EB] hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing with Sepolia...' : 'Sync with Sepolia RPC'}
          </button>
        </div>

        {/* Address Search Form */}
        <form onSubmit={handleSearch} className="mt-5 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter suspect or victim Ethereum address (0x...)"
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-[#1E293B] font-mono focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 transition-colors"
          >
            Explore
          </button>
        </form>

        {/* Current Target Meta Bar */}
        <div className="mt-4 pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Inspecting Wallet:</span>
            <span className="font-mono text-blue-700 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              {activeAddress}
            </span>
            <button
              onClick={() => copyToClipboard(activeAddress)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              title="Copy wallet address"
            >
              {copiedHash === activeAddress ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            <a
              href={`https://sepolia.etherscan.io/address/${activeAddress}`}
              target="_blank"
              rel="noreferrer"
              className="text-slate-400 hover:text-blue-600 transition-colors"
              title="View on Etherscan Sepolia"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <div className="flex items-center gap-4 text-slate-600">
            <div>
              <span className="text-slate-500 mr-1">Stored Records:</span>
              <span className="font-bold text-[#1E293B]">{total}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sync Summary Notification */}
      {syncSummary && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between text-xs text-blue-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>
              Sepolia Sync Complete: <strong>{syncSummary.fetched}</strong> fetched, <strong>{syncSummary.inserted}</strong> inserted into PostgreSQL, <strong>{syncSummary.duplicates}</strong> duplicates skipped.
            </span>
          </div>
          <button onClick={() => setSyncSummary(null)} className="text-slate-500 hover:text-slate-800 text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Tabs & Page Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
        {/* Direction Filter */}
        <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-lg border border-slate-200">
          {[
            { id: 'all', label: 'All Transactions' },
            { id: 'incoming', label: 'Incoming Only' },
            { id: 'outgoing', label: 'Outgoing Only' }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => { setDirection(item.id); setPage(1); }}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                direction === item.id
                  ? 'bg-[#2563EB] text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Page Size Selector */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 text-xs focus:outline-none focus:bg-white"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-6 h-6 text-[#2563EB] animate-spin" />
            <p className="text-xs text-slate-500">Retrieving stored transactions from database...</p>
          </div>
        ) : transactions.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3 text-center px-4">
            <Database className="w-10 h-10 text-slate-400" />
            <p className="text-sm font-semibold text-slate-700">No stored transactions found for this wallet</p>
            <p className="text-xs text-slate-500 max-w-md">
              Click the "Sync with Sepolia RPC" button above to query on-chain records from Ethereum Sepolia and persist them into the PostgreSQL database.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Tx Hash</th>
                  <th className="py-3 px-4">Block</th>
                  <th className="py-3 px-4">Direction</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">From</th>
                  <th className="py-3 px-4">To</th>
                  <th className="py-3 px-4">Value (ETH)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {transactions.map((tx) => {
                  const isIncoming = tx.direction === 'incoming';
                  return (
                    <tr key={tx.id || tx.tx_hash} className="hover:bg-slate-50/70 transition-colors">
                      {/* Hash with Copy & Etherscan */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[#2563EB] font-bold" title={tx.tx_hash}>
                            {shortenHash(tx.tx_hash)}
                          </span>
                          <button
                            onClick={() => copyToClipboard(tx.tx_hash)}
                            className="text-slate-400 hover:text-slate-600"
                            title="Copy full transaction hash"
                          >
                            {copiedHash === tx.tx_hash ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                          </button>
                          <a
                            href={`https://sepolia.etherscan.io/tx/${tx.tx_hash}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-400 hover:text-blue-600"
                            title="Open in Sepolia Explorer"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </td>

                      {/* Block */}
                      <td className="py-3 px-4 text-slate-700">
                        {tx.block_number || '—'}
                      </td>

                      {/* Direction */}
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          isIncoming
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                            : 'bg-amber-50 border-amber-200 text-amber-800'
                        }`}>
                          {isIncoming ? (
                            <ArrowDownLeft className="w-2.5 h-2.5 text-emerald-600" />
                          ) : (
                            <ArrowUpRight className="w-2.5 h-2.5 text-amber-600" />
                          )}
                          {tx.direction ? tx.direction.toUpperCase() : 'UNKNOWN'}
                        </span>
                      </td>

                      {/* Type */}
                      <td className="py-3 px-4">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                          {tx.transaction_type || 'native_transfer'}
                        </span>
                      </td>

                      {/* From */}
                      <td className="py-3 px-4">
                        <span className="text-slate-700" title={tx.from_address}>
                          {shortenAddress(tx.from_address)}
                        </span>
                      </td>

                      {/* To */}
                      <td className="py-3 px-4">
                        <span className="text-slate-700" title={tx.to_address}>
                          {shortenAddress(tx.to_address)}
                        </span>
                      </td>

                      {/* Value */}
                      <td className="py-3 px-4 font-bold text-[#1E293B]">
                        {tx.value_eth !== undefined ? `${tx.value_eth.toFixed(4)} ETH` : '0.0000 ETH'}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                          tx.receipt_status === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-red-50 text-red-700 border-red-200'
                        }`}>
                          {tx.receipt_status || 'SUCCESS'}
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {tx.block_timestamp ? new Date(tx.block_timestamp).toLocaleString() : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total transactions)
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1 || loading}
              className="px-3 py-1 bg-white hover:bg-slate-100 disabled:opacity-40 rounded-lg text-slate-700 border border-slate-200 transition-colors cursor-pointer"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages || loading}
              className="px-3 py-1 bg-white hover:bg-slate-100 disabled:opacity-40 rounded-lg text-slate-700 border border-slate-200 transition-colors cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
