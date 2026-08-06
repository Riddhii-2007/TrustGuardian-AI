import { apiClient } from './client';
import type { APIResponse } from '../types/common.types';

export interface Entity {
  id: string;
  label: string;
  properties: Record<string, any>;
}

export interface Relationship {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Entity[];
  edges: Relationship[];
}

export const graphApi = {
  getVisualizeData: async (): Promise<GraphData> => {
    const response = await apiClient.get<APIResponse<GraphData>>('/api/graph/visualize');
    return response.data.data;
  }
};
