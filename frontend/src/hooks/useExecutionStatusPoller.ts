import { useState, useEffect } from 'react';
import type { ExecutionStatusResponse } from '../types/api';
import { api } from '../services/api';

/**
 * Hook to poll execution status
 * Stops polling when all agents complete or fail
 */
export const useExecutionStatusPoller = (shouldPoll: boolean, intervalMs: number = 1200) => {
  const [status, setStatus] = useState<ExecutionStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(shouldPoll);
  const [error, setError] = useState<string | null>(null);

  // Sync isPolling when shouldPoll changes
  useEffect(() => {
    if (shouldPoll) {
      setIsPolling(true);
    }
  }, [shouldPoll]);

  useEffect(() => {
    if (!shouldPoll || !isPolling) return;

    let pollCount = 0;
    const maxPolls = 300; // ~6 minutes max

    const poll = async () => {
      try {
        pollCount++;
        const response = await api.getExecutionStatus();
        setStatus(response);

        // Stop polling if all agents are done
        const totalTriggered = response.agents_triggered.length;
        const totalCompleted = response.agents_completed.length + response.agents_failed.length;

        if (totalCompleted >= totalTriggered || pollCount >= maxPolls) {
          setIsPolling(false);
        }
      } catch (err) {
        // Silently continue polling - execution endpoint may not have data yet
        if (pollCount >= maxPolls) {
          setIsPolling(false);
        }
      }
    };

    const interval = setInterval(poll, intervalMs);
    poll(); // Immediate first poll

    return () => clearInterval(interval);
  }, [shouldPoll, isPolling, intervalMs]);

  return { status, isPolling, error };
};
