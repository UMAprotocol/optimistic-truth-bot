class QueryData:
    def __init__(
        self,
        query_id,
        unix_timestamp,
        ancillary_data,
        resolution_conditions,
        updates,
    ):
        self.query_id = query_id
        self.unix_timestamp = unix_timestamp
        self.ancillary_data = ancillary_data
        self.resolution_conditions = resolution_conditions
        self.updates = updates


# Sample data
queries = [
    QueryData(
        query_id="0x1cfc4c4f9307aeb267e2440d461d7edee842a089a5d4e32d40194371918d4b2c",
        unix_timestamp=1741040245,
        ancillary_data="""q: title: Will Donald Trump say "Coin" 5+ times during Crypto Summit on Friday?, description: Donald Trump is scheduled to deliver remarks at a White House Crypto Summit on March 7, 2025. You can read more about that summit here: https://thehill.com/policy/technology/5171305-white-house-to-host-first-crypto-summit/

This market will resolve to "Yes" if Donald Trump says the listed term during his main speech at this event. Otherwise, the market will resolve to "No".

Any usage of the term regardless of context will count toward the resolution of this market.

Pluralization/possessive of the term will count toward the resolution of this market, however other forms will NOT count.

Instances where the term is used in a compound word will count regardless of context (e.g. joyful is not a compound word for "joy," however "killjoy" is a compounding of the words "kill" and "joy").

If this event is definitively cancelled, or otherwise is not aired by March 7, 2025, 11:59 PM ET, this market will resolve to "No".

The resolution source will be video of the speech.""",
        resolution_conditions="""res_data: p1: 0, p2: 1, p3: 0.5. Where p1 corresponds to No, p2 to Yes, p3 to unknown/50-50.""",
        updates=[
            """As stated, only a main speech made by Trump will count toward market resolutions. Any Q&A will not count toward this market's resolution.""",
            """Per standard interpretations of English grammar, "Bitcoin" and "Dogecoin" are compound words. Compound words count as mentions of terms in relevant markets.""",
        ],
    ),
    QueryData(
        query_id="0x96b1fdd1ab38085cea9bd608740365397c9c0f1244f2a6be3af8df023138ed6a",
        unix_timestamp=1741040835,
        ancillary_data="""q: title: Will Donald Trump say "ETF" or "Exchange Traded Fund" during Crypto Summit on Friday?, description: Donald Trump is scheduled to deliver remarks at a White House Crypto Summit on March 7, 2025. You can read more about that summit here: https://thehill.com/policy/technology/5171305-white-house-to-host-first-crypto-summit/

This market will resolve to "Yes" if Donald Trump says the listed term during his main speech at this event. Otherwise, the market will resolve to "No".

Any usage of the term regardless of context will count toward the resolution of this market.

Pluralization/possessive of the term will count toward the resolution of this market, however other forms will NOT count.

Instances where the term is used in a compound word will count regardless of context (e.g. joyful is not a compound word for "joy," however "killjoy" is a compounding of the words "kill" and "joy").

If this event is definitively cancelled, or otherwise is not aired by March 7, 2025, 11:59 PM ET, this market will resolve to "No".

The resolution source will be video of the speech.""",
        resolution_conditions="""res_data: p1: 0, p2: 1, p3: 0.5. Where p1 corresponds to No, p2 to Yes, p3 to unknown/50-50.""",
        updates=[
            """As stated, only a main speech made by Trump will count toward market resolutions. Any Q&A will not count toward this markets's resolution."""
        ],
    ),
]