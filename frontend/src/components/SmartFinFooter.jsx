import React from 'react';

const SmartFinFooter = ({ iconClass = 'text-cyan-400', statusDotClass = 'bg-cyan-400' }) => {
  return (
    <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className={`${iconClass} text-lg`}></iconify-icon>
              <span className="font-display font-bold text-white">SmartFin</span>
              <span className="text-[10px] text-white/30 font-mono">v2.0.4</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={`w-1.5 h-1.5 rounded-full ${statusDotClass} animate-pulse`}></span>
              <span className="text-white/40">System Operational</span>
            </div>
          </div>
          <div className="text-xs text-white/30">
            Educational Use Only • College Project
          </div>
        </div>
      </div>
    </footer>
  );
};

export default SmartFinFooter;