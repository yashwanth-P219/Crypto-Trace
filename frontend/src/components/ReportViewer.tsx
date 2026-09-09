import React, { useState } from 'react';
import { FileText, CheckCircle, XCircle, Download, Printer, Shield, User, Building, AlertTriangle } from 'lucide-react';
import { ReportData, User as UserType } from '../types';
import { TruthBadge } from './TruthBadge';
import { api } from '../services/api';

interface ReportViewerProps {
  report: ReportData;
  currentUser: UserType | null;
  onStatusUpdated: () => void;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  report,
  currentUser,
  onStatusUpdated
}) => {
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const content = report.content_json || {};

  const handleReview = async (status: 'APPROVED' | 'REJECTED') => {
    setSubmitting(true);
    try {
      await api.reviewReport(report.report_id, status, comments || (status === 'APPROVED' ? 'Report approved for VASP subpoena.' : 'Revision required.'));
      onStatusUpdated();
    } catch (err: any) {
      alert(err.message || 'Review submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingCsv, setDownloadingCsv] = useState(false);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      const res = await fetch(api.getReportPdfUrl(report.report_id));
      if (!res.ok) throw new Error('Failed to download PDF');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.report_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Error downloading PDF');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    try {
      const res = await fetch(api.getReportCsvUrl(report.report_id));
      if (!res.ok) throw new Error('Failed to download CSV');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.report_id}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Error downloading CSV');
    } finally {
      setDownloadingCsv(false);
    }
  };

  const handleDownloadJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute('href', dataStr);
    dlAnchor.setAttribute('download', `${report.report_id}.json`);
    dlAnchor.click();
  };

  const isSupervisor = currentUser?.role === 'SUPERVISOR' || currentUser?.role === 'ADMINISTRATOR';

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-6 shadow-sm">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              {report.title}
            </h3>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
              report.status === 'APPROVED'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : report.status === 'REJECTED'
                ? 'bg-red-50 text-red-700 border-red-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}>
              {report.status}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            ID: {report.report_id} • Generated: {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloadingPdf ? 'Generating PDF...' : 'Official PDF Dossier'}</span>
          </button>
          <button
            onClick={handleDownloadCsv}
            disabled={downloadingCsv}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloadingCsv ? 'Exporting...' : 'Export CSV'}</span>
          </button>
          <button
            onClick={handleDownloadJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2563EB] hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Dossier</span>
          </button>
        </div>
      </div>

      {/* Forensic Document Body */}
      <div className="bg-[#F8FAFC] border border-slate-200 rounded-xl p-6 space-y-6 text-xs text-slate-700 shadow-inner">
        {/* Header Block */}
        <div className="border-b border-slate-200 pb-4 flex justify-between items-start">
          <div>
            <p className="text-[10px] uppercase font-bold tracking-widest text-[#2563EB]">
              GOVERNMENT OF INDIA • CYBER CRIME INVESTIGATION WING
            </p>
            <h2 className="text-base font-black text-[#1E293B] mt-1">
              BLOCKCHAIN FORENSIC INTELLIGENCE DOSSIER
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ref Complaint: {content['1_case_information']?.complaint_reference}
            </p>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-red-50 border border-red-200 text-red-700">
              CONFIDENTIAL // LE ONLY
            </span>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Investigator: {content.report_metadata?.investigator?.name}
            </p>
          </div>
        </div>

        {/* Section 1 & 2: Incident Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Victim & Incident Details
            </p>
            <p><strong>Victim:</strong> {content['3_victim_information']?.name}</p>
            <p><strong>Reported Loss:</strong> {content['3_victim_information']?.reported_loss}</p>
            <p><strong>Incident Date:</strong> {new Date(content['2_incident_summary']?.incident_date).toLocaleDateString()}</p>
          </div>
          <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Suspect Intake Target
            </p>
            <p className="font-mono"><strong>Wallet:</strong> {content['4_suspect_wallet']?.address}</p>
            <p><strong>Blockchain:</strong> {content['4_suspect_wallet']?.blockchain}</p>
            <p className="font-mono text-[10px] truncate"><strong>Deposit Tx:</strong> {content['2_incident_summary']?.initial_transaction_hash}</p>
          </div>
        </div>

        {/* Section 6: Verified Money Trail */}
        {content['6_money_trail']?.primary_terminal_path && (
          <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5" />
                Verified Terminal Liquidation Money Trail
              </p>
              <TruthBadge category="BLOCKCHAIN FACT" size="sm" />
            </div>
            <p className="text-xs text-[#1E293B] font-semibold">
              Funds reached liquidation destination <strong className="text-amber-700">{content['6_money_trail']?.primary_terminal_path?.destination_vasp}</strong> ({content['6_money_trail']?.primary_terminal_path?.destination_address}) across {content['6_money_trail']?.primary_terminal_path?.hops} hops.
            </p>

            <div className="space-y-2.5 pt-1">
              {content['6_money_trail']?.primary_terminal_path?.steps?.map((s: any, idx: number) => {
                const totalHops = content['6_money_trail']?.primary_terminal_path?.hops;
                const isVasp = s.is_destination_vasp || (idx === content['6_money_trail']?.primary_terminal_path?.steps?.length - 1 && content['6_money_trail']?.primary_terminal_path?.is_known_vasp);

                return (
                  <div key={idx} className="p-3 rounded-lg bg-white border border-amber-200/80 shadow-xs space-y-2 text-[11px]">
                    {/* Header: Hop index, Block #, Timestamp, Known VASP */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 font-mono font-bold text-[10px]">
                          Hop {s.hop_number || idx + 1} of {s.total_hops || totalHops}
                        </span>
                        {isVasp ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold text-[10px]">
                            Known VASP / Exchange ({s.to_label})
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-[10px]">
                            Unhosted / Intermediary Wallet
                          </span>
                        )}
                      </div>
                      <div className="text-slate-500 font-mono text-[10px] space-x-2">
                        {s.block_number && <span>Block #{s.block_number}</span>}
                        {s.timestamp && <span>• {new Date(s.timestamp).toLocaleString()}</span>}
                      </div>
                    </div>

                    {/* From -> To -> Amount */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
                      <div className="md:col-span-5 font-mono text-[10px]">
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">From Wallet ({s.from_label}):</span>
                        <span className="text-[#1E293B] font-semibold truncate block" title={s.from_address}>{s.from_address}</span>
                      </div>
                      <div className="md:col-span-2 text-center">
                        <span className="font-mono font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {s.amount} ETH
                        </span>
                      </div>
                      <div className="md:col-span-5 font-mono text-[10px]">
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">To Wallet ({s.to_label}):</span>
                        <span className={`font-semibold truncate block ${isVasp ? 'text-amber-800 font-bold' : 'text-[#1E293B]'}`} title={s.to_address}>
                          {s.to_address}
                        </span>
                      </div>
                    </div>

                    {/* Transaction Hash */}
                    <div className="font-mono text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded border border-slate-100 flex items-center justify-between">
                      <span className="truncate">Tx: {s.transaction_hash}</span>
                    </div>

                    {/* Suspicious Indicator */}
                    {s.suspicious_indicator && (
                      <div className="p-1.5 rounded bg-red-50 border border-red-200 text-red-800 text-[10px] font-semibold">
                        ⚠️ Suspicious Indicator: {s.suspicious_indicator}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Section 7 & 8: Behavioral Patterns & Risk */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3.5 rounded-lg bg-white border border-slate-200 space-y-2 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                System Inferred Patterns
              </p>
              <TruthBadge category="SYSTEM INFERENCE" size="sm" />
            </div>
            {content['7_suspicious_patterns_inference']?.map((p: any, idx: number) => (
              <p key={idx} className="text-[11px] text-slate-700">
                • <strong className="text-red-700">{p.type}</strong>: {p.explanation}
              </p>
            ))}
          </div>

          <div className="p-3.5 rounded-lg bg-white border border-slate-200 space-y-2 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                AI Assessment & Score
              </p>
              <TruthBadge category="AI ASSESSMENT" size="sm" />
            </div>
            <p className="text-base font-black font-mono text-[#1E293B]">
              Risk Score: {content['8_ai_risk_assessment']?.score} / 100 ({content['8_ai_risk_assessment']?.level})
            </p>
            <p className="text-[11px] text-slate-500 italic">
              Score derived from rapid fund dispersal, peeling chain structuring, multi-hop depth, and VASP deposit.
            </p>
          </div>
        </div>

        {/* Section 10: Evidence Locker References */}
        <div className="p-3.5 rounded-lg bg-white border border-slate-200 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Chain of Custody & Cryptographic Evidence Locker
            </p>
            <TruthBadge category="INVESTIGATOR DECISION" size="sm" />
          </div>
          {content['10_evidence_locker_references']?.map((ev: any) => (
            <div key={ev.evidence_id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[10px] space-y-0.5">
              <div className="flex justify-between text-blue-700 font-bold">
                <span>{ev.evidence_id} [{ev.tag}]</span>
                <span className="text-[#1E293B]">{ev.amount} ETH</span>
              </div>
              <p className="text-slate-600">Tx: {ev.tx_hash}</p>
              <p className="text-emerald-700 font-semibold">SHA-256: {ev.integrity_hash}</p>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-[10px] text-slate-500 italic border-t border-slate-200 pt-3">
          {content['13_disclaimer']}
        </p>

        {/* Supervisor Sign-Off Box */}
        {report.status === 'APPROVED' ? (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <p className="text-xs font-bold text-[#1E293B]">
                  Report Approved by Supervisor
                </p>
                <p className="text-[11px] text-emerald-800">
                  {report.supervisor_comments || 'Authorized for Section 91 CrPC notice dispatch.'}
                </p>
                <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                  Approved At: {report.approved_at ? new Date(report.approved_at).toLocaleString() : 'Recent'}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-1 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold">
              SEALED DOSSIER
            </span>
          </div>
        ) : isSupervisor && report.status === 'PENDING_REVIEW' ? (
          <div className="p-4 rounded-xl bg-white border border-blue-200 space-y-3 shadow-sm">
            <p className="text-xs font-bold text-blue-800 flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-[#2563EB]" />
              Supervisor Review & Sign-Off Authorization
            </p>
            <textarea
              rows={2}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Enter supervisor review comments, legal statutory orders, or requested revisions..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs text-[#1E293B] focus:bg-white focus:border-blue-500 focus:outline-none"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => handleReview('REJECTED')}
                disabled={submitting}
                className="px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 font-bold border border-red-200 flex items-center gap-1.5 transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject & Request Changes</span>
              </button>
              <button
                onClick={() => handleReview('APPROVED')}
                disabled={submitting}
                className="px-4 py-1.5 rounded-lg bg-[#16A34A] hover:bg-emerald-700 text-white font-bold shadow-sm flex items-center gap-1.5 transition-colors"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Approve & Seal Report</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-xs">
            Status: <span className="font-bold text-amber-700">{report.status}</span> (Awaiting Supervisor Review)
          </div>
        )}
      </div>
    </div>
  );
};
