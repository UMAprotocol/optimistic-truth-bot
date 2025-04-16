#!/usr/bin/env python3
"""
API for querying the LLM oracle experiment outputs from MongoDB
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="LLM Oracle API",
    description="API for querying LLM oracle experiment outputs from MongoDB",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# MongoDB connection
def get_mongo_client():
    """Get MongoDB client from MONGO_URI in .env file."""
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        logger.error("MONGO_URI not found in .env file")
        raise HTTPException(status_code=500, detail="Database configuration error")

    try:
        return MongoClient(mongo_uri)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")


def get_outputs_collection():
    """Get the outputs collection from MongoDB"""
    client = get_mongo_client()
    db_name = os.getenv("MONGODB_DB", "uma_oracle")
    collection_name = os.getenv("MONGODB_COLLECTION", "experiments")

    try:
        db = client[db_name]
        collection = db[f"{collection_name}_outputs"]
        return client, collection
    except Exception as e:
        logger.error(f"Error accessing MongoDB collection: {e}")
        if client:
            client.close()
        raise HTTPException(status_code=500, detail="Database collection access error")


# Helper function to format response
def format_response(doc: Dict[str, Any], full: bool = True) -> Dict[str, Any]:
    """Format the MongoDB document for API response"""
    if not full:
        # Return reduced version with essential fields
        return {
            "_id": str(doc.get("_id")),
            "experiment_id": doc.get("experiment_id"),
            "question_id": doc.get("question_id"),
            "query_id": doc.get("query_id"),
            "condition_id": doc.get("condition_id"),
            "recommendation": doc.get("recommendation"),
            "disputed": doc.get("disputed"),
            "proposed_price_outcome": doc.get("proposed_price_outcome"),
            "resolved_price_outcome": doc.get("resolved_price_outcome"),
            "transaction_hash": (
                doc.get("proposal_metadata", {}).get("transaction_hash")
                if doc.get("proposal_metadata")
                else None
            ),
            "tags": doc.get("tags", []),
        }
    else:
        # Return full version with all fields
        # Convert ObjectId to string for JSON serialization
        doc["_id"] = str(doc.get("_id"))
        return doc


# Endpoints
@app.get("/")
async def root():
    """Root endpoint for API health check"""
    return {"status": "online", "message": "LLM Oracle API is running"}


@app.get("/api/query", response_model=List[Dict[str, Any]])
async def query_by_params(
    query_id: Optional[str] = Query(None, description="Query by query_id"),
    condition_id: Optional[str] = Query(None, description="Query by condition_id"),
    transaction_hash: Optional[str] = Query(
        None, description="Query by transaction hash"
    ),
    full: bool = Query(
        True, description="Return full JSON if true, reduced version if false"
    ),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """Query experiments by query_id, condition_id, or transaction_hash"""
    client, collection = get_outputs_collection()

    try:
        # Build the query filter
        query_filter = {}

        if query_id:
            query_filter["query_id"] = query_id

        if condition_id:
            query_filter["condition_id"] = condition_id

        if transaction_hash:
            query_filter["$or"] = [
                {"proposal_metadata.transaction_hash": transaction_hash},
                {"transaction_hash": transaction_hash}
            ]

        if not query_filter:
            raise HTTPException(
                status_code=400,
                detail="At least one query parameter (query_id, condition_id, transaction_hash) is required",
            )

        # Execute the query
        results = list(collection.find(query_filter).limit(limit))

        if not results:
            return []

        # Format the response
        return [format_response(doc, full) for doc in results]

    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        client.close()


@app.get("/api/advanced-query", response_model=List[Dict[str, Any]])
async def advanced_query(
    identifier: Optional[str] = Query(None, description="Query by identifier (partial match on tags or other identifier fields)"),
    start_timestamp: Optional[int] = Query(None, description="Query by start timestamp (Unix timestamp)"),
    end_timestamp: Optional[int] = Query(None, description="Query by end timestamp (Unix timestamp)"),
    ancillary_data: Optional[str] = Query(None, description="Query by ancillary data (partial match)"),
    tags: Optional[List[str]] = Query(None, description="Query by tags (list of tags to match)"),
    recommendation: Optional[str] = Query(None, description="Query by recommendation (p1, p2, p3, p4)"),
    full: bool = Query(
        True, description="Return full JSON if true, reduced version if false"
    ),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """Advanced query with support for timestamp, ancillary data, and identifiers (GET method)"""
    return await _advanced_query(
        identifier=identifier,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        ancillary_data=ancillary_data,
        tags=tags,
        recommendation=recommendation,
        full=full,
        limit=limit
    )


from fastapi import Body
from pydantic import BaseModel
from typing import List as TypeList, Optional

class AdvancedQueryRequest(BaseModel):
    identifier: Optional[str] = None
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    ancillary_data: Optional[str] = None
    tags: Optional[TypeList[str]] = None
    recommendation: Optional[str] = None
    full: bool = True
    limit: int = 10

@app.post("/api/advanced-query", response_model=List[Dict[str, Any]])
async def advanced_query_post(
    query: AdvancedQueryRequest = Body(..., description="Advanced query parameters")
):
    """Advanced query with support for timestamp, ancillary data, and identifiers (POST method)"""
    return await _advanced_query(
        identifier=query.identifier,
        start_timestamp=query.start_timestamp,
        end_timestamp=query.end_timestamp,
        ancillary_data=query.ancillary_data,
        tags=query.tags,
        recommendation=query.recommendation,
        full=query.full,
        limit=query.limit
    )


async def _advanced_query(
    identifier: Optional[str] = None,
    start_timestamp: Optional[int] = None,
    end_timestamp: Optional[int] = None,
    ancillary_data: Optional[str] = None,
    tags: Optional[List[str]] = None,
    recommendation: Optional[str] = None,
    full: bool = True,
    limit: int = 10,
):
    """Internal implementation of advanced query logic"""
    client, collection = get_outputs_collection()

    try:
        # Build the query filter
        query_filter = {}

        # Handle identifier search (partial match on tags or other identifier fields)
        if identifier:
            query_filter["$or"] = [
                {"proposal_metadata.tags": {"$regex": identifier, "$options": "i"}},
                {"proposal_metadata.icon": {"$regex": identifier, "$options": "i"}},
                {"tags": {"$regex": identifier, "$options": "i"}},
                {"icon": {"$regex": identifier, "$options": "i"}},
                {"query_id": {"$regex": identifier, "$options": "i"}},
                {"condition_id": {"$regex": identifier, "$options": "i"}},
                {"transaction_hash": {"$regex": identifier, "$options": "i"}},
                {"proposal_metadata.transaction_hash": {"$regex": identifier, "$options": "i"}},
                {"question_id": {"$regex": identifier, "$options": "i"}}
            ]

        # Handle timestamp range
        if start_timestamp or end_timestamp:
            timestamp_filter = {}
            if start_timestamp:
                timestamp_filter["$gte"] = start_timestamp
            if end_timestamp:
                timestamp_filter["$lte"] = end_timestamp
            
            if timestamp_filter:
                query_filter["$or"] = [
                    {"proposal_metadata.request_timestamp": timestamp_filter},
                    {"request_timestamp": timestamp_filter}
                ]

        # Handle ancillary data (partial match)
        if ancillary_data:
            query_filter["$or"] = [
                {"proposal_metadata.ancillary_data": {"$regex": ancillary_data, "$options": "i"}},
                {"ancillary_data": {"$regex": ancillary_data, "$options": "i"}},
                {"ancillary_data_hex": {"$regex": ancillary_data, "$options": "i"}}
            ]

        # Handle tags (array contains any)
        if tags and len(tags) > 0:
            query_filter["$or"] = [
                {"proposal_metadata.tags": {"$in": tags}},
                {"tags": {"$in": tags}}
            ]

        # Handle recommendation filter
        if recommendation:
            recommendation = recommendation.lower()
            query_filter["$or"] = [
                {"recommendation": recommendation},
                {"result.recommendation": recommendation},
                {"proposed_price_outcome": recommendation},
                {"proposal_metadata.proposed_price_outcome": recommendation}
            ]

        # If no filters provided, return an error
        if not query_filter:
            raise HTTPException(
                status_code=400,
                detail="At least one query parameter is required"
            )

        # Execute the query
        results = list(collection.find(query_filter).limit(limit))

        if not results:
            return []

        # Format the response
        return [format_response(doc, full) for doc in results]

    except Exception as e:
        logger.error(f"Advanced query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        client.close()


@app.get("/api/experiment/{experiment_id}", response_model=List[Dict[str, Any]])
async def get_by_experiment_id(
    experiment_id: str,
    full: bool = Query(
        True, description="Return full JSON if true, reduced version if false"
    ),
    limit: int = Query(100, description="Maximum number of results to return"),
):
    """Get all questions for a specific experiment"""
    client, collection = get_outputs_collection()

    try:
        results = list(collection.find({"experiment_id": experiment_id}).limit(limit))

        if not results:
            return []

        return [format_response(doc, full) for doc in results]

    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        client.close()


@app.get("/api/question/{question_id}", response_model=Dict[str, Any])
async def get_by_question_id(
    question_id: str,
    full: bool = Query(
        True, description="Return full JSON if true, reduced version if false"
    ),
):
    """Get experiment by question_id"""
    client, collection = get_outputs_collection()

    try:
        result = collection.find_one({"question_id": question_id})

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Question ID {question_id} not found"
            )

        return format_response(result, full)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
