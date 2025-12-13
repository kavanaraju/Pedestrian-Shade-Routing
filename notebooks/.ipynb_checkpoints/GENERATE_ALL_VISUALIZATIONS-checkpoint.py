# ============================================================================
# COMPREHENSIVE VISUALIZATION GENERATION
# Run this in a new notebook or at end of Notebook 4
# Creates ALL visualizations for the website
# ============================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import contextily as cx

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory
output_dir = Path('outputs/figures')
output_dir.mkdir(parents=True, exist_ok=True)

print("🎨 Generating comprehensive visualizations...")

# ============================================================================
# VISUALIZATION 1: Network-Wide Shade Heatmap
# ============================================================================

print("\n1. Creating network shade heatmap...")

# Load the shade network
edges = gpd.read_file('data/processed/network_edges_with_shade.geojson')

# Create figure with 2x4 subplots for all scenarios
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle('Network Shade Coverage Across All Scenarios', fontsize=16, fontweight='bold')

scenarios = [
    ('shade_summer_morning', 'Summer Morning (7 AM)'),
    ('shade_summer_midday', 'Summer Midday (12 PM)'),
    ('shade_summer_evening', 'Summer Evening (5 PM)'),
    ('shade_winter_morning', 'Winter Morning (8 AM)'),
    ('shade_winter_midday', 'Winter Midday (12 PM)'),
    ('shade_winter_evening', 'Winter Evening (4 PM)'),
    ('shade_spring_midday', 'Spring Midday (12 PM)'),
    ('shade_fall_midday', 'Fall Midday (12 PM)')
]

