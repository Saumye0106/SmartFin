import React from 'react';

const Features = () => {
  return (
    <section id="features" className="py-32 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-20 max-w-3xl">
          <h2 className="font-display text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Built for the <br />
            <span className="text-gradient">velocity of money.</span>
          </h2>
          <p className="text-lg text-white/50 leading-relaxed">
            Advanced AI that understands your financial patterns, predicts risks, and provides actionable insights to help you achieve your financial goals.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Large Card */}
          <div className="col-span-1 md:col-span-2 glass-panel glass-panel-hover rounded-2xl p-8 md:p-12 relative overflow-hidden group">
            <div className="relative z-10">
              <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6">
                <iconify-icon icon="solar:shield-keyhole-linear" className="text-cyan-400 text-2xl"></iconify-icon>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Secure & Private</h3>
              <p className="text-white/50 max-w-md">
                Your financial data is encrypted and processed locally. We never share your information with third parties or use it for advertising.
              </p>
            </div>
            {/* Decorative Abstract Shapes */}
            <div className="absolute right-0 bottom-0 w-64 h-64 bg-gradient-to-tl from-cyan-900/30 to-transparent rounded-full blur-3xl group-hover:bg-cyan-800/40 transition-colors duration-500"></div>
            <div className="absolute right-10 top-10 w-full h-full border border-white/5 rounded-full border-dashed animate-spin-slow opacity-20"></div>
          </div>

          {/* Tall Card */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-8 relative overflow-hidden group">
            <div className="w-12 h-12 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-6">
              <iconify-icon icon="solar:bolt-circle-linear" className="text-purple-400 text-2xl"></iconify-icon>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Instant Analysis</h3>
            <p className="text-white/50 text-sm mb-8">
              Real-time financial health scoring with immediate insights and recommendations.
            </p>
            
            {/* Visual representation of speed */}
            <div className="space-y-3 mt-auto">
              <div className="flex items-center gap-3 text-xs font-mono text-white/40">
                <span className="text-green-400">SmartFin</span>
                <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-green-400 w-[10%]"></div>
                </div>
                <span>12ms</span>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono text-white/40">
                <span>Traditional</span>
                <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-white/30 w-[80%]"></div>
                </div>
                <span>800ms</span>
              </div>
            </div>
          </div>

          {/* Wide Card */}
          <div className="col-span-1 md:col-span-3 glass-panel glass-panel-hover rounded-2xl p-8 md:p-12 relative overflow-hidden flex flex-col md:flex-row items-center gap-12">
            <div className="flex-1 z-10">
              <div className="w-12 h-12 rounded-lg bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-6">
                <iconify-icon icon="solar:code-square-linear" className="text-pink-400 text-2xl"></iconify-icon>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Smart Predictions</h3>
              <p className="text-white/50 max-w-lg">
                Machine learning models analyze your spending patterns to predict future expenses, identify savings opportunities, and alert you to potential financial risks.
              </p>
              <a href="#" className="inline-flex items-center gap-2 text-pink-400 mt-6 text-sm font-medium hover:text-pink-300">
                Learn More
                <iconify-icon icon="solar:arrow-right-linear"></iconify-icon>
              </a>
            </div>
            <div className="flex-1 w-full max-w-md bg-[#050505] rounded-xl border border-white/10 p-5 shadow-2xl relative">
              {/* Header */}
              <div className="flex items-center justify-between mb-5">
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wider mb-1">Financial Health</div>
                  <div className="text-2xl font-bold text-white">Score: <span className="text-pink-400">78</span><span className="text-xs text-white/30 ml-1">/100</span></div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-green-400 flex items-center gap-1 justify-end">
                    <svg width="10" height="10" viewBox="0 0 10 10"><path d="M5 1L9 6H1L5 1Z" fill="currentColor"/></svg>
                    +4.2 pts
                  </div>
                  <div className="text-xs text-white/30">vs last month</div>
                </div>
              </div>

              {/* Mini bar chart – monthly score trend */}
              <div className="flex items-end gap-1.5 h-20 mb-4">
                {[62, 58, 65, 60, 68, 72, 70, 74, 71, 76, 74, 78].map((val, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className={`w-full rounded-sm transition-all ${i === 11 ? 'bg-pink-400' : 'bg-white/15 hover:bg-white/25'}`}
                      style={{ height: `${(val / 100) * 100}%` }}
                    ></div>
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-white/25 mb-5">
                <span>Jan</span><span>Mar</span><span>Jun</span><span>Sep</span><span>Dec</span>
              </div>

              {/* Prediction insights */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2">
                  <div className="w-7 h-7 rounded-md bg-green-500/15 flex items-center justify-center flex-shrink-0">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 9L5.5 5.5L8 8L12 3" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white/70">Savings trend</div>
                    <div className="text-[10px] text-green-400">&#8593; 12% above avg</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2">
                  <div className="w-7 h-7 rounded-md bg-yellow-500/15 flex items-center justify-center flex-shrink-0">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 3V8M7 10.5V11" stroke="#eab308" strokeWidth="1.5" strokeLinecap="round"/></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white/70">Spending alert</div>
                    <div className="text-[10px] text-yellow-400">EMI ratio nearing 30%</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2">
                  <div className="w-7 h-7 rounded-md bg-pink-500/15 flex items-center justify-center flex-shrink-0">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 11L5 5L8 7L12 2" stroke="#ec4899" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="12" cy="2" r="1.5" fill="#ec4899" opacity="0.4"/></svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white/70">Predicted score</div>
                    <div className="text-[10px] text-pink-400">82 by next quarter</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
