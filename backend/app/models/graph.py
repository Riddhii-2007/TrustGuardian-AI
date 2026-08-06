from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Entity(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class Relationship(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class GraphData(BaseModel):
    nodes: List[Entity]
    edges: List[Relationship]
