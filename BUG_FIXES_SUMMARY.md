# Bug Fixes - Page Refresh & State Management

## Issues Fixed

### 1. **Old Execution UI Persisting**
**Problem**: When user completed a query and started typing a new query, the old "System Orchestration" panel with agent timings from the previous query was still visible.

**Solution**:
- Modified `onChange` handler in input to clear `executionData` and `rosData` when user starts editing in COMPLETED state
- Clear data in `handleAnalyze()` when starting a new query
- Allow button to be clickable in COMPLETED state (not just IDLE)
- Input field now editable when in COMPLETED state

**Changes in Hypothesis.tsx**:
```typescript
// Input now clears old data when user starts typing
onChange={(val) => {
  if (consoleState === 'COMPLETED') {
    setExecutionData(null);    // ← NEW: Clear old execution
    setRosData(null);           // ← NEW: Clear old results
  }
  setQuery(val);
}}

// Input field now enabled in both IDLE and COMPLETED states
disabled={consoleState !== 'IDLE' && consoleState !== 'COMPLETED'}

// Button visible in COMPLETED state too
{(consoleState === 'IDLE' || consoleState === 'COMPLETED') && (
  <CalmButton onClick={handleAnalyze} ... />
)}
```

### 2. **Pages Not Refreshing on New Queries**
**Problem**: Graph, Timeline, Conflicts, and Execution pages were loading data only on mount (empty dependency array). When submitting a new query, these pages didn't refresh.

**Solution**: 
- Added `queryCount` to useEffect dependency arrays
- Pages now re-fetch data whenever `queryCount` changes
- Hypothesis page triggers `notifyQuerySubmitted()` after query completes
- Clear old data before fetching new data to prevent stale UI

**Changes in all data pages**:
```typescript
const { queryCount } = useQueryRefresh();  // Subscribe to query updates

useEffect(() => {
  const fetchData = async () => {
    setData(null);  // Clear old data first
    const newData = await api.fetchData();
    setData(newData);
  };
  fetchData();
}, [queryCount]);  // ← KEY: Now re-runs when query changes
```

### 3. **Added Debug Logging**
Added console logs to help track the refresh flow:
- `[Hypothesis]` - Query lifecycle events
- `[GraphExplorer]`, `[Timeline]`, `[Conflicts]`, `[Execution]` - Data fetch events

Look for these in browser DevTools Console to verify pages are refreshing.

## Testing Steps

1. **Open Browser DevTools** (F12) → Console tab
2. **Go to Research Console** (Hypothesis page)
3. **Submit Query A** (e.g., "Semaglutide for Alzheimer's")
   - Wait for completion
   - See: `[Hypothesis] Query completed, notifying pages...` in console
4. **Edit the input** to Query B
   - OLD BEHAVIOR: Execution panel still shows Query A data ❌
   - NEW BEHAVIOR: Panel disappears as you start typing ✅
5. **Submit Query B**
   - See: `[Hypothesis] Query completed, notifying pages...` again
6. **Navigate to Graph/Timeline/Conflicts pages**
   - OLD BEHAVIOR: Shows Query A data or nothing ❌
   - NEW BEHAVIOR: Shows Query B data automatically ✅
   - See console logs: `[GraphExplorer] Fetching graph data (queryCount: 2)`
7. **Go back to Research Console**
8. **Submit Query C**
   - Execution panel auto-clears ✅
   - Query count increments ✅
9. **Check each data page again**
   - ALL pages show Query C data ✅

## Files Modified

1. `/frontend/src/pages/v2/Hypothesis.tsx` - Fixed state management and UI logic
2. `/frontend/src/pages/v2/GraphExplorer.tsx` - Added queryCount dependency + logging
3. `/frontend/src/pages/v2/Timeline.tsx` - Added queryCount dependency + logging
4. `/frontend/src/pages/v2/Conflicts.tsx` - Added queryCount dependency + logging
5. `/frontend/src/pages/v2/Execution.tsx` - Added queryCount dependency + logging

## Architecture

The flow now works like this:

```
User submits Query A
    ↓
Research Console (Hypothesis) processes query
    ↓
handleCompletion() calls notifyQuerySubmitted()
    ↓
QueryContext increments queryCount
    ↓
All data pages (Graph, Timeline, Conflicts, Execution) useEffect triggers
    ↓
Pages fetch fresh data for Query A
    ↓
UI updates with new data
```

When user starts a new Query:

```
User edits input → OLD DATA CLEARED immediately
User clicks Analyze → MORE DATA CLEARED
Query processes → New data appears
```

## Benefits

✅ No stale UI from previous queries  
✅ Automatic refresh across all pages  
✅ Clean state management  
✅ Debuggable with console logs  
✅ Better UX when running multiple queries  
