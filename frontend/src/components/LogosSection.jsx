import React from 'react';

const LogosSection = () => {
  return (
    <section className="py-12 border-y border-white/5 bg-white/[0.01]">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-xs text-white/30 font-medium tracking-widest uppercase mb-8">
          Built with modern technologies
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
          {/* React */}
          <div className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity">
            <iconify-icon icon="logos:react" width="24"></iconify-icon>
            <span className="text-sm font-display font-semibold text-white tracking-tight">React</span>
          </div>
          
          {/* Python */}
          <div className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity">
            <iconify-icon icon="logos:python" width="24"></iconify-icon>
            <span className="text-sm font-display font-semibold text-white tracking-tight">Python</span>
          </div>
          
          {/* Flask */}
          <div className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity">
            <iconify-icon icon="simple-icons:flask" className="text-white" width="20"></iconify-icon>
            <span className="text-sm font-display font-semibold text-white tracking-tight">Flask</span>
          </div>
          
          {/* Machine Learning */}
          <div className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity">
            <iconify-icon icon="carbon:machine-learning-model" className="text-cyan-400" width="24"></iconify-icon>
            <span className="text-sm font-display font-semibold text-white tracking-tight">ML Model</span>
          </div>
          
          {/* Tailwind */}
          <div className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity">
            <iconify-icon icon="logos:tailwindcss-icon" width="24"></iconify-icon>
            <span className="text-sm font-display font-semibold text-white tracking-tight">Tailwind</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LogosSection;
