import React, { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../api/graph.api';
import CytoscapeComponent from 'react-cytoscapejs';
import { Network, Loader2, ShieldCheck, HardDrive } from 'lucide-react';

const GraphPage: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['graphData'],
    queryFn: graphApi.getVisualizeData
  });

  const [cy, setCy] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  // Bind selection listeners on cytoscape mount
  useEffect(() => {
    if (!cy) return;

    cy.on('tap', 'node', (evt: any) => {
      const node = evt.target;
      setSelectedNode(node.data());
    });

    cy.on('tap', (evt: any) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    return () => {
      if (cy) {
        cy.unbind('tap');
      }
    };
  }, [cy]);

  // Transform backend models into Cytoscape elements
  const elements = useMemo(() => {
    if (!data) return [];
    
    const nodes = data.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        name: node.properties.name || node.properties.address || node.properties.type || node.id,
        type: node.label,
        properties: node.properties
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
        'background-color': '#050816',
        'border-width': 2.5,
        'border-color': '#06b6d4',
        'label': 'data(name)',
        'color': '#94a3b8',
        'font-size': '11px',
        'font-family': 'JetBrains Mono, monospace',
        'text-valign': 'bottom' as const,
        'text-halign': 'center' as const,
        'text-margin-y': 6,
        'width': 36,
        'height': 36,
        'overlay-opacity': 0,
        'transition-property': 'background-color, border-color, width, height',
        'transition-duration': 0.3
      }
    },
    {
      selector: 'node[type = "Employee"]',
      style: {
        'border-color': '#3b82f6',
        'shape': 'ellipse' as const
      }
    },
    {
      selector: 'node[type = "Device"]',
      style: {
        'border-color': '#8b5cf6',
        'shape': 'round-rectangle' as const
      }
    },
    {
      selector: 'node[type = "IPAddress"]',
      style: {
        'border-color': '#f97316',
        'shape': 'hexagon' as const
      }
    },
    {
      selector: 'node:selected',
      style: {
        'width': 44,
        'height': 44,
        'border-color': '#22d3ee',
        'border-width': 4,
        'background-color': 'rgba(6, 182, 212, 0.15)'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': 'rgba(6, 182, 212, 0.15)',
        'target-arrow-color': 'rgba(6, 182, 212, 0.25)',
        'target-arrow-shape': 'triangle' as const,
        'curve-style': 'bezier' as const,
        'label': 'data(label)',
        'font-size': '9px',
        'font-family': 'JetBrains Mono, monospace',
        'color': '#64748b',
        'text-rotation': 'autorotate' as const,
        'text-margin-y': -8
      }
    },
    {
      selector: 'edge:hover',
      style: {
        'line-color': '#06b6d4',
        'width': 3
      }
    }
  ];

  return (
    <div className="h-full flex flex-col space-y-6 animate-fade-in pb-8">
      <header>
        <h2 className="text-3xl font-extrabold text-slate-100 flex items-center gap-3 tracking-tight">
          <Network className="text-cyan-400" /> Enterprise Knowledge Graph
        </h2>
        <p className="text-base text-slate-400 mt-2">Live correlation maps and actor profiles powered by Neo4j AuraDB.</p>
      </header>

      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Graph Display Area */}
        <div className="lg:col-span-3 cyber-panel p-0 overflow-hidden relative">
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/40">
              <Loader2 className="animate-spin text-cyan-500 mb-4" size={48} />
              <p className="text-slate-400 font-semibold">Querying Neo4j Cloud Database...</p>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/40 p-8 text-center">
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
              minZoom={0.4}
              maxZoom={2.5}
              cy={(cyRef) => setCy(cyRef)}
            />
          )}
        </div>

        {/* Selected Entity Details Panel (Palantir Gotham Style) */}
        <div className="lg:col-span-1 cyber-panel p-6 flex flex-col overflow-auto min-h-[400px]">
          <div className="border-b border-slate-800/40 pb-4 mb-4">
            <h3 className="font-bold text-slate-200 text-lg flex items-center gap-2">
              <HardDrive size={18} className="text-cyan-400" /> Entity Inspector
            </h3>
            <p className="text-xs text-slate-500 mt-1">Select any graph node to inspect live attributes.</p>
          </div>

          {selectedNode ? (
            <div className="flex-1 flex flex-col space-y-5">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Classification</span>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase border ${
                    selectedNode.type === 'IPAddress' 
                      ? 'bg-orange-500/10 border-orange-500/20 text-orange-400' 
                      : selectedNode.type === 'Employee' 
                      ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' 
                      : 'bg-purple-500/10 border-purple-500/20 text-purple-400'
                  }`}>
                    {selectedNode.type}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Entity Name / ID</span>
                <h4 className="text-base font-bold text-slate-100 mt-1 break-all font-mono">{selectedNode.name}</h4>
              </div>

              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Associated Properties</span>
                <div className="mt-2 bg-slate-950/40 border border-slate-900/60 rounded-xl p-3 space-y-3 font-mono text-[11px] text-slate-400">
                  {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, val]: [string, any]) => (
                    <div key={key} className="flex justify-between border-b border-slate-900/30 pb-1.5 last:border-0 last:pb-0">
                      <span className="text-slate-500 uppercase">{key}</span>
                      <span className="text-slate-300 select-all truncate max-w-[150px]">{String(val)}</span>
                    </div>
                  ))}
                  {(!selectedNode.properties || Object.keys(selectedNode.properties).length === 0) && (
                    <div className="text-slate-600 text-center py-2">No metadata properties found.</div>
                  )}
                </div>
              </div>

              <div className="mt-auto bg-cyan-950/15 border border-cyan-800/20 rounded-xl p-4 flex items-center gap-3">
                <ShieldCheck size={20} className="text-cyan-400 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-slate-200">Active Integrity Lock</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Audited by Guardian Engine</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-500 py-10">
              <Network size={40} className="text-slate-700 mb-3 animate-pulse" />
              <p className="text-sm font-semibold text-slate-400">No Node Selected</p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Click on any node in the graph layout to dump network parameters, credentials, or audit trails.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default GraphPage;