for idx, (col, title) in enumerate(scenarios):
    ax = axes[idx // 4, idx % 4]
    
    if col in edges.columns:
        edges.plot(column=col, ax=ax, legend=True, cmap='RdYlGn',
                   vmin=0, vmax=1, linewidth=0.5, 
                   legend_kwds={'label': 'Shade Coverage', 'shrink': 0.5})
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.axis('off')
        
        # Add basemap
        try:
            cx.add_basemap(ax, crs=edges.crs, source=cx.providers.CartoDB.Positron, alpha=0.3)
        except:
            pass
    else:
        ax.text(0.5, 0.5, 'Data not available', ha='center', va='center')
        ax.set_title(title, fontsize=11)
        ax.axis('off')

plt.tight_layout()
plt.savefig(output_dir / 'shade_heatmap_all_scenarios.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: shade_heatmap_all_scenarios.png")
plt.close()

# ============================================================================
# VISUALIZATION 2: Shade Distribution Histograms
# ============================================================================

print("\n2. Creating shade distribution histograms...")

fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle('Shade Score Distributions by Scenario', fontsize=16, fontweight='bold')

for idx, (col, title) in enumerate(scenarios):
    ax = axes[idx // 4, idx % 4]
    
    if col in edges.columns:
        data = edges[col].dropna()
        ax.hist(data, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
        ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.2f}')
        ax.axvline(data.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {data.median():.2f}')
        ax.set_xlabel('Shade Coverage', fontsize=10)
        ax.set_ylabel('Number of Segments', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'shade_distributions.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: shade_distributions.png")
plt.close()

# ============================================================================
# VISUALIZATION 3: Temporal Comparison Bar Chart
# ============================================================================

print("\n3. Creating temporal comparison chart...")

# Calculate statistics
stats = []
for col, title in scenarios:
    if col in edges.columns:
        data = edges[col]
        stats.append({
            'scenario': title.replace(' (', '\n('),
            'mean': data.mean(),
            'high_shade_pct': (data > 0.5).sum() / len(data) * 100
        })

stats_df = pd.DataFrame(stats)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Temporal Variation in Shade Availability', fontsize=16, fontweight='bold')

# Mean shade by scenario
bars1 = ax1.bar(range(len(stats_df)), stats_df['mean'], 
                color=['#d32f2f', '#f57c00', '#fbc02d', '#689f38', 
                       '#388e3c', '#1976d2', '#7b1fa2', '#c2185b'])
ax1.set_xticks(range(len(stats_df)))
ax1.set_xticklabels(stats_df['scenario'], rotation=45, ha='right', fontsize=9)
ax1.set_ylabel('Mean Shade Coverage', fontsize=12)
ax1.set_title('Average Shade Coverage by Scenario', fontsize=12, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim(0, 1)

# Add value labels
for i, (bar, val) in enumerate(zip(bars1, stats_df['mean'])):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
             f'{val:.1%}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# High-shade percentage
bars2 = ax2.bar(range(len(stats_df)), stats_df['high_shade_pct'],
                color=['#d32f2f', '#f57c00', '#fbc02d', '#689f38', 
                       '#388e3c', '#1976d2', '#7b1fa2', '#c2185b'])
ax2.set_xticks(range(len(stats_df)))
ax2.set_xticklabels(stats_df['scenario'], rotation=45, ha='right', fontsize=9)
ax2.set_ylabel('Percentage of Segments', fontsize=12)
ax2.set_title('Segments with >50% Shade', fontsize=12, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# Add value labels
for i, (bar, val) in enumerate(zip(bars2, stats_df['high_shade_pct'])):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
             f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'temporal_comparison.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: temporal_comparison.png")
plt.close()

# ============================================================================
# VISUALIZATION 4: Building vs Tree Contribution
# ============================================================================

print("\n4. Creating building vs tree contribution chart...")

# Calculate contributions
contributions = []
for scenario_name in ['summer_morning', 'summer_midday', 'summer_evening',
                      'winter_morning', 'winter_midday', 'winter_evening',
                      'spring_midday', 'fall_midday']:
    building_col = f'building_shadow_{scenario_name}'
    tree_col = f'tree_shadow_{scenario_name}'
    
    if building_col in edges.columns and tree_col in edges.columns:
        contributions.append({
            'scenario': scenario_name.replace('_', ' ').title(),
            'building': edges[building_col].mean(),
            'tree': edges[tree_col].mean()
        })

contrib_df = pd.DataFrame(contributions)

fig, ax = plt.subplots(figsize=(14, 7))

x = np.arange(len(contrib_df))
width = 0.35

bars1 = ax.bar(x - width/2, contrib_df['building'], width, 
               label='Building Shade', color='#1976d2', alpha=0.8)
bars2 = ax.bar(x + width/2, contrib_df['tree'], width,
               label='Tree Shade', color='#388e3c', alpha=0.8)

ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Shade Coverage', fontsize=12, fontweight='bold')
ax.set_title('Building vs Tree Shade Contribution by Scenario', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(contrib_df['scenario'], rotation=45, ha='right')
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1%}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(output_dir / 'building_vs_tree_contribution.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: building_vs_tree_contribution.png")
plt.close()

# ============================================================================
# VISUALIZATION 5: Summer vs Winter Comparison Map
# ============================================================================

print("\n5. Creating summer vs winter comparison map...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle('Summer Midday vs Winter Morning Shade Coverage', fontsize=16, fontweight='bold')

# Summer midday
if 'shade_summer_midday' in edges.columns:
    edges.plot(column='shade_summer_midday', ax=ax1, legend=True, cmap='RdYlGn',
               vmin=0, vmax=1, linewidth=0.5,
               legend_kwds={'label': 'Shade Coverage', 'shrink': 0.8})
    ax1.set_title('Summer Midday (12 PM)\nWorst Shade Conditions', fontsize=12, fontweight='bold')
    ax1.axis('off')
    try:
        cx.add_basemap(ax1, crs=edges.crs, source=cx.providers.CartoDB.Positron, alpha=0.3)
    except:
        pass

# Winter morning
if 'shade_winter_morning' in edges.columns:
    edges.plot(column='shade_winter_morning', ax=ax2, legend=True, cmap='RdYlGn',
               vmin=0, vmax=1, linewidth=0.5,
               legend_kwds={'label': 'Shade Coverage', 'shrink': 0.8})
    ax2.set_title('Winter Morning (8 AM)\nBest Shade Conditions', fontsize=12, fontweight='bold')
    ax2.axis('off')
    try:
        cx.add_basemap(ax2, crs=edges.crs, source=cx.providers.CartoDB.Positron, alpha=0.3)
    except:
        pass

plt.tight_layout()
plt.savefig(output_dir / 'summer_vs_winter_comparison.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: summer_vs_winter_comparison.png")
plt.close()

# ============================================================================
# VISUALIZATION 6: High Shade vs Low Shade Corridors Map
# ============================================================================

print("\n6. Creating shade corridors map...")

if 'shade_summer_midday' in edges.columns:
    # Classify segments
    edges['shade_class'] = pd.cut(edges['shade_summer_midday'], 
                                   bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                   labels=['Very Low (0-20%)', 'Low (20-40%)', 
                                           'Moderate (40-60%)', 'High (60-80%)', 
                                           'Very High (80-100%)'])
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    colors = ['#d32f2f', '#f57c00', '#fbc02d', '#689f38', '#388e3c']
    
    edges.plot(column='shade_class', ax=ax, legend=True, 
               categorical=True, cmap='RdYlGn', linewidth=1,
               legend_kwds={'title': 'Shade Category', 'loc': 'upper left'})
    
    ax.set_title('Shade Corridors - Summer Midday\nIdentifying Shade Deserts and Shaded Routes',
                 fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    try:
        cx.add_basemap(ax, crs=edges.crs, source=cx.providers.CartoDB.Positron, alpha=0.3)
    except:
        pass
    
    plt.tight_layout()
    plt.savefig(output_dir / 'shade_corridors_map.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: shade_corridors_map.png")
    plt.close()

# ============================================================================
# VISUALIZATION 7: Box Plot Comparison
# ============================================================================

print("\n7. Creating box plot comparison...")

# Prepare data for box plots
box_data = []
for col, title in scenarios:
    if col in edges.columns:
        values = edges[col].dropna()
        for val in values:
            box_data.append({'Scenario': title, 'Shade': val})

box_df = pd.DataFrame(box_data)

fig, ax = plt.subplots(figsize=(14, 7))

sns.boxplot(data=box_df, x='Scenario', y='Shade', ax=ax, palette='Set2')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.set_ylabel('Shade Coverage', fontsize=12, fontweight='bold')
ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
ax.set_title('Shade Distribution by Scenario - Box Plot Comparison', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'shade_boxplot_comparison.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: shade_boxplot_comparison.png")
plt.close()

# ============================================================================
# VISUALIZATION 8: Summary Dashboard
# ============================================================================

print("\n8. Creating summary dashboard...")

fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Title
fig.suptitle('University City Shade Analysis - Complete Dashboard', 
             fontsize=18, fontweight='bold', y=0.98)

# 1. Mean shade by scenario (bar chart)
ax1 = fig.add_subplot(gs[0, :2])
bars = ax1.bar(range(len(stats_df)), stats_df['mean'], 
               color=plt.cm.RdYlGn(stats_df['mean']))
ax1.set_xticks(range(len(stats_df)))
ax1.set_xticklabels([s.split('\n')[0] for s in stats_df['scenario']], 
                     rotation=45, ha='right', fontsize=9)
ax1.set_ylabel('Mean Shade Coverage', fontsize=10, fontweight='bold')
ax1.set_title('Average Shade by Scenario', fontsize=11, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)
for bar, val in zip(bars, stats_df['mean']):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f'{val:.1%}', ha='center', fontsize=8)

# 2. Key statistics
ax2 = fig.add_subplot(gs[0, 2])
ax2.axis('off')
stats_text = f"""
KEY STATISTICS

Network Size:
• {len(edges):,} segments
• {edges.geometry.length.sum()/5280:.1f} miles

Best Scenario:
• {stats_df.iloc[stats_df['mean'].idxmax()]['scenario'].split(chr(10))[0]}
• {stats_df['mean'].max():.1%} mean shade

Worst Scenario:
• {stats_df.iloc[stats_df['mean'].idxmin()]['scenario'].split(chr(10))[0]}
• {stats_df['mean'].min():.1%} mean shade

Variation:
• {stats_df['mean'].max() - stats_df['mean'].min():.1%} range
• {stats_df['mean'].std():.1%} std dev
"""
ax2.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# 3. Building vs Tree contribution
ax3 = fig.add_subplot(gs[1, :])
if len(contrib_df) > 0:
    x = np.arange(len(contrib_df))
    width = 0.35
    ax3.bar(x - width/2, contrib_df['building'], width, label='Buildings', 
            color='#1976d2', alpha=0.8)
    ax3.bar(x + width/2, contrib_df['tree'], width, label='Trees',
            color='#388e3c', alpha=0.8)
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.split()[0] for s in contrib_df['scenario']], 
                         rotation=45, ha='right')
    ax3.set_ylabel('Mean Shade Coverage', fontsize=10, fontweight='bold')
    ax3.set_title('Shade Source Contribution', fontsize=11, fontweight='bold')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)

# 4. Shade distribution histogram (summer midday)
ax4 = fig.add_subplot(gs[2, 0])
if 'shade_summer_midday' in edges.columns:
    data = edges['shade_summer_midday'].dropna()
    ax4.hist(data, bins=30, color='coral', edgecolor='black', alpha=0.7)
    ax4.axvline(data.mean(), color='red', linestyle='--', linewidth=2)
    ax4.set_xlabel('Shade Coverage', fontsize=9)
    ax4.set_ylabel('Frequency', fontsize=9)
    ax4.set_title('Summer Midday Distribution', fontsize=10, fontweight='bold')

# 5. Shade distribution histogram (winter morning)
ax5 = fig.add_subplot(gs[2, 1])
if 'shade_winter_morning' in edges.columns:
    data = edges['shade_winter_morning'].dropna()
    ax5.hist(data, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
    ax5.axvline(data.mean(), color='green', linestyle='--', linewidth=2)
    ax5.set_xlabel('Shade Coverage', fontsize=9)
    ax5.set_ylabel('Frequency', fontsize=9)
    ax5.set_title('Winter Morning Distribution', fontsize=10, fontweight='bold')

# 6. High shade percentage
ax6 = fig.add_subplot(gs[2, 2])
bars = ax6.barh(range(len(stats_df)), stats_df['high_shade_pct'],
                color=plt.cm.RdYlGn(stats_df['mean']))
ax6.set_yticks(range(len(stats_df)))
ax6.set_yticklabels([s.split('\n')[0] for s in stats_df['scenario']], fontsize=8)
ax6.set_xlabel('% Segments >50% Shade', fontsize=9, fontweight='bold')
ax6.set_title('High-Shade Segments', fontsize=10, fontweight='bold')
ax6.grid(axis='x', alpha=0.3)

plt.savefig(output_dir / 'dashboard_summary.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: dashboard_summary.png")
plt.close()

# ============================================================================
# VISUALIZATION 9: Study Area Overview Map
# ============================================================================

print("\n9. Creating study area overview map...")

fig, ax = plt.subplots(figsize=(12, 12))

# Plot network
edges.plot(ax=ax, color='gray', linewidth=0.5, alpha=0.5)

# Add basemap
try:
    cx.add_basemap(ax, crs=edges.crs, source=cx.providers.CartoDB.Positron)
except:
    pass

ax.set_title('Study Area: University City, Philadelphia\nPedestrian Network Coverage',
             fontsize=14, fontweight='bold', pad=20)
ax.axis('off')

# Add scale bar and north arrow (simple text)
ax.text(0.05, 0.05, f'{len(edges):,} segments\n{edges.geometry.length.sum()/5280:.1f} miles',
        transform=ax.transAxes, fontsize=11, verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(output_dir / 'study_area_overview.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: study_area_overview.png")
plt.close()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("✅ VISUALIZATION GENERATION COMPLETE!")
print("="*70)

print(f"\nGenerated {len(list(output_dir.glob('*.png')))} visualization files in: {output_dir}")
print("\nFiles created:")
for f in sorted(output_dir.glob('*.png')):
    print(f"  ✓ {f.name}")

print("\n📋 Next steps:")
print("1. Copy all PNG files to your website's figures/ folder")
print("2. Images are referenced in the updated website pages")
print("3. Render website with 'quarto render'")
print("\n🎨 Your website will be super visual!")
