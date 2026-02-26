import React from 'react';

const CTA = ({ onGetStarted }) => {
  return (
    <section className="py-32 px-6">
      <div className="max-w-4xl mx-auto text-center relative">
        {/* Glow behind */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <h2 className="font-display text-4xl md:text-6xl font-bold text-white mb-8 tracking-tighter">
          Ready to optimize <br />your finances?
        </h2>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button 
            onClick={onGetStarted}
            className="bg-white text-black hover:bg-gray-200 px-8 py-3 rounded-full font-medium transition-colors flex items-center gap-2"
          >
            Start Analysis
            <iconify-icon icon="solar:arrow-right-linear"></iconify-icon>
          </button>
          <button className="px-8 py-3 rounded-full font-medium text-white/70 hover:text-white border border-white/10 hover:bg-white/5 transition-colors">
            Learn More
          </button>
        </div>
      </div>
    </section>
  );
};

export default CTA;
