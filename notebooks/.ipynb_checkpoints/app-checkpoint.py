"""
Shade-Optimized Pedestrian Routing Tool
University City, Philadelphia

Interactive web application for calculating shade-optimized walking routes to transit.

Author: Kavana Raju
Course: MUSA 5500 - Geospatial Data Science with Python
"""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
import osmnx as ox
import networkx as nx
import folium
from folium import plugins
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Shade Routing Tool - University City",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
    }
    .info-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🌳 Shade-Optimized Pedestrian Routing Tool</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Find the shadiest walking routes to transit in University City, Philadelphia</p>', unsafe_allow_html=True)

# Cache data loading
@st.cache_resource
def load_data():
    """Load all necessary data files."""
    try:
        # Load network
        G = ox.load_graphml('data/processed/university_city_network_with_shade.graphml')
        
        # Load GeoDataFrames
        septa_gdf = gpd.read_file('data/processed/septa_stops.geojson')
        edges_gdf = gpd.read_file('data/processed/network_edges_with_shade.geojson')
        study_area = gpd.read_file('data/processed/study_area.geojson')
        
        # Get major stations for dropdown
        major_stations = septa_gdf[septa_gdf['category'] == 'Major Transit'].copy()
        
        return G, septa_gdf, edges_gdf, study_area, major_stations
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Load data
with st.spinner("Loading network data..."):
    G, septa_gdf, edges_gdf, study_area, major_stations = load_data()

# Study area bounds
bounds = study_area.total_bounds  # [minx, miny, maxx, maxy]
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

# Sidebar
st.sidebar.header("🎯 Route Planning")

# Input method selection
input_method = st.sidebar.radio(
    "How would you like to select your origin?",
    ["📍 Click on Map", "📝 Enter Coordinates", "🏢 Use Example Locations"]
)

origin_lat = None
origin_lon = None
destination_name = None

# Handle different input methods
if input_method == "📍 Click on Map":
    st.sidebar.info("👇 Click on the map below to select your starting location")
    
elif input_method == "📝 Enter Coordinates":
    st.sidebar.markdown("### Enter Coordinates")
    origin_lat = st.sidebar.number_input("Latitude", value=39.9540, format="%.4f", min_value=39.945, max_value=39.965)
    origin_lon = st.sidebar.number_input("Longitude", value=-75.1980, format="%.4f", min_value=-75.230, max_value=-75.180)
    
elif input_method == "🏢 Use Example Locations":
    example_locations = {
        "Penn Campus (Locust Walk)": (39.9522, -75.1950),
        "Drexel University (Main Building)": (39.9550, -75.2030),
        "Clark Park": (39.9480, -75.2150),
        "30th Street Station Area": (39.9560, -75.1810),
        "40th & Walnut": (39.9540, -75.2020)
    }
    
    selected_location = st.sidebar.selectbox(
        "Select a location:",
        list(example_locations.keys())
    )
    origin_lat, origin_lon = example_locations[selected_location]

# Destination selection
st.sidebar.markdown("### Choose Destination")
destination_name = st.sidebar.selectbox(
    "Select transit station:",
    major_stations['name'].tolist()
)

# Calculate button
calculate_button = st.sidebar.button("🚀 Calculate Routes", type="primary", use_container_width=True)

# Sidebar info
with st.sidebar.expander("ℹ️ How to Use"):
    st.markdown("""
    **Steps:**
    1. Choose how to select your origin
    2. Select a destination transit station
    3. Click "Calculate Routes"
    4. View shortest and shadiest routes!
    
    **Tips:**
    - Red route = shortest distance
    - Green route = shadiest path
    - Check the detour vs shade trade-off
    """)

with st.sidebar.expander("📊 About This Tool"):
    st.markdown("""
    This tool uses high-resolution tree canopy data 
    and building footprints to calculate walking routes 
    that maximize shade coverage while minimizing detour.
    
    **Data Sources:**
    - Tree Canopy: 2018 LiDAR (0.5m resolution)
    - Network: OpenStreetMap
    - Transit: SEPTA Spring 2025 GTFS
    
    **Author:** Kavana Raju  
    **Course:** MUSA 5500 - Penn MUSA Program
    """)

