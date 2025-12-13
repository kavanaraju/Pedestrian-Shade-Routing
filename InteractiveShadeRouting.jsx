import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Priority Queue for Dijkstra
class PriorityQueue {
  constructor() {
    this.items = [];
  }
  
  enqueue(item, priority) {
    this.items.push({ item, priority });
    this.items.sort((a, b) => a.priority - b.priority);
  }
  
  dequeue() {
    return this.items.shift()?.item;
  }
  
  isEmpty() {
    return this.items.length === 0;
  }
}

// Dijkstra's algorithm
function dijkstra(graph, start, end, useShade = false, scenario = 'summer_midday', shadeWeight = 0.3) {
  const distances = {};
  const previous = {};
  const pq = new PriorityQueue();
  
  // Initialize
  Object.keys(graph).forEach(node => {
    distances[node] = Infinity;
    previous[node] = null;
  });
  
  distances[start] = 0;
  pq.enqueue(start, 0);
  
  while (!pq.isEmpty()) {
    const current = pq.dequeue();
    
    if (current === end) break;
    if (!graph[current]) continue;
    
    graph[current].forEach(({ node, length, shade }) => {
      // Calculate cost
      let cost = length;
      if (useShade && shade && shade[scenario] !== undefined) {
        // Shade-weighted cost: length × (1 - shadeWeight × shade)
        cost = length * (1 - shadeWeight * shade[scenario]);
      }
      
      const newDist = distances[current] + cost;
      
      if (newDist < distances[node]) {
        distances[node] = newDist;
        previous[node] = current;
        pq.enqueue(node, newDist);
      }
    });
  }
  
  // Reconstruct path
  const path = [];
  let current = end;
  while (current) {
    path.unshift(current);
    current = previous[current];
  }
  
  return path.length > 1 ? path : null;
}

// Calculate route metrics
function calculateRouteMetrics(path, graph, scenario) {
  let totalLength = 0;
  let totalShade = 0;
  
  for (let i = 0; i < path.length - 1; i++) {
    const current = path[i];
    const next = path[i + 1];
    
    const edge = graph[current]?.find(e => e.node === next);
    if (edge) {
      totalLength += edge.length;
      const shade = edge.shade?.[scenario] || 0;
      totalShade += shade * edge.length;
    }
  }
  
  return {
    length: totalLength,
    avgShade: totalLength > 0 ? totalShade / totalLength : 0
  };
}

// Map click handler component
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng);
    }
  });
  return null;
}

