import openai # For embeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct, Distance, VectorParams # Ensure models is imported correctly if using older client version syntax. For newer, it's often just 'models'
from app.core.config import settings
from typing import List, Optional
from uuid import UUID
import datetime # Added for potential timestamping in payload

# OpenAI embedding model details
EMBEDDING_MODEL = "text-embedding-ada-002" # OpenAI's Ada v2 model
EMBEDDING_DIMENSION = 1536 # Dimension for text-embedding-ada-002

qdrant_client_instance: Optional[QdrantClient] = None # Renamed to avoid conflict with module

async def get_qdrant_client() -> QdrantClient:
    global qdrant_client_instance
    if qdrant_client_instance is None:
        try:
            qdrant_client_instance = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                # prefer_grpc=True, # Enable if QDRANT_PORT is set to gRPC port like 6333
            )
            print("Qdrant client initialized.")
        except Exception as e:
            print(f"Failed to initialize Qdrant client: {e}")
            raise # Re-raise to signal problem during startup or first use
    return qdrant_client_instance

async def ensure_resume_collection():
    client = await get_qdrant_client()
    collection_name = settings.QDRANT_RESUME_COLLECTION
    try:
        # Check if collection exists
        # get_collection throws an exception if not found, so this is a valid check.
        client.get_collection(collection_name)
        print(f"Collection '{collection_name}' already exists.")
    except Exception: # Exception typically means collection not found (e.g. UnexpectedResponse for HTTP, or specific gRPC error)
        print(f"Collection '{collection_name}' not found, creating it.")
        client.recreate_collection( # Use recreate_collection for simplicity, or create_collection if specific config needed and sure it doesn't exist
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=EMBEDDING_DIMENSION, distance=models.Distance.COSINE) # Using models.VectorParams and models.Distance
        )
        print(f"Collection '{collection_name}' created.")

async def get_text_embedding(text: str, model: str = EMBEDDING_MODEL) -> Optional[List[float]]:
    if not settings.OPENAI_API_KEY:
        print("OPENAI_API_KEY not set. Cannot generate embeddings.")
        return None
    try:
        aclient = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await aclient.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

async def upsert_resume_embedding(resume_id: UUID, user_id: UUID, resume_text: str):
    client = await get_qdrant_client()
    collection_name = settings.QDRANT_RESUME_COLLECTION

    embedding = await get_text_embedding(resume_text)
    if embedding is None:
        print(f"Failed to generate embedding for resume_id: {resume_id}. Skipping Qdrant upsert.")
        return

    point = models.PointStruct( # Using models.PointStruct
        id=str(resume_id),
        vector=embedding,
        payload={
            "user_id": str(user_id),
            "resume_id": str(resume_id),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat() # Add timestamp for potential filtering/sorting
        }
    )

    try:
        await ensure_resume_collection() # Ensure collection exists before upserting

        client.upsert(collection_name=collection_name, points=[point])
        print(f"Successfully upserted embedding for resume_id: {resume_id}")
    except Exception as e:
        print(f"Error upserting embedding to Qdrant for resume_id {resume_id}: {e}")

async def delete_resume_embedding(resume_id: UUID):
    client = await get_qdrant_client()
    collection_name = settings.QDRANT_RESUME_COLLECTION
    try:
        # Check if collection exists before attempting delete to avoid errors if it doesn't
        # However, ensure_resume_collection would create it if it's missing.
        # A delete operation on a non-existent collection or non-existent point usually doesn't error harshly in Qdrant,
        # but behavior can vary. It's safer to assume collection exists if upserts are happening.
        client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=[str(resume_id)]) # Using models.PointIdsList
        )
        print(f"Successfully deleted embedding for resume_id: {resume_id} from Qdrant.")
    except Exception as e:
        # Catching specific Qdrant errors might be better if known, e.g. if collection doesn't exist after all
        print(f"Error deleting embedding from Qdrant for resume_id {resume_id}: {e}")

# Example of how to initialize Qdrant on app startup (optional, can be lazy loaded)
# In main.py:
# from app.services.vector_service import ensure_resume_collection, get_qdrant_client
# @app.on_event("startup")
# async def startup_event():
# try:
# await get_qdrant_client() # Initialize client
# await ensure_resume_collection() # Ensure collection exists
# print("Qdrant connection and collection checked successfully.")
# except Exception as e:
# print(f"QDRANT STARTUP ERROR: {e}")
