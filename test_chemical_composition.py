#!/usr/bin/env python3
"""
Quick test script for Chemical Composition Analysis
Tests the service and API endpoint
"""

import sys
import os
import requests
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_service():
    """Test the chemical composition service directly"""
    print("=" * 70)
    print("Testing Chemical Composition Service")
    print("=" * 70)
    
    try:
        from services.chemical_composition_service import ChemicalCompositionService
        
        service = ChemicalCompositionService()
        print("✅ Service initialized successfully")
        
        # Test with a common drug
        test_compound = "Aspirin"
        print(f"\n📊 Analyzing: {test_compound}")
        print("-" * 70)
        
        result = service.analyze_chemical_composition(
            compound_name=test_compound,
            context="Nonsteroidal anti-inflammatory drug for pain relief"
        )
        
        # Check key fields
        key_fields = [
            'compound_name',
            'chemical_formula',
            'molecular_weight',
            'mechanism_of_action',
            'evidence_confidence',
            'analysis_status'
        ]
        
        print("\n✓ Analysis Results:")
        print(f"  Compound: {result.get('compound_name')}")
        print(f"  Formula: {result.get('chemical_formula', 'N/A')}")
        print(f"  MW: {result.get('molecular_weight', 'N/A')} g/mol")
        print(f"  Similarity Score: {result.get('similarity_score', 'N/A')}")
        print(f"  Similar Drugs: {result.get('similar_drugs', [])}")
        print(f"  Confidence: {result.get('evidence_confidence')}")
        print(f"  Status: {result.get('analysis_status', 'success')}")
        
        # Check all key fields are present
        missing = [f for f in key_fields if f not in result]
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
        else:
            print("\n✅ All key fields present!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n" + "=" * 70)
    print("Testing API Endpoint")
    print("=" * 70)
    
    try:
        # Check if backend is running
        health_url = "http://localhost:8000/api/"
        print(f"\n🔍 Checking backend at {health_url}")
        
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code != 200:
                print(f"❌ Backend returned status {response.status_code}")
                print("   Make sure backend is running: cd backend && python main.py")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to backend")
            print("   Make sure backend is running: cd backend && python main.py")
            return False
        
        print("✅ Backend is running")
        
        # Test the chemical composition endpoint
        endpoint = "http://localhost:8000/api/chemical-composition"
        test_data = {
            "compound_name": "Metformin",
            "context": "Diabetes medication"
        }
        
        print(f"\n📊 Testing endpoint: {endpoint}")
        print(f"   Compound: {test_data['compound_name']}")
        
        response = requests.post(
            endpoint,
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ API request successful (200)")
            result = response.json()
            
            print(f"   Compound: {result.get('compound_name')}")
            print(f"   Formula: {result.get('chemical_formula', 'N/A')}")
            print(f"   MW: {result.get('molecular_weight', 'N/A')}")
            print(f"   Confidence: {result.get('evidence_confidence')}")
            
            if result.get('error'):
                print(f"   Error: {result.get('error')}")
                return False
            
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def print_summary(service_ok, api_ok):
    """Print test summary"""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print(f"{'Service Test':<30} {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"{'API Endpoint Test':<30} {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if service_ok and api_ok:
        print("\n🎉 All tests passed! Chemical composition feature is ready.")
        return True
    elif service_ok:
        print("\n⚠️  Service works but API endpoint needs setup.")
        print("   Ensure backend is running: cd backend && python main.py")
        return False
    else:
        print("\n❌ Tests failed. Check configuration.")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 Chemical Composition Analysis - Test Suite".center(70))
    print("=" * 70 + "\n")
    
    # Run tests
    service_ok = test_service()
    api_ok = test_api_endpoint()
    
    # Print summary
    success = print_summary(service_ok, api_ok)
    
    sys.exit(0 if success else 1)