// Main Interactive Map Component
export default function InteractiveShadeRouting() {
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [scenario, setScenario] = useState('summer_midday');
  const [scenarios, setScenarios] = useState([]);
  
  const [shortestRoute, setShortestRoute] = useState(null);
  const [shadiestRoute, setShadiestRoute] = useState(null);
  const [metrics, setMetrics] = useState(null);
  
  const [selectingOrigin, setSelectingOrigin] = useState(true);
  
  // Load network data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        // Load all data files
        const [nodesRes, edgesRes, metadataRes] = await Promise.all([
          fetch('/data/nodes.json'),
          fetch('/data/edges.json'),
          fetch('/data/metadata.json')
        ]);
        
        const nodes = await nodesRes.json();
        const edges = await edgesRes.json();
        const metadata = await metadataRes.json();
        
        // Build graph structure
        const graph = {};
        
        // Initialize nodes
        nodes.forEach(node => {
          graph[node.id] = [];
        });
        
        // Add edges
        edges.forEach(edge => {
          if (!graph[edge.u]) graph[edge.u] = [];
          if (!graph[edge.v]) graph[edge.v] = [];
          
          graph[edge.u].push({
            node: edge.v,
            length: edge.length,
            shade: edge.shade,
            coordinates: edge.coordinates
          });
          
          // Add reverse edge (undirected graph)
          graph[edge.v].push({
            node: edge.u,
            length: edge.length,
            shade: edge.shade,
            coordinates: [...edge.coordinates].reverse()
          });
        });
        
        setNetworkData({ graph, nodes, edges, metadata });
        setScenarios(metadata.scenarios);
        setLoading(false);
        
      } catch (err) {
        setError('Failed to load network data: ' + err.message);
        setLoading(false);
      }
    }
    
    loadData();
  }, []);
  
  // Find nearest node to clicked location
  function findNearestNode(latlng) {
    if (!networkData) return null;
    
    let nearest = null;
    let minDist = Infinity;
    
    networkData.nodes.forEach(node => {
      const dist = Math.sqrt(
        Math.pow(node.lat - latlng.lat, 2) +
        Math.pow(node.lon - latlng.lng, 2)
      );
      
      if (dist < minDist) {
        minDist = dist;
        nearest = node;
      }
    });
    
    return nearest;
  }
  
  // Handle map click
  function handleMapClick(latlng) {
    const node = findNearestNode(latlng);
    if (!node) return;
    
    if (selectingOrigin) {
      setOrigin(node);
      setSelectingOrigin(false);
      setShortestRoute(null);
      setShadiestRoute(null);
      setMetrics(null);
    } else {
      setDestination(node);
      setSelectingOrigin(true);
    }
  }
  
  // Calculate routes when origin and destination are set
  useEffect(() => {
    if (!networkData || !origin || !destination) return;
    
    try {
      // Calculate shortest route
      const shortPath = dijkstra(
        networkData.graph,
        origin.id,
        destination.id,
        false
      );
      
      // Calculate shadiest route
      const shadyPath = dijkstra(
        networkData.graph,
        origin.id,
        destination.id,
        true,
        scenario,
        0.3
      );
      
      if (shortPath) {
        // Convert to coordinates
        const shortCoords = shortPath.map(nodeId => {
          const node = networkData.nodes.find(n => n.id === nodeId);
          return [node.lat, node.lon];
        });
        
        setShortestRoute(shortCoords);
        
        // Calculate metrics for shortest
        const shortMetrics = calculateRouteMetrics(
          shortPath,
          networkData.graph,
          scenario
        );
        
        if (shadyPath) {
          const shadyCoords = shadyPath.map(nodeId => {
            const node = networkData.nodes.find(n => n.id === nodeId);
            return [node.lat, node.lon];
          });
          
          setShadiestRoute(shadyCoords);
          
          // Calculate metrics for shadiest
          const shadyMetrics = calculateRouteMetrics(
            shadyPath,
            networkData.graph,
            scenario
          );
          
          // Calculate trade-offs
          const detour = shadyMetrics.length - shortMetrics.length;
          const detourPct = (detour / shortMetrics.length) * 100;
          const shadeImprovement = shadyMetrics.avgShade - shortMetrics.avgShade;
          const shadeImprovementPct = (shadeImprovement / Math.max(shortMetrics.avgShade, 0.001)) * 100;
          
          setMetrics({
            shortest: shortMetrics,
            shadiest: shadyMetrics,
            detour: detour,
            detourPct: detourPct,
            shadeImprovement: shadeImprovement,
            shadeImprovementPct: shadeImprovementPct
          });
        } else {
          setMetrics({ shortest: shortMetrics });
        }
      }
      
    } catch (err) {
      console.error('Error calculating routes:', err);
    }
  }, [networkData, origin, destination, scenario]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <div className="text-2xl font-bold mb-4">Loading Network Data...</div>
          <div className="text-gray-600">This may take a moment...</div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-red-50">
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600 mb-4">Error</div>
          <div className="text-gray-700">{error}</div>
        </div>
      </div>
    );
  }
  
  const center = networkData?.metadata?.bounds 
    ? [
        (networkData.metadata.bounds.north + networkData.metadata.bounds.south) / 2,
        (networkData.metadata.bounds.east + networkData.metadata.bounds.west) / 2
      ]
    : [39.9540, -75.1960];
  
  return (
    <div className="relative h-screen w-full">
      {/* Map */}
      <MapContainer
        center={center}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        
        <MapClickHandler onMapClick={handleMapClick} />
        
        {/* Origin marker */}
        {origin && (
          <Marker position={[origin.lat, origin.lon]}>
            <Popup>Origin</Popup>
          </Marker>
        )}
        
        {/* Destination marker */}
        {destination && (
          <Marker position={[destination.lat, destination.lon]}>
            <Popup>Destination</Popup>
          </Marker>
        )}
        
        {/* Shortest route */}
        {shortestRoute && (
          <Polyline
            positions={shortestRoute}
            color="blue"
            weight={4}
            opacity={0.7}
          />
        )}
        
        {/* Shadiest route */}
        {shadiestRoute && (
          <Polyline
            positions={shadiestRoute}
            color="green"
            weight={4}
            opacity={0.7}
          />
        )}
      </MapContainer>
      
      {/* Control Panel */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-[1000]">
        <h2 className="text-xl font-bold mb-4">Shade Routing Calculator</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Step {selectingOrigin ? '1' : '2'}: {selectingOrigin ? 'Select Origin' : 'Select Destination'}
          </label>
          <div className="text-sm text-gray-600">
            Click anywhere on the map to {selectingOrigin ? 'set origin' : 'set destination'}
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Scenario</label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            {scenarios.map(s => (
              <option key={s} value={s}>
                {s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>
        
        {metrics && (
          <div className="border-t pt-4 mt-4">
            <h3 className="font-bold mb-2">Route Comparison</h3>
            
            <div className="mb-3">
              <div className="text-sm font-medium text-blue-600">Shortest Route</div>
              <div className="text-xs text-gray-600">
                Distance: {metrics.shortest.length.toFixed(0)}m<br/>
                Avg Shade: {metrics.shortest.avgShade.toFixed(3)}
              </div>
            </div>
            
            {metrics.shadiest && (
              <>
                <div className="mb-3">
                  <div className="text-sm font-medium text-green-600">Shadiest Route</div>
                  <div className="text-xs text-gray-600">
                    Distance: {metrics.shadiest.length.toFixed(0)}m<br/>
                    Avg Shade: {metrics.shadiest.avgShade.toFixed(3)}
                  </div>
                </div>
                
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-xs font-medium mb-1">Trade-offs:</div>
                  <div className="text-xs text-gray-700">
                    Extra distance: {metrics.detour.toFixed(0)}m ({metrics.detourPct.toFixed(1)}%)<br/>
                    Shade gain: +{metrics.shadeImprovement.toFixed(3)} ({metrics.shadeImprovementPct.toFixed(1)}%)
                  </div>
                </div>
              </>
            )}
          </div>
        )}
        
        <button
          onClick={() => {
            setOrigin(null);
            setDestination(null);
            setShortestRoute(null);
            setShadiestRoute(null);
            setMetrics(null);
            setSelectingOrigin(true);
          }}
          className="w-full mt-4 bg-red-500 text-white rounded py-2 hover:bg-red-600"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
