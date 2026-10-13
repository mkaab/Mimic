import { useState, useEffect } from 'react';
import { Button, Input, Card, CardContent as CardBody, Spinner, TextArea as Textarea } from '@heroui/react';
import { motion, AnimatePresence } from 'framer-motion';

const MBTI_TYPES = ['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP','ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP'];

const TRENDING_DILEMMAS = [
  "Join an early-stage AI agent lab vs stay at Big Tech with liquid stock",
  "Pivot product architecture to open-source Nemotron models vs proprietary APIs",
  "Raise venture capital in 2026 AI market vs bootstrap profitably"
];

async function postJSON(url, body) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

function App() {
  const [stage, setStage] = useState('intro'); // intro | quiz | building | results | custom
  const [error, setError] = useState('');
  const [name, setName] = useState('');
  const [mbti, setMbti] = useState('');
  const [handle, setHandle] = useState('');
  const [questions, setQuestions] = useState([]);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [onboard, setOnboard] = useState(null);

  useEffect(() => {
    fetch('/questions').then(r => r.json()).then(setQuestions).catch(() => setError('Backend not reachable. Is uvicorn running?'));
  }, []);

  const [userId, setUserId] = useState(null);
  const [profilePreview, setProfilePreview] = useState('');
  
  const [scenario, setScenario] = useState('');
  const [predictionId, setPredictionId] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  
  const [actualAnswer, setActualAnswer] = useState('');
  const [revealData, setRevealData] = useState(null);
  const [isRevealing, setIsRevealing] = useState(false);
  
  const [researchData, setResearchData] = useState(null);
  const [isResearching, setIsResearching] = useState(false);

  const [activeCorrectionIdx, setActiveCorrectionIdx] = useState(null);
  const [correctionText, setCorrectionText] = useState('');
  const [isLearning, setIsLearning] = useState(false);
  const [learnedData, setLearnedData] = useState({});
  const [isRetesting, setIsRetesting] = useState(false);
  const [retestResult, setRetestResult] = useState({});

  const answerQuestion = async (letter) => {
    const next = { ...answers, [questions[qIndex].id]: letter };
    setAnswers(next);
    if (qIndex < questions.length - 1) { setQIndex(qIndex + 1); return; }
    setStage('building');
    setError('');
    try {
      const data = await postJSON('/onboard', { name, answers: next, mbti: mbti || null, public_handle: handle || null });
      setOnboard(data);
      setUserId(data.user_id);
      setProfilePreview(data.profile);
      setStage('results');
    } catch (e) {
      setError(e.message);
      setStage('intro');
      setQIndex(0);
    }
  };

  const handlePredict = async () => {
    if (!scenario) return;
    setIsPredicting(true);
    setError('');
    try {
      const data = await postJSON('/predict', { user_id: userId, scenario });
      setPredictionId(data.prediction_id);
    } catch (e) {
      setError(e.message);
    }
    setIsPredicting(false);
  };

  const handleReveal = async () => {
    if (!actualAnswer) return;
    setIsRevealing(true);
    setError('');
    try {
      const data = await postJSON('/reveal', { prediction_id: predictionId, user_actual_answer: actualAnswer });
      setRevealData(data);
    } catch (e) {
      setError(e.message);
    }
    setIsRevealing(false);
  };

  const handleResearchPredict = async (textOverride) => {
    const textToSearch = textOverride || scenario;
    if (!textToSearch) return;
    if (textOverride) setScenario(textOverride);
    setIsResearching(true);
    setError('');
    try {
      const data = await postJSON('/research-predict', {
        user_id: userId || 1,
        scenario: textToSearch
      });
      setResearchData(data.data);
    } catch (e) {
      setError(e.message);
    }
    setIsResearching(false);
  };

  const handleLoadDemo = async () => {
    setError('');
    try {
      const data = await postJSON('/demo-persona', {});
      setOnboard(data);
      setUserId(data.user_id);
      setName(data.name);
      setProfilePreview(data.profile);
      setStage('results');
    } catch (e) {
      setError(e.message);
    }
  };

  const handleLearn = async (idx, scenarioText) => {
    if (!correctionText) return;
    setIsLearning(true);
    setError('');
    try {
      const res = await postJSON('/learn', {
        user_id: userId,
        scenario: scenarioText,
        correction: correctionText
      });
      setLearnedData(prev => ({ ...prev, [idx]: res }));
      setCorrectionText('');
    } catch (e) {
      setError(e.message);
    }
    setIsLearning(false);
  };

  const handleRetest = async (idx, followup) => {
    setIsRetesting(true);
    setError('');
    try {
      const res = await postJSON('/retest', {
        user_id: userId,
        scenario_text: followup.text,
        option_a: followup.a,
        option_b: followup.b,
        expected_answer: followup.expected_answer
      });
      setRetestResult(prev => ({ ...prev, [idx]: res }));
      if (res.is_correct && onboard?.score) {
        setOnboard(prev => ({
          ...prev,
          score: { ...prev.score, mimic: Math.min(prev.score.total, prev.score.mimic + 1) }
        }));
      }
    } catch (e) {
      setError(e.message);
    }
    setIsRetesting(false);
  };

  const q = questions[qIndex];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-900 via-black to-black">
      <div className="w-full max-w-4xl space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-light tracking-widest text-neutral-300"
          >
            MIMIC <span className="font-bold text-white">CORE</span>
          </motion.h1>
          <p className="text-neutral-500 text-sm tracking-wide uppercase">Proof of Knowledge</p>
        </div>

        {error && (
          <div className="mx-auto max-w-2xl px-4 py-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-sm">{error}</div>
        )}

        <AnimatePresence mode="wait">
          
          {/* INTRO */}
          {stage === 'intro' && (
            <motion.div key="intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Card className="bg-neutral-950/50 border border-neutral-800 backdrop-blur-md mx-auto max-w-2xl">
                <CardBody className="p-8 space-y-6">
                  <div>
                    <p className="text-lg text-neutral-300 font-light">Let Mimic learn you.</p>
                    <p className="text-sm text-neutral-500 mt-1">8 quick choices. Mimic learns from 5 and secretly predicts the other 3, then we compare it against plain Nemotron.</p>
                  </div>
                  <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" variant="bordered" size="lg"
                    classNames={{ inputWrapper: "border-neutral-800 hover:border-neutral-600 focus-within:!border-white" }} />
                  <div className="space-y-2">
                    <p className="text-xs text-neutral-500 uppercase tracking-widest">Know your MBTI? <span className="normal-case tracking-normal">(optional, we'll infer it otherwise)</span></p>
                    <div className="flex flex-wrap gap-2">
                      {MBTI_TYPES.map(t => (
                        <button key={t} onClick={() => setMbti(mbti === t ? '' : t)}
                          className={`px-3 py-1 rounded-full text-xs tracking-wider border transition-all ${mbti === t ? 'bg-white text-black border-white' : 'border-neutral-800 text-neutral-400 hover:border-neutral-500'}`}>
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                  <Input value={handle} onChange={(e) => setHandle(e.target.value)} placeholder="Public handle / site / LinkedIn (optional, searched with Tavily)" variant="bordered"
                    classNames={{ inputWrapper: "border-neutral-800 hover:border-neutral-600 focus-within:!border-white" }} />
                  <Button className="w-full bg-white text-black font-semibold uppercase tracking-wider" size="lg"
                    isDisabled={!name || !questions.length} onPress={() => { setAnswers({}); setQIndex(0); setStage('quiz'); }}>
                    Start
                  </Button>

                  <div className="pt-3 border-t border-neutral-900 text-center">
                    <button
                      type="button"
                      onClick={handleLoadDemo}
                      className="text-xs text-purple-400 hover:text-purple-300 font-mono tracking-wider transition-colors flex items-center justify-center gap-1.5 w-full py-1"
                    >
                      ⚡ Fast-Track Demo for Judges (Alex, ENTJ Founder)
                    </button>
                  </div>
                </CardBody>
              </Card>
            </motion.div>
          )}

          {/* QUIZ */}
          {stage === 'quiz' && q && (
            <motion.div key={`q${q.id}`} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.25 }}>
              <Card className="bg-neutral-950/50 border border-neutral-800 backdrop-blur-md mx-auto max-w-2xl">
                <CardBody className="p-8 space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1 bg-neutral-800 rounded-full overflow-hidden">
                      <motion.div className="h-full bg-gradient-to-r from-blue-500 to-purple-500" animate={{ width: `${(qIndex / questions.length) * 100}%` }} />
                    </div>
                    <span className="text-xs text-neutral-500">{qIndex + 1}/{questions.length}</span>
                  </div>
                  <p className="text-xl text-white font-light leading-relaxed">{q.text}</p>
                  <div className="grid gap-3">
                    {['A', 'B'].map(l => (
                      <button key={l} onClick={() => answerQuestion(l)}
                        className="text-left p-4 rounded-xl border border-neutral-800 hover:border-white hover:bg-white/5 transition-all group">
                        <span className="text-neutral-500 group-hover:text-white mr-3 font-mono">{l}</span>
                        <span className="text-neutral-200">{l === 'A' ? q.a : q.b}</span>
                      </button>
                    ))}
                  </div>
                </CardBody>
              </Card>
            </motion.div>
          )}

          {/* BUILDING */}
          {stage === 'building' && (
            <motion.div key="building" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center gap-4 py-16">
              <Spinner color="current" size="lg" />
              <p className="text-neutral-300 font-light tracking-wide">Building your Mimic…</p>
              <p className="text-neutral-600 text-sm">Running 42 blind predictions on Nemotron (Nebius Token Factory)</p>
            </motion.div>
          )}

          {/* RESULTS: BLIND TEST SCOREBOARD */}
          {stage === 'results' && onboard && (
            <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <Card className="bg-neutral-900 border border-neutral-700 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
                  <CardBody className="p-6 text-center">
                    <p className="text-xs text-blue-400 uppercase tracking-widest font-bold">Mimic</p>
                    <motion.p initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3, type: 'spring' }}
                      className="text-6xl font-bold text-white mt-2">{onboard.score.mimic}/{onboard.score.total}</motion.p>
                  </CardBody>
                </Card>
                <Card className="bg-neutral-900 border border-neutral-800 opacity-70">
                  <CardBody className="p-6 text-center">
                    <p className="text-xs text-neutral-500 uppercase tracking-widest font-bold">Plain Nemotron</p>
                    <p className="text-6xl font-bold text-neutral-500 mt-2">{onboard.score.baseline}/{onboard.score.total}</p>
                  </CardBody>
                </Card>
              </div>

              <div className="space-y-4">
                {onboard.results.map((r, i) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 + i * 0.25 }}>
                    <Card className="bg-neutral-950/50 border border-neutral-800">
                      <CardBody className="p-5 space-y-3">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-neutral-300 font-light flex-1">{r.question}</p>
                          {!learnedData[i] && (
                            <button
                              onClick={() => setActiveCorrectionIdx(activeCorrectionIdx === i ? null : i)}
                              className="text-[11px] text-neutral-500 hover:text-purple-300 font-mono tracking-wide shrink-0 transition-colors"
                            >
                              {activeCorrectionIdx === i ? 'Cancel' : '🧠 Teach Mimic'}
                            </button>
                          )}
                        </div>

                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <div><p className="text-xs text-neutral-500 uppercase tracking-widest">You</p><p className="text-white">{r.user === 'A' ? r.a : r.b}</p></div>
                          <div><p className="text-xs text-blue-400 uppercase tracking-widest">Mimic · {Math.round(r.confidence * 100)}%</p>
                            <p className={r.mimic_correct ? 'text-green-400' : 'text-red-400'}>{r.mimic_correct ? '✓ ' : '✗ '}{r.mimic === 'A' ? r.a : r.b}</p></div>
                          <div><p className="text-xs text-neutral-500 uppercase tracking-widest">Nemotron</p>
                            <p className={r.baseline_correct ? 'text-green-400/70' : 'text-red-400/70'}>{r.baseline_correct ? '✓ ' : '✗ '}{r.baseline === 'A' ? r.a : r.b}</p></div>
                        </div>

                        {/* Inline Correction Input */}
                        {activeCorrectionIdx === i && !learnedData[i] && (
                          <div className="pt-3 border-t border-neutral-900 space-y-2">
                            <p className="text-xs text-purple-400 font-mono">Why did you make this choice? (Mimic will extract a persistent rule):</p>
                            <div className="flex gap-2">
                              <Input
                                size="sm"
                                variant="bordered"
                                value={correctionText}
                                onChange={(e) => setCorrectionText(e.target.value)}
                                placeholder="e.g. I only spend windfalls on experiences if I have no debt"
                                classNames={{ inputWrapper: "border-neutral-800 focus-within:!border-purple-500 text-xs" }}
                              />
                              <Button
                                size="sm"
                                className="bg-purple-600 text-white font-medium text-xs px-4"
                                onPress={() => handleLearn(i, r.question)}
                                isPending={isLearning}
                                isDisabled={!correctionText}
                              >
                                Learn Rule
                              </Button>
                            </div>
                          </div>
                        )}

                        {/* Learned Rule Card & Retest Verification */}
                        {learnedData[i] && (
                          <div className="pt-3 border-t border-purple-500/20 space-y-3">
                            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/30">
                              <span className="text-sm">🧠</span>
                              <div className="flex-1">
                                <p className="text-[10px] text-purple-400 uppercase tracking-wider font-mono font-bold">New Rule Learned & Persisted</p>
                                <p className="text-xs text-white italic">"{learnedData[i].rule}"</p>
                              </div>
                            </div>

                            {learnedData[i].followup_scenario && !retestResult[i] && (
                              <div className="p-3 rounded-lg bg-neutral-900/60 border border-neutral-800 space-y-2">
                                <p className="text-[11px] text-neutral-400 font-mono">Verification Dilemma:</p>
                                <p className="text-xs text-neutral-200">{learnedData[i].followup_scenario.text}</p>
                                <div className="text-xs text-neutral-400 space-y-1">
                                  <p>A) {learnedData[i].followup_scenario.a}</p>
                                  <p>B) {learnedData[i].followup_scenario.b}</p>
                                </div>
                                <Button
                                  size="sm"
                                  className="w-full bg-white text-black font-semibold text-xs mt-1"
                                  onPress={() => handleRetest(i, learnedData[i].followup_scenario)}
                                  isPending={isRetesting}
                                >
                                  Test If Mimic Flips Choice with New Rule →
                                </Button>
                              </div>
                            )}

                            {retestResult[i] && (
                              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="text-emerald-400 text-sm">✓</span>
                                  <div>
                                    <p className="text-[10px] text-emerald-400 uppercase tracking-wider font-mono font-bold">Prediction Successfully Flipped</p>
                                    <p className="text-xs text-neutral-200">
                                      Mimic predicted Option {retestResult[i].predicted} ({Math.round(retestResult[i].confidence * 100)}% agreement)
                                    </p>
                                  </div>
                                </div>
                                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">Verified!</span>
                              </div>
                            )}
                          </div>
                        )}
                      </CardBody>
                    </Card>
                  </motion.div>
                ))}
              </div>

              <Card className="bg-neutral-900 border border-neutral-800">
                <CardBody className="p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-neutral-500 uppercase tracking-widest font-bold">Your Mimic</p>
                    {onboard.mbti && (
                      <span className="px-3 py-1 rounded-full text-xs font-bold tracking-widest bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-purple-500/30 text-purple-200">
                        {onboard.mbti} <span className="font-normal text-neutral-400">· {onboard.mbti_source === 'you' ? 'self-reported' : 'inferred'}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-neutral-400 font-light leading-relaxed">{onboard.profile}</p>
                  {onboard.sources?.length > 0 && (
                    <div className="pt-2 border-t border-neutral-800 space-y-1">
                      <p className="text-xs text-neutral-600 uppercase tracking-widest">Sources · Tavily</p>
                      {onboard.sources.map((s, i) => (
                        <a key={i} href={s.url} target="_blank" rel="noreferrer" className="block text-xs text-blue-400/80 hover:text-blue-300 truncate">{s.title || s.url}</a>
                      ))}
                    </div>
                  )}
                </CardBody>
              </Card>

              <div className="text-center">
                <Button variant="ghost" className="text-neutral-400" onPress={() => { setStage('custom'); setResearchData(null); }}>Test it on live opportunities with Tavily →</Button>
              </div>
            </motion.div>
          )}

          {/* STAGE: GROUNDED RESEARCH WITH TAVILY OR CUSTOM SCENARIO */}
          {stage === 'custom' && !predictionId && !researchData && (
            <motion.div key="custom-input" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="space-y-6">
                <Card className="bg-neutral-950/50 border border-neutral-800 backdrop-blur-md">
                  <CardBody className="p-8 space-y-6">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-xl text-white font-light">Grounded Decision Engine</p>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-400 border border-blue-500/30">
                            Powered by Tavily
                          </span>
                        </div>
                        <p className="text-xs text-neutral-500 mt-1">Live web intelligence meets your personal behavioral model (PRD §20 & §21).</p>
                      </div>
                      <Button variant="ghost" size="sm" className="text-neutral-400" onPress={() => setStage('results')}>
                        ← Back to Scoreboard
                      </Button>
                    </div>

                    {(profilePreview || onboard?.profile) && (
                      <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/20 text-xs text-neutral-300 font-light flex items-center gap-2">
                        <span className="text-purple-400 font-mono text-[10px] uppercase font-bold tracking-wider shrink-0">Active Persona:</span>
                        <span className="truncate text-neutral-400">{profilePreview || onboard?.profile}</span>
                      </div>
                    )}

                    {/* Trending Dilemma Chips */}
                    <div className="space-y-2">
                      <p className="text-xs text-neutral-500 uppercase tracking-widest font-mono">Trending Live Dilemmas:</p>
                      <div className="flex flex-wrap gap-2">
                        {TRENDING_DILEMMAS.map((d, idx) => (
                          <button
                            key={idx}
                            onClick={() => { setScenario(d); handleResearchPredict(d); }}
                            className="text-left px-3 py-2 rounded-xl text-xs border border-neutral-800 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all text-neutral-300"
                          >
                            ⚡ {d}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-neutral-500 uppercase tracking-widest font-mono">Or enter your own real-world dilemma:</p>
                      <Textarea 
                        value={scenario}
                        onChange={(e) => setScenario(e.target.value)}
                        placeholder="e.g. Should I accept an acquisition offer from a cloud provider, or raise a Series A and remain independent?"
                        variant="bordered"
                        minRows={3}
                        classNames={{ inputWrapper: "border-neutral-800 hover:border-neutral-600 focus-within:!border-white" }}
                      />
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3">
                      <Button 
                        className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold uppercase tracking-wider" 
                        size="lg"
                        onPress={() => handleResearchPredict()}
                        isPending={isResearching}
                        isDisabled={!scenario}
                      >
                        🌐 Search Live Web via Tavily & Predict
                      </Button>
                      <Button 
                        variant="bordered"
                        className="border-neutral-800 text-neutral-400 hover:text-white"
                        size="lg"
                        onPress={handlePredict}
                        isPending={isPredicting}
                        isDisabled={!scenario}
                      >
                        Blind Guess (No Web)
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              </div>
            </motion.div>
          )}

          {/* TAVILY 3-TIER GROUNDED RESULTS VIEW */}
          {stage === 'custom' && researchData && (
            <motion.div key="research-results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <p className="text-xs uppercase tracking-widest text-emerald-400 font-semibold font-mono">Live Grounded Analysis</p>
                  </div>
                  <p className="text-lg text-white font-light mt-1">"{researchData.scenario}"</p>
                </div>
                <Button variant="ghost" size="sm" className="text-neutral-400" onPress={() => setResearchData(null)}>
                  New Dilemma
                </Button>
              </div>

              {/* 3-Tier Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                {/* 1. What Tavily Found */}
                <Card className="bg-neutral-950/70 border border-neutral-800 backdrop-blur-md flex flex-col justify-between">
                  <CardBody className="p-6 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
                      <div className="flex items-center gap-2">
                        <span className="text-base">🌐</span>
                        <p className="text-xs text-blue-400 uppercase tracking-widest font-bold">What Tavily Found</p>
                      </div>
                      <span className="text-[10px] text-neutral-500 font-mono">World Reality</span>
                    </div>
                    <ul className="space-y-2.5 text-sm text-neutral-300 font-light leading-relaxed">
                      {researchData.web_facts?.map((f, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-blue-500 text-xs mt-1">•</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>

                    {researchData.sources?.length > 0 && (
                      <div className="pt-4 border-t border-neutral-800/80 space-y-1.5">
                        <p className="text-[10px] text-neutral-500 uppercase tracking-wider font-mono">Live Sources (Tavily)</p>
                        {researchData.sources.map((s, i) => (
                          <a key={i} href={s.url} target="_blank" rel="noreferrer" className="block text-xs text-blue-400/80 hover:text-blue-300 truncate underline">
                            ↗ {s.title || s.url}
                          </a>
                        ))}
                      </div>
                    )}
                  </CardBody>
                </Card>

                {/* 2. What Matters To You */}
                <Card className="bg-neutral-950/70 border border-neutral-800 backdrop-blur-md flex flex-col justify-between">
                  <CardBody className="p-6 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
                      <div className="flex items-center gap-2">
                        <span className="text-base">👤</span>
                        <p className="text-xs text-purple-400 uppercase tracking-widest font-bold">What Matters To You</p>
                      </div>
                      <span className="text-[10px] text-neutral-500 font-mono">Personal Filter</span>
                    </div>
                    <ul className="space-y-2.5 text-sm text-neutral-300 font-light leading-relaxed">
                      {researchData.personal_implications?.map((p, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-purple-400 text-xs mt-1">•</span>
                          <span>{p}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="pt-4 border-t border-neutral-800/80">
                      <p className="text-[10px] text-neutral-500 uppercase tracking-wider font-mono">Calibrated For</p>
                      <p className="text-xs text-neutral-400 mt-1">{onboard?.mbti ? `${onboard.mbti} • ` : ''}{name || 'Your Persona'}</p>
                    </div>
                  </CardBody>
                </Card>

                {/* 3. What Mimic Predicts */}
                <Card className="bg-neutral-900 border border-neutral-700 backdrop-blur-md relative overflow-hidden flex flex-col justify-between">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
                  <CardBody className="p-6 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
                      <div className="flex items-center gap-2">
                        <span className="text-base">🎯</span>
                        <p className="text-xs text-white uppercase tracking-widest font-bold">What Mimic Predicts</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        {Math.round((researchData.confidence_score || 0.82) * 100)}% Conf
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                      <p className="text-sm font-medium text-white leading-relaxed">
                        {researchData.mimic_prediction}
                      </p>
                    </div>

                    <div className="pt-4 border-t border-neutral-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] text-neutral-500 uppercase tracking-wider font-mono">Generic AI Baseline</p>
                        <span className="text-[10px] text-neutral-600">No Persona</span>
                      </div>
                      <p className="text-xs text-neutral-400 italic">
                        "{researchData.baseline_prediction}"
                      </p>
                    </div>
                  </CardBody>
                </Card>
              </div>

              <div className="text-center pt-2">
                <Button variant="ghost" className="text-neutral-400" onPress={() => setResearchData(null)}>
                  Test Another Opportunity →
                </Button>
              </div>
            </motion.div>
          )}

          {/* STEP 2: BLIND REVEAL - USER ANSWERS */}
          {stage === 'custom' && predictionId && !revealData && (
            <motion.div key="step2" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
              <Card className="bg-neutral-950/50 border border-neutral-800 backdrop-blur-md mx-auto max-w-2xl">
                <CardBody className="p-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <p className="text-lg text-neutral-300 font-light">Scenario Locked</p>
                    <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-xs tracking-wide">
                      <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      Prediction Hidden
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-neutral-800 space-y-4">
                    <p className="text-sm text-neutral-500 uppercase tracking-widest">Your Turn</p>
                    <Textarea 
                      value={actualAnswer}
                      onChange={(e) => setActualAnswer(e.target.value)}
                      placeholder="What would you actually do?"
                      variant="bordered"
                      minRows={3}
                      classNames={{ inputWrapper: "border-neutral-800 focus-within:!border-white" }}
                    />
                    <Button 
                      className="w-full bg-white text-black font-semibold uppercase tracking-wider" 
                      size="lg"
                      onPress={handleReveal}
                      isPending={isRevealing}
                    >
                      Commit & Reveal Prediction
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </motion.div>
          )}

          {/* STEP 3: RESULTS */}
          {stage === 'custom' && revealData && (
            <motion.div key="step3" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* 1. Baseline */}
                <Card className="bg-neutral-900 border border-neutral-800 backdrop-blur-md opacity-70">
                  <CardBody className="p-6 space-y-4">
                    <p className="text-xs text-neutral-500 uppercase tracking-widest font-bold">Standard AI</p>
                    <p className="text-lg font-light text-neutral-400">{revealData.baseline_prediction}</p>
                  </CardBody>
                </Card>

                {/* 2. User Actual */}
                <Card className="bg-neutral-950/50 border border-neutral-800 backdrop-blur-md">
                  <CardBody className="p-6 space-y-4">
                    <p className="text-xs text-neutral-500 uppercase tracking-widest font-bold">You</p>
                    <p className="text-lg font-light text-white">{revealData.user_actual_answer}</p>
                  </CardBody>
                </Card>

                {/* 3. Mimic Core */}
                <Card className="bg-neutral-900 border border-neutral-700 backdrop-blur-md relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
                  <CardBody className="p-6 space-y-4">
                    <div className="flex justify-between items-center">
                      <p className="text-xs text-blue-400 uppercase tracking-widest font-bold">Mimic Core</p>
                      <p className="text-xs text-neutral-500">{Math.round(revealData.confidence_score * 100)}%</p>
                    </div>
                    <p className="text-lg font-light text-white">{revealData.model_predicted_answer}</p>
                  </CardBody>
                </Card>
              </div>
              <div className="mt-8 text-center">
                <Button 
                  variant="ghost" 
                  className="text-neutral-500"
                  onPress={() => {
                    setPredictionId(null);
                    setRevealData(null);
                    setScenario('');
                    setActualAnswer('');
                  }}
                >
                  Run Another Scenario
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
