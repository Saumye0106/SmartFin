import React from 'react';

const Hero = ({ onInitialize }) => {
  return (
    <section className="px-6 mb-32 relative">
      <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
        {/* Badge */}
        <div className="animate-fade-in-up inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
          <span className="text-xs text-white/70 font-medium">AI-Powered Financial Intelligence</span>
        </div>

        {/* Main Headline */}
        <h1 className="animate-fade-in-up delay-[100ms] font-display text-5xl md:text-7xl lg:text-8xl font-bold text-white mb-8 tracking-tighter leading-[1.1]">
          Your Financial
          <br />
          <span className="text-gradient">Neural Engine</span>
        </h1>

        {/* Subheadline */}
        <p className="animate-fade-in-up delay-[200ms] text-base md:text-lg text-white/50 max-w-2xl mx-auto leading-relaxed mb-12 font-light">
          Autonomous financial intelligence that analyzes your spending, predicts risks, and provides personalized guidance with zero latency.
        </p>

        {/* Hero Buttons */}
        <div className="animate-fade-in-up delay-[300ms] flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
          <button 
            onClick={onInitialize}
            className="relative inline-flex h-11 overflow-hidden rounded-full p-[1px] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50"
          >
            <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2E8F0_0%,#06b6d4_50%,#E2E8F0_100%)]"></span>
            <span className="inline-flex h-full w-full items-center justify-center rounded-full bg-black px-8 py-1 text-sm font-medium text-white backdrop-blur-3xl">
              Initialize Protocol
            </span>
          </button>
          <button className="text-sm text-white/60 hover:text-white transition-colors flex items-center gap-2 px-4">
            <iconify-icon icon="solar:document-text-linear" width="18"></iconify-icon>
            Read Documentation
          </button>
        </div>

        {/* Interface Visualization */}
        <div className="animate-fade-in-up delay-[400ms] w-full max-w-5xl mx-auto relative group perspective-1000">
          {/* Glow behind */}
          <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000 group-hover:duration-200"></div>
          
          {/* Main Window */}
          <div className="relative glass-panel rounded-xl overflow-hidden shadow-2xl bg-[#0a0a0a]/90 flex flex-col min-h-[500px] text-left border border-white/10">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-white/10"></div>
                  <div className="w-3 h-3 rounded-full bg-white/10"></div>
                  <div className="w-3 h-3 rounded-full bg-white/10"></div>
                </div>
                <span className="ml-4 text-[10px] font-mono text-white/30">smartfin_agent.tsx</span>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-cyan-500 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></span>
                LIVE CONNECTION
              </div>
            </div>

            {/* Chat/Code Layout */}
            <div className="flex flex-col md:flex-row h-full flex-1">
              {/* Sidebar (Code/Context) */}
              <div className="hidden md:flex w-64 border-r border-white/5 flex-col p-4 bg-black/20">
                <div className="text-[10px] uppercase tracking-wider text-white/40 mb-3 font-semibold">Active Context</div>
                <div className="space-y-2 font-mono text-[10px] text-white/60">
                  <div className="flex items-center gap-2 p-2 rounded bg-white/5 border border-white/5">
                    <iconify-icon icon="solar:database-linear" className="text-cyan-400"></iconify-icon>
                    <span>financial_data</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded bg-white/5 border border-white/5">
                    <iconify-icon icon="solar:shield-check-linear" className="text-green-400"></iconify-icon>
                    <span>verified_user</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded bg-white/5 border border-white/5">
                    <iconify-icon icon="solar:graph-up-linear" className="text-purple-400"></iconify-icon>
                    <span>risk_low</span>
                  </div>
                </div>
                <div className="mt-auto">
                  <div className="h-32 rounded bg-gradient-to-t from-cyan-900/10 to-transparent relative overflow-hidden border border-white/5">
                    {/* Fake graph */}
                    <svg className="absolute bottom-0 left-0 right-0 text-cyan-500/40" viewBox="0 0 100 40" preserveAspectRatio="none">
                      <path d="M0 40 L0 30 L10 25 L20 35 L30 20 L40 22 L50 15 L60 25 L70 10 L80 15 L90 5 L100 10 L100 40 Z" fill="currentColor"></path>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Chat Area */}
              <div className="flex-1 p-6 flex flex-col relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 mix-blend-overlay pointer-events-none bg-[url(default)] bg-cover bg-center"></div>
                
                <div className="space-y-6 mt-auto">
                  {/* User Message */}
                  <div className="flex items-end gap-3 justify-end opacity-0 animate-[fadeInUp_0.5s_ease-out_0.5s_forwards]">
                    <div className="bg-white/10 text-white text-sm px-4 py-3 rounded-2xl rounded-tr-sm backdrop-blur-sm border border-white/5 max-w-md">
                      Analyze my spending patterns for the last quarter.
                    </div>
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-black border border-white/10 flex items-center justify-center text-[10px] font-bold">JD</div>
                  </div>

                  {/* AI Message */}
                  <div className="flex items-start gap-3 opacity-0 animate-[fadeInUp_0.5s_ease-out_1.5s_forwards]">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
                      <iconify-icon icon="solar:stars-minimalistic-bold" width="16"></iconify-icon>
                    </div>
                    <div className="flex flex-col gap-2 max-w-lg">
                      <div className="bg-black/40 text-white/90 text-sm px-5 py-4 rounded-2xl rounded-tl-sm backdrop-blur-md border border-cyan-500/20">
                        <p className="mb-3">I've detected a <span className="text-cyan-300 font-medium">15% increase</span> in discretionary spending. Your savings rate has improved to 22%.</p>
                        
                        {/* Mini Widget inside chat */}
                        <div className="bg-black/40 rounded-lg p-3 border border-white/10 font-mono text-xs">
                          <div className="flex justify-between text-white/40 mb-1">
                            <span>Target Savings</span>
                            <span>20%</span>
                          </div>
                          <div className="w-full bg-white/10 h-1.5 rounded-full mb-3">
                            <div className="bg-white/40 h-1.5 rounded-full w-[80%]"></div>
                          </div>
                          <div className="flex justify-between text-cyan-400 mb-1">
                            <span>Actual Savings</span>
                            <span>22%</span>
                          </div>
                          <div className="w-full bg-cyan-900/30 h-1.5 rounded-full">
                            <div className="bg-cyan-400 h-1.5 rounded-full w-[88%] relative">
                              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full shadow-[0_0_10px_rgba(34,211,238,0.8)]"></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] text-white/30 pl-1">Processing time: 12ms</span>
                    </div>
                  </div>

                  {/* Action Suggestion */}
                  <div className="flex gap-2 pl-11 opacity-0 animate-[fadeIn_0.5s_ease-out_2.5s_forwards]">
                    <button className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-xs text-white/70 transition-colors flex items-center gap-2">
                      <iconify-icon icon="solar:file-download-linear"></iconify-icon>
                      Export Report
                    </button>
                    <button className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-xs text-white/70 transition-colors flex items-center gap-2">
                      <iconify-icon icon="solar:tuning-square-2-linear"></iconify-icon>
                      Adjust Parameters
                    </button>
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

export default Hero;
