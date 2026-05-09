import { Search, Database, Filter, ExternalLink, CheckCircle2, AlertCircle, ChevronDown, X, Plus, Grid3x3, BookOpen, Sparkles, TrendingUp, Calendar, Scale } from 'lucide-react';
import { motion } from 'motion/react';
import { useState } from 'react';

export default function App() {
  const [view, setView] = useState<'search' | 'results' | 'statute' | 'workspace'>('search');
  const [searchTab, setSearchTab] = useState<'citation' | 'factor' | 'natural'>('citation');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [selectedStates, setSelectedStates] = useState<string[]>([]);

  const factors = [
    'Duty of Care', 'Breach', 'Causation', 'Damages', 'Negligence', 'Strict Liability',
    'Proximate Cause', 'Foreseeability', 'Standard of Care', 'Reasonable Person',
    'Contributory Negligence', 'Comparative Fault', 'Assumption of Risk', 'Joint & Several',
    'Economic Damages', 'Pain & Suffering', 'Loss of Consortium'
  ];

  const states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI'];

  const statuteResults = [
    {
      id: 1,
      citation: 'Cal. Civ. Code § 1714',
      title: 'Responsibility for Willful Acts and Negligence',
      factors: ['Duty of Care', 'Negligence', 'Damages'],
      state: 'CA',
      confidence: 0.96,
      source: 'ca.gov/codes/civ',
      excerpt: 'Everyone is responsible, not only for the result of his or her willful acts, but also for an injury occasioned to another by his or her want of ordinary care or skill in the management of his or her property or person...'
    },
    {
      id: 2,
      citation: 'Restatement (Second) of Torts § 402A',
      title: 'Special Liability of Seller of Product for Physical Harm to User or Consumer',
      factors: ['Strict Liability', 'Damages', 'Causation'],
      state: 'Federal',
      confidence: 0.94,
      source: 'ali.org/restatement',
      excerpt: 'One who sells any product in a defective condition unreasonably dangerous to the user or consumer or to his property is subject to liability for physical harm thereby caused...'
    },
    {
      id: 3,
      citation: 'N.Y. C.P.L.R. § 1411',
      title: 'Damages Recoverable When Contributory Negligence or Assumption of Risk is Established',
      factors: ['Comparative Fault', 'Contributory Negligence', 'Damages'],
      state: 'NY',
      confidence: 0.92,
      source: 'ny.gov/cplr',
      excerpt: 'In any action to recover damages for personal injury, injury to property, or wrongful death, the culpable conduct attributable to the claimant or to the decedent...'
    }
  ];

  const workspaceColumns = {
    primary: [statuteResults[0]],
    supporting: [statuteResults[1]],
    background: [statuteResults[2]]
  };

  const coverageGrid = [
    { factor: 'Duty of Care', CA: true, NY: true, TX: false, FL: true, IL: true },
    { factor: 'Breach', CA: true, NY: false, TX: true, FL: false, IL: true },
    { factor: 'Causation', CA: true, NY: true, TX: true, FL: true, IL: false },
    { factor: 'Damages', CA: true, NY: true, TX: true, FL: true, IL: true },
    { factor: 'Negligence', CA: true, NY: false, TX: false, FL: true, IL: false },
  ];

  const toggleFactor = (factor: string) => {
    setSelectedFactors(prev =>
      prev.includes(factor) ? prev.filter(f => f !== factor) : [...prev, factor]
    );
  };

  const toggleState = (state: string) => {
    setSelectedStates(prev =>
      prev.includes(state) ? prev.filter(s => s !== state) : [...prev, state]
    );
  };

  return (
    <div className="min-h-screen bg-[#0F111A]" style={{ fontFamily: 'var(--font-serif)' }}>
      {/* Top Navigation */}
      <nav className="border-b border-[#272B3D] bg-[#1A1D29] sticky top-0 z-50 backdrop-blur-xl bg-opacity-90">
        <div className="px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] rounded-lg flex items-center justify-center">
                <Scale className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] bg-clip-text text-transparent" style={{ fontFamily: 'var(--font-sans)' }}>LEXIS TERMINAL</span>
            </div>
            <div className="flex items-center gap-1 text-xs" style={{ fontFamily: 'var(--font-mono)' }}>
              <button
                onClick={() => setView('search')}
                className={`px-3 py-1.5 rounded ${view === 'search' ? 'bg-[#6366F1] text-white' : 'text-[#94A3B8] hover:text-[#F1F5F9]'}`}
              >
                SEARCH
              </button>
              <button
                onClick={() => setView('results')}
                className={`px-3 py-1.5 rounded ${view === 'results' ? 'bg-[#6366F1] text-white' : 'text-[#94A3B8] hover:text-[#F1F5F9]'}`}
              >
                RESULTS
              </button>
              <button
                onClick={() => setView('statute')}
                className={`px-3 py-1.5 rounded ${view === 'statute' ? 'bg-[#6366F1] text-white' : 'text-[#94A3B8] hover:text-[#F1F5F9]'}`}
              >
                STATUTE
              </button>
              <button
                onClick={() => setView('workspace')}
                className={`px-3 py-1.5 rounded ${view === 'workspace' ? 'bg-[#6366F1] text-white' : 'text-[#94A3B8] hover:text-[#F1F5F9]'}`}
              >
                WORKSPACE
              </button>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs" style={{ fontFamily: 'var(--font-mono)' }}>
            <span className="text-[#94A3B8]">USER: <span className="text-[#F1F5F9]">partner@firm.com</span></span>
            <span className="text-[#94A3B8]">TIER: <span className="text-[#6366F1]">PROFESSIONAL</span></span>
          </div>
        </div>
      </nav>

      {/* Main Search View */}
      {view === 'search' && (
        <div className="max-w-7xl mx-auto px-6 py-12">
          {/* Search Tabs */}
          <div className="mb-8">
            <div className="flex gap-2 mb-6">
              {(['citation', 'factor', 'natural'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSearchTab(tab)}
                  className={`px-6 py-3 text-sm uppercase transition-all ${
                    searchTab === tab
                      ? 'bg-[#1E2130] text-[#6366F1] border-b-2 border-[#6366F1]'
                      : 'text-[#94A3B8] hover:text-[#F1F5F9]'
                  }`}
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  {tab === 'citation' && 'Citation Search'}
                  {tab === 'factor' && 'Factor Analysis'}
                  {tab === 'natural' && 'Natural Language'}
                </button>
              ))}
            </div>

            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94A3B8]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={
                  searchTab === 'citation' ? 'Enter citation (e.g., Cal. Civ. Code § 1714)' :
                  searchTab === 'factor' ? 'Search by legal factor (e.g., duty of care)' :
                  'Describe your legal question in plain language'
                }
                className="w-full pl-12 pr-6 py-4 bg-[#1A1D29] border border-[#272B3D] rounded text-[#F1F5F9] placeholder-[#94A3B8] focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/20 focus:outline-none transition-all"
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-4 gap-4 mb-12">
            {[
              { label: 'Statutes Indexed', value: '2,847,291', icon: Database },
              { label: 'Jurisdictions', value: '54', icon: Grid3x3 },
              { label: 'Last Updated', value: 'May 9, 2026', icon: Calendar },
              { label: 'Query Accuracy', value: '98.7%', icon: TrendingUp }
            ].map((stat, i) => (
              <div key={i} className="bg-[#1A1D29] border border-[#272B3D] rounded p-4 hover:border-[#6366F1]/50 transition-all hover:shadow-lg hover:shadow-[#6366F1]/10">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className="w-4 h-4 text-[#6366F1]" />
                  <span className="text-xs text-[#94A3B8] uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                    {stat.label}
                  </span>
                </div>
                <div className="text-2xl font-bold text-[#F1F5F9]" style={{ fontFamily: 'var(--font-mono)' }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Quick Results Preview */}
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm text-[#94A3B8] uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                Recent Searches
              </h3>
            </div>
            {statuteResults.map((result) => (
              <motion.div
                key={result.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#1A1D29] border border-[#272B3D] rounded p-4 hover:border-[#6366F1] hover:shadow-lg hover:shadow-[#6366F1]/20 transition-all cursor-pointer group"
                onClick={() => setView('results')}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-[#6366F1] font-semibold mb-1" style={{ fontFamily: 'var(--font-mono)' }}>
                      {result.citation}
                    </div>
                    <div className="text-sm text-[#F1F5F9]">{result.title}</div>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1 bg-[#1E2130] rounded" style={{ fontFamily: 'var(--font-mono)' }}>
                    <span className="text-xs text-[#94A3B8]">CONF</span>
                    <span className="text-sm text-[#10B981]">{(result.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mb-3">
                  {result.factors.map((factor) => (
                    <span
                      key={factor}
                      className="px-2 py-0.5 bg-[#1E2130] text-[#6366F1] text-xs rounded border border-[#6366F1]/30"
                      style={{ fontFamily: 'var(--font-mono)' }}
                    >
                      {factor.toUpperCase()}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Results View */}
      {view === 'results' && (
        <div className="flex h-[calc(100vh-60px)]">
          {/* Filters Sidebar */}
          <div className="w-80 bg-[#1A1D29] border-r border-[#272B3D] p-6 overflow-y-auto">
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm text-[#94A3B8] uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                  Legal Factors
                </h3>
                <Filter className="w-4 h-4 text-[#94A3B8]" />
              </div>
              <div className="space-y-2">
                {factors.map((factor) => (
                  <button
                    key={factor}
                    onClick={() => toggleFactor(factor)}
                    className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                      selectedFactors.includes(factor)
                        ? 'bg-[#1E2130] text-[#6366F1] border border-[#6366F1]/30'
                        : 'text-[#94A3B8] hover:bg-[#1E2130] hover:text-[#F1F5F9]'
                    }`}
                    style={{ fontFamily: 'var(--font-mono)' }}
                  >
                    {factor.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-sm text-[#94A3B8] uppercase mb-4" style={{ fontFamily: 'var(--font-mono)' }}>
                Jurisdictions
              </h3>
              <div className="flex flex-wrap gap-2">
                {states.map((state) => (
                  <button
                    key={state}
                    onClick={() => toggleState(state)}
                    className={`px-3 py-1.5 rounded text-xs transition-all ${
                      selectedStates.includes(state)
                        ? 'bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white shadow-lg shadow-[#6366F1]/50'
                        : 'bg-[#1E2130] text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#272B3D]'
                    }`}
                    style={{ fontFamily: 'var(--font-mono)' }}
                  >
                    {state}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results List */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl text-[#F1F5F9] mb-1">Search Results</h2>
                <p className="text-sm text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>
                  {statuteResults.length} statutes found • {selectedFactors.length} factors selected
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {statuteResults.map((result) => (
                <motion.div
                  key={result.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-[#1A1D29] border border-[#272B3D] rounded-lg p-6 hover:border-[#6366F1] hover:shadow-xl hover:shadow-[#6366F1]/20 transition-all cursor-pointer group"
                  onClick={() => setView('statute')}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg text-[#6366F1] font-semibold" style={{ fontFamily: 'var(--font-mono)' }}>
                          {result.citation}
                        </h3>
                        <span className="px-2 py-0.5 bg-[#1E2130] text-[#94A3B8] text-xs rounded" style={{ fontFamily: 'var(--font-mono)' }}>
                          {result.state}
                        </span>
                      </div>
                      <h4 className="text-base text-[#F1F5F9] mb-3">{result.title}</h4>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1E2130] rounded">
                        <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                        <span className="text-sm text-[#10B981]" style={{ fontFamily: 'var(--font-mono)' }}>
                          {(result.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {result.factors.map((factor) => (
                      <span
                        key={factor}
                        className="px-3 py-1 bg-[#1E2130] text-[#6366F1] text-xs rounded border border-[#6366F1]/30"
                        style={{ fontFamily: 'var(--font-mono)' }}
                      >
                        {factor.toUpperCase()}
                      </span>
                    ))}
                  </div>

                  <p className="text-sm text-[#94A3B8] mb-4 leading-relaxed">
                    {result.excerpt}
                  </p>

                  <div className="flex items-center justify-between pt-4 border-t border-[#272B3D]">
                    <div className="flex items-center gap-2 text-xs text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>
                      <ExternalLink className="w-3 h-3" />
                      <span>SOURCE: {result.source}</span>
                    </div>
                    <button className="px-4 py-1.5 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white text-xs rounded hover:shadow-lg hover:shadow-[#6366F1]/50 transition-all" style={{ fontFamily: 'var(--font-mono)' }}>
                      ADD TO WORKSPACE
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Single Statute View */}
      {view === 'statute' && (
        <div className="flex h-[calc(100vh-60px)]">
          {/* Full Text */}
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl">
              <div className="mb-8">
                <h1 className="text-2xl text-[#6366F1] font-bold mb-2" style={{ fontFamily: 'var(--font-mono)' }}>
                  Cal. Civ. Code § 1714
                </h1>
                <h2 className="text-xl text-[#F1F5F9] mb-4">
                  Responsibility for Willful Acts and Negligence
                </h2>
                <div className="flex items-center gap-4 text-sm text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>
                  <span>EFFECTIVE: Jan 1, 1872</span>
                  <span>•</span>
                  <span>AMENDED: Jan 1, 2019</span>
                  <span>•</span>
                  <span>STATUS: ACTIVE</span>
                </div>
              </div>

              {/* AI Summary */}
              <div className="bg-gradient-to-br from-[#1A1D29] to-[#1E2130] border border-[#6366F1]/30 rounded-lg p-6 mb-8 shadow-lg shadow-[#6366F1]/10">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] rounded-lg flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <h3 className="text-sm bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] bg-clip-text text-transparent uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                    AI Summary
                  </h3>
                </div>
                <p className="text-sm text-[#F1F5F9] leading-relaxed mb-4">
                  This foundational California statute establishes general liability for both intentional acts and negligent conduct. It forms the basis for most personal injury claims in California, creating a duty of care that extends to all persons for both their intentional wrongdoing and their failure to exercise ordinary care.
                </p>
                <p className="text-sm text-[#94A3B8] leading-relaxed">
                  Key Application: Courts have broadly interpreted this section to recognize duties in various contexts, including premises liability, professional malpractice, and general negligence claims. The statute works in conjunction with common law to define the scope of duty of care.
                </p>
              </div>

              {/* Full Text */}
              <div className="prose prose-invert max-w-none">
                <div className="bg-[#1A1D29] border border-[#272B3D] rounded p-8">
                  <p className="text-[#F1F5F9] leading-relaxed mb-4">
                    Everyone is responsible, not only for the result of his or her willful acts, but also for an injury occasioned to another by his or her want of ordinary care or skill in the management of his or her property or person, except so far as the latter has, willfully or by want of ordinary care, brought the injury upon himself or herself.
                  </p>
                  <p className="text-[#F1F5F9] leading-relaxed mb-4">
                    The extent of liability in these cases is defined by the Title on Compensatory Relief.
                  </p>
                  <p className="text-[#94A3B8] text-sm italic" style={{ fontFamily: 'var(--font-mono)' }}>
                    [Enacted in 1872. Amended by Stats. 1987, Ch. 1498, Sec. 1.]
                  </p>
                </div>
              </div>

              {/* Related Statutes */}
              <div className="mt-8">
                <h3 className="text-sm text-[#94A3B8] uppercase mb-4" style={{ fontFamily: 'var(--font-mono)' }}>
                  Related Statutes
                </h3>
                <div className="space-y-2">
                  {[
                    'Cal. Civ. Code § 1714.1 - Liability of Parents',
                    'Cal. Civ. Code § 1714.3 - Commercial Relationships',
                    'Cal. Civ. Code § 3333 - Measure of Damages'
                  ].map((statute, i) => (
                    <div key={i} className="bg-[#1A1D29] border border-[#272B3D] rounded p-3 text-sm text-[#94A3B8] hover:border-[#6366F1] hover:text-[#6366F1] cursor-pointer transition-colors" style={{ fontFamily: 'var(--font-mono)' }}>
                      {statute}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Metadata Panel */}
          <div className="w-96 bg-[#1A1D29] border-l border-[#272B3D] p-6 overflow-y-auto">
            <h3 className="text-sm text-[#94A3B8] uppercase mb-4" style={{ fontFamily: 'var(--font-mono)' }}>
              Metadata
            </h3>

            <div className="space-y-4 mb-6">
              <div>
                <div className="text-xs text-[#94A3B8] mb-1" style={{ fontFamily: 'var(--font-mono)' }}>JURISDICTION</div>
                <div className="text-sm text-[#F1F5F9]">California</div>
              </div>
              <div>
                <div className="text-xs text-[#94A3B8] mb-1" style={{ fontFamily: 'var(--font-mono)' }}>CATEGORY</div>
                <div className="text-sm text-[#F1F5F9]">Civil Code / Tort Law</div>
              </div>
              <div>
                <div className="text-xs text-[#94A3B8] mb-1" style={{ fontFamily: 'var(--font-mono)' }}>CONFIDENCE SCORE</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-[#1E2130] rounded-full overflow-hidden">
                    <div className="h-full w-[96%] bg-[#10B981] rounded-full"></div>
                  </div>
                  <span className="text-sm text-[#10B981]" style={{ fontFamily: 'var(--font-mono)' }}>96%</span>
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-xs text-[#94A3B8] uppercase mb-3" style={{ fontFamily: 'var(--font-mono)' }}>
                Legal Factors
              </h4>
              <div className="flex flex-wrap gap-2">
                {['Duty of Care', 'Negligence', 'Damages', 'Causation'].map((factor) => (
                  <span
                    key={factor}
                    className="px-2 py-1 bg-[#1E2130] text-[#6366F1] text-xs rounded border border-[#6366F1]/30"
                    style={{ fontFamily: 'var(--font-mono)' }}
                  >
                    {factor.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-xs text-[#94A3B8] uppercase mb-3" style={{ fontFamily: 'var(--font-mono)' }}>
                Source Verification
              </h4>
              <div className="bg-[#1E2130] border border-[#10B981]/30 rounded p-3">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  <span className="text-xs text-[#10B981]" style={{ fontFamily: 'var(--font-mono)' }}>VERIFIED</span>
                </div>
                <a href="#" className="text-xs text-[#94A3B8] hover:text-[#6366F1] flex items-center gap-1" style={{ fontFamily: 'var(--font-mono)' }}>
                  <ExternalLink className="w-3 h-3" />
                  leginfo.legislature.ca.gov
                </a>
              </div>
            </div>

            <div className="space-y-2">
              <button className="w-full px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white rounded hover:shadow-lg hover:shadow-[#6366F1]/50 transition-all text-sm" style={{ fontFamily: 'var(--font-mono)' }}>
                ADD TO WORKSPACE
              </button>
              <button className="w-full px-4 py-2 bg-[#1E2130] text-[#94A3B8] rounded hover:text-[#F1F5F9] hover:bg-[#272B3D] transition-all text-sm" style={{ fontFamily: 'var(--font-mono)' }}>
                EXPORT CITATION
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Case Workspace View */}
      {view === 'workspace' && (
        <div className="p-6 overflow-y-auto">
          <div className="mb-8">
            <h2 className="text-2xl text-[#F1F5F9] mb-2">Case Workspace</h2>
            <p className="text-sm text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>
              Johnson v. ABC Corp. • PI-2026-00142
            </p>
          </div>

          {/* Kanban Columns */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            {(['primary', 'supporting', 'background'] as const).map((column) => (
              <div key={column} className="bg-[#1A1D29] border border-[#272B3D] rounded-lg p-4 hover:border-[#6366F1]/30 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] bg-clip-text text-transparent uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                    {column} ({workspaceColumns[column].length})
                  </h3>
                  <Plus className="w-4 h-4 text-[#94A3B8] cursor-pointer hover:text-[#6366F1] transition-colors" />
                </div>
                <div className="space-y-3">
                  {workspaceColumns[column].map((statute) => (
                    <div key={statute.id} className="bg-[#1E2130] border border-[#272B3D] rounded-lg p-3 hover:border-[#6366F1] hover:shadow-lg hover:shadow-[#6366F1]/20 transition-all cursor-pointer group">
                      <div className="text-xs text-[#6366F1] mb-1" style={{ fontFamily: 'var(--font-mono)' }}>
                        {statute.citation}
                      </div>
                      <div className="text-xs text-[#94A3B8] mb-2 line-clamp-2">
                        {statute.title}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {statute.factors.slice(0, 2).map((factor) => (
                          <span key={factor} className="px-1.5 py-0.5 bg-[#1A1D29] text-[#94A3B8] text-[10px] rounded" style={{ fontFamily: 'var(--font-mono)' }}>
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Coverage Gap Grid */}
          <div className="bg-[#1A1D29] border border-[#272B3D] rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] rounded-lg flex items-center justify-center">
                <Grid3x3 className="w-4 h-4 text-white" />
              </div>
              <h3 className="text-sm bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] bg-clip-text text-transparent uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                Coverage Gap Analysis
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ fontFamily: 'var(--font-mono)' }}>
                <thead>
                  <tr className="border-b border-[#272B3D]">
                    <th className="text-left py-2 px-3 text-[#94A3B8]">FACTOR</th>
                    {['CA', 'NY', 'TX', 'FL', 'IL'].map((state) => (
                      <th key={state} className="text-center py-2 px-3 text-[#94A3B8]">{state}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {coverageGrid.map((row) => (
                    <tr key={row.factor} className="border-b border-[#272B3D]">
                      <td className="py-2 px-3 text-[#F1F5F9]">{row.factor}</td>
                      {(['CA', 'NY', 'TX', 'FL', 'IL'] as const).map((state) => (
                        <td key={state} className="py-2 px-3">
                          <div className={`w-full h-8 rounded flex items-center justify-center ${
                            row[state] ? 'bg-[#10B981]/20 border border-[#10B981]/40' : 'bg-[#EF4444]/20 border border-[#EF4444]/40'
                          }`}>
                            {row[state] ? (
                              <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-[#EF4444]" />
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center gap-6 mt-4 pt-4 border-t border-[#272B3D]">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-[#10B981]/20 border border-[#10B981]/40 rounded"></div>
                <span className="text-xs text-[#94A3B8]">Covered</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-[#EF4444]/20 border border-[#EF4444]/40 rounded"></div>
                <span className="text-xs text-[#94A3B8]">Gap Identified</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}