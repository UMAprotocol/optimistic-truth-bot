"""Router agent for determining which solver to use for PolyMarket proposals."""

from __future__ import annotations

from pydantic import BaseModel
from agents import Agent


class RoutingDecision(BaseModel):
    """Routing decision for a proposal."""
    solvers: list[str]
    reason: str
    multi_solver_strategy: str = ""


router_agent = Agent(
    name="Router Agent",
    instructions="""You are a routing expert for the UMA PolyMarket Oracle system. Your job is to analyze PolyMarket proposals and decide which solver(s) should handle them.

Available solvers:
1. **perplexity**: Best for general knowledge questions, recent events, and queries requiring web search
   - Can search the internet for up-to-date information
   - Good for complex, nuanced questions requiring general knowledge
   - Can interpret and explain concepts, events, and outcomes

2. **code_runner**: Best for precise data queries that require API access
   - Fetches real-time data from supported APIs (Binance crypto prices, Sports data)
   - Handles timezone conversions and date-specific queries
   - Provides deterministic results based on data sources
   - Limited to specifically supported data sources

3. **combined**: Use both solvers when the query benefits from both precise data and contextual understanding

Guidelines for routing decisions:
- For cryptocurrency price queries with specific dates/times → code_runner
- For sports game results with specific dates → code_runner  
- For general knowledge, politics, current events → perplexity
- For complex questions needing both precise data AND context → combined
- For questions about future events that haven't occurred → perplexity

When using multiple solvers, explain how they complement each other.""",
    output_type=RoutingDecision,
)