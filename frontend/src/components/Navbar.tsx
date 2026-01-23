import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, FileText, Network, Clock, Target } from 'lucide-react';

const Navbar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: null },
    { path: '/hypothesis', label: 'Research', icon: Activity },
    { path: '/graph', label: 'Graph', icon: Network },
    { path: '/timeline', label: 'Timeline', icon: Clock },
    { path: '/confidence', label: 'Confidence', icon: Target },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-warm-divider">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-gradient-to-br from-terracotta-500 to-terracotta-600 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-warm-text font-inter tracking-tight">
              MAESTRO
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm transition-all font-inter
                    ${isActive 
                      ? 'bg-terracotta-50 text-terracotta-700 shadow-sm' 
                      : 'text-warm-text-light hover:text-warm-text hover:bg-warm-bg-alt'
                    }
                  `}
                >
                  <div className="flex items-center gap-2">
                    {Icon && <Icon className="w-4 h-4" />}
                    {item.label}
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Status Indicator */}
          <div className="flex items-center gap-2 text-sm text-warm-text-light">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="font-inter">Live</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
