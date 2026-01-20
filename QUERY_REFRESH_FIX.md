# Query Refresh Fix - Page State Update on New Queries

## Problem
When submitting a new query from the Hypothesis (Research Console) page, the data pages (Graph, Timeline, Conflicts, Execution) were not refreshing with new data. They only loaded data once on component mount and never updated when a different query was executed.

## Root Cause
Each page component used `useEffect` with an empty dependency array `[]`, which means the data-fetching code only ran once when the component mounted:

```tsx
useEffect(() => {
  // fetch data
}, []); // Empty array = never re-run
```

This meant that navigating to these pages after running different queries would still show old data, or no data at all if the page hadn't been visited before.

## Solution
Implemented a **Query Context** pattern to broadcast query submissions across the application:

### 1. Created QueryContext (`src/context/QueryContext.tsx`)
- Provides `queryCount` state that increments on every query submission
- Exports `useQueryRefresh()` hook for pages to listen to query changes
- Uses a simple number to force re-renders (React re-runs effects when dependencies change)

### 2. Updated App.tsx
- Wrapped the entire app with `<QueryProvider>` to enable context across all pages

### 3. Updated Hypothesis.tsx (Research Console)
- Imported `useQueryRefresh` hook
- Added `notifyQuerySubmitted()` call in `handleCompletion()` 
- This fires after a query completes, telling all pages to refresh

### 4. Updated Data Pages
- **GraphExplorer.tsx**: Added `queryCount` to useEffect dependency array
- **Timeline.tsx**: Added `queryCount` to useEffect dependency array  
- **Conflicts.tsx**: Added `queryCount` to useEffect dependency array
- **Execution.tsx**: Added `queryCount` to useEffect dependency array

## How It Works

1. User submits a query from Hypothesis page
2. Backend processes the query (agents run, data updates)
3. `handleCompletion()` calls `notifyQuerySubmitted()`
4. Context increments `queryCount` 
5. All pages' `useEffect` hooks re-run (because dependency changed)
6. Pages fetch fresh data from the API
7. UI updates with new data

## Code Changes Summary

### QueryContext.tsx (New File)
```typescript
export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [queryCount, setQueryCount] = useState(0);
  const [lastQueryTime, setLastQueryTime] = useState(Date.now());

  const notifyQuerySubmitted = useCallback(() => {
    setQueryCount(prev => prev + 1);
    setLastQueryTime(Date.now());
  }, []);
  // ...
};

export const useQueryRefresh = () => {
  // Hook to access queryCount
};
```

### Each Data Page (Example: Timeline.tsx)
```typescript
export const Timeline: React.FC = () => {
  const { queryCount } = useQueryRefresh(); // Subscribe to changes
  
  useEffect(() => {
    const fetchData = async () => {
      // ... fetch code
    };
    fetchData();
  }, [queryCount]); // Re-run when queryCount changes
  
  // ...
};
```

### Hypothesis.tsx (Research Console)
```typescript
const handleCompletion = async () => {
  // ... fetch results
  notifyQuerySubmitted(); // Tell all pages to refresh
};
```

## Benefits
✅ **Automatic Refresh**: Pages automatically refresh when new queries complete  
✅ **No Manual Polling**: No need for user to manually refresh pages  
✅ **Clean Architecture**: Uses React Context pattern, no external state management  
✅ **Minimal Changes**: Only changed dependency arrays and added notification call  
✅ **Backward Compatible**: Doesn't break existing functionality  

## Testing
To verify the fix works:

1. Go to Research Console (Hypothesis page)
2. Submit a query (e.g., "Semaglutide for Alzheimer's disease")
3. Wait for completion
4. Navigate to Graph, Timeline, Conflicts, or Execution pages
5. **Expected**: Pages should show new data from the query
6. Go back to Research Console
7. Submit a **different** query
8. Navigate back to data pages
9. **Expected**: Pages automatically show updated data (no manual refresh needed)

## Files Modified
- `/frontend/src/context/QueryContext.tsx` (NEW)
- `/frontend/src/App.tsx` (Added QueryProvider)
- `/frontend/src/pages/v2/Hypothesis.tsx` (Added notification)
- `/frontend/src/pages/v2/GraphExplorer.tsx` (Added queryCount dependency)
- `/frontend/src/pages/v2/Timeline.tsx` (Added queryCount dependency)
- `/frontend/src/pages/v2/Conflicts.tsx` (Added queryCount dependency)
- `/frontend/src/pages/v2/Execution.tsx` (Added queryCount dependency)
