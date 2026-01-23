#!/bin/bash
# Quick verification test after fixes

echo "============================================"
echo "MAESTRO QUICK VERIFICATION TEST"
echo "============================================"
echo ""

# Check if .env has correct keys
echo "1. Checking environment configuration..."
if grep -q "SERPAPI_KEY=" .env; then
    echo "   ✅ SERPAPI_KEY configured"
else
    echo "   ❌ SERPAPI_KEY missing in .env"
fi

if grep -q "GEMINI_API_KEY=" .env; then
    echo "   ✅ GEMINI_API_KEY configured"
else
    echo "   ⚠️  GEMINI_API_KEY missing (optional)"
fi

if grep -q "GROQ_API_KEY=" .env; then
    echo "   ✅ GROQ_API_KEY configured"
else
    echo "   ❌ GROQ_API_KEY missing"
fi

echo ""
echo "2. Testing backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running on port 8000"
else
    echo "   ❌ Backend not responding. Start with: python main.py"
fi

echo ""
echo "3. Testing frontend connection..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend is running on port 5173"
else
    echo "   ⚠️  Frontend not responding. Start with: npm run dev"
fi

echo ""
echo "============================================"
echo "Next: Submit a test query in the browser:"
echo "  'GLP-1 market analysis and clinical trials'"
echo "============================================"
