from neo4j import AsyncGraphDatabase
from app.models.graph import GraphData, Entity, Relationship
from app.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class GraphService:
    """
    Service for Neo4j operations connecting to AuraDB.
    """
    def __init__(self):
        self.driver = None
        
    async def connect(self):
        if not self.driver:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI, 
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Test connection
                await self.driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j AuraDB.")
                await self._seed_mock_graph()
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")

    async def _seed_mock_graph(self):
        """Seeds the AuraDB with an initial TrustGuardian mock network if empty."""
        seed_query = """
        MATCH (n) RETURN count(n) as count
        """
        create_query = """
        CREATE (e1:Employee {id: 'emp-001', name: 'John Doe', department: 'Finance', risk_score: 15})
        CREATE (e2:Employee {id: 'emp-002', name: 'Jane Smith', department: 'Engineering', risk_score: 5})
        CREATE (d1:Device {id: 'dev-101', type: 'Laptop', os: 'Windows 11', compliant: true})
        CREATE (d2:Device {id: 'dev-102', type: 'Mobile', os: 'iOS 17', compliant: false})
        CREATE (ip1:IPAddress {id: 'ip-201', address: '192.168.1.50', location: 'New York'})
        CREATE (ip2:IPAddress {id: 'ip-202', address: '45.33.22.11', location: 'Unknown (VPN)'})
        
        CREATE (e1)-[:OWNS]->(d1)
        CREATE (e2)-[:OWNS]->(d2)
        CREATE (d1)-[:LOGGED_IN_FROM]->(ip1)
        CREATE (d2)-[:LOGGED_IN_FROM]->(ip2)
        CREATE (e1)-[:COMMUNICATES_WITH {frequency: 'high'}]->(e2)
        """
        async with self.driver.session() as session:
            result = await session.run(seed_query)
            record = await result.single()
            if record and record["count"] == 0:
                logger.info("Database is empty. Seeding mock graph...")
                await session.run(create_query)
                logger.info("Seeding complete.")

    async def get_visualize_data(self) -> GraphData:
        if not self.driver:
            await self.connect()
            
        if not self.driver:
            return GraphData(nodes=[], edges=[])

        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT 100
        """
        nodes = {}
        edges = []
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query)
                async for record in result:
                    n = record["n"]
                    m = record["m"]
                    r = record["r"]
                    
                    # Add Source Node
                    if n.element_id not in nodes:
                        nodes[n.element_id] = Entity(
                            id=n.element_id, 
                            label=list(n.labels)[0] if n.labels else "Unknown", 
                            properties=dict(n.items())
                        )
                        
                    # Add Target Node
                    if m.element_id not in nodes:
                        nodes[m.element_id] = Entity(
                            id=m.element_id, 
                            label=list(m.labels)[0] if m.labels else "Unknown", 
                            properties=dict(m.items())
                        )
                        
                    # Add Edge
                    edges.append(Relationship(
                        id=r.element_id,
                        source=r.nodes[0].element_id,
                        target=r.nodes[1].element_id,
                        type=r.type,
                        properties=dict(r.items())
                    ))
                    
            return GraphData(nodes=list(nodes.values()), edges=edges)
            
        except Exception as e:
            logger.error(f"Error querying Neo4j: {e}")
            return GraphData(nodes=[], edges=[])

graph_service = GraphService()
