import React, { useEffect } from 'react';
import Navigation from './Navigation';
import Hero from './Hero';
import LogosSection from './LogosSection';
import Features from './Features';
import Integration from './Integration';
import CTA from './CTA';
import Footer from './Footer';

const LandingPage = ({ onGetStarted }) => {
  useEffect(() => {
    // Initialize UnicornStudio after component mounts
    const timer = setTimeout(() => {
      if (window.UnicornStudio && window.UnicornStudio.init) {
        window.UnicornStudio.init();
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen overflow-x-hidden relative bg-[#030303]">
      {/* UnicornStudio Animated Background */}
      <div className="fixed top-0 w-full h-screen z-0" style={{
        maskImage: 'linear-gradient(to bottom, transparent, black 5%, black 70%, transparent)',
        WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 5%, black 70%, transparent)'
      }}>
        <div data-us-project="c7u06rukkPvuN1M2YbD0" style={{ width: '100%', height: '100%' }}></div>
      </div>

      {/* Background Layers - Fixed positioning like original */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid pointer-events-none"></div>
        {/* Ambient Glows - Make these more visible */}
        <div className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] bg-cyan-500/30 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation */}
      <Navigation onGetStarted={onGetStarted} />

      {/* Main Content */}
      <main className="relative z-10 pt-32 pb-24">
        <Hero onInitialize={onGetStarted} />
        <LogosSection />
        <Features />
        <Integration />
        <CTA onGetStarted={onGetStarted} />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default LandingPage;
