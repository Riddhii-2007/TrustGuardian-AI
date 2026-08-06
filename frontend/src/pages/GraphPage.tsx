import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../api/graph.api';
import CytoscapeComponent from 'react-cytoscapejs';
import { Network, Loader2 } from 'lucide-react';

const GraphPage: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['graphData'],
    queryFn: graphApi.getVisualizeData
  });

  // Transform backend models into Cytoscape elements
  const elements = useMemo(() => {
    if (!data) return [];
    
    const nodes = data.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        name: node.properties.name || node.properties.address || node.id,
        type: node.label
      }
    }));

    const edges = data.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.type
      }
    }));

    return [...nodes, ...edges];
  }, [data]);

  const cytoscapeStylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': '#06b6d4',
        'label': 'data(name)',
        'color': '#f8fafc',
        'font-size': '12px',
        'text-valign': 'bottom' as const,
        'text-halign': 'center' as const,
        'text-margin-y': 5,
        'width': 40,
        'height': 40
      }
    },
    {
      selector: 'node[type = "Employee"]',
      style: {
        'background-color': '#3b82f6',
        'shape': 'ellipse' as const
      }
    },
    {
      selector: 'node[type = "Device"]',
      style: {
        'background-color': '#8b5cf6',
        'shape': 'round-rectangle' as const
      }
    },
    {
      selector: 'node[type = "IPAddress"]',
      style: {
        'background-color': '#10b981',
        'shape': 'hexagon' as const
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#475569',
        'target-arrow-color': '#475569',
        'target-arrow-shape': 'triangle' as const,
        'curve-style': 'bezier' as const,
        'label': 'data(label)',
        'font-size': '10px',
        'color': '#94a3b8',
        'text-rotation': 'autorotate' as const,
        'text-margin-y': -10
      }
    }
  ];

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in">
      <header>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Network className="text-cyan-400" /> Enterprise Knowledge Graph
        </h2>
        <p className="text-slate-400 mt-1">Live context and relationship mapping powered by Neo4j AuraDB.</p>
      </header>

      <div className="flex-1 min-h-0 glass-card p-0 overflow-hidden relative">
        {isLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/50">
            <Loader2 className="animate-spin text-cyan-500 mb-4" size={48} />
            <p className="text-slate-400">Querying Neo4j Cloud Database...</p>
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/50 p-8 text-center">
            <div className="text-red-400 text-xl font-bold mb-2">Connection Error</div>
            <p className="text-slate-400 max-w-md">
              Failed to connect to Neo4j. Please ensure your AuraDB instance is running and the credentials in the .env file are correct.
            </p>
          </div>
        ) : (
          <CytoscapeComponent
            elements={elements}
            stylesheet={cytoscapeStylesheet}
            style={{ width: '100%', height: '100%' }}
            layout={{ name: 'cose', padding: 50, animate: true }}
            minZoom={0.5}
            maxZoom={2}
          />
        )}
      </div>
    </div>
  );
};

export default GraphPage;
