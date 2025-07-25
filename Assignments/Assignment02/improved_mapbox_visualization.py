#!/usr/bin/env python3
"""
改进的Mapbox可视化脚本 - 确保所有数据层都正确显示
包含：照片位置点、地价热力图、PLUTO土地利用数据
"""

import json
import requests
import geojson
from datetime import datetime

# Mapbox token
MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw'

# NYC Open Data endpoints
PLUTO_API_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.geojson"
PROPERTY_VALUES_API_URL = "https://data.cityofnewyork.us/resource/yjxr-fw8i.json"

def load_photo_data():
    """加载照片位置数据"""
    try:
        # 加载聚合的照片数据
        with open('photo_locations_aggregated.geojson', 'r') as f:
            aggregated_data = json.load(f)
        
        # 加载个体照片数据  
        with open('photo_locations_individual.geojson', 'r') as f:
            individual_data = json.load(f)
            
        print(f"加载了 {len(aggregated_data['features'])} 个聚合照片点")
        print(f"加载了 {len(individual_data['features'])} 个个体照片点")
        
        return aggregated_data, individual_data
    except Exception as e:
        print(f"加载照片数据错误: {e}")
        return None, None

def fetch_property_values_for_area(min_lat, max_lat, min_lon, max_lon, limit=1000):
    """获取指定区域的地价数据"""
    try:
        # 构建地理边界查询
        where_clause = f"latitude BETWEEN {min_lat} AND {max_lat} AND longitude BETWEEN {min_lon} AND {max_lon}"
        
        params = {
            '$where': where_clause,
            '$limit': limit,
            '$select': 'latitude,longitude,assessedvalue,fullmarketvalue,borough,zipcode,address,ownername,yearbuilt',
            '$order': 'assessedvalue DESC'
        }
        
        response = requests.get(PROPERTY_VALUES_API_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"获取了 {len(data)} 条地价数据")
        
        # 转换为GeoJSON格式
        features = []
        for record in data:
            if record.get('latitude') and record.get('longitude'):
                try:
                    lat = float(record['latitude'])
                    lon = float(record['longitude'])
                    assessed_value = float(record.get('assessedvalue', 0))
                    market_value = float(record.get('fullmarketvalue', 0))
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "assessed_value": assessed_value,
                            "market_value": market_value,
                            "borough": record.get('borough', ''),
                            "zipcode": record.get('zipcode', ''),
                            "address": record.get('address', ''),
                            "owner": record.get('ownername', ''),
                            "year_built": record.get('yearbuilt', ''),
                            # 计算价值等级用于颜色分类
                            "value_category": "high" if assessed_value > 1000000 else "medium" if assessed_value > 500000 else "low"
                        }
                    }
                    features.append(feature)
                except (ValueError, TypeError):
                    continue
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
        
    except Exception as e:
        print(f"获取地价数据错误: {e}")
        return {"type": "FeatureCollection", "features": []}

def fetch_pluto_data_for_area(min_lat, max_lat, min_lon, max_lon, limit=500):
    """获取PLUTO土地利用数据"""
    try:
        # 构建地理边界查询 - PLUTO使用GeoJSON格式，需要空间查询
        bbox_param = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        
        params = {
            '$where': f"within_box(the_geom, {min_lat}, {min_lon}, {max_lat}, {max_lon})",
            '$limit': limit,
            '$select': 'the_geom,landuse,zonedist1,bldgclass,yearbuilt,assessland,assesstot,bldgarea,residfar,commfar,builtfar'
        }
        
        response = requests.get(PLUTO_API_URL, params=params)
        response.raise_for_status()
        
        pluto_data = response.json()
        
        # 为每个要素添加土地利用分类信息
        if 'features' in pluto_data:
            for feature in pluto_data['features']:
                props = feature['properties']
                landuse_code = props.get('landuse', '')
                
                # 土地利用代码映射
                landuse_mapping = {
                    '01': 'One Family Dwellings',
                    '02': 'Two Family Dwellings', 
                    '03': 'Three Family Dwellings',
                    '04': 'Multi-Family Walkup',
                    '05': 'Multi-Family Elevator',
                    '06': 'Mixed Residential/Commercial',
                    '07': 'Residential Hotels',
                    '08': 'Rentals',
                    '09': 'Rentals',
                    '10': 'Rentals',
                    '11': 'Special Use',
                    '05': 'Apartment Buildings'
                }
                
                props['landuse_description'] = landuse_mapping.get(landuse_code, f'Code {landuse_code}')
                props['zone_category'] = 'Residential' if landuse_code in ['01','02','03','04','05'] else 'Mixed Use' if landuse_code in ['06'] else 'Other'
                
                # 添加颜色分类
                if landuse_code in ['01','02','03']:
                    props['color_category'] = 'residential_low'
                elif landuse_code in ['04','05']:
                    props['color_category'] = 'residential_high'
                elif landuse_code in ['06']:
                    props['color_category'] = 'mixed_use'
                else:
                    props['color_category'] = 'other'
        
        print(f"获取了 {len(pluto_data.get('features', []))} 个PLUTO地块")
        return pluto_data
        
    except Exception as e:
        print(f"获取PLUTO数据错误: {e}")
        return {"type": "FeatureCollection", "features": []}

