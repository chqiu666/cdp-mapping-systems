import React, { useState, useEffect, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ArcLayer, ScatterplotLayer } from '@deck.gl/layers';
import { MapView } from '@deck.gl/core';
import { StaticMap } from 'react-map-gl';

// Mapbox token from environment
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw';

// NYC center coordinates
const INITIAL_VIEW_STATE = {
  longitude: -74.006,
  latitude: 40.7128,
  zoom: 11,
  pitch: 45,
  bearing: 0
};

const LoadingComponent = () => (
  <div className="loading-container">
    <div className="spinner"></div>
    <div className="loading-text">Loading address connections...</div>
  </div>
);

const ErrorComponent = ({ error }) => (
  <div className="error-container">
    <div className="error-title">Unable to Load Data</div>
    <div className="error-message">
      {error || 'Please ensure the data collection scripts have been run successfully.'}
    </div>
  </div>
);

const StatsPanel = ({ connections, loading }) => {
  const stats = useMemo(() => {
    if (!connections || connections.length === 0) return {};
    
    const avgDistance = connections.reduce((sum, conn) => 
      sum + (conn.connection?.distance_km || 0), 0) / connections.length;
    
    const uniqueImages = new Set(connections.map(conn => conn.image_id)).size;
    
    return {
      totalConnections: connections.length,
      uniqueImages,
      avgDistance: avgDistance.toFixed(2),
      maxDistance: Math.max(...connections.map(conn => conn.connection?.distance_km || 0)).toFixed(2)
    };
  }, [connections]);

  if (loading) return null;

  return (
    <div className="stats">
      <h3>Statistics</h3>
      <div className="stat-item">
        <span className="stat-label">Total Connections</span>
        <span className="stat-value">{stats.totalConnections || 0}</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Street View Images</span>
        <span className="stat-value">{stats.uniqueImages || 0}</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Avg Distance</span>
        <span className="stat-value">{stats.avgDistance || 0} km</span>
      </div>
      <div className="stat-item">
        <span className="stat-label">Max Distance</span>
        <span className="stat-value">{stats.maxDistance || 0} km</span>
      </div>
    </div>
  );
};

const Legend = () => (
  <div className="legend">
    <h3>Legend</h3>
    <div className="legend-item">
      <div className="legend-color source"></div>
      <span>Street View Location</span>
    </div>
    <div className="legend-item">
      <div className="legend-color target"></div>
      <span>Geocoded Address</span>
    </div>
    <div className="legend-item">
      <div className="legend-color arc"></div>
      <span>Text-Location Connection</span>
    </div>
  </div>
);

