import React from 'react';

const Navigation = ({ onGetStarted }) => {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
      <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
        {/* Logo */}
        <a href="#" className="flex items-center gap-3 group">
          <div className="w-9 h-9 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-cyan-500/50 transition-colors backdrop-blur-sm">
            <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
          </div>
          <span className="font-display font-semibold text-lg text-white tracking-tight">SmartFin</span>
        </a>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm text-white/60 hover:text-white transition-colors">Features</a>
          <a href="#integration" className="text-sm text-white/60 hover:text-white transition-colors">Integration</a>
          <a href="#" className="text-sm text-white/60 hover:text-white transition-colors">Documentation</a>
        </div>

        {/* CTA Button */}
        <button 
          onClick={onGetStarted}
          className="hidden md:block px-5 py-2 rounded-full bg-white text-black text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          Get Started
        </button>

        {/* Mobile Menu Button */}
        <button className="md:hidden text-white/60 hover:text-white">
          <iconify-icon icon="solar:hamburger-menu-linear" width="24"></iconify-icon>
        </button>
      </div>
    </nav>
  );
};

export default Navigation;
