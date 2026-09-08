import {
  User, Case, Transaction, SubgraphData, MoneyTrailPath,
  RiskFinding, RiskAssessment, PriorityWallet, EvidenceItem,
  MonitoredWallet, AlertItem, ReportData, AuditLogItem, CopilotResponse,
  Phase4GraphResponse,
  Phase4PathDiscoveryResponse,
  Phase4CounterpartiesResponse,
  PatternAnalysisResponse,
  InvestigationRiskResponse,
  EntityResolveResponse,
  CombinedInvestigationResponse,
  PriorityScoreItem,
  PriorityQueueResponse,
  PriorityCalculationRequest,
  TimelineEvent,
  CaseWorkspaceData,
  CopilotChatMessage,
  CopilotChatQueryRequest,
  CopilotGroundedAnswer,
  CopilotSuggestionsResponse,
  AlertRuleItem,
  CreateAlertRulePayload,
  AuditVerificationResult,
  BlockchainNetworkInfo,
  MultichainWalletSummary,
  CrossChainLinkItem,
  RecordCrossChainLinkPayload,
  InvestigatorProfile,
  AvailableInvestigator,
  InAppNotification,
  CaseAssignment,
  InvestigationRecommendation,
  CaseRecommendationsResponse
} from '../types';

export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('cryptotrace_api_base');
    if (custom && custom.trim()) {
      let u = custom.trim();
      if (!u.startsWith('http://') && !u.startsWith('https://')) {
        u = `https://${u}`;
      }
      return `${u.replace(/\/$/, '')}/api`;
    }
  }
  let envUrl = ((import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL || '').trim();
  if (envUrl) {
    if (!envUrl.startsWith('http://') && !envUrl.startsWith('https://')) {
      envUrl = `https://${envUrl}`;
    }
    return `${envUrl.replace(/\/$/, '')}/api`;
  }
  return '/api';
}

export function setApiBase(url: string) {
  if (typeof window !== 'undefined') {
    if (url && url.trim()) {
      localStorage.setItem('cryptotrace_api_base', url.trim());
    } else {
      localStorage.removeItem('cryptotrace_api_base');
    }
    window.location.reload();
  }
}

export const API_BASE = getApiBase();

function getAuthHeader(): HeadersInit {
  const token = localStorage.getItem('sih_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseJsonResponse<T = any>(res: Response, defaultMessage: string = 'Operation failed'): Promise<T> {
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    if (contentType.includes('application/json')) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || defaultMessage);
    } else {
      if (res.status === 401) {
        throw new Error('Incorrect username or password. Please try investigator / password123.');
      } else if (res.status === 404) {
        throw new Error('API route not found (404). Please ensure the backend web service is running.');
      } else if (res.status >= 500) {
        throw new Error('Backend server is waking up on Render (free tier cold start). Please wait 30 seconds and try again.');
      }
      throw new Error(defaultMessage);
    }
  }

  if (!contentType.includes('application/json')) {
    throw new Error('Backend service returned a non-JSON response. It may still be starting up on Render. Please wait 30 seconds and try again.');
  }

  return res.json();
}