const App = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  // Load connection data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Try to load the connections data
        const response = await fetch('../data/connections/all_connections.json');
        
        if (!response.ok) {
          throw new Error(`Failed to load data: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!Array.isArray(data) || data.length === 0) {
          throw new Error('No connection data available. Please run the data collection scripts first.');
        }
        
        setConnections(data);
        
        // Adjust view to fit data
        if (data.length > 0) {
          const lats = data.flatMap(d => [d.source.latitude, d.target.latitude]);
          const lngs = data.flatMap(d => [d.source.longitude, d.target.longitude]);
          
          const bounds = {
            minLat: Math.min(...lats),
            maxLat: Math.max(...lats),
            minLng: Math.min(...lngs),
            maxLng: Math.max(...lngs)
          };
          
          const centerLat = (bounds.minLat + bounds.maxLat) / 2;
          const centerLng = (bounds.minLng + bounds.maxLng) / 2;
          
          setViewState(prev => ({
            ...prev,
            latitude: centerLat,
            longitude: centerLng,
            zoom: 10
          }));
        }
        
      } catch (err) {
        console.error('Error loading data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Create deck.gl layers
  const layers = useMemo(() => {
    if (!connections || connections.length === 0) return [];

    const arcData = connections.map(conn => ({
      sourcePosition: [conn.source.longitude, conn.source.latitude],
      targetPosition: [conn.target.longitude, conn.target.latitude],
      addressText: conn.connection.address_text,
      distance: conn.connection.distance_km,
      confidence: conn.connection.confidence
    }));

    const sourcePoints = connections.map(conn => ({
      position: [conn.source.longitude, conn.source.latitude],
      type: 'source'
    }));

    const targetPoints = connections.map(conn => ({
      position: [conn.target.longitude, conn.target.latitude],
      type: 'target'
    }));

    return [
      // Arc layer for connections
      new ArcLayer({
        id: 'address-connections',
        data: arcData,
        getSourcePosition: d => d.sourcePosition,
        getTargetPosition: d => d.targetPosition,
        getSourceColor: [78, 205, 196, 180], // Teal with transparency
        getTargetColor: [255, 107, 107, 180], // Red with transparency
        getWidth: d => Math.max(2, Math.min(8, d.distance * 0.5)),
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 100],
        getTooltip: ({ object }) => object && {
          html: `
            <div style="padding: 8px; background: rgba(0,0,0,0.8); color: white; border-radius: 4px;">
              <strong>Address:</strong> ${object.addressText}<br/>
              <strong>Distance:</strong> ${object.distance.toFixed(2)} km<br/>
              <strong>Confidence:</strong> ${object.confidence}
            </div>
          `,
          style: {
            backgroundColor: 'transparent',
            fontSize: '12px'
          }
        }
      }),

      // Source points (street view locations)
      new ScatterplotLayer({
        id: 'source-points',
        data: sourcePoints,
        getPosition: d => d.position,
        getRadius: 100,
        getFillColor: [78, 205, 196, 200],
        getLineColor: [255, 255, 255, 255],
        lineWidthMinPixels: 2,
        pickable: true,
        autoHighlight: true
      }),

      // Target points (geocoded addresses)
      new ScatterplotLayer({
        id: 'target-points',
        data: targetPoints,
        getPosition: d => d.position,
        getRadius: 80,
        getFillColor: [255, 107, 107, 200],
        getLineColor: [255, 255, 255, 255],
        lineWidthMinPixels: 2,
        pickable: true,
        autoHighlight: true
      })
    ];
  }, [connections]);

  return (
    <div className="map-container">
      <DeckGL
        initialViewState={viewState}
        controller={true}
        layers={layers}
        views={new MapView({ repeat: true })}
        onViewStateChange={({ viewState }) => setViewState(viewState)}
        getTooltip={({ object, layer }) => {
          if (!object) return null;
          
          if (layer.id === 'address-connections') {
            return {
              html: `
                <div style="padding: 12px; background: rgba(0,0,0,0.9); color: white; border-radius: 6px; max-width: 300px;">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #4ecdc4;">Address Connection</div>
                  <div style="margin-bottom: 4px;"><strong>Text:</strong> "${object.addressText}"</div>
                  <div style="margin-bottom: 4px;"><strong>Distance:</strong> ${object.distance.toFixed(2)} km</div>
                  <div><strong>Confidence:</strong> ${object.confidence}</div>
                </div>
              `
            };
          }
          
          if (layer.id === 'source-points') {
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: white; border-radius: 6px;">
                  <div style="color: #4ecdc4; font-weight: bold;">Street View Location</div>
                  <div>Original image capture point</div>
                </div>
              `
            };
          }
          
          if (layer.id === 'target-points') {
            return {
              html: `
                <div style="padding: 8px; background: rgba(0,0,0,0.9); color: white; border-radius: 6px;">
                  <div style="color: #ff6b6b; font-weight: bold;">Geocoded Address</div>
                  <div>Parsed address location</div>
                </div>
              `
            };
          }
          
          return null;
        }}
      >
        <StaticMap
          mapStyle="mapbox://styles/mapbox/dark-v10"
          mapboxApiAccessToken={MAPBOX_ACCESS_TOKEN}
        />
      </DeckGL>

      <div className="ui-overlay">
        <div className="header">
          <h1>Address Spatial Visualizer</h1>
          <p>
            Explore how abstract address text from street view images connects to actual spatial locations. 
            Each arc represents a link between text extracted via OCR and its geocoded coordinates.
          </p>
        </div>

        {loading && <LoadingComponent />}
        {error && <ErrorComponent error={error} />}
        
        {!loading && !error && (
          <>
            <StatsPanel connections={connections} loading={loading} />
            <Legend />
          </>
        )}
      </div>
    </div>
  );
};

export default App;