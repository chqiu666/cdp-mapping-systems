#!/usr/bin/env python3
"""
增强的Mapbox可视化 - 照片位置 + 地价 + PLUTO用地类型
包含美观的UI切换功能
"""

import json
import requests
import time

# Mapbox token
MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw'

def load_photo_data():
    """加载照片位置数据"""
    with open('photo_locations_individual.geojson', 'r') as f:
        return json.load(f)

def fetch_property_values(bbox):
    """获取地价数据"""
    print("正在获取地价数据...")
    
    # 使用NYC Property Assessment数据
    url = "https://data.cityofnewyork.us/resource/yjxr-fw8i.json"
    
    params = {
        '$where': f'latitude between {bbox[1]} and {bbox[3]} and longitude between {bbox[0]} and {bbox[2]}',
        '$limit': 2000,
        '$select': 'latitude,longitude,avtot,address,ownername,bbl'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 个地价数据点")
            
            # 转换为GeoJSON格式
            features = []
            for record in data:
                if 'latitude' in record and 'longitude' in record and 'avtot' in record:
                    try:
                        lat = float(record['latitude'])
                        lon = float(record['longitude'])
                        value = float(record['avtot']) if record['avtot'] else 0
                        
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "value": value,
                                "address": record.get('address', ''),
                                "owner": record.get('ownername', ''),
                                "bbl": record.get('bbl', ''),
                                # 标准化数值用于颜色映射
                                "value_normalized": min(value / 10000000, 1.0) if value > 0 else 0
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
        print(f"地价数据获取失败: {e}")
    
    return {"type": "FeatureCollection", "features": []}

def fetch_pluto_data(bbox):
    """获取PLUTO用地类型数据"""
    print("正在获取PLUTO用地类型数据...")
    
    url = "https://data.cityofnewyork.us/resource/64uk-42ks.geojson"
    
    params = {
        '$where': f'latitude between {bbox[1]} and {bbox[3]} and longitude between {bbox[0]} and {bbox[2]}',
        '$limit': 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data.get('features', []))} 个PLUTO数据")
            
            # 标准化用地类型
            land_use_map = {
                '01': {'type': '住宅-单户', 'color': '#2E8B57'},
                '02': {'type': '住宅-多户', 'color': '#228B22'}, 
                '03': {'type': '住宅-混合', 'color': '#32CD32'},
                '04': {'type': '商业-办公', 'color': '#4169E1'},
                '05': {'type': '商业-零售', 'color': '#0000FF'},
                '06': {'type': '工业-制造', 'color': '#8B4513'},
                '07': {'type': '交通-运输', 'color': '#A0A0A0'},
                '08': {'type': '公共-教育', 'color': '#FFD700'},
                '09': {'type': '开放空间-绿地', 'color': '#00FF00'},
                '10': {'type': '公共-停车', 'color': '#808080'},
                '11': {'type': '公共-其他', 'color': '#FFA500'}
            }
            
            # 处理特征属性
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                landuse = props.get('landuse', '00')
                
                # 获取用地类型信息
                landuse_info = land_use_map.get(landuse, {'type': '其他', 'color': '#DDA0DD'})
                
                # 添加标准化属性
                props.update({
                    'landuse_type': landuse_info['type'],
                    'landuse_color': landuse_info['color'],
                    'landuse_code': landuse
                })
            
            return data
    except Exception as e:
        print(f"PLUTO数据获取失败: {e}")
    
    return {"type": "FeatureCollection", "features": []}

