#!/usr/bin/env python3
"""
Test script to verify OpenAI agent functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_imports():
    """Test all required imports"""
    print("🧪 Testing imports...")
    
    try:
        from agents import Agent, Runner
        print("✅ agents SDK imported successfully")
    except ImportError as e:
        print(f"❌ agents SDK import failed: {e}")
        return False
    
    try:
        from agents_sdk.openai_sdk import generate_notion_docs, ALL_TOOLS
        print("✅ openai_sdk imported successfully")
        print(f"📊 Available tools: {len(ALL_TOOLS)}")
    except ImportError as e:
        print(f"❌ openai_sdk import failed: {e}")
        return False
    
    try:
        from env import LLM_API_KEY, NOTION_DATABASE_ID
        print("✅ Environment variables imported successfully")
        print(f"🔐 LLM_API_KEY: {'SET' if LLM_API_KEY else 'NOT SET'}")
        print(f"🔐 NOTION_DATABASE_ID: {'SET' if NOTION_DATABASE_ID else 'NOT SET'}")
    except ImportError as e:
        print(f"❌ Environment import failed: {e}")
        return False
    
    return True

def test_simple_agent():
    """Test creating a simple agent"""
    print("\n🤖 Testing simple agent creation...")
    
    try:
        from agents import Agent
        
        # Create a very simple agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant. Just say hello.",
            model="gpt-4o"
        )
        print("✅ Simple agent created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Simple agent creation failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_agent_with_tools():
    """Test creating agent with tools"""
    print("\n🛠️ Testing agent with tools...")
    
    try:
        from agents import Agent
        from agents_sdk.openai_sdk import ALL_TOOLS
        
        # Create agent with tools
        agent = Agent(
            name="Documentation Generator",
            instructions="You are a documentation generator.",
            tools=ALL_TOOLS,
            model="gpt-4o"
        )
        print("✅ Agent with tools created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Agent with tools creation failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_minimal_run():
    """Test running a minimal agent"""
    print("\n🏃 Testing minimal agent run...")
    
    try:
        from agents import Agent, Runner
        
        # Create and run a minimal agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant. When asked to say hello, just respond with 'Hello, World!'",
            model="gpt-4o"
        )
        
        print("🚀 Running agent...")
        result = Runner.run_sync(agent, "Say hello")
        print(f"✅ Agent run completed")
        print(f"📊 Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Agent run failed: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function"""
    print(f"\n{'='*60}")
    print(f"🧪 AGENT TESTING SUITE")
    print(f"{'='*60}\n")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed - stopping here")
        return False
    
    # Test 2: Simple agent
    if not test_simple_agent():
        print("\n❌ Simple agent test failed")
        return False
    
    # Test 3: Agent with tools
    if not test_agent_with_tools():
        print("\n❌ Agent with tools test failed")
        return False
    
    # Test 4: Minimal run
    if not test_minimal_run():
        print("\n❌ Minimal run test failed")
        return False
    
    print(f"\n{'='*60}")
    print(f"✅ ALL TESTS PASSED!")
    print(f"{'='*60}\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
