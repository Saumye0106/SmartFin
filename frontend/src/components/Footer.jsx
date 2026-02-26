import React from 'react';

const Footer = () => {
  return (
    <footer className="relative z-20 border-t border-white/10 bg-black pt-16 pb-8 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2 md:col-span-2">
            <a href="#" className="flex items-center gap-2 mb-4">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
              <span className="font-display font-bold text-lg text-white">SmartFin</span>
            </a>
            <p className="text-sm text-white/40 max-w-xs">
              AI-powered financial intelligence for smarter money management. A college project demonstrating modern web technologies.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#features" className="hover:text-cyan-400 transition-colors">Features</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Security</a></li>
              <li><a href="#integration" className="hover:text-cyan-400 transition-colors">How It Works</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">About</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">API Reference</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">GitHub</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Support</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-white/40">
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Privacy</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Terms</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">License</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Contact</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/5 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-white/20">© 2024 SmartFin. College Project. All rights reserved.</p>
          <div className="flex gap-4 text-white/40">
            <a href="#" className="hover:text-white transition-colors">
              <iconify-icon icon="solar:brand-twitter-linear" width="20"></iconify-icon>
            </a>
            <a href="#" className="hover:text-white transition-colors">
              <iconify-icon icon="solar:brand-github-linear" width="20"></iconify-icon>
            </a>
            <a href="#" className="hover:text-white transition-colors">
              <iconify-icon icon="solar:brand-discord-linear" width="20"></iconify-icon>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
