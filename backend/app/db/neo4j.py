from neo4j import GraphDatabase
from app.config import settings

driver = None

def init_neo4j():
    global driver
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

def get_neo4j_driver():
    return driver

def close_neo4j():
    global driver
    if driver is not None:
        driver.close()
