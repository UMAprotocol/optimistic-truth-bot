#!/usr/bin/env python3
"""Test script for the PolyMarket Oracle agentic system."""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from polymarket_oracle.manager import PolyMarketOracleManager


async def test_single_proposal():
    """Test processing a single proposal."""
    print("🧪 Testing PolyMarket Oracle Agentic System")
    print("=" * 50)
    
    # Sample proposal data (simplified version)
    sample_proposal = {
        "query_id": "0xe5373cc54eb12bc20210bbc945d0eb96881c6bdd90057b67abe6958bcce77a9d",
        "transaction_hash": "0xde871f58887ef3e98ef9f941df53ccd32766eaa3acb6800535564d2482c323b6",
        "block_number": 69125278,
        "request_timestamp": 1741964809,
        "ancillary_data": "q: title: Bitcoin Up or Down on March 16?, description: This market will resolve to \"Up\" if the \"Close\" price for the Binance 1 minute candle for BTCUSDT 15 Mar '25 12:00 in the ET timezone (noon) is lower than the final \"Close\" price for the 16 Mar '25 12:00 ET candle.\nThis market will resolve to \"Down\" if the \"Close\" price for the Binance 1 minute candle for BTCUSDT 15 Mar '25 12:00 in the ET timezone (noon) is higher than the final \"Close\" price for the 16 Mar '25 12:00 ET candle.",
        "resolution_conditions": "res_data:p1: 0, p2: 1, p3: 0.5. Where p1 corresponds to Down, p2 to Up, p3 to unknown/50-50.",
        "proposed_price": 0,
        "proposed_price_outcome": "p1",
        "tags": ["Crypto", "Bitcoin", "Crypto Prices", "Recurring"],
        "icon": "https://polymarket-upload.s3.us-east-2.amazonaws.com/bitcoin-up-or-down-on-march-13-ppoEj3rBtGBr.jpg",
        "condition_id": "0x0ecdbc27eda94366284bf4c8e990017491d57f95c53dcd2353d6104ff7cb9e54",
        "creator": "0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74",
        "proposer": "0xcf12F5b99605CB299Fb11d5EfF4fB304De008d02"
    }
    
    # Initialize manager
    manager = PolyMarketOracleManager(verbose=True)
    
    try:
        # Process the proposal
        print("\n🔮 Processing sample Bitcoin price proposal...")
        result = await manager.process_proposal(sample_proposal)
        
        print("\n📋 RESULTS:")
        print(f"Query ID: {result.get('query_id')}")
        print(f"Final Recommendation: {result.get('recommendation')}")
        
        # Show routing decision
        routing = result.get('agentic_results', {}).get('routing_decision', {})
        print(f"Selected Solvers: {', '.join(routing.get('solvers', []))}")
        print(f"Routing Reason: {routing.get('reason', 'N/A')}")
        
        # Show overseer decision
        overseer = result.get('agentic_results', {}).get('overseer_evaluation', {})
        print(f"Overseer Verdict: {overseer.get('verdict', 'N/A')}")
        print(f"Confidence Score: {overseer.get('confidence_score', 0)}")
        
        # Save result for inspection
        output_file = Path("test_result.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full result saved to: {output_file}")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_routing_only():
    """Test just the routing functionality."""
    print("\n🔄 Testing Router Agent Only")
    print("-" * 30)
    
    from polymarket_oracle.agents.router_agent import router_agent
    from agents import Runner
    
    # Test different types of questions
    test_questions = [
        "Bitcoin price on March 16th vs March 15th",
        "Who won the 2024 presidential election?", 
        "Yankees vs Red Sox game score on April 1st",
        "Will inflation exceed 3% in Q2 2025?"
    ]
    
    for question in test_questions:
        try:
            print(f"\nQuestion: {question}")
            result = await Runner.run(router_agent, question)
            routing_decision = result.final_output
            print(f"  → Solvers: {routing_decision.solvers}")
            print(f"  → Reason: {routing_decision.reason}")
        except Exception as e:
            print(f"  → Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting PolyMarket Oracle Agentic System Tests")
    
    async def run_all_tests():
        # Test routing first
        await test_routing_only()
        
        # Then test full system
        success = await test_single_proposal()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n💥 Some tests failed!")
    
    asyncio.run(run_all_tests())