def create_enhanced_html():
    """创建增强的HTML可视化"""
    
    # 加载照片数据
    photo_data = load_photo_data()
    
    # 计算边界框
    coords = [f['geometry']['coordinates'] for f in photo_data['features']]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    
    padding = 0.01
    bbox = [
        min(lons) - padding,  # min_lon
        min(lats) - padding,  # min_lat  
        max(lons) + padding,  # max_lon
        max(lats) + padding   # max_lat
    ]
    
    center_lat = (bbox[1] + bbox[3]) / 2
    center_lon = (bbox[0] + bbox[2]) / 2
    
    print(f"照片数据范围: {bbox}")
    print(f"地图中心点: ({center_lat:.6f}, {center_lon:.6f})")
    
    # 获取相关数据集
    property_data = fetch_property_values(bbox)
    pluto_data = fetch_pluto_data(bbox)
    
    # 保存数据文件
    with open('property_values.geojson', 'w') as f:
        json.dump(property_data, f)
    
    with open('pluto_landuse.geojson', 'w') as f:
        json.dump(pluto_data, f)
    
    print(f"地价数据点数量: {len(property_data['features'])}")
    print(f"PLUTO数据点数量: {len(pluto_data.get('features', []))}")

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8' />
    <title>个人照片位置分析 + NYC城市数据</title>
    <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
    <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
    <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
    <style>
        body {{ 
            margin: 0; 
            padding: 0; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8f9fa;
        }}
        
        #map {{ 
            position: absolute; 
            top: 0; 
            bottom: 0; 
            width: 100%; 
        }}
        
        .control-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            z-index: 1000;
            min-width: 280px;
        }}
        
        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2d3748;
            border-bottom: 2px solid #4299e1;
            padding-bottom: 8px;
        }}
        
        .layer-controls {{
            margin-bottom: 15px;
        }}
        
        .layer-toggle {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid transparent;
        }}
        
        .layer-toggle:hover {{
            background: rgba(66, 153, 225, 0.1);
            border-color: #4299e1;
        }}
        
        .layer-toggle.active {{
            background: linear-gradient(135deg, #4299e1, #3182ce);
            color: white;
            box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
        }}
        
        .layer-toggle input[type="radio"] {{
            margin-right: 10px;
            transform: scale(1.2);
        }}
        
        .layer-label {{
            font-weight: 500;
            font-size: 14px;
        }}
        
        .legend {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}
        
        .legend-title {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #2d3748;
            font-size: 13px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 6px;
            font-size: 12px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            margin-right: 8px;
            border: 1px solid rgba(0, 0, 0, 0.2);
        }}
        
        .info-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            max-width: 300px;
            z-index: 1000;
        }}
        
        .mapboxgl-popup-content {{
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }}
        
        .data-stats {{
            font-size: 12px;
            color: #718096;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>

<div id='map'></div>

<div class='control-panel'>
    <div class='panel-title'>🗺️ 数据层控制</div>
    
    <div class='layer-controls'>
        <div class='layer-toggle active' onclick='toggleLayer("photos")'>
            <input type='radio' name='layer' value='photos' checked />
            <span class='layer-label'>📸 照片位置 (8个点)</span>
        </div>
        
        <div class='layer-toggle' onclick='toggleLayer("property")'>
            <input type='radio' name='layer' value='property' />
            <span class='layer-label'>💰 地价分布</span>
        </div>
        
        <div class='layer-toggle' onclick='toggleLayer("landuse")'>
            <input type='radio' name='layer' value='landuse' />
            <span class='layer-label'>🏢 用地类型 (PLUTO)</span>
        </div>
    </div>
    
    <div id='legend' class='legend'></div>
</div>

<div class='info-panel'>
    <strong>个人照片地理分析</strong><br>
    <small>结合NYC开放数据进行城市空间分析</small>
    <div class='data-stats'>
        <div>📍 照片数据点: 8个</div>
        <div>🏘️ 地价数据: {len(property_data['features'])}个</div>
        <div>🏗️ PLUTO数据: {len(pluto_data.get('features', []))}个</div>
    </div>
</div>

<script>
mapboxgl.accessToken = '{MAPBOX_TOKEN}';

const map = new mapboxgl.Map({{
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v11',
    center: [{center_lon}, {center_lat}],
    zoom: 12
}});

// 照片位置数据
const photoData = {json.dumps(photo_data)};

// 地价数据  
const propertyData = {json.dumps(property_data)};

// PLUTO用地类型数据
const plutoData = {json.dumps(pluto_data)};

let currentLayer = 'photos';

map.on('load', function() {{
    // 添加照片数据源
    map.addSource('photos', {{
        'type': 'geojson',
        'data': photoData
    }});
    
    // 添加地价数据源
    map.addSource('property-values', {{
        'type': 'geojson', 
        'data': propertyData
    }});
    
    // 添加PLUTO数据源
    map.addSource('pluto-landuse', {{
        'type': 'geojson',
        'data': plutoData
    }});
    
    // 照片位置图层
    map.addLayer({{
        'id': 'photos-layer',
        'type': 'circle',
        'source': 'photos',
        'paint': {{
            'circle-radius': [
                'interpolate',
                ['linear'],
                ['zoom'],
                10, 8,
                15, 16
            ],
            'circle-color': '#FF6B6B',
            'circle-stroke-width': 3,
            'circle-stroke-color': '#ffffff',
            'circle-opacity': 0.9
        }}
    }});
    
    // 地价热力图图层
    map.addLayer({{
        'id': 'property-layer',
        'type': 'circle',
        'source': 'property-values',
        'paint': {{
            'circle-radius': [
                'interpolate',
                ['linear'],
                ['zoom'],
                10, 3,
                15, 8
            ],
            'circle-color': [
                'interpolate',
                ['linear'],
                ['get', 'value_normalized'],
                0, '#ffffcc',
                0.2, '#ffeda0', 
                0.4, '#fed976',
                0.6, '#feb24c',
                0.8, '#fd8d3c',
                1, '#f03b20'
            ],
            'circle-opacity': 0.7,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
        }},
        'layout': {{
            'visibility': 'none'
        }}
    }});
    
    // PLUTO用地类型图层
    map.addLayer({{
        'id': 'landuse-layer',
        'type': 'fill',
        'source': 'pluto-landuse',
        'paint': {{
            'fill-color': ['get', 'landuse_color'],
            'fill-opacity': 0.6,
            'fill-outline-color': '#ffffff'
        }},
        'layout': {{
            'visibility': 'none'
        }}
    }});
    
    // 设置初始图例
    updateLegend('photos');
    
    // 点击事件
    map.on('click', 'photos-layer', showPhotoPopup);
    map.on('click', 'property-layer', showPropertyPopup);  
    map.on('click', 'landuse-layer', showLandusePopup);
    
    // 鼠标悬停效果
    map.on('mouseenter', 'photos-layer', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'photos-layer', () => map.getCanvas().style.cursor = '');
    map.on('mouseenter', 'property-layer', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'property-layer', () => map.getCanvas().style.cursor = '');
    map.on('mouseenter', 'landuse-layer', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'landuse-layer', () => map.getCanvas().style.cursor = '');
}});

function toggleLayer(layerType) {{
    // 更新按钮状态
    document.querySelectorAll('.layer-toggle').forEach(toggle => {{
        toggle.classList.remove('active');
    }});
    event.currentTarget.classList.add('active');
    
    // 更新radio按钮
    document.querySelectorAll('input[name="layer"]').forEach(radio => {{
        radio.checked = radio.value === layerType;
    }});
    
    // 隐藏所有图层
    map.setLayoutProperty('photos-layer', 'visibility', 'none');
    map.setLayoutProperty('property-layer', 'visibility', 'none');
    map.setLayoutProperty('landuse-layer', 'visibility', 'none');
    
    // 显示选中的图层
    map.setLayoutProperty(layerType === 'photos' ? 'photos-layer' :
                         layerType === 'property' ? 'property-layer' : 'landuse-layer', 
                         'visibility', 'visible');
    
    currentLayer = layerType;
    updateLegend(layerType);
}}

function updateLegend(layerType) {{
    const legendDiv = document.getElementById('legend');
    
    if (layerType === 'photos') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>照片位置图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #FF6B6B; border-radius: 50%;'></div>
                <span>照片拍摄位置</span>
            </div>
        `;
    }} else if (layerType === 'property') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>地价分布图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #ffffcc;'></div>
                <span>低价值</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #fed976;'></div>
                <span>中等价值</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #f03b20;'></div>
                <span>高价值</span>
            </div>
        `;
    }} else if (layerType === 'landuse') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>用地类型图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #2E8B57;'></div>
                <span>住宅</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #4169E1;'></div>
                <span>商业</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #8B4513;'></div>
                <span>工业</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #00FF00;'></div>
                <span>绿地</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #FFD700;'></div>
                <span>公共设施</span>
            </div>
        `;
    }}
}}

function showPhotoPopup(e) {{
    const coordinates = e.features[0].geometry.coordinates.slice();
    const props = e.features[0].properties;
    
    new mapboxgl.Popup()
        .setLngLat(coordinates)
        .setHTML(`
            <div style='padding: 5px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>📸 照片位置</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>坐标:</strong> ${{coordinates[1].toFixed(6)}}, ${{coordinates[0].toFixed(6)}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>文件:</strong> ${{props.filename || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>时间:</strong> ${{props.timestamp || '未知'}}</p>
            </div>
        `)
        .addTo(map);
}}

function showPropertyPopup(e) {{
    const coordinates = e.features[0].geometry.coordinates.slice();
    const props = e.features[0].properties;
    
    new mapboxgl.Popup()
        .setLngLat(coordinates)
        .setHTML(`
            <div style='padding: 5px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>💰 房产信息</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>地址:</strong> ${{props.address || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>评估价值:</strong> $${{props.value ? props.value.toLocaleString() : '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>业主:</strong> ${{props.owner || '未知'}}</p>
            </div>
        `)
        .addTo(map);
}}

function showLandusePopup(e) {{
    const props = e.features[0].properties;
    
    new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(`
            <div style='padding: 5px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>🏢 用地信息</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>用地类型:</strong> ${{props.landuse_type || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>地块编号:</strong> ${{props.bbl || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>建筑年份:</strong> ${{props.yearbuilt || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>建筑面积:</strong> ${{props.bldgarea || '未知'}} sq ft</p>
            </div>
        `)
        .addTo(map);
}}

</script>

</body>
</html>
"""
    
    # 保存HTML文件
    with open('enhanced_photo_visualization.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 增强可视化已创建: enhanced_photo_visualization.html")
    print(f"   - 照片数据点: {len(photo_data['features'])}个")
    print(f"   - 地价数据点: {len(property_data['features'])}个") 
    print(f"   - PLUTO数据点: {len(pluto_data.get('features', []))}个")

if __name__ == "__main__":
    create_enhanced_html()