# Main content area
def calculate_route_from_coords(lat, lon, destination_stop_name, graph, septa_df):
    """Calculate walking route from coordinates to transit stop."""
    try:
        # Find nearest network node to origin
        origin_node = ox.nearest_nodes(graph, lon, lat)
        
        # Find destination stop
        dest_stops = septa_df[septa_df['name'] == destination_stop_name]
        if len(dest_stops) == 0:
            return None
        
        dest_stop = dest_stops.iloc[0]
        dest_node = ox.nearest_nodes(graph, dest_stop.geometry.x, dest_stop.geometry.y)
        
        results = {
            'origin_lat': lat,
            'origin_lon': lon,
            'dest_name': dest_stop['name'],
            'dest_lat': dest_stop.geometry.y,
            'dest_lon': dest_stop.geometry.x,
        }
        
        # Calculate shortest route
        shortest_path = nx.shortest_path(graph, origin_node, dest_node, weight='length')
        shortest_length = 0
        shortest_shade_weighted = 0
        
        for i in range(len(shortest_path) - 1):
            u, v = shortest_path[i], shortest_path[i+1]
            edge_data = graph[u][v][0]
            edge_length = edge_data['length']
            shortest_length += edge_length
            shortest_shade_weighted += edge_data.get('shade_score', 0) * edge_length
        
        shortest_avg_shade = shortest_shade_weighted / shortest_length if shortest_length > 0 else 0
        
        results['shortest_path'] = shortest_path
        results['shortest_length_ft'] = shortest_length
        results['shortest_length_m'] = shortest_length * 0.3048
        results['shortest_shade_score'] = shortest_avg_shade
        
        # Calculate shadiest route
        shadiest_path = nx.shortest_path(graph, origin_node, dest_node, weight='shade_weight')
        shadiest_length = 0
        shadiest_shade_weighted = 0
        
        for i in range(len(shadiest_path) - 1):
            u, v = shadiest_path[i], shadiest_path[i+1]
            edge_data = graph[u][v][0]
            edge_length = edge_data['length']
            shadiest_length += edge_length
            shadiest_shade_weighted += edge_data.get('shade_score', 0) * edge_length
        
        shadiest_avg_shade = shadiest_shade_weighted / shadiest_length if shadiest_length > 0 else 0
        
        results['shadiest_path'] = shadiest_path
        results['shadiest_length_ft'] = shadiest_length
        results['shadiest_length_m'] = shadiest_length * 0.3048
        results['shadiest_shade_score'] = shadiest_avg_shade
        
        # Calculate comparison metrics
        results['length_increase_ft'] = shadiest_length - shortest_length
        results['length_increase_m'] = results['length_increase_ft'] * 0.3048
        results['length_increase_pct'] = (results['length_increase_ft'] / shortest_length * 100) if shortest_length > 0 else 0
        results['shade_improvement'] = shadiest_avg_shade - shortest_avg_shade
        results['shade_improvement_pct'] = (results['shade_improvement'] / shortest_avg_shade * 100) if shortest_avg_shade > 0 else 0
        
        if results['length_increase_m'] > 0:
            results['shade_per_meter_detour'] = results['shade_improvement'] / results['length_increase_m']
        else:
            results['shade_per_meter_detour'] = float('inf')
        
        return results
        
    except nx.NetworkXNoPath:
        return None
    except Exception as e:
        st.error(f"Error calculating route: {str(e)}")
        return None

def path_to_coords(path, graph):
    """Convert node path to coordinate list."""
    coords = []
    for node in path:
        node_data = graph.nodes[node]
        coords.append([node_data['y'], node_data['x']])  # [lat, lon] for folium
    return coords

