"""
Neo4j Database Configuration
Configuration settings for Neo4j graph database connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j Connection Settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "forensics123")

# Connection Pool Settings
NEO4J_MAX_CONNECTION_LIFETIME = 3600  # 1 hour
NEO4J_MAX_CONNECTION_POOL_SIZE = 50
NEO4J_CONNECTION_TIMEOUT = 30  # seconds

# Database Settings
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")  # Default database

# Retry Settings
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds
