#!/usr/bin/env python3
"""
Comprehensive test script for AI Translation System
Tests all components: Glossary, RAG, MCP, LLM, and Feedback
"""

import asyncio
import json
import requests
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Test an endpoint and return results"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        if response.status_code == 200:
            return {"status": "✅ Success", "data": response.json()}
        else:
            return {"status": "❌ Failed", "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"status": "❌ Error", "error": str(e)}

def run_comprehensive_tests():
    """Run all system tests"""
    print("🧪 AI Translation System - Comprehensive Testing")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    health = test_endpoint("/health")
    results["health"] = health
    print(f"   {health['status']}")
    
    # Test 2: System Stats
    print("\n2. Testing System Stats...")
    stats = test_endpoint("/stats")
    results["stats"] = stats
    print(f"   {stats['status']}")
    
    # Test 3: Glossary Extraction
    print("\n3. Testing Glossary Extraction...")
    glossary = test_endpoint("/debug/glossary?text=The cloud server and database connection failed&target_language=fr")
    results["glossary"] = glossary
    if glossary['status'] == "✅ Success":
        matches = glossary['data'].get('matches', [])
        print(f"   Found {len(matches)} glossary terms:")
        for match in matches:
            print(f"   - {match['term']} → {match['translation']}")
    
    # Test 4: RAG Memory Search
    print("\n4. Testing RAG Memory Search...")
    memory = test_endpoint("/debug/memory?text=The server is down&target_language=fr")
    results["memory"] = memory
    if memory['status'] == "✅ Success":
        matches = memory['data'].get('matches', [])
        print(f"   Found {len(matches)} memory matches:")
        for match in matches:
            print(f"   - '{match['source_text']}' → '{match['target_text']}' (similarity: {match['similarity_score']})")
    
    # Test 5: MCP Prompt Construction
    print("\n5. Testing MCP Prompt Construction...")
    mcp = test_endpoint("/debug/mcp?text=The cloud server failed&target_language=fr")
    results["mcp"] = mcp
    if mcp['status'] == "✅ Success":
        print(f"   Built MCP prompt with {mcp['data']['glossary_matches']} glossary terms and {mcp['data']['memory_matches']} memory matches")
        print(f"   Prompt length: {mcp['data']['prompt_length']} characters")
    
    # Test 6: Translation
    print("\n6. Testing Translation...")
    translation = test_endpoint("/translate", "POST", {
        "text": "The cloud server failed to connect to the database",
        "target_language": "fr"
    })
    results["translation"] = translation
    print(f"   {translation['status']}")
    if translation['status'] == "✅ Success":
        print(f"   Translation: {translation['data']['translation']}")
        print(f"   Confidence: {translation['data']['confidence']}")
        print(f"   Processing time: {translation['data']['processing_time']:.2f}s")
    
    # Test 7: Feedback System
    print("\n7. Testing Feedback System...")
    feedback = test_endpoint("/feedback", "POST", {
        "source_text": "The authentication service is down",
        "target_text": "Le service d'authentification est hors service",
        "target_language": "fr",
        "is_accepted": True,
        "confidence": 0.95
    })
    results["feedback"] = feedback
    print(f"   {feedback['status']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    working_components = 0
    total_components = len(results)
    
    for component, result in results.items():
        status = "✅" if result['status'] == "✅ Success" else "❌"
        print(f"{status} {component.title()}: {result['status']}")
        if result['status'] == "✅ Success":
            working_components += 1
    
    print(f"\nOverall: {working_components}/{total_components} components working")
    
    if working_components == total_components:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some components need attention")
    
    return results

if __name__ == "__main__":
    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    import time
    time.sleep(3)
    
    results = run_comprehensive_tests()
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n📄 Detailed results saved to test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if all(r['status'] == "✅ Success" for r in results.values()) else 1)
