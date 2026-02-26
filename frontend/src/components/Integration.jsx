import React from 'react';

const Integration = () => {
  return (
    <section id="integration" className="py-24 px-6 relative">
      <div className="absolute inset-0 bg-white/[0.02] -skew-y-1 transform origin-bottom-right scale-110 z-0"></div>
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="flex flex-col md:flex-row justify-between items-end mb-16">
          <div>
            <h2 className="font-display text-3xl font-bold text-white mb-2">How It Works</h2>
            <p className="text-white/50">From data input to intelligent insights in seconds.</p>
          </div>
        </div>

        <div className="relative">
          {/* Connector Line */}
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent hidden md:block"></div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="relative group">
              <div className="w-10 h-10 rounded-full bg-black border border-white/20 flex items-center justify-center text-white/50 font-mono text-sm mb-6 mx-auto relative z-10 group-hover:border-cyan-500 group-hover:text-cyan-400 transition-colors">
                1
              </div>
              <div className="glass-panel p-6 rounded-xl text-center hover:bg-white/5 transition-colors">
                <div className="mb-4 text-cyan-400 flex justify-center">
                  <iconify-icon icon="solar:server-square-cloud-linear" width="32"></iconify-icon>
                </div>
                <h4 className="text-white font-semibold mb-2">Input Your Data</h4>
                <p className="text-xs text-white/50">
                  Enter your financial information securely. All data is encrypted and processed locally on your device.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative group">
              <div className="w-10 h-10 rounded-full bg-black border border-white/20 flex items-center justify-center text-white/50 font-mono text-sm mb-6 mx-auto relative z-10 group-hover:border-cyan-500 group-hover:text-cyan-400 transition-colors">
                2
              </div>
              <div className="glass-panel p-6 rounded-xl text-center hover:bg-white/5 transition-colors">
                <div className="mb-4 text-purple-400 flex justify-center">
                  <iconify-icon icon="solar:tuning-3-linear" width="32"></iconify-icon>
                </div>
                <h4 className="text-white font-semibold mb-2">AI Analysis</h4>
                <p className="text-xs text-white/50">
                  Our machine learning model analyzes your financial health, spending patterns, and risk factors instantly.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative group">
              <div className="w-10 h-10 rounded-full bg-black border border-white/20 flex items-center justify-center text-white/50 font-mono text-sm mb-6 mx-auto relative z-10 group-hover:border-cyan-500 group-hover:text-cyan-400 transition-colors">
                3
              </div>
              <div className="glass-panel p-6 rounded-xl text-center hover:bg-white/5 transition-colors">
                <div className="mb-4 text-green-400 flex justify-center">
                  <iconify-icon icon="solar:rocket-2-linear" width="32"></iconify-icon>
                </div>
                <h4 className="text-white font-semibold mb-2">Get Insights</h4>
                <p className="text-xs text-white/50">
                  Receive personalized recommendations, alerts, and actionable insights to improve your financial health.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Integration;
