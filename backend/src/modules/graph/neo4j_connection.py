"""
Neo4j Connection Handler
Manages Neo4j database connections with error handling and connection pooling
Authors: Krusha (Primary), Mohit (Integration)
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import time
import os

# Import config with fallback for standalone execution
try:
    from .config import (
        NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, 
        NEO4J_MAX_CONNECTION_LIFETIME, NEO4J_MAX_CONNECTION_POOL_SIZE,
        NEO4J_CONNECTION_TIMEOUT, MAX_RETRY_ATTEMPTS, RETRY_DELAY
    )
except ImportError:
    # Fallback for standalone execution
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "forensics123")
    NEO4J_MAX_CONNECTION_LIFETIME = 3600
    NEO4J_MAX_CONNECTION_POOL_SIZE = 50
    NEO4J_CONNECTION_TIMEOUT = 30
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2



class Neo4jConnection:
    """
    Handles Neo4j database connections with automatic retry and error handling
    """
    
    def __init__(self, uri=None, user=None, password=None):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j URI (defaults to config)
            user: Neo4j username (defaults to config)
            password: Neo4j password (defaults to config)
        """
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j with retry logic"""
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                print(f"🔌 Connecting to Neo4j at {self.uri}...")
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_lifetime=NEO4J_MAX_CONNECTION_LIFETIME,
                    max_connection_pool_size=NEO4J_MAX_CONNECTION_POOL_SIZE,
                    connection_timeout=NEO4J_CONNECTION_TIMEOUT
                )
                # Test connection
                self.driver.verify_connectivity()
                print("✅ Successfully connected to Neo4j!")
                return
            except ServiceUnavailable as e:
                print(f"⚠️  Neo4j not available (attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS})")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    print(f"   Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise ConnectionError(
                        "❌ Could not connect to Neo4j. Please ensure:\n"
                        "   1. Docker is running\n"
                        "   2. Neo4j container is started: docker-compose up -d\n"
                        "   3. Neo4j is accessible at bolt://localhost:7687"
                    ) from e
            except AuthError as e:
                raise ConnectionError(
                    "❌ Neo4j authentication failed. Please check:\n"
                    "   - Username: neo4j\n"
                    "   - Password: forensics123\n"
                    "   - Or update credentials in docker-compose.yml"
                ) from e
            except Exception as e:
                raise ConnectionError(f"❌ Unexpected error connecting to Neo4j: {str(e)}") from e
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed")
    
    def execute_query(self, query, parameters=None):
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Dictionary of query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise ConnectionError("No active Neo4j connection")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"❌ Query execution failed: {str(e)}")
            print(f"   Query: {query}")
            print(f"   Parameters: {parameters}")
            raise
    
    def execute_write_transaction(self, transaction_function, *args, **kwargs):
        """
        Execute a write transaction with automatic retry
        
        Args:
            transaction_function: Function that takes a transaction object
            *args, **kwargs: Arguments to pass to transaction_function
            
        Returns:
            Result from transaction_function
        """
        if not self.driver:
            raise ConnectionError("No active Neo4j connection")
        
        with self.driver.session() as session:
            return session.write_transaction(transaction_function, *args, **kwargs)
    
    def execute_read_transaction(self, transaction_function, *args, **kwargs):
        """
        Execute a read transaction
        
        Args:
            transaction_function: Function that takes a transaction object
            *args, **kwargs: Arguments to pass to transaction_function
            
        Returns:
            Result from transaction_function
        """
        if not self.driver:
            raise ConnectionError("No active Neo4j connection")
        
        with self.driver.session() as session:
            return session.read_transaction(transaction_function, *args, **kwargs)
    
    def clear_database(self):
        """
        ⚠️ WARNING: Delete all nodes and relationships in the database
        Use only for testing/development
        """
        print("⚠️  Clearing Neo4j database...")
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        print("✅ Database cleared")
    
    def get_node_count(self):
        """Get total number of nodes in database"""
        query = "MATCH (n) RETURN count(n) as count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0
    
    def get_relationship_count(self):
        """Get total number of relationships in database"""
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0
    
    def get_database_stats(self):
        """Get database statistics"""
        return {
            "nodes": self.get_node_count(),
            "relationships": self.get_relationship_count()
        }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Test connection if run directly
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Testing Neo4j Connection")
    print("="*60 + "\n")
    
    try:
        # Test basic connection
        with Neo4jConnection() as conn:
            print("\n📊 Database Stats:")
            stats = conn.get_database_stats()
            print(f"   Nodes: {stats['nodes']}")
            print(f"   Relationships: {stats['relationships']}")
            
            # Test simple query
            print("\n🧪 Testing simple query...")
            result = conn.execute_query("RETURN 1 as test, 'Hello Neo4j' as message")
            print(f"   Result: {result}")
            
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
