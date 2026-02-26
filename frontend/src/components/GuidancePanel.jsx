const GuidancePanel = ({ guidance }) => {
  if (!guidance) return null;

  const { strengths, warnings, recommendations } = guidance;

  const sections = [
    {
      key: 'strengths',
      title: 'Strengths',
      items: strengths,
      icon: 'solar:check-circle-linear',
      color: '#10b981',
      bgColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: 'rgba(16, 185, 129, 0.3)'
    },
    {
      key: 'warnings',
      title: 'Warnings',
      items: warnings,
      icon: 'solar:shield-warning-linear',
      color: '#f97316',
      bgColor: 'rgba(249, 115, 22, 0.1)',
      borderColor: 'rgba(249, 115, 22, 0.3)'
    },
    {
      key: 'recommendations',
      title: 'Recommendations',
      items: recommendations,
      icon: 'solar:lightbulb-bolt-linear',
      color: '#06b6d4',
      bgColor: 'rgba(6, 182, 212, 0.1)',
      borderColor: 'rgba(6, 182, 212, 0.3)'
    }
  ].filter(section => section.items && section.items.length > 0);

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:lightbulb-linear" className="text-cyan-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Personalized Guidance</h2>
          <p className="text-xs text-white/50">AI-powered insights tailored for you</p>
        </div>
      </div>
      
      <div className="space-y-6">
        {sections.map((section) => (
          <div key={section.key}>
            <div className="flex items-center gap-2 mb-3">
              <iconify-icon icon={section.icon} style={{ color: section.color }} width="18"></iconify-icon>
              <h3 className="text-sm font-semibold text-white">{section.title}</h3>
            </div>
            <div className="space-y-2">
              {section.items.map((item, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg border backdrop-blur-sm"
                  style={{
                    backgroundColor: section.bgColor,
                    borderColor: section.borderColor
                  }}
                >
                  <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: section.color }}></div>
                  <p className="text-sm text-white/80 leading-relaxed flex-1">{item}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GuidancePanel;
