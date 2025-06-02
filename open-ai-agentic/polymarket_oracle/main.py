"""Main entry point for the PolyMarket Oracle agentic system."""

import asyncio
import argparse
import json
from pathlib import Path

from .manager import PolyMarketOracleManager


async def main():
    """Main entry point for the PolyMarket Oracle system."""
    parser = argparse.ArgumentParser(description="PolyMarket Oracle Agentic System")
    parser.add_argument(
        "--proposals-dir", 
        type=str, 
        default="../proposals/01042025-backtest-cherrypicked/proposals",
        help="Directory containing proposal JSON files"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="./output",
        help="Directory to save results"
    )
    parser.add_argument(
        "--max-proposals", 
        type=int, 
        default=5,
        help="Maximum number of proposals to process (for testing)"
    )
    parser.add_argument(
        "--single-proposal", 
        type=str,
        help="Path to a single proposal JSON file to process"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--api-keys-config",
        type=str,
        default="../api_keys_config.json",
        help="Path to API keys configuration file"
    )
    
    args = parser.parse_args()
    
    # Initialize the manager
    manager = PolyMarketOracleManager(
        verbose=args.verbose,
        api_keys_config_path=args.api_keys_config
    )
    
    if args.single_proposal:
        # Process a single proposal
        print(f"🔮 Processing single proposal: {args.single_proposal}")
        
        with open(args.single_proposal, 'r') as f:
            proposal_data = json.load(f)
        
        # Handle both single proposal and list format
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            proposal_data = proposal_data[0]
        
        result = await manager.process_proposal(proposal_data)
        
        # Save result
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        output_file = output_path / f"result_{result['short_id']}_{result['timestamp']}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Result saved to {output_file}")
        print(f"🎯 Recommendation: {result['recommendation']}")
        
    else:
        # Process multiple proposals from directory
        print(f"📁 Processing proposals from: {args.proposals_dir}")
        print(f"💾 Saving results to: {args.output_dir}")
        
        results = await manager.process_proposals_from_directory(
            proposals_dir=args.proposals_dir,
            output_dir=args.output_dir,
            max_proposals=args.max_proposals
        )
        
        # Print summary
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"Total proposals processed: {len(results)}")
        
        recommendations = {}
        for result in results:
            rec = result.get('recommendation', 'unknown')
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        for rec, count in recommendations.items():
            print(f"  {rec}: {count}")


if __name__ == "__main__":
    asyncio.run(main())