def create_route_map(route_results, graph, edges_gdf, septa_gdf):
    """Create Folium map with both routes."""
    
    # Create base map
    m = folium.Map(
        location=[route_results['origin_lat'], route_results['origin_lon']],
        zoom_start=15,
        tiles='CartoDB positron'
    )
    
    # Add network edges colored by shade (background)
    # Simplify for performance
    edges_sample = edges_gdf.sample(min(1000, len(edges_gdf)))
    
    for idx, edge in edges_sample.iterrows():
        shade_score = edge['shade_score']
        # Color from red (low shade) to green (high shade)
        color = f'#{int(255*(1-shade_score)):02x}{int(255*shade_score):02x}00'
        
        coords = [(point[1], point[0]) for point in edge.geometry.coords]
        folium.PolyLine(
            coords,
            color=color,
            weight=2,
            opacity=0.3
        ).add_to(m)
    
    # Convert paths to coordinates
    shortest_coords = path_to_coords(route_results['shortest_path'], graph)
    shadiest_coords = path_to_coords(route_results['shadiest_path'], graph)
    
    # Add shortest route
    folium.PolyLine(
        shortest_coords,
        color='red',
        weight=5,
        opacity=0.8,
        popup=f"Shortest: {route_results['shortest_length_m']:.0f}m"
    ).add_to(m)
    
    # Add shadiest route
    folium.PolyLine(
        shadiest_coords,
        color='darkgreen',
        weight=5,
        opacity=0.8,
        dash_array='10',
        popup=f"Shadiest: {route_results['shadiest_length_m']:.0f}m"
    ).add_to(m)
    
    # Add origin marker
    folium.Marker(
        [route_results['origin_lat'], route_results['origin_lon']],
        popup='Origin',
        icon=folium.Icon(color='blue', icon='home', prefix='fa')
    ).add_to(m)
    
    # Add destination marker
    folium.Marker(
        [route_results['dest_lat'], route_results['dest_lon']],
        popup=route_results['dest_name'],
        icon=folium.Icon(color='red', icon='train', prefix='fa')
    ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; 
                background-color: white; 
                padding: 10px; 
                border: 2px solid grey; 
                border-radius: 5px;
                font-size: 14px;
                z-index: 9999;">
        <b>Route Legend</b><br>
        <i class="fa fa-minus" style="color:red"></i> Shortest Route<br>
        <i class="fa fa-minus" style="color:darkgreen"></i> Shadiest Route<br>
        <i class="fa fa-home" style="color:blue"></i> Origin<br>
        <i class="fa fa-train" style="color:red"></i> Destination
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Fit bounds
    all_coords = shortest_coords + shadiest_coords
    m.fit_bounds(all_coords)
    
    return m

# Create interactive map for clicking
if input_method == "📍 Click on Map":
    st.markdown("### 📍 Click on the map to select your starting location")
    
    # Create base map
    click_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles='CartoDB positron'
    )
    
    # Add study area boundary
    folium.GeoJson(
        study_area,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'blue',
            'weight': 3,
            'dashArray': '5, 5'
        }
    ).add_to(click_map)
    
    # Add major transit stations
    for idx, station in major_stations.iterrows():
        folium.Marker(
            [station.geometry.y, station.geometry.x],
            popup=station['name'],
            icon=folium.Icon(color='red', icon='train', prefix='fa')
        ).add_to(click_map)
    
    # Display map and get click
    map_data = st_folium(click_map, width=700, height=500)
    
    # Get clicked coordinates
    if map_data and map_data.get('last_clicked'):
        origin_lat = map_data['last_clicked']['lat']
        origin_lon = map_data['last_clicked']['lng']
        st.success(f"📍 Selected location: {origin_lat:.4f}, {origin_lon:.4f}")

