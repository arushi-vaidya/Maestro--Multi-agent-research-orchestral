# Debug Steps - Edge Visibility Issue

## Step 1: Open Browser Console

1. Navigate to http://localhost:3000/graph
2. Open Developer Tools (View → Developer → JavaScript Console or Cmd+Option+J)
3. Look for these specific log messages:

### Required Logs to Share:

```
[Connectivity] Nodes: X raw → Y filtered → Z final
[Connectivity] ID map size: N entries
[Connectivity] Edges: X raw → Y remapped → Z scientific → W final
[Edge Types After Filter]: { ... }
[EDGE PIPELINE] { raw: X, remapped: Y, scientific: Z, final: W }
```

## Step 2: Check These Values

- `[EDGE PIPELINE] { final: X }` - What is X? Should be >0
- If final = 0, where did edges get lost? Check remapped count
- If final >0 but no edges visible, it's a rendering issue

## Step 3: Check Graph Data Passed to Visualization

In console, type:
```javascript
// This will show what data is being passed to the graph
console.log(document.querySelector('[class*="ForceGraph"]'))
```

## Step 4: Share Results

Please copy/paste:
1. All console logs from [Connectivity] and [EDGE PIPELINE]
2. The final edge count
3. Any errors in red
