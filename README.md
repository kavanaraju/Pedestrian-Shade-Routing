# Shade-Optimized Pedestrian Routing to Transit
**University City, Philadelphia**

**Website:** [https://kavanaraju.github.io/Pedestrian-Shade-Routing/](https://kavanaraju.github.io/Pedestrian-Shade-Routing/)

**Author:** Kavana Raju  
**Course:** MUSA 5500 - Geospatial Data Science with Python  

---

## Project Overview

This project develops a **shade-optimized pedestrian routing system** for University City, Philadelphia. Using real solar position modeling and high-resolution LiDAR data, the system finds shadier walking routes to transit stops across 8 different time scenarios (different times of day and seasons).

### Key Findings

- *8-15% typical detours** yield **25-40% shade improvement**
- Routes change geometry between scenarios (not just shade values)
- Summer midday offers best routing opportunities
- Practical for real-world deployment

---

## Study Area

- **Location:** University City, Philadelphia
- **Area:** 3.2 square kilometers
- **Network:** 23,486 street segments, 7,343 nodes
- **Buildings:** 16,635 with LiDAR heights (99.7% coverage)
- **Transit:** 5 SEPTA stops

---

## Data Sources

| Dataset | Source | Use |
|---------|--------|-----|
| Street Network | OpenStreetMap (OSMnx) | Routing base |
| Building Heights | OpenDataPhilly LiDAR 2018 | Shadow calculation |
| Tree Canopy | OpenDataPhilly LiDAR 2018 | Shade coverage |
| Transit Stops | SEPTA GTFS (Spring 2025) | Destinations |

---

## Repository Structure

```
shade-routing-philly/
├── index.html                    # Main website (GitHub Pages)
├── README.md                     # This file
├── notebooks/
│   ├── 01-data-acquisition.ipynb
│   ├── 02-network-shade.ipynb
│   ├── 03-routing.ipynb
│   └── 04-route-visualizations.ipynb
├── outputs/
│   ├── maps/                     # Base maps
│   └── figures/                  # Analysis visualizations
├── data/
│   └── processed/                # Small processed files only
├── environment.yml               # Conda environment
└── requirements.txt              # Python dependencies
```

**Note:** Large data files (LiDAR point clouds, rasters, full network) are not included due to size limits. Instructions to download and generate these files are in the notebooks.

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Conda (recommended) or pip
- 8GB+ RAM for analysis
- ~15GB disk space (with data)

### Quick Start

```bash
# Clone repository
git clone https://github.com/kavanaraju/Pedestrian-Shade-Routing.git
cd shade-routing-philly

# Create environment
conda env create -f environment.yml
conda activate shade-routing

# Launch Jupyter
jupyter lab

# Run notebooks in order: 01 → 02 → 03 → 04
```

---

## How to Use

### View the Website
Visit: [https://github.com/kavanaraju/Pedestrian-Shade-Routing/](https://github.com/kavanaraju/Pedestrian-Shade-Routing/)

### Run the Analysis
1. Open `notebooks/01-data-acquisition.ipynb`
2. Follow instructions to download data
3. Run notebooks in sequence
4. Outputs save to `outputs/` folder

---

## Methodology

### Solar Position Modeling
Uses `pvlib` library to calculate accurate sun position for 8 scenarios:
- **Summer:** Morning (8 AM), Midday (12 PM), Evening (5 PM)
- **Winter:** Morning (8 AM), Midday (12 PM), Evening (5 PM)
- **Spring & Fall:** Midday (12 PM)

### Shadow Calculation
```python
# Building shadows
shadow_length = building_height / tan(sun_altitude)
shadow_direction = (sun_azimuth + 180°) % 360°

# Combined shade score
shade_score = 0.4 × tree_coverage + 0.6 × building_shadow
```

### Routing Algorithm
```python
# Cost function
cost = length × (1 - 0.3 × shade)

# Effect: Fully shaded streets "cost" 30% less
# Uses NetworkX Dijkstra for minimum weighted path
```

---

## Key Results

### Network Statistics

| Scenario | Mean Shade | High Shade Streets (>0.7) |
|----------|------------|---------------------------|
| Winter Morning | **0.45** | **18.5%** |
| Summer Midday | **0.43** | 16.0% |
| Winter Evening | **0.25** | 0.0% |

### Example Routes

**Penn to 40th Street Station (Summer Midday):**
- Detour: +37m (+12%)
- Shade improvement: +38%
- Efficiency: 3.2 (HIGH)

**Drexel to 34th Street Station (Summer Evening):**
- Detour: +67m (+13%)
- Shade improvement: +44%
- Efficiency: 3.4 (HIGH)

---

## Technologies Used

- **Python 3.10** with GeoPandas, Pandas, NumPy
- **OSMnx** for street network extraction
- **NetworkX** for routing algorithms
- **pvlib** for solar position modeling
- **rasterio & rasterstats** for raster operations
- **matplotlib & seaborn** for visualization

---

## Future Work

1. **3D Tree Modeling:** Use LiDAR point clouds for actual tree heights
2. **Real-Time API:** Deploy as web service with current conditions
3. **Multi-Factor Routing:** Integrate air quality, noise, safety
4. **Mobile App:** Native interface for real-world use
5. **User Studies:** Validate preferences and parameters

---

## License

MIT License - See LICENSE file for details.

This is an educational project completed for MUSA 5500 at University of Pennsylvania.

---

## Author

**Kavana Raju**  
Master of City Planning
Stuart Weitzman School of Design,University of Pennsylvania

- Email: [kavana@upenn.edu](mailto:kavana@upenn.edu)
- LinkedIn: [https://www.linkedin.com/in/kavanaraju/](https://www.linkedin.com/in/kavanaraju/)
- GitHub: [@kavanaraju](https://github.com/kavanaraju)

---

<div align="center">

[View Website](https://github.com/kavanaraju/Pedestrian-Shade-Routing/) | [Report Issue](https://github.com/kavanaraju/Pedestrian-Shade-Routing/issues) | [Contact](mailto:kavana@upenn.edu)

</div>
