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
            <div className="flex-1 w-full max-w-md bg-[#050505] rounded-lg border border-white/10 p-4 font-mono text-xs shadow-2xl relative">
              <div className="flex gap-1.5 mb-4">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/20"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/20"></div>
              </div>
              <div className="text-blue-400">import</div> <div className="text-white inline">{'{ SmartFin }'}</div> <div className="text-blue-400 inline">from</div> <div className="text-green-400 inline">'@smartfin/sdk'</div>;
              <br /><br />
              <div className="text-purple-400">const</div> <div className="text-white inline">analyzer</div> = <div className="text-purple-400 inline">new</div> <div className="text-yellow-400 inline">SmartFin</div>{'({'}
              <div className="pl-4 text-white">apiKey: <span className="text-green-400">'sf_live_...'</span>,</div>
              <div className="pl-4 text-white">features: [<span className="text-green-400">'predict'</span>, <span className="text-green-400">'analyze'</span>]</div>
              {'});'}
              <br /><br />
              <div className="text-gray-500">// Get insights</div>
              <div className="text-purple-400">await</div> <div className="text-white inline">analyzer</div>.<div className="text-yellow-400 inline">analyze</div>{'({'}
              <div className="pl-4 text-white">period: <span className="text-green-400">'monthly'</span>,</div>
              <div className="pl-4 text-white">metrics: [<span className="text-green-400">'spending'</span>, <span className="text-green-400">'savings'</span>]</div>
              {'});'}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