def create_enhanced_visualization():
    """创建增强的可视化文件"""
    
    # 加载照片数据
    photo_aggregated, photo_individual = load_photo_data()
    if not photo_aggregated:
        return
    
    # 计算数据边界
    all_coords = []
    for feature in photo_aggregated['features']:
        coords = feature['geometry']['coordinates']
        all_coords.append(coords)
    
    if not all_coords:
        print("没有找到有效的照片坐标")
        return
        
    lons = [coord[0] for coord in all_coords]
    lats = [coord[1] for coord in all_coords]
    
    # 扩大边界以获取更多周边数据
    buffer = 0.01  # 约1km
    min_lon, max_lon = min(lons) - buffer, max(lons) + buffer
    min_lat, max_lat = min(lats) - buffer, max(lats) + buffer
    
    print(f"数据边界: {min_lat:.4f}, {min_lon:.4f} 到 {max_lat:.4f}, {max_lon:.4f}")
    
    # 获取地价数据
    property_data = fetch_property_values_for_area(min_lat, max_lat, min_lon, max_lon)
    
    # 获取PLUTO数据  
    pluto_data = fetch_pluto_data_for_area(min_lat, max_lat, min_lon, max_lon)
    
    # 创建HTML可视化
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>照片位置 vs NYC地价和土地利用数据</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        
        .legend {{
            background-color: white;
            border-radius: 5px;
            bottom: 30px;
            left: 10px;
            padding: 15px;
            position: absolute;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .legend h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
            font-weight: bold;
        }}
        
        .legend-section {{
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 12px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border-radius: 50%;
            border: 1px solid #ccc;
        }}
        
        .legend-square {{
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border: 1px solid #ccc;
        }}
        
        .controls {{
            background-color: white;
            border-radius: 5px;
            top: 10px;
            left: 10px;
            padding: 15px;
            position: absolute;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .control-group {{
            margin-bottom: 12px;
        }}
        
        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 14px;
        }}
        
        input[type="checkbox"] {{
            margin-right: 8px;
        }}
        
        .mapboxgl-popup-content {{
            max-width: 300px;
            font-size: 12px;
        }}
        
        .popup-title {{
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }}
        
        .popup-detail {{
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="controls">
        <div class="control-group">
            <label>数据层控制</label>
            <div>
                <input type="checkbox" id="photos-toggle" checked>
                <label for="photos-toggle">照片位置点</label>
            </div>
            <div>
                <input type="checkbox" id="property-toggle" checked>
                <label for="property-toggle">地价数据</label>
            </div>
            <div>
                <input type="checkbox" id="pluto-toggle" checked>
                <label for="pluto-toggle">PLUTO土地利用</label>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <h3>图例说明</h3>
        
        <div class="legend-section">
            <h4>照片位置点</h4>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ff6b6b; width: 20px; height: 20px;"></div>
                <span>高兴趣 (3+ 张照片)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #4ecdc4; width: 15px; height: 15px;"></div>
                <span>中兴趣 (2 张照片)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #45b7d1; width: 10px; height: 10px;"></div>
                <span>低兴趣 (1 张照片)</span>
            </div>
        </div>
        
        <div class="legend-section">
            <h4>地价等级</h4>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #d73027;"></div>
                <span>高价值 (>$1M)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #fc8d59;"></div>
                <span>中价值 ($500K-$1M)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #91bfdb;"></div>
                <span>低价值 (<$500K)</span>
            </div>
        </div>
        
        <div class="legend-section">
            <h4>土地利用类型</h4>
            <div class="legend-item">
                <div class="legend-square" style="background-color: #2b8cbe;"></div>
                <span>低密度住宅</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background-color: #7bccc4;"></div>
                <span>高密度住宅</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background-color: #bae4bc;"></div>
                <span>混合用途</span>
            </div>
            <div class="legend-item">
                <div class="legend-square" style="background-color: #f0f0f0;"></div>
                <span>其他用途</span>
            </div>
        </div>
    </div>

    <script>
        mapboxgl.accessToken = '{MAPBOX_TOKEN}';
        
        // 初始化地图
        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/light-v10',
            center: [{(min_lon + max_lon)/2}, {(min_lat + max_lat)/2}],
            zoom: 12
        }});
        
        // 数据
        const photoData = {json.dumps(photo_aggregated)};
        const propertyData = {json.dumps(property_data)};
        const plutoData = {json.dumps(pluto_data)};
        
        map.on('load', function() {{
            console.log('地图加载完成');
            console.log('照片数据点数:', photoData.features.length);
            console.log('地价数据点数:', propertyData.features.length);
            console.log('PLUTO数据点数:', plutoData.features.length);
            
            // 添加照片数据源和图层
            map.addSource('photos', {{
                'type': 'geojson',
                'data': photoData
            }});
            
            // 照片点图层
            map.addLayer({{
                'id': 'photo-points',
                'type': 'circle',
                'source': 'photos',
                'paint': {{
                    'circle-radius': [
                        'case',
                        ['>=', ['get', 'photo_count'], 3], 20,
                        ['>=', ['get', 'photo_count'], 2], 15,
                        10
                    ],
                    'circle-color': [
                        'case',
                        ['>=', ['get', 'photo_count'], 3], '#ff6b6b',
                        ['>=', ['get', 'photo_count'], 2], '#4ecdc4',
                        '#45b7d1'
                    ],
                    'circle-opacity': 0.8,
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#ffffff'
                }}
            }});
            
            // 添加地价数据源和图层
            map.addSource('property-values', {{
                'type': 'geojson',
                'data': propertyData
            }});
            
            // 地价点图层
            map.addLayer({{
                'id': 'property-points',
                'type': 'circle',
                'source': 'property-values',
                'paint': {{
                    'circle-radius': 6,
                    'circle-color': [
                        'case',
                        ['==', ['get', 'value_category'], 'high'], '#d73027',
                        ['==', ['get', 'value_category'], 'medium'], '#fc8d59',
                        '#91bfdb'
                    ],
                    'circle-opacity': 0.7,
                    'circle-stroke-width': 1,
                    'circle-stroke-color': '#ffffff'
                }}
            }});
            
            // 添加PLUTO数据源和图层
            map.addSource('pluto', {{
                'type': 'geojson',
                'data': plutoData
            }});
            
            // PLUTO多边形图层
            map.addLayer({{
                'id': 'pluto-polygons',
                'type': 'fill',
                'source': 'pluto',
                'paint': {{
                    'fill-color': [
                        'case',
                        ['==', ['get', 'color_category'], 'residential_low'], '#2b8cbe',
                        ['==', ['get', 'color_category'], 'residential_high'], '#7bccc4',
                        ['==', ['get', 'color_category'], 'mixed_use'], '#bae4bc',
                        '#f0f0f0'
                    ],
                    'fill-opacity': 0.6
                }}
            }});
            
            // PLUTO边界图层
            map.addLayer({{
                'id': 'pluto-borders',
                'type': 'line',
                'source': 'pluto',
                'paint': {{
                    'line-color': '#000000',
                    'line-width': 0.5,
                    'line-opacity': 0.8
                }}
            }});
            
            // 点击事件 - 照片点
            map.on('click', 'photo-points', function(e) {{
                const props = e.features[0].properties;
                const coords = e.features[0].geometry.coordinates;
                
                new mapboxgl.Popup()
                    .setLngLat(coords)
                    .setHTML(`
                        <div class="popup-title">📷 照片位置点</div>
                        <div class="popup-detail"><strong>照片数量:</strong> ${{props.photo_count}}</div>
                        <div class="popup-detail"><strong>兴趣等级:</strong> ${{props.interest_level}}</div>
                        <div class="popup-detail"><strong>位置:</strong> ${{coords[1].toFixed(4)}}, ${{coords[0].toFixed(4)}}</div>
                    `)
                    .addTo(map);
            }});
            
            // 点击事件 - 地价点
            map.on('click', 'property-points', function(e) {{
                const props = e.features[0].properties;
                const coords = e.features[0].geometry.coordinates;
                
                new mapboxgl.Popup()
                    .setLngLat(coords)
                    .setHTML(`
                        <div class="popup-title">💰 地价信息</div>
                        <div class="popup-detail"><strong>评估价值:</strong> $$${{props.assessed_value.toLocaleString()}}</div>
                        <div class="popup-detail"><strong>市场价值:</strong> $$${{props.market_value.toLocaleString()}}</div>
                        <div class="popup-detail"><strong>地址:</strong> ${{props.address}}</div>
                        <div class="popup-detail"><strong>建造年份:</strong> ${{props.year_built}}</div>
                        <div class="popup-detail"><strong>区:</strong> ${{props.borough}}</div>
                    `)
                    .addTo(map);
            }});
            
            // 点击事件 - PLUTO地块
            map.on('click', 'pluto-polygons', function(e) {{
                const props = e.features[0].properties;
                
                new mapboxgl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div class="popup-title">🏢 土地利用信息</div>
                        <div class="popup-detail"><strong>土地利用:</strong> ${{props.landuse_description}}</div>
                        <div class="popup-detail"><strong>分区:</strong> ${{props.zonedist1}}</div>
                        <div class="popup-detail"><strong>建筑类别:</strong> ${{props.bldgclass}}</div>
                        <div class="popup-detail"><strong>建筑面积:</strong> ${{props.bldgarea}} sq ft</div>
                        <div class="popup-detail"><strong>土地评估:</strong> $$${{props.assessland}}</div>
                    `)
                    .addTo(map);
            }});
            
            // 图层控制
            document.getElementById('photos-toggle').addEventListener('change', function(e) {{
                const visibility = e.target.checked ? 'visible' : 'none';
                map.setLayoutProperty('photo-points', 'visibility', visibility);
            }});
            
            document.getElementById('property-toggle').addEventListener('change', function(e) {{
                const visibility = e.target.checked ? 'visible' : 'none';
                map.setLayoutProperty('property-points', 'visibility', visibility);
            }});
            
            document.getElementById('pluto-toggle').addEventListener('change', function(e) {{
                const visibility = e.target.checked ? 'visible' : 'none';
                map.setLayoutProperty('pluto-polygons', 'visibility', visibility);
                map.setLayoutProperty('pluto-borders', 'visibility', visibility);
            }});
            
            // 添加鼠标悬停效果
            map.on('mouseenter', 'photo-points', function() {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'photo-points', function() {{
                map.getCanvas().style.cursor = '';
            }});
            
            map.on('mouseenter', 'property-points', function() {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'property-points', function() {{
                map.getCanvas().style.cursor = '';
            }});
            
            map.on('mouseenter', 'pluto-polygons', function() {{
                map.getCanvas().style.cursor = 'pointer';
            }});
            
            map.on('mouseleave', 'pluto-polygons', function() {{
                map.getCanvas().style.cursor = '';
            }});
        }});
    </script>
</body>
</html>"""
    
    # 保存新的可视化文件
    with open('enhanced_visualization.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 创建了增强版可视化文件: enhanced_visualization.html")
    print(f"📊 数据统计:")
    print(f"   - 照片数据点: {len(photo_aggregated['features'])}")
    print(f"   - 地价数据点: {len(property_data['features'])}")
    print(f"   - PLUTO地块: {len(pluto_data.get('features', []))}")

if __name__ == "__main__":
    create_enhanced_visualization()