export const api = {
  // Auth
  async login(username: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await parseJsonResponse(res, 'Authentication failed. Please verify credentials.');
    localStorage.setItem('sih_auth_token', data.access_token);
    localStorage.setItem('sih_user', JSON.stringify(data.user));
    return data;
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to retrieve user profile');
    return res.json();
  },

  async seedDemoUsers(): Promise<void> {
    await fetch(`${API_BASE}/auth/seed-users`, { method: 'POST' });
  },

  // Cases
  async getCases(): Promise<Case[]> {
    const res = await fetch(`${API_BASE}/cases`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to fetch cases');
    return res.json();
  },

  async getCase(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to fetch case');
    return res.json();
  },

  async createCase(caseData: Partial<Case>): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(caseData)
    });
    if (!res.ok) throw new Error('Failed to create case');
    return res.json();
  },

  async seedDemoCase(): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/seed-demo`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to seed demo case');
    return res.json();
  },

  async getCaseNotes(caseId: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/notes`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async addCaseNote(caseId: string, content: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ case_id: caseId, content })
    });
    if (!res.ok) throw new Error('Failed to save note');
    return res.json();
  },

  // Transactions
  async getCaseTransactions(caseId: string): Promise<Transaction[]> {
    const res = await fetch(`${API_BASE}/transactions/case/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  // Analysis & Graph
  async getGraph(caseId: string, hops: number = 3, suspiciousOnly: boolean = false): Promise<SubgraphData> {
    const res = await fetch(`${API_BASE}/analysis/graph/${caseId}?hops=${hops}&suspicious_only=${suspiciousOnly}`, {
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to load transaction graph');
    return res.json();
  },

  async getMoneyTrail(caseId: string, maxHops: number = 5): Promise<{
    case_id: string;
    victim_name: string;
    suspect_wallet: string;
    amount_lost: number;
    currency: string;
    paths_to_vasp: MoneyTrailPath[];
    verified_paths_count: number;
    status_message: string;
  }> {
    const res = await fetch(`${API_BASE}/analysis/trail/${caseId}?max_hops=${maxHops}`, {
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to trace money trail');
    return res.json();
  },

  async getPatterns(caseId: string): Promise<{
    case_id: string;
    risk_assessment: RiskAssessment;
    findings: RiskFinding[];
  }> {
    const res = await fetch(`${API_BASE}/analysis/patterns/${caseId}`, {
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to load risk findings');
    return res.json();
  },

  // Wallet Direct Analysis
  async analyzeWallet(address: string, blockchain: string = 'Ethereum', hops: number = 2): Promise<any> {
    const res = await fetch(`${API_BASE}/wallets/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ address, blockchain, hops })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(err.detail || 'Wallet analysis failed');
    }
    return res.json();
  },

  // Evidence
  async getEvidence(caseId: string): Promise<EvidenceItem[]> {
    const res = await fetch(`${API_BASE}/evidence/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async saveEvidence(evidenceData: Partial<EvidenceItem>): Promise<EvidenceItem> {
    const res = await fetch(`${API_BASE}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(evidenceData)
    });
    if (!res.ok) throw new Error('Failed to preserve evidence');
    return res.json();
  },

  // Copilot
  async queryCopilot(caseId: string, question: string): Promise<CopilotResponse> {
    const res = await fetch(`${API_BASE}/copilot/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ case_id: caseId, question })
    });
    if (!res.ok) throw new Error('Investigation copilot unavailable');
    return res.json();
  },

  // Monitoring
  async getMonitoredWallets(caseId: string): Promise<MonitoredWallet[]> {
    const res = await fetch(`${API_BASE}/monitoring/case/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async addMonitoredWallet(caseId: string, walletAddress: string, blockchain: string, label?: string): Promise<MonitoredWallet> {
    const res = await fetch(`${API_BASE}/monitoring`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ case_id: caseId, wallet_address: walletAddress, blockchain, label })
    });
    if (!res.ok) throw new Error('Failed to add to watchlist');
    return res.json();
  },

  async simulateAlert(monitoringId: number): Promise<AlertItem> {
    const res = await fetch(`${API_BASE}/monitoring/simulate-alert/${monitoringId}`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    if (!res.ok) throw new Error('Failed to simulate alert');
    return res.json();
  },

  async getAlerts(unreadOnly: boolean = false): Promise<AlertItem[]> {
    const res = await fetch(`${API_BASE}/monitoring/alerts?unread_only=${unreadOnly}`, {
      headers: getAuthHeader()
    });
    if (!res.ok) return [];
    return res.json();
  },

  // Reports
  async getReports(caseId: string): Promise<ReportData[]> {
    const res = await fetch(`${API_BASE}/reports/case/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async generateReport(caseId: string, title?: string): Promise<ReportData> {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ case_id: caseId, title })
    });
    if (!res.ok) throw new Error('Failed to generate report');
    return res.json();
  },

  async reviewReport(reportId: string, status: 'APPROVED' | 'REJECTED', comments: string): Promise<ReportData> {
    const res = await fetch(`${API_BASE}/reports/${reportId}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ status, supervisor_comments: comments })
    });
    if (!res.ok) throw new Error('Failed to review report');
    return res.json();
  },

  // Audit Logs
  async getAuditLogs(caseId?: string): Promise<AuditLogItem[]> {
    const url = caseId ? `${API_BASE}/audit/case/${caseId}` : `${API_BASE}/audit`;
    const res = await fetch(url, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  // Labels
  async getLabels(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/labels`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async saveLabel(labelData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/labels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(labelData)
    });
    if (!res.ok) throw new Error('Failed to save label');
    return res.json();
  },

  // System Status
  async getSystemStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) return null;
    return res.json();
  },

  // Phase 3: Blockchain Transaction Layer
  async validateAddress(address: string): Promise<{ address: string; is_valid: boolean; blockchain: string; chain_id: number }> {
    const res = await fetch(`${API_BASE}/wallets/${address}/validate`);
    if (!res.ok) throw new Error('Failed to validate address');
    return res.json();
  },

  async getWalletTransactions(
    address: string,
    params: { page?: number; page_size?: number; direction?: string; from_block?: number; to_block?: number } = {}
  ): Promise<{
    wallet: string;
    blockchain: string;
    chain_id: number;
    page: number;
    page_size: number;
    total: number;
    transactions: any[];
  }> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));
    if (params.direction) query.set('direction', params.direction);
    if (params.from_block) query.set('from_block', String(params.from_block));
    if (params.to_block) query.set('to_block', String(params.to_block));

    const res = await fetch(`${API_BASE}/wallets/${address}/transactions?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Failed to fetch transactions' }));
      throw new Error(err.error || err.detail || 'Failed to fetch transactions');
    }
    return res.json();
  },

  async syncWalletTransactions(address: string, caseId?: string): Promise<{
    wallet: string;
    blockchain: string;
    chain_id: number;
    fetched: number;
    inserted: number;
    updated: number;
    duplicates: number;
    failed: number;
  }> {
    const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : '';
    const res = await fetch(`${API_BASE}/wallets/${address}/transactions/sync${query}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Sync failed' }));
      throw new Error(err.error || err.detail || 'Sync failed');
    }
    return res.json();
  },

  async syncCaseTransactions(caseId: string): Promise<{
    wallet: string;
    blockchain: string;
    chain_id: number;
    fetched: number;
    inserted: number;
    updated: number;
    duplicates: number;
    failed: number;
  }> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/transactions/sync`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Case sync failed' }));
      throw new Error(err.error || err.detail || 'Case sync failed');
    }
    return res.json();
  },

  async getTransactionDetail(txHash: string): Promise<any> {
    const res = await fetch(`${API_BASE}/transactions/${txHash}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Transaction not found' }));
      throw new Error(err.error || err.detail || 'Transaction not found');
    }
    return res.json();
  },

  async getDatabaseStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/database/status`);
    if (!res.ok) throw new Error('Database status unavailable');
    return res.json();
  },

  // Phase 4: Graph and Multi-Hop Tracing
  async getWalletGraph(
    address: string,
    params?: {
      max_hops?: number;
      direction?: string;
      min_value?: number;
      max_value?: number;
      from_block?: number;
      to_block?: number;
    }
  ): Promise<Phase4GraphResponse> {
    const query = new URLSearchParams();
    if (params?.max_hops) query.set('max_hops', String(params.max_hops));
    if (params?.direction) query.set('direction', params.direction);
    if (params?.min_value !== undefined && params.min_value !== null) query.set('min_value', String(params.min_value));
    if (params?.max_value !== undefined && params.max_value !== null) query.set('max_value', String(params.max_value));
    if (params?.from_block) query.set('from_block', String(params.from_block));
    if (params?.to_block) query.set('to_block', String(params.to_block));

    const res = await fetch(`${API_BASE}/graph/wallet/${address}?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Failed to retrieve wallet graph' }));
      throw new Error(err.error || err.detail || 'Failed to retrieve wallet graph');
    }
    return res.json();
  },

  async getWalletPaths(
    address: string,
    params?: { max_hops?: number; direction?: string; min_value?: number }
  ): Promise<Phase4PathDiscoveryResponse> {
    const query = new URLSearchParams();
    if (params?.max_hops) query.set('max_hops', String(params.max_hops));
    if (params?.direction) query.set('direction', params.direction);
    if (params?.min_value !== undefined) query.set('min_value', String(params.min_value));

    const res = await fetch(`${API_BASE}/graph/paths/${address}?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Failed to discover paths' }));
      throw new Error(err.error || err.detail || 'Failed to discover paths');
    }
    return res.json();
  },

  async getWalletCounterparties(address: string): Promise<Phase4CounterpartiesResponse> {
    const res = await fetch(`${API_BASE}/wallets/${address}/counterparties`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Failed to retrieve counterparties' }));
      throw new Error(err.error || err.detail || 'Failed to retrieve counterparties');
    }
    return res.json();
  },

  async getCaseGraphPhase4(
    caseId: string,
    params?: { max_hops?: number; direction?: string; min_value?: number }
  ): Promise<Phase4GraphResponse> {
    const query = new URLSearchParams();
    if (params?.max_hops) query.set('max_hops', String(params.max_hops));
    if (params?.direction) query.set('direction', params.direction);
    if (params?.min_value !== undefined) query.set('min_value', String(params.min_value));

    const res = await fetch(`${API_BASE}/cases/${caseId}/graph?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Failed to retrieve case graph' }));
      throw new Error(err.error || err.detail || 'Failed to retrieve case graph');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 5: Suspicious Pattern Detection
  // ==========================================
  async getWalletPatterns(address: string, maxHops: number = 3): Promise<PatternAnalysisResponse> {
    const res = await fetch(`${API_BASE}/analysis/wallet/${address}/patterns?max_hops=${maxHops}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to analyze patterns' }));
      throw new Error(err.detail || 'Failed to analyze patterns');
    }
    return res.json();
  },

  async getCasePatterns(caseId: string, maxHops: number = 3): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/case/${caseId}/patterns?max_hops=${maxHops}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to analyze case patterns' }));
      throw new Error(err.detail || 'Failed to analyze case patterns');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 6: Risk Engine & Explainable ML
  // ==========================================
  async getWalletRisk(address: string, maxHops: number = 3): Promise<InvestigationRiskResponse> {
    const res = await fetch(`${API_BASE}/risk/wallet/${address}?max_hops=${maxHops}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to assess risk' }));
      throw new Error(err.detail || 'Failed to assess risk');
    }
    return res.json();
  },

  async getCaseRisk(caseId: string, maxHops: number = 3): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/case/${caseId}?max_hops=${maxHops}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to assess case risk' }));
      throw new Error(err.detail || 'Failed to assess case risk');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 7: Entity & VASP Identification
  // ==========================================
  async getEntityByAddress(address: string): Promise<EntityResolveResponse> {
    const res = await fetch(`${API_BASE}/entities/address/${address}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to resolve entity' }));
      throw new Error(err.detail || 'Failed to resolve entity');
    }
    return res.json();
  },

  async searchEntities(query: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/entities/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) return [];
    return res.json();
  },

  // ==========================================
  // COMBINED INVESTIGATION PIPELINE
  // ==========================================
  async getWalletInvestigationAnalysis(
    address: string,
    caseId?: string,
    maxHops: number = 3
  ): Promise<CombinedInvestigationResponse> {
    const query = new URLSearchParams({ max_hops: String(maxHops) });
    if (caseId) query.set('case_id', caseId);

    const res = await fetch(`${API_BASE}/investigation/wallet/${address}/analysis?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to execute investigation analysis' }));
      throw new Error(err.detail || 'Failed to execute investigation analysis');
    }
    return res.json();
  },

  async getCaseInvestigationAnalysis(
    caseId: string,
    maxHops: number = 3
  ): Promise<CombinedInvestigationResponse> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/analysis?max_hops=${maxHops}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to analyze case investigation' }));
      throw new Error(err.detail || 'Failed to analyze case investigation');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 8: Investigation Priority Engine
  // ==========================================
  async getPriorityQueue(status?: string, priorityLevel?: string, limit: number = 50): Promise<PriorityQueueResponse> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (status) query.set('status', status);
    if (priorityLevel) {
      query.set('category', priorityLevel);
      query.set('priority_level', priorityLevel);
    }
    const res = await fetch(`${API_BASE}/priority/queue?${query.toString()}`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load priority queue');
    const data = await res.json();
    const rawItems: any[] = data.queue || data.items || [];
    const normalizedItems = rawItems.map((item: any) => ({
      ...item,
      id: String(item.id),
      target_type: item.target_type || item.object_type || 'WALLET',
      target_identifier: item.target_identifier || item.wallet_address || item.object_id || 'Unknown Target',
      priority_score: Number(item.priority_score || 0),
      priority_level: (item.priority_level || item.priority_category || 'LOW').toUpperCase(),
      priority_category: (item.priority_category || item.priority_level || 'LOW').toUpperCase(),
      urgency_score: item.urgency_score ?? Math.min(100, Math.round(Number(item.priority_score || 0) * 0.9)),
      severity_score: item.severity_score ?? Math.min(100, Math.round(Number(item.priority_score || 0) * 0.95)),
      asset_exposure: item.asset_exposure ?? Math.min(100, Math.round(Number(item.priority_score || 0) * 0.8)),
      evidence_strength: item.evidence_strength ?? ((item.supporting_evidence || []).length > 0 ? item.supporting_evidence.length * 20 : 60),
      explanation: item.explanation || item.reasons || [],
      reasons: item.reasons || item.explanation || [],
      factor_points: item.factor_points || {
        topological_risk: Math.round(Number(item.priority_score || 0) * 0.4),
        asset_exposure: Math.round(Number(item.priority_score || 0) * 0.3),
        urgency: Math.round(Number(item.priority_score || 0) * 0.3),
      },
      status: (item.status || 'NEW').toUpperCase()
    }));
    return {
      total: data.total_leads ?? data.total ?? normalizedItems.length,
      total_leads: data.total_leads ?? data.total ?? normalizedItems.length,
      critical_count: data.critical_count ?? 0,
      high_count: data.high_count ?? 0,
      medium_count: data.medium_count ?? 0,
      low_count: data.low_count ?? 0,
      items: normalizedItems,
      queue: normalizedItems
    };
  },

  async calculatePriority(payload: PriorityCalculationRequest): Promise<PriorityScoreItem> {
    let res = await fetch(`${API_BASE}/priority/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      // Fallback to GET /priority/wallet/{address}
      const q = new URLSearchParams();
      if (payload.case_id) q.set('case_id', payload.case_id);
      res = await fetch(`${API_BASE}/priority/wallet/${payload.wallet_address}?${q.toString()}`, {
        headers: getAuthHeader()
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to calculate priority' }));
        throw new Error(err.detail || 'Failed to calculate priority');
      }
      const list = await res.json();
      const raw = Array.isArray(list) ? list[0] : list;
      return {
        ...raw,
        id: String(raw.id),
        target_type: raw.target_type || raw.object_type || 'WALLET',
        target_identifier: raw.target_identifier || raw.wallet_address || raw.object_id || payload.wallet_address,
        priority_score: Number(raw.priority_score || 0),
        priority_level: (raw.priority_level || raw.priority_category || 'LOW').toUpperCase(),
        priority_category: (raw.priority_category || raw.priority_level || 'LOW').toUpperCase(),
        urgency_score: raw.urgency_score ?? Math.min(100, Math.round(Number(raw.priority_score || 0) * 0.9)),
        severity_score: raw.severity_score ?? Math.min(100, Math.round(Number(raw.priority_score || 0) * 0.95)),
        asset_exposure: raw.asset_exposure ?? Math.min(100, Math.round(Number(raw.priority_score || 0) * 0.8)),
        evidence_strength: raw.evidence_strength ?? 70,
        explanation: raw.explanation || raw.reasons || [],
        reasons: raw.reasons || raw.explanation || [],
        factor_points: raw.factor_points || {
          topological_risk: Math.round(Number(raw.priority_score || 0) * 0.4),
          asset_exposure: Math.round(Number(raw.priority_score || 0) * 0.3),
          urgency: Math.round(Number(raw.priority_score || 0) * 0.3),
        },
        status: (raw.status || 'NEW').toUpperCase()
      };
    }
    return res.json();
  },

  async reviewPriorityLead(leadId: string, notes?: string): Promise<PriorityScoreItem> {
    const res = await fetch(`${API_BASE}/priority/${leadId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to review priority lead' }));
      throw new Error(err.detail || 'Failed to review priority lead');
    }
    return res.json();
  },

  async assignPriorityLead(leadId: string, assignedTo: string): Promise<PriorityScoreItem> {
    const res = await fetch(`${API_BASE}/priority/${leadId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ assigned_to: assignedTo })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to assign priority lead' }));
      throw new Error(err.detail || 'Failed to assign priority lead');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 9: Investigation Workspace & Timeline
  // ==========================================
  async getCaseWorkspace(caseId: string): Promise<CaseWorkspaceData> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/workspace`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to fetch case workspace');
    return res.json();
  },

  async getCaseTimeline(caseId: string): Promise<TimelineEvent[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/timeline`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async updateCaseStatus(caseId: string, status: string, notes?: string): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ status, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to update case status' }));
      throw new Error(err.detail || 'Failed to update case status');
    }
    return res.json();
  },

  // ==========================================
  // PHASE 10: Investigation Copilot & Explainable AI
  // ==========================================
  async askCaseCopilot(payload: CopilotChatQueryRequest): Promise<CopilotGroundedAnswer> {
    const res = await fetch(`${API_BASE}/copilot/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Copilot query failed' }));
      throw new Error(err.detail || 'Copilot query failed');
    }
    return res.json();
  },

  async getCaseSuggestions(caseId: string): Promise<string[]> {
    const res = await fetch(`${API_BASE}/copilot/suggestions/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    const data: CopilotSuggestionsResponse = await res.json();
    return data.suggestions || [];
  },

  async getCopilotHistory(caseId: string): Promise<CopilotChatMessage[]> {
    const res = await fetch(`${API_BASE}/copilot/history/${caseId}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  // ==========================================
  // PHASE 11: Monitoring Rules, Reports & Audit
  // ==========================================
  async getAlertRules(caseId?: string): Promise<AlertRuleItem[]> {
    const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : '';
    const res = await fetch(`${API_BASE}/monitoring/rules${query}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async createAlertRule(payload: CreateAlertRulePayload): Promise<AlertRuleItem> {
    const res = await fetch(`${API_BASE}/monitoring/rules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create alert rule' }));
      throw new Error(err.detail || 'Failed to create alert rule');
    }
    return res.json();
  },

  async deleteAlertRule(ruleId: string): Promise<void> {
    await fetch(`${API_BASE}/monitoring/rules/${ruleId}`, {
      method: 'DELETE',
      headers: getAuthHeader()
    });
  },

  async acknowledgeAlert(alertId: number): Promise<AlertItem> {
    const res = await fetch(`${API_BASE}/monitoring/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to acknowledge alert');
    }
    return res.json();
  },

  getReportPdfUrl(reportId: string): string {
    return `${API_BASE}/reports/${reportId}/pdf`;
  },

  getReportCsvUrl(reportId: string): string {
    return `${API_BASE}/reports/${reportId}/csv`;
  },

  async getReportJson(reportId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/reports/${reportId}/json`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load report JSON');
    return res.json();
  },

  async verifyAuditIntegrity(): Promise<AuditVerificationResult> {
    const res = await fetch(`${API_BASE}/audit/verify`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to verify audit log integrity');
    return res.json();
  },

  // ==========================================
  // PHASE 12: Multi-Chain Architecture & Cross-Chain
  // ==========================================
  async getChains(): Promise<BlockchainNetworkInfo[]> {
    const res = await fetch(`${API_BASE}/chains`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async getMultichainWallet(address: string): Promise<MultichainWalletSummary> {
    const res = await fetch(`${API_BASE}/chains/wallet/${address}`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to fetch multi-chain wallet data');
    return res.json();
  },

  async getCrossChainBridges(): Promise<Array<{ name: string; supported_chains: number[]; description: string }>> {
    const res = await fetch(`${API_BASE}/cross-chain/bridges`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async getCrossChainLinks(walletAddress?: string): Promise<CrossChainLinkItem[]> {
    const query = walletAddress ? `?wallet_address=${encodeURIComponent(walletAddress)}` : '';
    const res = await fetch(`${API_BASE}/cross-chain/links${query}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async recordCrossChainLink(payload: RecordCrossChainLinkPayload): Promise<CrossChainLinkItem> {
    const res = await fetch(`${API_BASE}/cross-chain/record-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to record cross chain link' }));
      throw new Error(err.detail || 'Failed to record cross chain link');
    }
    return res.json();
  },

  // ==========================================
  // MULTI-USER DYNAMIC PLATFORM METHODS
  // ==========================================

  // Registration
  async register(payload: any): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return parseJsonResponse<User>(res, 'Registration failed. Please check details.');
  },

  // Investigators
  async getAvailableInvestigators(): Promise<AvailableInvestigator[]> {
    const res = await fetch(`${API_BASE}/investigators/available`);
    if (!res.ok) return [];
    return res.json();
  },

  async getMyInvestigatorProfile(): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/profile/me`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load investigator profile');
    return res.json();
  },

  async updateInvestigatorAvailability(availabilityStatus: string, maxCases?: number): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/availability`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ availability_status: availabilityStatus, max_active_cases: maxCases })
    });
    if (!res.ok) throw new Error('Failed to update availability status');
    return res.json();
  },

  async getAdminInvestigatorList(status?: string): Promise<InvestigatorProfile[]> {
    const query = status ? `?status_filter=${encodeURIComponent(status)}` : '';
    const res = await fetch(`${API_BASE}/investigators/admin/list${query}`, { headers: getAuthHeader() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to load investigator applications' }));
      throw new Error(err.detail || 'Failed to load investigator applications');
    }
    return res.json();
  },

  async approveInvestigator(userId: number, reason?: string): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/admin/${userId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ reason })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to approve investigator' }));
      throw new Error(err.detail || 'Failed to approve investigator');
    }
    return res.json();
  },

  async rejectInvestigator(userId: number, reason: string): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/admin/${userId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ rejection_reason: reason })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to reject investigator' }));
      throw new Error(err.detail || 'Failed to reject investigator');
    }
    return res.json();
  },

  async suspendInvestigator(userId: number, reason?: string): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/admin/${userId}/suspend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ reason })
    });
    if (!res.ok) throw new Error('Failed to suspend investigator');
    return res.json();
  },

  async reactivateInvestigator(userId: number): Promise<InvestigatorProfile> {
    const res = await fetch(`${API_BASE}/investigators/admin/${userId}/reactivate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() }
    });
    if (!res.ok) throw new Error('Failed to reactivate investigator');
    return res.json();
  },

  // Notifications
  async getNotifications(unreadOnly = false): Promise<InAppNotification[]> {
    const res = await fetch(`${API_BASE}/notifications?unread_only=${unreadOnly}`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async getUnreadNotificationCount(): Promise<number> {
    const res = await fetch(`${API_BASE}/notifications/unread-count`, { headers: getAuthHeader() });
    if (!res.ok) return 0;
    const data = await res.json();
    return data.unread_count || 0;
  },

  async markNotificationRead(id: number): Promise<void> {
    await fetch(`${API_BASE}/notifications/${id}/read`, {
      method: 'PATCH',
      headers: getAuthHeader()
    });
  },

  async markAllNotificationsRead(): Promise<void> {
    await fetch(`${API_BASE}/notifications/read-all`, {
      method: 'PATCH',
      headers: getAuthHeader()
    });
  },

  // Case Lifecycle Workflow
  async acceptCase(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/accept`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to accept case' }));
      throw new Error(err.detail || 'Failed to accept case');
    }
    return res.json();
  },

  async startInvestigation(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/start-investigation`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start investigation' }));
      throw new Error(err.detail || 'Failed to start investigation');
    }
    return res.json();
  },

  async getCaseAssignments(caseId: string): Promise<CaseAssignment[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/assignments`, { headers: getAuthHeader() });
    if (!res.ok) return [];
    return res.json();
  },

  async getCaseRecommendations(caseId: string): Promise<CaseRecommendationsResponse> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/recommendations`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load case recommendations');
    return res.json();
  },

  async exportCaseNcrp(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/export/ncrp`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to export NCRP formatted dossier');
    return res.json();
  },

  async exportCaseSahyog(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/export/sahyog`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to export SAHYOG intelligence record');
    return res.json();
  }
};

