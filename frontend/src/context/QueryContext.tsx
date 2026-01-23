/**
 * QueryContext - Global Query State Management
 *
 * Broadcasts query submissions across the application so that all
 * data pages (Graph, Timeline, Conflicts, Execution) can refresh
 * when a new query is executed from the Hypothesis page.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

interface QueryContextType {
  queryCount: number;
  lastQueryTime: number;
  notifyQuerySubmitted: () => void;
}

const QueryContext = createContext<QueryContextType | undefined>(undefined);

export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [queryCount, setQueryCount] = useState(0);
  const [lastQueryTime, setLastQueryTime] = useState(Date.now());

  const notifyQuerySubmitted = useCallback(() => {
    setQueryCount(prev => prev + 1);
    setLastQueryTime(Date.now());
  }, []);

  const value: QueryContextType = {
    queryCount,
    lastQueryTime,
    notifyQuerySubmitted,
  };

  return (
    <QueryContext.Provider value={value}>
      {children}
    </QueryContext.Provider>
  );
};

/**
 * Hook to use query context
 * Trigger re-fetches whenever queryCount changes
 */
export const useQueryRefresh = () => {
  const context = useContext(QueryContext);
  if (!context) {
    throw new Error('useQueryRefresh must be used within QueryProvider');
  }
  return context;
};