# Calculate routes when button clicked
if calculate_button:
    if origin_lat is None or origin_lon is None:
        st.error("⚠️ Please select an origin location first!")
    elif destination_name is None:
        st.error("⚠️ Please select a destination!")
    else:
        # Validate coordinates
        if not (bounds[0] <= origin_lon <= bounds[2] and bounds[1] <= origin_lat <= bounds[3]):
            st.warning("⚠️ Coordinates are outside the study area. Results may be inaccurate.")
        
        with st.spinner("Calculating routes... 🚶‍♀️"):
            route_results = calculate_route_from_coords(
                origin_lat, origin_lon, destination_name, G, septa_gdf
            )
        
        if route_results is None:
            st.error("❌ Could not calculate route. Please try a different location or destination.")
        else:
            # Success! Show results
            st.success("✅ Routes calculated successfully!")
            
            # Display metrics
            st.markdown("### 📊 Route Comparison")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Shortest Distance",
                    f"{route_results['shortest_length_m']:.0f}m",
                    help="Minimum walking distance"
                )
            
            with col2:
                st.metric(
                    "Shadiest Distance",
                    f"{route_results['shadiest_length_m']:.0f}m",
                    delta=f"+{route_results['length_increase_m']:.0f}m",
                    help="Distance of shade-optimized route"
                )
            
            with col3:
                st.metric(
                    "Detour",
                    f"{route_results['length_increase_pct']:.1f}%",
                    delta=f"+{route_results['length_increase_m']:.0f}m",
                    help="Extra walking distance for shade"
                )
            
            with col4:
                st.metric(
                    "Shade Improvement",
                    f"{route_results['shade_improvement']:.3f}",
                    delta=f"+{route_results['shade_improvement_pct']:.1f}%",
                    help="Increase in shade coverage"
                )
            
            # Detailed comparison
            st.markdown("### 🌳 Shade Coverage Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("#### 🔴 Shortest Route")
                st.markdown(f"**Distance:** {route_results['shortest_length_m']:.0f}m ({route_results['shortest_length_m']/1609:.2f} mi)")
                st.markdown(f"**Shade Score:** {route_results['shortest_shade_score']:.3f}")
                st.markdown(f"**Shade Quality:** {'🌳🌳🌳 Excellent' if route_results['shortest_shade_score'] > 0.6 else '🌳🌳 Good' if route_results['shortest_shade_score'] > 0.4 else '🌳 Moderate' if route_results['shortest_shade_score'] > 0.2 else '☀️ Poor'}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("#### 🟢 Shadiest Route")
                st.markdown(f"**Distance:** {route_results['shadiest_length_m']:.0f}m ({route_results['shadiest_length_m']/1609:.2f} mi)")
                st.markdown(f"**Shade Score:** {route_results['shadiest_shade_score']:.3f}")
                st.markdown(f"**Shade Quality:** {'🌳🌳🌳 Excellent' if route_results['shadiest_shade_score'] > 0.6 else '🌳🌳 Good' if route_results['shadiest_shade_score'] > 0.4 else '🌳 Moderate' if route_results['shadiest_shade_score'] > 0.2 else '☀️ Poor'}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Efficiency analysis
            st.markdown("### ⚡ Routing Efficiency")
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            
            if route_results['shade_per_meter_detour'] == float('inf'):
                st.markdown("**Perfect!** The shadiest route is also the shortest route!")
            else:
                efficiency = route_results['shade_per_meter_detour']
                
                if efficiency > 0.01:
                    verdict = "🌟 **Excellent trade-off!** Significant shade benefit for minimal detour."
                elif efficiency > 0.005:
                    verdict = "✅ **Good trade-off!** Notable shade improvement worth the detour."
                elif efficiency > 0.001:
                    verdict = "👍 **Fair trade-off.** Moderate shade improvement for the detour."
                else:
                    verdict = "⚠️ **Marginal trade-off.** Small shade benefit for the detour."
                
                st.markdown(f"**Efficiency:** {efficiency:.4f} shade score per meter of detour")
                st.markdown(verdict)
                
                # Walking time estimate
                avg_speed_mps = 1.4  # meters per second (typical walking speed)
                shortest_time = route_results['shortest_length_m'] / avg_speed_mps / 60
                shadiest_time = route_results['shadiest_length_m'] / avg_speed_mps / 60
                
                st.markdown(f"**Estimated walking time:**")
                st.markdown(f"- Shortest route: {shortest_time:.1f} minutes")
                st.markdown(f"- Shadiest route: {shadiest_time:.1f} minutes (+{shadiest_time-shortest_time:.1f} min)")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display map
            st.markdown("### 🗺️ Route Visualization")
            
            route_map = create_route_map(route_results, G, edges_gdf, septa_gdf)
            st_folium(route_map, width=1000, height=600)
            
            # Recommendation
            st.markdown("### 💡 Recommendation")
            
            if route_results['length_increase_pct'] < 5:
                st.success("✅ **Take the shadiest route!** It's barely longer and much more comfortable.")
            elif route_results['length_increase_pct'] < 15 and route_results['shade_improvement'] > 0.15:
                st.info("👍 **Consider the shadiest route** for hot days. Good shade improvement for reasonable detour.")
            elif route_results['length_increase_pct'] < 25 and route_results['shade_improvement'] > 0.25:
                st.warning("🤔 **Shadiest route has significant detour** but excellent shade. Choose based on weather and time available.")
            else:
                st.warning("⏱️ **Stick with the shortest route** unless shade is a priority. Detour is significant.")
            
            # Save results option
            st.markdown("### 💾 Export Results")
            
            results_dict = {
                'origin_lat': route_results['origin_lat'],
                'origin_lon': route_results['origin_lon'],
                'destination': route_results['dest_name'],
                'shortest_distance_m': route_results['shortest_length_m'],
                'shortest_shade_score': route_results['shortest_shade_score'],
                'shadiest_distance_m': route_results['shadiest_length_m'],
                'shadiest_shade_score': route_results['shadiest_shade_score'],
                'length_increase_pct': route_results['length_increase_pct'],
                'shade_improvement': route_results['shade_improvement'],
                'efficiency': route_results.get('shade_per_meter_detour', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            results_json = json.dumps(results_dict, indent=2)
            
            st.download_button(
                label="📥 Download Results (JSON)",
                data=results_json,
                file_name=f"shade_route_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

else:
    # Show welcome message
    st.markdown("### 👋 Welcome!")
    
    st.markdown("""
    <div class="info-box">
    This tool helps you find the <b>shadiest walking routes</b> to transit stations in University City, Philadelphia.
    
    <b>How it works:</b>
    1. Select your starting location (click map, enter coordinates, or choose example)
    2. Choose your destination transit station
    3. Click "Calculate Routes" to see comparison
    
    <b>Features:</b>
    - 🌳 High-resolution tree canopy data (0.5m LiDAR)
    - 🏢 Building shadow estimates
    - 📊 Detailed route comparison metrics
    - ⚡ Efficiency analysis (shade benefit vs detour cost)
    - 🗺️ Interactive map visualization
    
    <b>Get started by selecting an input method in the sidebar!</b> →
    </div>
    """, unsafe_allow_html=True)
    
    # Show study area map
    st.markdown("### 📍 Study Area: University City")
    
    preview_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='CartoDB positron'
    )
    
    # Add study area
    folium.GeoJson(
        study_area,
        style_function=lambda x: {
            'fillColor': 'lightblue',
            'color': 'blue',
            'weight': 3,
            'fillOpacity': 0.2
        }
    ).add_to(preview_map)
    
    # Add major stations
    for idx, station in major_stations.iterrows():
        folium.Marker(
            [station.geometry.y, station.geometry.x],
            popup=station['name'],
            tooltip=station['name'],
            icon=folium.Icon(color='red', icon='train', prefix='fa')
        ).add_to(preview_map)
    
    st_folium(preview_map, width=700, height=400)
    
    # Statistics
    st.markdown("### 📊 Network Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Network Nodes", f"{len(G.nodes):,}")
    with col2:
        st.metric("Network Edges", f"{len(G.edges):,}")
    with col3:
        st.metric("Transit Stations", len(major_stations))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <b>Shade-Optimized Pedestrian Routing Tool</b><br>
    Created by Kavana Raju | MUSA 5500 - Penn MUSA Program | December 2025<br>
    Data: PASDA (tree canopy), OpenStreetMap (network), SEPTA (transit)
</div>
""", unsafe_allow_html=True)
