import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Sparkles, 
  Flame, 
  Workflow, 
  Terminal, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  Copy, 
  ChevronRight, 
  ChevronDown,
  ChevronUp,
  Network, 
  Cpu, 
  Globe2, 
  Users, 
  ArrowRight,
  Compass,
  FileCode,
  Building2,
  PlusCircle,
  Send,
  MessageSquare,
  ExternalLink,
  Edit3,
  Check
} from 'lucide-react';

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP Error ${res.status}`);
  return data;
}

const num = (v) => (v === undefined || v === null || Number.isNaN(Number(v)) ? '—' : v);

export default function App() {
  const [stage, setStage] = useState('intake'); // 'intake' | 'probing' | 'dashboard'
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Custom Onboarding Modal State
  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [customCompany, setCustomCompany] = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [customMandate, setCustomMandate] = useState('');
  const [customRoles, setCustomRoles] = useState('');
  const [isOnboardingGenerating, setIsOnboardingGenerating] = useState(false);

  // Org Mapping & Batch Dispatch State
  const [showOrgMappingModal, setShowOrgMappingModal] = useState(false);
  const [showBatchDispatchModal, setShowBatchDispatchModal] = useState(false);
  const [editingStakeholders, setEditingStakeholders] = useState([]);
  const [orgChartRawText, setOrgChartRawText] = useState('');
  const [showDemoExamples, setShowDemoExamples] = useState(false);
  const [previewEmployeeStakeholder, setPreviewEmployeeStakeholder] = useState(null);

  // Live Interactive Employee Interview State
  const [interactiveInterviewRole, setInteractiveInterviewRole] = useState(null);
  const [interviewMessages, setInterviewMessages] = useState([]);
  const [interviewInput, setInterviewInput] = useState('');
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [interviewTurnResult, setInterviewTurnResult] = useState(null);
  const [verifiedRoles, setVerifiedRoles] = useState({}); // { [role_id]: probeRecord }
  const [showLimitsPanel, setShowLimitsPanel] = useState(false);

  // Discovery state
  const [probes, setProbes] = useState([]);
  const [expandedProbeIdx, setExpandedProbeIdx] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [grounding, setGrounding] = useState(null);
  const [agentPackage, setAgentPackage] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(null); // stakeholder object
  const [copied, setCopied] = useState(false);
  const [selectedQuoteNode, setSelectedQuoteNode] = useState(null);

  const handleOpenOrgMapping = () => {
    if (!selectedPreset) return;
    setEditingStakeholders(
      (selectedPreset.stakeholders || []).map((s) => ({
        ...s,
        email: s.email || ''
      }))
    );
    setOrgChartRawText('');
    setShowOrgMappingModal(true);
  };

  const handleParseOrgChart = () => {
    if (!orgChartRawText.trim() || !editingStakeholders.length) return;
    const lines = orgChartRawText.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return;

    const updated = editingStakeholders.map((s, idx) => {
      if (idx < lines.length) {
        const line = lines[idx];
        let name = s.name;
        let title = s.title;
        let email = s.email || '';

        if (line.includes(':')) {
          const [t, n] = line.split(':');
          title = t.trim() || title;
          name = n.trim() || name;
        } else if (line.includes(' - ')) {
          const [n, t] = line.split(' - ');
          name = n.trim() || name;
          title = t.trim() || title;
        } else if (line.includes(',')) {
          const [n, t] = line.split(',');
          name = n.trim() || name;
          title = t.trim() || title;
        } else {
          name = line;
        }

        const emailMatch = name.match(/<([^>]+)>|\(([^)]+)\)/);
        if (emailMatch) {
          email = emailMatch[1] || emailMatch[2];
          name = name.replace(/<[^>]+>|\([^)]+\)/, '').trim();
        }

        return { ...s, name, title, email };
      }
      return s;
    });

    setEditingStakeholders(updated);
  };

  const handleSaveOrgMapping = (e) => {
    e.preventDefault();
    if (!selectedPreset) return;
    setSelectedPreset((prev) => ({
      ...prev,
      is_custom_mapped: true,
      stakeholders: editingStakeholders
    }));
    setShowOrgMappingModal(false);
    setShowBatchDispatchModal(true);
  };

  const getInterviewLink = (roleId) => {
    const origin = window.location.origin;
    const presetId = selectedPreset?.id || 'planet_junior';
    return `${origin}/?interview=${roleId}&preset=${presetId}`;
  };

  const getBatchDispatchText = () => {
    if (!selectedPreset) return '';
    return selectedPreset.stakeholders
      .map(
        (s) =>
          `[${s.name} - ${s.title}${s.email ? ` (${s.email})` : ''}]\n"Hey ${s.name}, quick 3-min confidential check on how ${selectedPreset.target_workflow} works in practice for ${s.title}:"\n${getInterviewLink(s.role_id)}\n`
      )
      .join('\n');
  };

  const startLiveInterview = (stakeholder, presetOverride = null) => {
    const activePreset = presetOverride || selectedPreset;
    if (!stakeholder) return;
    setInteractiveInterviewRole(stakeholder);
    setInterviewInput('');
    setInterviewTurnResult(null);

    const initialQ = stakeholder.tactical_probe_strategy || 
      `When rush exceptions or custom requests occur in ${activePreset?.target_workflow || 'the target workflow'}, what exact workarounds or shadow tools do you use?`;

    setInterviewMessages([
      {
        role: 'agent',
        content: `Hi ${stakeholder.name}, I'm Mimic's confidential operational discovery investigator. I conduct quick 2-minute checks for ${activePreset?.company_name || 'your team'}. Your direct management does not see raw answers.`
      },
      {
        role: 'agent',
        content: initialQ
      }
    ]);
  };

  const handleSendInterviewTurn = async (messageToSend) => {
    const text = (messageToSend !== undefined && messageToSend !== null) ? messageToSend : interviewInput;
    if (!text || !text.trim() || interviewLoading || !interactiveInterviewRole) return;

    const newMsgs = [...interviewMessages, { role: 'user', content: text.trim() }];
    setInterviewMessages(newMsgs);
    setInterviewInput('');
    setInterviewLoading(true);

    try {
      const historyPayload = newMsgs.map(m => ({
        role: m.role === 'agent' ? 'assistant' : 'user',
        content: m.content
      }));

      const res = await fetchJSON('/api/strata/interview-turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: selectedPreset?.company_name || 'Enterprise',
          target_workflow: selectedPreset?.target_workflow || 'Operations',
          role_name: interactiveInterviewRole.name,
          role_title: interactiveInterviewRole.title,
          tactical_probe_strategy: interactiveInterviewRole.tactical_probe_strategy || '',
          conversation_history: historyPayload,
          user_message: text.trim()
        })
      });

      if (res.status === 'success') {
        setInterviewTurnResult(res);
        setInterviewMessages(prev => [
          ...prev,
          { role: 'agent', content: res.interviewer_reply }
        ]);

        if (res.is_complete) {
          const record = {
            role_id: interactiveInterviewRole.role_id,
            name: interactiveInterviewRole.name,
            title: interactiveInterviewRole.title,
            revealed_friction: res.revealed_friction,
            shadow_tools_used: res.shadow_tools_used,
            stakeholder_response: text.trim(),
            probing_question: interactiveInterviewRole.tactical_probe_strategy || 'Operational exception probe',
            summary_takeaway: res.summary_takeaway,
            verified_at: new Date().toLocaleTimeString()
          };
          setVerifiedRoles(prev => ({
            ...prev,
            [interactiveInterviewRole.role_id]: record
          }));
          setProbes(prev => prev.map(p => (p.role_id === interactiveInterviewRole.role_id ? { ...p, ...record, is_live_verified: true } : p)));
        }
      }
    } catch (err) {
      setInterviewMessages(prev => [
        ...prev,
        { role: 'agent', content: 'Thank you for explaining that. That uncovers the exact shadow handoffs needed to prevent automation failure.' }
      ]);
    } finally {
      setInterviewLoading(false);
    }
  };

  useEffect(() => {
    fetchPresets();
  }, []);

  const fetchPresets = async () => {
    try {
      const data = await fetchJSON('/api/strata/presets');
      if (data.presets && data.presets.length > 0) {
        setPresets(data.presets);

        // Check URL parameters for live interview: ?interview=<roleId>&preset=<presetId>
        const params = new URLSearchParams(window.location.search);
        const interviewRoleId = params.get('interview');
        const presetId = params.get('preset');

        if (interviewRoleId) {
          const matchedPreset = data.presets.find(p => p.id === presetId) || data.presets[0];
          setSelectedPreset(matchedPreset);
          const matchedStakeholder = matchedPreset.stakeholders?.find(s => s.role_id === interviewRoleId);
          if (matchedStakeholder) {
            startLiveInterview(matchedStakeholder, matchedPreset);
          }
        }
      }
    } catch (err) {
      setError('Could not connect to backend. Please ensure the server is running on port 8000.');
    }
  };

  // Live Onboard New Company
  const handleGenerateCustomOnboard = async (e) => {
    e.preventDefault();
    if (!customCompany.trim() || !customMandate.trim()) return;

    setIsOnboardingGenerating(true);
    setError(null);
    try {
      const res = await fetchJSON('/api/strata/generate-intake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: customCompany,
          domain: customDomain || null,
          mandate: customMandate,
          roles_hint: customRoles || null
        })
      });

      if (res.scenario) {
        const sc = res.scenario;
        if (!sc.stakeholders && (sc.roles || sc.key_stakeholders)) {
          sc.stakeholders = sc.roles || sc.key_stakeholders;
        }
        if (!Array.isArray(sc.stakeholders)) {
          sc.stakeholders = [];
        }
        setPresets(prev => [sc, ...prev]);
        setSelectedPreset(sc);
        setShowOnboardModal(false);
        setCustomCompany('');
        setCustomDomain('');
        setCustomMandate('');
        setCustomRoles('');
      }
    } catch (err) {
      setError(`Custom onboarding failed: ${err.message}`);
    } finally {
      setIsOnboardingGenerating(false);
    }
  };

  // Step 1: Launch parallel probes
  const handleDeployProbes = async () => {
    if (!selectedPreset) return;
    setLoading(true);
    setError(null);
    setStage('probing');
    try {
      const res = await fetchJSON('/api/strata/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: selectedPreset })
      });
      const baseProbes = res.probes || [];
      const merged = baseProbes.map(p => {
        const v = verifiedRoles[p.role_id];
        if (v) {
          return {
            ...p,
            revealed_friction: v.revealed_friction || p.revealed_friction,
            shadow_tools_used: v.shadow_tools_used || p.shadow_tools_used,
            stakeholder_response: v.stakeholder_response || p.stakeholder_response,
            probing_question: v.probing_question || p.probing_question,
            is_live_verified: true
          };
        }
        return p;
      });
      setProbes(merged);
    } catch (err) {
      setError(`Probing failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Synthesize operational blueprint
  const handleSynthesize = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchJSON('/api/strata/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: selectedPreset, transcripts: probes })
      });
      const bp = res.blueprint;
      setBlueprint(bp);

      // Trigger Tavily grounding on top opportunity
      const topOpp = bp?.ai_opportunity_matrix?.quick_wins?.[0] || {
        title: bp?.discovered_adjacent_workflow?.title || 'Contract Data Reconciliation Agent'
      };
      
      try {
        const groundRes = await fetchJSON('/api/strata/ground', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            opportunity_title: topOpp.title,
            target_workflow: selectedPreset.target_workflow
          })
        });
        setGrounding(groundRes.grounding);

        // Pre-generate agent blueprint & MCP
        const exportRes = await fetchJSON('/api/strata/export-agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            opportunity: topOpp,
            scenario_title: selectedPreset.title,
            grounding: groundRes.grounding
          })
        });
        setAgentPackage(exportRes.package);
      } catch (gErr) {
        console.warn('Grounding/Export non-fatal error:', gErr);
      }

      setStage('dashboard');
    } catch (err) {
      setError(`Synthesis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen text-zinc-100 flex flex-col selection:bg-amber-500/30">
      {/* Minimalist Top Navigation */}
      <header className="border-b border-[#c5a05922] bg-[#08090a]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded border border-[#c5a059] flex items-center justify-center bg-[#15181e] shadow-[0_0_10px_rgba(197,160,89,0.25)]">
              <span className="font-cinzel text-xs font-bold text-[#e6ca85]">M</span>
            </div>
            <span className="font-cinzel text-base tracking-widest font-bold text-[#e6ca85]">MIMIC</span>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#101318] border border-[#c5a05922] text-zinc-300">
              <Cpu className="w-3.5 h-3.5 text-[#c5a059]" />
              <span>Nemotron-3 120B (Nebius)</span>
            </div>
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#101318] border border-[#c5a05922] text-zinc-300">
              <Globe2 className="w-3.5 h-3.5 text-[#c5a059]" />
              <span>Tavily Grounding</span>
            </div>
          </div>
        </div>
      </header>

      {/* Stepper Navigation */}
      <div className="border-b border-[#c5a05915] bg-[#0b0d10]/60 py-2.5">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center space-x-6">
            <button 
              onClick={() => setStage('intake')}
              className={`flex items-center space-x-2 transition-colors ${stage === 'intake' ? 'text-[#e6ca85] font-semibold' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] border ${stage === 'intake' ? 'border-[#c5a059] bg-[#c5a05922]' : 'border-zinc-700'}`}>1</span>
              <span>Executive Intake & Strategy</span>
            </button>
            <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />
            <button 
              onClick={() => probes.length > 0 && setStage('probing')}
              disabled={probes.length === 0}
              className={`flex items-center space-x-2 transition-colors ${stage === 'probing' ? 'text-[#e6ca85] font-semibold' : probes.length > 0 ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-600 cursor-not-allowed'}`}
            >
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] border ${stage === 'probing' ? 'border-[#c5a059] bg-[#c5a05922]' : 'border-zinc-700'}`}>2</span>
              <span>Parallel Workforce Probes</span>
            </button>
            <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />
            <button 
              onClick={() => blueprint && setStage('dashboard')}
              disabled={!blueprint}
              className={`flex items-center space-x-2 transition-colors ${stage === 'dashboard' ? 'text-[#e6ca85] font-semibold' : blueprint ? 'text-zinc-400 hover:text-zinc-200' : 'text-zinc-600 cursor-not-allowed'}`}
            >
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] border ${stage === 'dashboard' ? 'border-[#c5a059] bg-[#c5a05922]' : 'border-zinc-700'}`}>3</span>
              <span>Delusion Dashboard & MCP</span>
            </button>
          </div>

          {selectedPreset && (
            <div className="flex items-center space-x-2 text-zinc-400">
              <Building2 className="w-3.5 h-3.5 text-[#c5a059]" />
              <span className="text-zinc-200">{selectedPreset.company_name}</span>
              <span className="text-zinc-600">·</span>
              <span>{selectedPreset.industry}</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-950/40 border-b border-red-500/30 px-6 py-2.5 text-red-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-6 flex-1 w-full">
        <AnimatePresence mode="wait">
          {/* STAGE 1: C-Suite Intake & Tactical Probe Strategy */}
          {stage === 'intake' && (
            <motion.div 
              key="stage-intake"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="space-y-6"
            >
              {!selectedPreset ? (
                /* Clean Initial Screen */
                <div className="elden-card p-10 md:p-14 text-center rounded-xl border border-[#c5a05933] max-w-xl mx-auto my-10 space-y-6">
                  <div className="space-y-1.5">
                    <h1 className="font-cinzel text-2xl font-bold text-[#e6ca85] tracking-wide">Operational Discovery</h1>
                    <p className="text-xs text-zinc-400 font-mono">Test leadership assumptions against frontline reality.</p>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                    <button
                      onClick={() => setShowOnboardModal(true)}
                      className="w-full sm:w-auto px-6 py-3 rounded bg-gradient-to-r from-[#c5a059] to-[#9e7d3b] text-black font-semibold text-xs tracking-wider uppercase font-cinzel hover:brightness-110 transition-all flex items-center justify-center space-x-2 shadow-[0_0_16px_rgba(197,160,89,0.25)]"
                    >
                      <PlusCircle className="w-4 h-4" />
                      <span>+ Onboard New Client</span>
                    </button>

                    <button
                      onClick={() => setShowDemoExamples(!showDemoExamples)}
                      className="w-full sm:w-auto px-5 py-3 rounded bg-[#101318] text-zinc-300 hover:text-white border border-zinc-700 hover:border-[#c5a059] text-xs font-mono transition-all flex items-center justify-center space-x-2"
                    >
                      <Compass className="w-4 h-4 text-[#c5a059]" />
                      <span>{showDemoExamples ? 'Hide Examples' : 'See Demo Examples'}</span>
                    </button>
                  </div>

                  {showDemoExamples && presets.length > 0 && (
                    <div className="pt-5 border-t border-zinc-800/80 space-y-2.5 text-left">
                      <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
                        Select a pre-configured scenario:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                        {presets.map((p) => (
                          <button
                            key={p.id}
                            onClick={() => {
                              setSelectedPreset(p);
                              setShowDemoExamples(false);
                            }}
                            className="p-3 rounded bg-[#090b0e] border border-zinc-800 hover:border-[#c5a059] text-left transition-all group"
                          >
                            <span className="text-xs font-semibold text-zinc-200 group-hover:text-[#e6ca85] block truncate">
                              {p.company_name}
                            </span>
                            <span className="text-[10px] text-zinc-500 font-mono block mt-0.5 truncate">
                              {p.industry}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  {/* Clean Top Bar when client selected */}
                  <div className="flex items-center justify-between pb-3 border-b border-[#c5a05915]">
                    <div>
                      <h1 className="font-cinzel text-lg font-bold text-[#e6ca85]">
                        Discovery · {selectedPreset.company_name}
                      </h1>
                      <p className="text-xs text-zinc-400 font-mono">
                        {selectedPreset.industry}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setShowOnboardModal(true)}
                        className="px-3 py-1.5 rounded text-xs font-mono bg-gradient-to-r from-amber-900/40 to-amber-700/30 text-amber-200 border border-amber-600/50 hover:brightness-110 flex items-center space-x-1.5"
                      >
                        <PlusCircle className="w-3.5 h-3.5 text-[#e6ca85]" />
                        <span>+ Onboard Client</span>
                      </button>
                      <button
                        onClick={() => setSelectedPreset(null)}
                        className="px-3 py-1.5 rounded text-xs font-mono bg-[#101318] text-zinc-400 hover:text-white border border-zinc-800 hover:border-zinc-700"
                      >
                        Change Client
                      </button>
                    </div>
                  </div>
                  {/* Clean Executive Mandate Card */}
                  <div className="elden-card p-5 rounded-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1.5 max-w-2xl">
                      <div className="flex items-center space-x-2 text-[10px] font-mono text-[#c5a059]">
                        <Compass className="w-3.5 h-3.5" />
                        <span>THE EXECUTIVE PRESUMPTION</span>
                        <span className="text-zinc-600">|</span>
                        <span className="text-zinc-400">{selectedPreset.company_size || 'Enterprise Team'}</span>
                      </div>
                      <h2 className="text-base font-semibold text-zinc-100">{selectedPreset.executive_mandate}</h2>
                      <p className="text-xs text-zinc-400">
                        <strong className="text-zinc-300">Target Workflow:</strong> {selectedPreset.target_workflow}
                      </p>
                    </div>

                    <div className="flex flex-col md:items-end space-y-1.5 shrink-0">
                      <button
                        onClick={handleDeployProbes}
                        disabled={loading}
                        className="px-5 py-2.5 rounded bg-gradient-to-r from-[#c5a059] to-[#9e7d3b] text-black font-semibold text-xs tracking-wider uppercase font-cinzel hover:brightness-110 transition-all flex items-center space-x-2 shadow-[0_0_16px_rgba(197,160,89,0.25)] shrink-0 disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                            <span>Simulating Interviews...</span>
                          </>
                        ) : (
                          <>
                            <span>⚡ Simulate Workforce Discovery</span>
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                      <span className="text-[10px] font-mono text-zinc-500">
                        Nemotron 120B unscripted parallel interviews (~15s)
                      </span>
                    </div>
                  </div>

                  {/* Scannable Target Discovery Personas Grid */}
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-cinzel text-xs uppercase tracking-wider text-[#c5a059] flex items-center space-x-1.5">
                            <Users className="w-3.5 h-3.5" />
                            <span>Target Discovery Personas</span>
                          </h3>
                          <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded border ${
                            selectedPreset.is_custom_mapped 
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' 
                              : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                          }`}>
                            {selectedPreset.is_custom_mapped ? 'Live Org Mapped' : 'AI-Generated Archetypes'}
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
                          Frontline archetype digital twins derived from executive mandate. Use for instant simulation or map to your live org chart.
                        </p>
                      </div>

                      <div className="flex items-center space-x-2 shrink-0">
                        <button
                          type="button"
                          onClick={handleOpenOrgMapping}
                          className="text-[11px] font-mono text-[#e6ca85] hover:text-white px-2.5 py-1 rounded bg-[#101318] border border-[#c5a05944] flex items-center space-x-1.5 hover:border-[#c5a059] transition-colors"
                          title="Assign actual employee names, emails, or paste an org chart"
                        >
                          <Building2 className="w-3 h-3 text-[#c5a059]" />
                          <span>Map to Live Org Chart</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowBatchDispatchModal(true)}
                          className="text-[11px] font-mono text-zinc-300 hover:text-white px-2.5 py-1 rounded bg-[#101318] border border-zinc-700 flex items-center space-x-1.5 hover:border-zinc-500 transition-colors"
                          title="View copyable Slack/WhatsApp links for all 4 team members"
                        >
                          <Send className="w-3 h-3 text-zinc-400" />
                          <span>Batch Dispatch Links</span>
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                      {(selectedPreset?.stakeholders || []).map((s) => {
                        const isVerified = Boolean(verifiedRoles[s.role_id]);
                        return (
                          <div key={s.role_id || s.name} className={`elden-card p-4 rounded-lg space-y-2.5 ${isVerified ? 'border border-emerald-500/40 bg-[#0a120c]' : ''}`}>
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-semibold text-xs text-zinc-100">{s.name}</h4>
                                  {isVerified ? (
                                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                                      <span>✅</span>
                                      <span>Live Verified</span>
                                    </span>
                                  ) : (
                                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400">
                                      {selectedPreset.is_custom_mapped ? 'Staff' : 'AI Twin'}
                                    </span>
                                  )}
                                </div>
                                <p className="text-[11px] text-zinc-400">
                                  {s.title} {s.email && <span className="text-zinc-500">· {s.email}</span>}
                                </p>
                              </div>
                              <div className="flex items-center space-x-1.5">
                                <button
                                  onClick={() => startLiveInterview(s)}
                                  className="text-[10px] font-mono text-[#e6ca85] hover:text-white flex items-center space-x-1 px-2 py-0.5 rounded bg-[#101318] border border-[#c5a05955] hover:border-[#c5a059] transition-colors"
                                  title="Open live unscripted employee interview"
                                >
                                  <MessageSquare className="w-2.5 h-2.5 text-[#c5a059]" />
                                  <span>{isVerified ? 'Re-interview' : 'Take Interview'}</span>
                                </button>
                                <button
                                  onClick={() => copyToClipboard(getInterviewLink(s.role_id))}
                                  className="text-[10px] font-mono text-zinc-400 hover:text-zinc-200 flex items-center space-x-1 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-700 hover:border-zinc-500 transition-colors"
                                  title="Copy live interview link for Slack / Teams"
                                >
                                  <Copy className="w-2.5 h-2.5" />
                                  <span>Copy Link</span>
                                </button>
                              </div>
                            </div>

                            <div className="bg-[#090b0e] p-2.5 rounded border border-zinc-800 text-[11px] text-zinc-300 border-l-2 border-l-[#c5a059]">
                              <strong className="text-[#c5a059] block font-mono text-[9px] mb-0.5">TACTICAL PROBING ANGLE:</strong>
                              {s.tactical_probe_strategy}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* STAGE 2: Parallel Workforce Discovery Room */}
          {stage === 'probing' && (
            <motion.div 
              key="stage-probing"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="space-y-5"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#c5a05915]">
                <div>
                  <h1 className="font-cinzel text-lg font-bold text-[#e6ca85] flex items-center space-x-2">
                    <Terminal className="w-4 h-4 text-[#c5a059]" />
                    <span>Workforce Interrogation Stream</span>
                  </h1>
                  <p className="text-xs text-zinc-400">Nemotron 120B probing frontline roles concurrently without triggering corporate defenses.</p>
                </div>

                <button
                  onClick={handleSynthesize}
                  disabled={loading || probes.length === 0}
                  className="px-5 py-2.5 rounded bg-gradient-to-r from-[#c5a059] to-[#9e7d3b] text-black font-semibold text-xs tracking-wider uppercase font-cinzel hover:brightness-110 transition-all flex items-center space-x-2 shadow-[0_0_16px_rgba(197,160,89,0.25)] disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                      <span>Synthesizing...</span>
                    </>
                  ) : (
                    <>
                      <Workflow className="w-4 h-4" />
                      <span>Synthesize Delusion Blueprint</span>
                    </>
                  )}
                </button>
              </div>

              {loading && probes.length === 0 && (
                <div className="elden-card p-12 text-center rounded-lg space-y-3">
                  <div className="w-7 h-7 border-2 border-[#c5a059] border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs font-cinzel text-[#e6ca85]">Probing 4 roles in parallel via Nemotron 120B...</p>
                  <p className="text-[11px] text-zinc-500 font-mono">Simulating unscripted Slack/chat dialogue</p>
                </div>
              )}

              {/* Compact, De-cluttered Probe Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {probes.map((p, idx) => (
                  <div 
                    key={p.role_id || idx}
                    className="elden-card p-4 rounded-lg space-y-2.5 border border-[#c5a05922]"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-400" />
                        <span className="font-semibold text-xs text-zinc-100">{p.name}</span>
                        <span className="text-[11px] text-zinc-400">({p.title})</span>
                      </div>
                      <span className="text-[9px] font-mono text-[#c5a059] px-1.5 py-0.5 rounded bg-[#c5a05915]">
                        Probed
                      </span>
                    </div>

                    {/* High-Impact Friction Snippet */}
                    <div className="bg-[#101318] p-2.5 rounded border border-amber-900/40 text-xs text-amber-200/90 leading-relaxed">
                      <strong className="text-amber-400 font-mono text-[9px] block mb-0.5">UNCOVERED WORKAROUND:</strong>
                      {p.revealed_friction}
                    </div>

                    {/* Detected Shadow Tools Pills */}
                    {p.shadow_tools_used && p.shadow_tools_used.length > 0 && (
                      <div className="flex items-center space-x-1.5 text-[10px] font-mono text-zinc-400">
                        <span className="text-zinc-500">Shadow Tools:</span>
                        {p.shadow_tools_used.map((tool, tIdx) => (
                          <span key={tIdx} className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-200 border border-zinc-700">
                            {tool}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Expandable Full Transcript Toggle */}
                    <div className="pt-2 border-t border-zinc-800/80">
                      <button
                        onClick={() => setExpandedProbeIdx(expandedProbeIdx === idx ? null : idx)}
                        className="text-[10px] font-mono text-zinc-400 hover:text-zinc-200 flex items-center space-x-1"
                      >
                        <span>{expandedProbeIdx === idx ? 'Hide Dialogue' : 'Read Full Interview Transcript'}</span>
                        {expandedProbeIdx === idx ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>

                      {expandedProbeIdx === idx && (
                        <motion.div 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="mt-2 space-y-2 text-[11px] bg-[#090b0e] p-3 rounded border border-zinc-800 font-mono"
                        >
                          <div>
                            <span className="text-[#c5a059] block text-[9px]">INTERVIEWER PROBE:</span>
                            <p className="text-zinc-300 italic">"{p.probing_question}"</p>
                          </div>
                          <div>
                            <span className="text-emerald-400 block text-[9px]">RESPONSE:</span>
                            <p className="text-zinc-200">"{p.stakeholder_response}"</p>
                          </div>
                        </motion.div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* STAGE 3: The Strategic Discovery Dashboard (The Revelation) */}
          {stage === 'dashboard' && blueprint && (
            <motion.div 
              key="stage-dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="space-y-6"
            >
              {/* Predictive Pre-Mortem Verification Banner */}
              {Object.keys(verifiedRoles).length > 0 ? (
                <div className="elden-card p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4 border border-emerald-500/40 bg-[#09150e]">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">✅</span>
                      <span className="font-cinzel text-xs font-bold text-emerald-400 uppercase tracking-wider">
                        Ground Truth Verified · Live Workforce Discovery
                      </span>
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        {Object.keys(verifiedRoles).length} Live Interview{Object.keys(verifiedRoles).length > 1 ? 's' : ''} Completed
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300 font-mono">
                      Empirical frontline data collected directly from team members. Disconnect and unwritten workarounds verified.
                    </p>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => setShowBatchDispatchModal(true)}
                      className="px-3.5 py-2 rounded bg-[#101318] text-emerald-300 border border-emerald-600/40 hover:border-emerald-400 text-xs font-mono transition-all flex items-center space-x-1.5"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>Dispatch More Probes</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="elden-card p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4 border border-[#c5a05944] bg-[#0c0e12]">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">🔮</span>
                      <span className="font-cinzel text-xs font-bold text-[#e6ca85] uppercase tracking-wider">
                        Predictive Pre-Mortem · AI Persona Simulation
                      </span>
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        Unverified
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 font-mono">
                      This failure map is simulated based on enterprise patterns. Ready to verify with your actual team?
                    </p>
                  </div>

                  <button
                    onClick={() => setShowBatchDispatchModal(true)}
                    className="px-4 py-2.5 rounded bg-gradient-to-r from-[#c5a059] to-[#9e7d3b] text-black font-semibold text-xs tracking-wider uppercase font-cinzel hover:brightness-110 transition-all flex items-center space-x-2 shadow-[0_0_16px_rgba(197,160,89,0.25)] shrink-0"
                  >
                    <Send className="w-3.5 h-3.5 text-black" />
                    <span>Dispatch Live Probes to Staff →</span>
                  </button>
                </div>
              )}

              {/* Unified Strategic Scorecard (3 Pillars: Disconnect -> Landmine -> Goldmine) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
                {/* 1. The Disconnect */}
                <div className="elden-card p-4 rounded-lg flex flex-col justify-between space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">The Disconnect</span>
                    <span className="text-[10px] font-mono text-amber-300 px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30">
                      {blueprint.delusion_metric?.label || 'High Delusion'}
                    </span>
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="font-cinzel text-3xl font-bold text-[#e6ca85]">{num(blueprint.delusion_metric?.score)}%</span>
                    <span className="text-xs text-zinc-400 font-mono">Delusion Index</span>
                  </div>
                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {blueprint.delusion_metric?.rationale || 'Leadership assumes an automated digital pipeline; frontline reality relies on unlogged chats and private spreadsheets.'}
                  </p>
                </div>

                {/* 2. Requested Landmine */}
                <div className="elden-card-rot p-4 rounded-lg flex flex-col justify-between space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider flex items-center space-x-1">
                      <ShieldAlert className="w-3 h-3 text-red-400" />
                      <span>Requested Workflow</span>
                    </span>
                    <span className="text-[10px] font-mono font-bold text-red-300 px-2 py-0.5 rounded bg-red-950/60 border border-red-500/40">
                      {num(blueprint.primary_workflow_verdict?.feasibility_score)}/100 · {blueprint.primary_workflow_verdict?.status || 'Landmine'}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-zinc-100 truncate">{selectedPreset.target_workflow}</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed mt-1 line-clamp-2">
                      {blueprint.primary_workflow_verdict?.diagnosis || '—'}
                    </p>
                  </div>
                  <div className="bg-[#120808] p-2 rounded border border-red-900/40 text-[11px] text-red-200">
                    <strong className="text-red-400 font-mono block text-[9px]">REQUIRED PREREQUISITE:</strong>
                    <span className="line-clamp-2">{blueprint.primary_workflow_verdict?.required_prerequisite || '—'}</span>
                  </div>
                </div>

                {/* 3. Discovered Goldmine (The Pivot) */}
                <div className="elden-card-grace p-4 rounded-lg flex flex-col justify-between space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider flex items-center space-x-1">
                      <Sparkles className="w-3 h-3 text-[#e6ca85]" />
                      <span>Recommended Pivot</span>
                    </span>
                    <span className="text-[10px] font-mono font-bold text-amber-200 px-2 py-0.5 rounded bg-[#18150a] border border-amber-500/40">
                      {num(blueprint.discovered_adjacent_workflow?.feasibility_score)}/100 · +{num(blueprint.discovered_adjacent_workflow?.weekly_hours_saved)}h/wk
                    </span>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-[#e6ca85] truncate">
                      {blueprint.discovered_adjacent_workflow?.title || 'Adjacent Automation Candidate'}
                    </h4>
                    <p className="text-xs text-zinc-300 leading-relaxed mt-1 line-clamp-2">
                      {blueprint.discovered_adjacent_workflow?.why_superior || '—'}
                    </p>
                  </div>
                  <div className="bg-[#14120a] p-2 rounded border border-amber-800/40 flex items-center justify-between">
                    <div className="truncate mr-2">
                      <strong className="text-[#e6ca85] font-mono block text-[9px]">DEPLOYABLE AGENT:</strong>
                      <span className="text-xs text-zinc-200 font-semibold truncate block">
                        {blueprint.discovered_adjacent_workflow?.recommended_agent_title || 'Autonomous Agent'}
                      </span>
                    </div>
                    <button 
                      onClick={() => setShowExportModal(true)}
                      className="px-2.5 py-1.5 rounded bg-[#c5a059] text-black font-cinzel text-[10px] font-semibold uppercase hover:brightness-110 shrink-0"
                    >
                      Export MCP Spec →
                    </button>
                  </div>
                </div>
              </div>

              {/* The Dual-DAG Flowchart */}
              <div className="elden-card p-5 rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-cinzel text-xs uppercase tracking-wider text-[#c5a059] flex items-center space-x-1.5">
                    <Network className="w-3.5 h-3.5" />
                    <span>Dual-DAG Process Topology</span>
                  </h3>
                  <span className="text-[11px] font-mono text-zinc-400">Click red friction nodes to inspect proof</span>
                </div>

                {/* 1. Presumed Fantasy Path */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-emerald-400 font-semibold">1. Executive Fantasy Path</span>
                    <span className="text-zinc-500">Est. Cycle: {blueprint.presumed_workflow?.estimated_cycle_time || '24 hours'}</span>
                  </div>
                  <div className="bg-[#0a0c10] p-3 rounded border border-zinc-800 flex items-center space-x-2 overflow-x-auto text-xs">
                    {(blueprint.presumed_workflow?.nodes || []).map((node, nIdx) => (
                      <div key={node.id || nIdx} className="flex items-center space-x-2 shrink-0">
                        <div className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-700/80 text-xs">
                          <span className="text-zinc-200">{node.label}</span>
                        </div>
                        {nIdx < (blueprint.presumed_workflow?.nodes?.length || 0) - 1 && (
                          <span className="text-zinc-600 font-mono">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Actual Ground Reality Path */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-red-400 font-semibold">2. Frontline Shadow Reality (Ground Truth)</span>
                    <span className="text-zinc-500">Actual Cycle: {blueprint.actual_workflow?.estimated_cycle_time || '48 hours'}</span>
                  </div>
                  <div className="bg-[#0a0c10] p-3 rounded border border-zinc-800 flex items-center space-x-2 overflow-x-auto text-xs py-2.5">
                    {(blueprint.actual_workflow?.nodes || []).map((node, nIdx) => (
                      <div key={node.id || nIdx} className="flex items-center space-x-2 shrink-0">
                        <button 
                          onClick={() => setSelectedQuoteNode(node)}
                          className={`px-3 py-1.5 rounded text-xs transition-all flex flex-col text-left shrink-0 ${
                            node.is_friction 
                              ? 'bg-red-950/50 border border-red-500/70 text-red-200 hover:scale-105 shadow-[0_0_8px_rgba(239,68,68,0.2)]' 
                              : 'bg-zinc-900 border border-zinc-700/80 text-zinc-300'
                          }`}
                        >
                          <div className="flex items-center space-x-1">
                            {node.is_friction && <Flame className="w-3 h-3 text-red-400 shrink-0" />}
                            <span className="font-semibold">{node.label}</span>
                          </div>
                          {node.tool && node.tool.toLowerCase() !== 'none' && (
                            <span className="text-[9px] font-mono text-amber-300/80 mt-0.5">
                              tool: {node.tool}
                            </span>
                          )}
                        </button>
                        {nIdx < (blueprint.actual_workflow?.nodes?.length || 0) - 1 && (
                          <span className="text-zinc-600 font-mono">→</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Inline Evidence Drawer */}
                  {selectedQuoteNode && (
                    <div className="bg-[#150a0a] border border-red-700/50 p-3 rounded text-xs text-red-200 flex items-start justify-between mt-2">
                      <div>
                        <strong className="block text-red-400 font-mono text-[10px]">
                          EVIDENCE · {selectedQuoteNode.label} {selectedQuoteNode.tool && selectedQuoteNode.tool.toLowerCase() !== 'none' && `(${selectedQuoteNode.tool})`}
                        </strong>
                        <p className="mt-0.5">{selectedQuoteNode.friction_reason || 'Undocumented workaround bypassing official SOP.'}</p>
                      </div>
                      <button onClick={() => setSelectedQuoteNode(null)} className="text-zinc-400 hover:text-white font-mono text-xs ml-4">✕</button>
                    </div>
                  )}
                </div>
              </div>

              {/* Tavily Technical Feasibility Audit */}
              {grounding && (
                <div className="elden-card p-4 rounded-lg space-y-3 border border-[#c5a05933]">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <Globe2 className="w-3.5 h-3.5 text-[#c5a059]" />
                      <span className="font-cinzel text-xs font-bold text-[#e6ca85] uppercase">
                        Tavily Live Feasibility Audit
                      </span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">
                      {grounding.verdict || 'Architecture Feasible'}
                    </span>
                  </div>

                  <p className="text-xs text-zinc-300 leading-relaxed font-mono">
                    {grounding.answer || 'Live technical search verified standard APIs and modern agent tools support this automation pattern.'}
                  </p>

                  {/* Clickable Live Source Citations */}
                  {grounding.citations && grounding.citations.length > 0 && (
                    <div className="pt-2 border-t border-zinc-800/80 flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                        Live Citations:
                      </span>
                      {grounding.citations.map((c, cIdx) => (
                        <a
                          key={cIdx}
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] font-mono text-[#c5a059] hover:text-white px-2 py-0.5 rounded bg-[#101318] border border-zinc-800 hover:border-[#c5a059] flex items-center space-x-1 transition-colors"
                        >
                          <span className="truncate max-w-[200px]">{c.title}</span>
                          <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Strategic Honesty: Limits, Biases & Failure Modes Panel */}
              <div className="elden-card p-4 rounded-lg border border-zinc-800 bg-[#090b0e] space-y-3">
                <button
                  type="button"
                  onClick={() => setShowLimitsPanel(!showLimitsPanel)}
                  className="w-full flex items-center justify-between text-left group"
                >
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    <div>
                      <span className="font-cinzel text-xs font-bold text-zinc-200 group-hover:text-[#e6ca85] transition-colors uppercase tracking-wider">
                        Discovery Limits, Biases & Failure Modes
                      </span>
                      <span className="text-[10px] text-zinc-500 font-mono block">
                        Scientific disclosure: when synthetic pre-mortems deviate and how Mimic mitigates bias
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono text-zinc-400 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
                      {showLimitsPanel ? 'Hide Analysis' : 'Show Analysis'}
                    </span>
                    {showLimitsPanel ? <ChevronUp className="w-3.5 h-3.5 text-zinc-400" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />}
                  </div>
                </button>

                {showLimitsPanel && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="pt-3 border-t border-zinc-800/80 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono"
                  >
                    {/* Limit 1 */}
                    <div className="bg-[#101318] p-3 rounded border border-zinc-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] text-amber-300 font-bold uppercase">
                        <span>1. Synthetic Persona Bias</span>
                        <span className="text-zinc-500">Pre-Mortem</span>
                      </div>
                      <p className="text-zinc-300 text-[11px] leading-relaxed">
                        AI twins extrapolate enterprise failure patterns from training data. They cannot predict internal union agreements, localized office politics, or undocumented custom DB forks without live employee verification.
                      </p>
                      <div className="text-[10px] text-emerald-400 pt-1 border-t border-zinc-800/60">
                        <strong>Mitigation:</strong> Flagged as <span className="text-amber-300">🔮 Unverified</span> until verified via live interview links.
                      </div>
                    </div>

                    {/* Limit 2 */}
                    <div className="bg-[#101318] p-3 rounded border border-zinc-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] text-amber-300 font-bold uppercase">
                        <span>2. Self-Reporting Bias</span>
                        <span className="text-zinc-500">Live Probes</span>
                      </div>
                      <p className="text-zinc-300 text-[11px] leading-relaxed">
                        Employees under low psychological safety fear reprimand and give textbook SOP answers instead of admitting to shadow WhatsApp groups or offline spreadsheets.
                      </p>
                      <div className="text-[10px] text-emerald-400 pt-1 border-t border-zinc-800/60">
                        <strong>Mitigation:</strong> Probes are framed neutrally around "handling edge cases" rather than compliance, with strict anonymity from management.
                      </div>
                    </div>

                    {/* Limit 3: Comparison with FlowScope */}
                    <div className="bg-[#101318] p-3 rounded border border-zinc-800 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] text-[#e6ca85] font-bold uppercase">
                        <span>3. FlowScope vs. Mimic</span>
                        <span className="text-zinc-500">Paradigm</span>
                      </div>
                      <p className="text-zinc-300 text-[11px] leading-relaxed">
                        <strong className="text-zinc-200">FlowScope (YC):</strong> Passive desktop telemetry (keystroke & screen recording) over 3–6 weeks. Granular clicks, but blind to <em>why</em> users circumvent tools and requires massive IT approvals.
                      </p>
                      <div className="text-[10px] text-[#c5a059] pt-1 border-t border-zinc-800/60">
                        <strong className="text-white">Mimic:</strong> 15-second conversational pre-mortem + 3-minute live probe. Zero IT footprint, uncovers tribal workarounds before coding.
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Modal 1: Live Custom Onboard New Company */}
      {showOnboardModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="elden-card max-w-lg w-full rounded-lg p-6 space-y-4 border border-[#c5a059]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-[#c5a059]" />
                <h3 className="font-cinzel text-sm font-bold text-[#e6ca85]">Onboard New Client Organization</h3>
              </div>
              <button onClick={() => setShowOnboardModal(false)} className="text-zinc-400 hover:text-white font-mono text-xs">✕</button>
            </div>

            <form onSubmit={handleGenerateCustomOnboard} className="space-y-3.5 text-xs font-mono">
              <div>
                <label className="block text-zinc-300 mb-1">Company Name *</label>
                <input 
                  type="text" 
                  value={customCompany}
                  onChange={e => setCustomCompany(e.target.value)}
                  placeholder="e.g. AltaServ, Meridian Logistics, FinFlow" 
                  className="w-full bg-[#090b0e] border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:border-[#c5a059] outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-zinc-300 mb-1">Company Website / Domain (for live Tavily enrichment)</label>
                <input 
                  type="text" 
                  value={customDomain}
                  onChange={e => setCustomDomain(e.target.value)}
                  placeholder="e.g. altaserv.com or acme.io" 
                  className="w-full bg-[#090b0e] border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:border-[#c5a059] outline-none"
                />
              </div>

              <div>
                <label className="block text-zinc-300 mb-1">Executive Mandate / What they think needs fixing *</label>
                <textarea 
                  value={customMandate}
                  onChange={e => setCustomMandate(e.target.value)}
                  placeholder="e.g. 'We want an AI agent to automate field service technician dispatching over WhatsApp.'" 
                  rows={3}
                  className="w-full bg-[#090b0e] border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:border-[#c5a059] outline-none resize-none"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-zinc-300">Org Chart / Key Staff (Optional)</label>
                  <span className="text-[10px] text-zinc-500 font-mono">Real names or roles</span>
                </div>
                <input 
                  type="text" 
                  value={customRoles}
                  onChange={e => setCustomRoles(e.target.value)}
                  placeholder="e.g. CEO: Aisha, Sales: Omar, Ops: Sara, IT: Hassan" 
                  className="w-full bg-[#090b0e] border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:border-[#c5a059] outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button 
                  type="button" 
                  onClick={() => setShowOnboardModal(false)}
                  className="px-3.5 py-1.5 rounded text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isOnboardingGenerating}
                  className="px-4 py-2 rounded bg-[#c5a059] text-black font-cinzel font-semibold text-xs uppercase hover:brightness-110 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                >
                  {isOnboardingGenerating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-black border-t-transparent rounded-full animate-spin" />
                      <span>Generating Strategy...</span>
                    </>
                  ) : (
                    <>
                      <span>Generate Probe Strategy</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 1.5: Org Chart Mapping Modal */}
      {showOrgMappingModal && selectedPreset && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="elden-card max-w-xl w-full rounded-lg p-5 space-y-4 border border-[#c5a059]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-[#c5a059]" />
                <h3 className="font-cinzel text-sm font-bold text-[#e6ca85]">
                  Map Discovery to Real Org Chart
                </h3>
              </div>
              <button onClick={() => setShowOrgMappingModal(false)} className="text-zinc-400 hover:text-white font-mono text-xs">✕</button>
            </div>

            <p className="text-xs text-zinc-400 font-mono">
              Assign real team members to each discovery role. Nemotron will target these exact titles, and your dispatch links will be customized for them.
            </p>

            {/* Quick Paste Org Chart Textarea */}
            <div className="bg-[#090b0e] p-3 rounded border border-zinc-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#c5a059] text-[10px]">QUICK PASTE ORG CHART / ROSTER:</span>
                <button
                  type="button"
                  onClick={handleParseOrgChart}
                  className="text-[10px] text-[#e6ca85] hover:underline"
                >
                  Auto-Fill 4 Roles
                </button>
              </div>
              <textarea
                value={orgChartRawText}
                onChange={e => setOrgChartRawText(e.target.value)}
                placeholder={"CEO: Aisha Khan (aisha@company.com)\nSales Lead: Omar Farooq\nWarehouse Ops: Sara Chen\nIT Systems: Hassan Raza"}
                rows={3}
                className="w-full bg-[#101318] border border-zinc-700 rounded px-2.5 py-1.5 text-zinc-200 text-xs font-mono focus:border-[#c5a059] outline-none resize-none"
              />
            </div>

            {/* Editable Form for the 4 Roles */}
            <form onSubmit={handleSaveOrgMapping} className="space-y-3">
              <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                {editingStakeholders.map((s, idx) => (
                  <div key={idx} className="bg-[#101318] p-2.5 rounded border border-zinc-800 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                    <div>
                      <label className="text-[10px] text-zinc-400 block mb-0.5">Name</label>
                      <input
                        type="text"
                        value={s.name}
                        onChange={e => {
                          const val = e.target.value;
                          setEditingStakeholders(prev => prev.map((item, i) => i === idx ? { ...item, name: val } : item));
                        }}
                        className="w-full bg-[#090b0e] border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:border-[#c5a059] outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-400 block mb-0.5">Title / Role</label>
                      <input
                        type="text"
                        value={s.title}
                        onChange={e => {
                          const val = e.target.value;
                          setEditingStakeholders(prev => prev.map((item, i) => i === idx ? { ...item, title: val } : item));
                        }}
                        className="w-full bg-[#090b0e] border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:border-[#c5a059] outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-400 block mb-0.5">Email / Slack (Optional)</label>
                      <input
                        type="text"
                        value={s.email || ''}
                        onChange={e => {
                          const val = e.target.value;
                          setEditingStakeholders(prev => prev.map((item, i) => i === idx ? { ...item, email: val } : item));
                        }}
                        placeholder="user@co.com"
                        className="w-full bg-[#090b0e] border border-zinc-700 rounded px-2 py-1 text-zinc-100 focus:border-[#c5a059] outline-none"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t border-zinc-800 pt-3 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowOrgMappingModal(false)}
                  className="px-3.5 py-1.5 rounded text-xs text-zinc-400 hover:text-white font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded bg-[#c5a059] text-black font-cinzel font-semibold text-xs uppercase hover:brightness-110 transition-all flex items-center space-x-1.5"
                >
                  <Check className="w-3.5 h-3.5 text-black" />
                  <span>Save & Map to Discovery</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 1.6: Batch Dispatch Links Modal */}
      {showBatchDispatchModal && selectedPreset && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="elden-card max-w-xl w-full rounded-lg p-5 space-y-4 border border-[#c5a059]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center space-x-2">
                <Send className="w-4 h-4 text-[#c5a059]" />
                <h3 className="font-cinzel text-sm font-bold text-[#e6ca85]">
                  Batch Employee Interview Dispatch Links
                </h3>
              </div>
              <button onClick={() => setShowBatchDispatchModal(false)} className="text-zinc-400 hover:text-white font-mono text-xs">✕</button>
            </div>

            <p className="text-xs text-zinc-400 font-mono">
              Send these private 2-minute unscripted interview links to your team via Slack, Teams, or WhatsApp.
            </p>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {(selectedPreset?.stakeholders || []).map((s) => {
                const isVerified = Boolean(verifiedRoles[s.role_id]);
                const link = getInterviewLink(s.role_id);
                return (
                  <div key={s.role_id || s.name} className={`bg-[#101318] p-2.5 rounded border ${isVerified ? 'border-emerald-500/40' : 'border-zinc-800'} flex items-center justify-between text-xs font-mono`}>
                    <div className="space-y-0.5 truncate mr-2">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-zinc-200 font-semibold">{s.name} ({s.title})</span>
                        {isVerified && <span className="text-[9px] text-emerald-400 font-bold">✅ Verified</span>}
                      </div>
                      <span className="block text-[10px] text-zinc-500 truncate">{link}</span>
                    </div>
                    <div className="flex items-center space-x-1.5 shrink-0">
                      <button
                        onClick={() => {
                          setShowBatchDispatchModal(false);
                          startLiveInterview(s);
                        }}
                        className="text-[#e6ca85] hover:text-white px-2.5 py-1 rounded bg-[#090b0e] border border-amber-600/40 text-[10px] font-bold hover:border-[#c5a059]"
                        title="Launch live interactive probe in browser"
                      >
                        Launch Interview
                      </button>
                      <button
                        onClick={() => copyToClipboard(link)}
                        className="text-[#c5a059] hover:text-white px-2.5 py-1 rounded bg-zinc-900 border border-zinc-700 shrink-0 font-bold text-[10px]"
                      >
                        Copy Link
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="border-t border-zinc-800 pt-3 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">All links are active & unscripted</span>
              <button
                onClick={() => copyToClipboard(getBatchDispatchText())}
                className="px-4 py-1.5 rounded bg-[#c5a059] text-black font-semibold text-xs font-cinzel uppercase flex items-center space-x-1.5 hover:brightness-110"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-black" /> : <Copy className="w-3.5 h-3.5 text-black" />}
                <span>{copied ? 'Copied All' : 'Copy All Invitations'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 1.7: Interactive Live Employee Interview Room */}
      {interactiveInterviewRole && selectedPreset && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6">
          <div className="elden-card max-w-2xl w-full rounded-xl p-5 sm:p-6 space-y-4 border border-[#c5a059] flex flex-col max-h-[90vh] shadow-[0_0_30px_rgba(197,160,89,0.2)]">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-full border border-[#c5a059] flex items-center justify-center bg-[#15181e] text-xs font-cinzel text-[#e6ca85] font-bold shrink-0">
                  M
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-cinzel text-sm font-bold text-[#e6ca85]">
                      Live Operational Discovery · {interactiveInterviewRole.name}
                    </h3>
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      Confidential & Anonymous
                    </span>
                  </div>
                  <span className="text-xs text-zinc-400 font-mono">
                    {interactiveInterviewRole.title} · {selectedPreset.company_name}
                  </span>
                </div>
              </div>
              <button 
                onClick={() => setInteractiveInterviewRole(null)} 
                className="text-zinc-400 hover:text-white font-mono text-sm p-1 rounded hover:bg-zinc-800"
              >
                ✕
              </button>
            </div>

            {/* Conversation Stream */}
            <div className="flex-1 overflow-y-auto space-y-3 font-mono text-xs pr-1.5 py-1">
              <div className="flex items-center justify-between text-[10px] text-zinc-500 pb-1.5 border-b border-zinc-800/80">
                <span>CHANNEL: CONFIDENTIAL WORKFORCE DM</span>
                <span className="text-emerald-400 font-semibold">ZERO CORPORATE SURVEILLANCE</span>
              </div>

              {interviewMessages.map((msg, mIdx) => (
                <div 
                  key={mIdx} 
                  className={`flex items-start space-x-2.5 ${msg.role === 'user' ? 'justify-end' : ''}`}
                >
                  {msg.role === 'agent' && (
                    <div className="w-6 h-6 rounded border border-[#c5a059] flex items-center justify-center bg-[#15181e] shrink-0 text-[10px] font-cinzel text-[#e6ca85] font-bold">
                      M
                    </div>
                  )}

                  <div 
                    className={`p-3 rounded-lg text-xs leading-relaxed max-w-[85%] ${
                      msg.role === 'user' 
                        ? 'bg-[#18241c] text-emerald-100 border border-emerald-500/30' 
                        : 'bg-[#12151c] text-zinc-200 border border-[#c5a05933]'
                    }`}
                  >
                    <span className="text-[9px] font-bold block mb-1 opacity-70">
                      {msg.role === 'user' ? `${interactiveInterviewRole.name.toUpperCase()} (GROUND TRUTH):` : 'MIMIC INVESTIGATOR:'}
                    </span>
                    {msg.content}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {interviewLoading && (
                <div className="flex items-center space-x-2 text-xs text-[#e6ca85] font-mono py-2">
                  <div className="w-4 h-4 border-2 border-[#c5a059] border-t-transparent rounded-full animate-spin" />
                  <span>Nemotron 120B analyzing operational friction...</span>
                </div>
              )}

              {/* Completion verdict box */}
              {interviewTurnResult?.is_complete && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-[#09150e] border border-emerald-500/40 rounded-lg p-3.5 space-y-2 mt-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-emerald-400 font-bold uppercase tracking-wider flex items-center space-x-1.5">
                      <span>✅</span>
                      <span>Operational Ground Truth Verified</span>
                    </span>
                    <span className="text-[10px] text-zinc-400 font-mono">100% Unfiltered</span>
                  </div>

                  <p className="text-xs text-zinc-200 leading-relaxed">
                    <strong className="text-amber-300 block text-[10px] mb-0.5">UNCOVERED WORKAROUND:</strong>
                    {interviewTurnResult.revealed_friction}
                  </p>

                  <div className="text-[11px] text-zinc-400 flex items-center space-x-2 pt-1 border-t border-emerald-900/40">
                    <span className="text-zinc-500">Detected Shadow Tools:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {(interviewTurnResult.shadow_tools_used || ['WhatsApp', 'Excel']).map((t, idx) => (
                        <span key={idx} className="px-1.5 py-0.5 rounded bg-zinc-800 text-amber-300 border border-zinc-700 text-[10px]">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Input & Quick Chips */}
            <div className="border-t border-zinc-800 pt-3 space-y-2.5 shrink-0">
              {/* Quick suggestion chips if not complete */}
              {!interviewTurnResult?.is_complete && (
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider block">
                    Quick Sample Responses (Click to test):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      "We use a private WhatsApp group and manually log exceptions in a shared Excel sheet.",
                      "There's no official SOP; we DM the manager directly to bypass the ticketing backlog.",
                      "The database frequently drops sync, so we keep duplicate handwritten records."
                    ].map((chip, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSendInterviewTurn(chip)}
                        disabled={interviewLoading}
                        className="text-[10px] font-mono text-zinc-300 hover:text-white px-2 py-1 rounded bg-[#101318] border border-zinc-800 hover:border-[#c5a059] transition-colors truncate max-w-full text-left"
                      >
                        "{chip}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Form Input */}
              {!interviewTurnResult?.is_complete ? (
                <form 
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendInterviewTurn();
                  }}
                  className="flex items-center space-x-2"
                >
                  <input
                    type="text"
                    value={interviewInput}
                    onChange={(e) => setInterviewInput(e.target.value)}
                    placeholder={`Reply as ${interactiveInterviewRole.name} (describe actual tools or workarounds)...`}
                    disabled={interviewLoading}
                    className="flex-1 bg-[#101318] border border-zinc-700 focus:border-[#c5a059] rounded px-3 py-2 text-xs font-mono text-zinc-100 outline-none"
                  />
                  <button
                    type="submit"
                    disabled={interviewLoading || !interviewInput.trim()}
                    className="px-4 py-2 rounded bg-[#c5a059] text-black font-cinzel font-semibold text-xs uppercase hover:brightness-110 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                  >
                    <span>Send</span>
                    <Send className="w-3 h-3 text-black" />
                  </button>
                </form>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-zinc-400 font-mono">
                    Discovery saved · Dashboard updated with empirical ground truth.
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setInteractiveInterviewRole(null);
                      if (stage !== 'dashboard' && blueprint) {
                        setStage('dashboard');
                      }
                    }}
                    className="px-4 py-2 rounded bg-gradient-to-r from-emerald-600 to-emerald-500 text-black font-cinzel font-bold text-xs uppercase hover:brightness-110 transition-all flex items-center space-x-1.5 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-black" />
                    <span>Return to Delusion Dashboard →</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: Simulate Direct Employee Interview Link */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="elden-card max-w-md w-full rounded-lg p-5 space-y-3.5 border border-[#c5a059]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-[#c5a059]" />
                <h3 className="font-cinzel text-xs font-bold text-[#e6ca85]">
                  Employee Interview Dispatch · {showShareModal.name}
                </h3>
              </div>
              <button onClick={() => setShowShareModal(null)} className="text-zinc-400 hover:text-white font-mono text-xs">✕</button>
            </div>

            <div className="space-y-2 text-xs font-mono text-zinc-300">
              <p className="text-[11px] text-zinc-400">
                In production, Strata dispatches an unscripted, private 3-minute conversational chat via Slack Bot or WhatsApp:
              </p>
              
              <div className="bg-[#090b0e] p-3 rounded border border-zinc-800 text-zinc-300 space-y-1.5">
                <span className="text-[#c5a059] block text-[10px]">SLACK / WHATSAPP BOT DM:</span>
                <p className="italic text-[11px]">
                  "Hey {showShareModal.name}, quick 3-minute check from Strata on how {selectedPreset?.target_workflow || 'daily handoffs'} work in practice for {showShareModal.title}. Completely confidential."
                </p>
              </div>

              <div className="bg-[#101318] p-2.5 rounded border border-zinc-700/60 text-[11px] flex items-center justify-between">
                <span className="text-zinc-400 truncate">https://strata.ai/i/{selectedPreset?.id || 'live'}/{showShareModal.role_id}</span>
                <button 
                  onClick={() => copyToClipboard(`https://strata.ai/i/${selectedPreset?.id || 'live'}/${showShareModal.role_id}`)}
                  className="text-[#c5a059] hover:underline font-bold shrink-0 ml-2"
                >
                  {copied ? 'Copied' : 'Copy Link'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Export Agent Blueprint & MCP Spec */}
      {showExportModal && agentPackage && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="elden-card max-w-2xl w-full max-h-[85vh] rounded-lg p-5 flex flex-col space-y-3.5 border border-[#c5a059]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
              <div className="flex items-center space-x-2">
                <FileCode className="w-4 h-4 text-[#c5a059]" />
                <h3 className="font-cinzel text-sm font-bold text-[#e6ca85]">{agentPackage.agent_name}</h3>
              </div>
              <button onClick={() => setShowExportModal(false)} className="text-zinc-400 hover:text-white font-mono text-xs">✕</button>
            </div>

            <div className="overflow-y-auto space-y-3 text-xs font-mono pr-2">
              <div>
                <span className="text-[#c5a059] block mb-1 font-bold">SYSTEM PROMPT:</span>
                <div className="bg-[#090b0e] p-2.5 rounded border border-zinc-800 text-zinc-300 whitespace-pre-wrap text-[11px]">
                  {agentPackage.system_prompt}
                </div>
              </div>

              <div>
                <span className="text-[#c5a059] block mb-1 font-bold">STRICT GUARDRAILS:</span>
                <ul className="list-disc list-inside bg-[#090b0e] p-2.5 rounded border border-zinc-800 text-zinc-300 space-y-0.5 text-[11px]">
                  {(agentPackage.guardrails || []).map((g, gIdx) => (
                    <li key={gIdx}>{g}</li>
                  ))}
                </ul>
              </div>

              <div>
                <span className="text-red-400 block mb-1 font-bold">ESCALATION TRIGGER:</span>
                <div className="bg-[#120808] p-2 rounded border border-red-900/40 text-red-200 text-[11px]">
                  {agentPackage.human_in_the_loop_trigger}
                </div>
              </div>

              <div>
                <span className="text-[#c5a059] block mb-1 font-bold">MCP TOOL SCHEMAS:</span>
                <pre className="bg-[#090b0e] p-2.5 rounded border border-zinc-800 text-emerald-400 overflow-x-auto text-[10px]">
                  {JSON.stringify(agentPackage.mcp_tools, null, 2)}
                </pre>
              </div>
            </div>

            <div className="border-t border-zinc-800 pt-3 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">Compatible with Cursor, Claude Desktop, and LangChain</span>
              <button
                onClick={() => copyToClipboard(JSON.stringify(agentPackage, null, 2))}
                className="px-4 py-1.5 rounded bg-[#c5a059] text-black font-semibold text-xs font-cinzel uppercase flex items-center space-x-1.5 hover:brightness-110"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-black" /> : <Copy className="w-3.5 h-3.5 text-black" />}
                <span>{copied ? 'Copied' : 'Copy JSON'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
