/**
 * Navigation Header Component
 * Used across all v2 pages for consistent navigation
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, FileText, Network, Clock, AlertTriangle, PlayCircle } from 'lucide-react';

interface NavigationHeaderProps {
  currentPage?: 'Research' | 'KnowledgeGraph' | 'Timeline' | 'Conflicts' | 'Execution';
}

const NavigationHeader: React.FC<NavigationHeaderProps> = ({ currentPage }) => {
  const location = useLocation();

  const navItems = [
    { path: '/hypothesis', label: 'Research', icon: Activity, id: 'Research' },
    { path: '/graph', label: 'Graph', icon: Network, id: 'KnowledgeGraph' },
    { path: '/timeline', label: 'Timeline', icon: Clock, id: 'Timeline' },
    { path: '/conflicts', label: 'Conflicts', icon: AlertTriangle, id: 'Conflicts' },
    { path: '/execution', label: 'Execution', icon: PlayCircle, id: 'Execution' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-gradient-to-br from-slate-700 to-slate-800 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900 tracking-tight">
              MAESTRO
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = currentPage === item.id || location.pathname === item.path;
              const Icon = item.icon;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    px-4 py-2 rounded-lg font-medium text-sm transition-all
                    ${isActive
                      ? 'bg-slate-100 text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
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
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationHeader;
