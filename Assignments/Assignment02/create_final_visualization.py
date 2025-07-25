#!/usr/bin/env python3
"""
创建最终完整的可视化
"""

import json

# Mapbox token
MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw'

def create_final_visualization():
    """创建最终的完整可视化"""
    
    # 加载照片数据
    with open('photo_locations_individual.geojson', 'r') as f:
        photo_data = json.load(f)
    
    # 创建示例地价数据
    property_features = []
    base_coords = [
        [-73.958764, 40.810231, 2500000],  # 曼哈顿上西区
        [-73.961433, 40.808544, 2200000],
        [-73.961631, 40.807331, 2800000],
        [-73.958969, 40.810444, 2600000],
        [-73.958825, 40.810244, 2400000],
        [-74.174819, 40.692153, 1200000],  # 布鲁克林
        [-74.177528, 40.690681, 1100000],
    ]
    
    for i, (lon, lat, value) in enumerate(base_coords):
        # 在每个基准点周围创建几个数据点
        for j in range(4):
            offset_lon = lon + (j - 1.5) * 0.001
            offset_lat = lat + (j - 1.5) * 0.0005
            offset_value = value + (j - 1.5) * 150000
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [offset_lon, offset_lat]
                },
                "properties": {
                    "value": int(offset_value),
                    "address": f"地址 {i+1}-{j+1}",
                    "owner": f"业主 {i+1}-{j+1}",
                    "bbl": f"BBL{i}{j}",
                    "value_normalized": min(offset_value / 3000000, 1.0)
                }
            }
            property_features.append(feature)
    
    property_data = {
        "type": "FeatureCollection",
        "features": property_features
    }
    
    # 加载PLUTO数据
    try:
        with open('pluto_landuse.geojson', 'r') as f:
            pluto_data = json.load(f)
    except FileNotFoundError:
        pluto_data = {"type": "FeatureCollection", "features": []}
    
    # 计算地图中心
    coords = [f['geometry']['coordinates'] for f in photo_data['features']]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    print(f"照片数据点: {len(photo_data['features'])}个")
    print(f"地价数据点: {len(property_data['features'])}个")
    print(f"PLUTO数据点: {len(pluto_data.get('features', []))}个")
    
    # 创建HTML内容
    html_content = f"""<!DOCTYPE html>
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
            max-width: 320px;
        }}
        
        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2d3748;
            border-bottom: 2px solid #4299e1;
            padding-bottom: 8px;
            text-align: center;
        }}
        
        .layer-controls {{
            margin-bottom: 15px;
        }}
        
        .layer-toggle {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 12px;
            border-radius: 8px;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid transparent;
            background: rgba(248, 250, 252, 0.8);
        }}
        
        .layer-toggle:hover {{
            background: rgba(66, 153, 225, 0.1);
            border-color: #4299e1;
            transform: translateY(-1px);
        }}
        
        .layer-toggle.active {{
            background: linear-gradient(135deg, #4299e1, #3182ce);
            color: white;
            box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
            transform: translateY(-1px);
        }}
        
        .layer-toggle input[type="radio"] {{
            margin-right: 12px;
            transform: scale(1.2);
        }}
        
        .layer-label {{
            font-weight: 500;
            font-size: 14px;
            flex: 1;
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
        
        .stats-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
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
            <span class='layer-label'>📸 照片位置</span>
        </div>
        
        <div class='layer-toggle' onclick='toggleLayer("property")'>
            <input type='radio' name='layer' value='property' />
            <span class='layer-label'>💰 地价分布</span>
        </div>
        
        <div class='layer-toggle' onclick='toggleLayer("landuse")'>
            <input type='radio' name='layer' value='landuse' />
            <span class='layer-label'>🏢 用地类型</span>
        </div>
    </div>
    
    <div id='legend' class='legend'></div>
</div>

<div class='info-panel'>
    <strong>📍 个人照片地理分析</strong><br>
    <small>结合NYC开放数据进行城市空间分析</small>
    <div class='data-stats'>
        <div class='stats-item'>
            <span>📸 照片数据点:</span>
            <span>{len(photo_data['features'])}个</span>
        </div>
        <div class='stats-item'>
            <span>💰 地价数据:</span>
            <span>{len(property_data['features'])}个</span>
        </div>
        <div class='stats-item'>
            <span>🏢 PLUTO数据:</span>
            <span>{len(pluto_data.get('features', []))}个</span>
        </div>
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

// 数据定义
const photoData = {json.dumps(photo_data, ensure_ascii=False)};
const propertyData = {json.dumps(property_data, ensure_ascii=False)};
const plutoData = {json.dumps(pluto_data, ensure_ascii=False)};

let currentLayer = 'photos';

map.on('load', function() {{
    // 添加数据源
    map.addSource('photos', {{
        'type': 'geojson',
        'data': photoData
    }});
    
    map.addSource('property-values', {{
        'type': 'geojson', 
        'data': propertyData
    }});
    
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
                10, 10,
                15, 20
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
                10, 4,
                15, 10
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
            'circle-opacity': 0.8,
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
            'fill-color': [
                'match',
                ['get', 'landuse'],
                '01', '#2E8B57',  // 住宅-单户
                '02', '#228B22',  // 住宅-多户
                '03', '#32CD32',  // 住宅-混合
                '04', '#4169E1',  // 商业-办公
                '05', '#0000FF',  // 商业-零售
                '06', '#8B4513',  // 工业-制造
                '07', '#A0A0A0',  // 交通-运输
                '08', '#FFD700',  // 公共-教育
                '09', '#00FF00',  // 开放空间-绿地
                '10', '#808080',  // 公共-停车
                '11', '#FFA500',  // 公共-其他
                '#DDA0DD'         // 默认颜色
            ],
            'fill-opacity': 0.7,
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
    ['photos-layer', 'property-layer', 'landuse-layer'].forEach(layer => {{
        map.on('mouseenter', layer, () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', layer, () => map.getCanvas().style.cursor = '');
    }});
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
    const layerMap = {{
        'photos': 'photos-layer',
        'property': 'property-layer', 
        'landuse': 'landuse-layer'
    }};
    
    map.setLayoutProperty(layerMap[layerType], 'visibility', 'visible');
    
    currentLayer = layerType;
    updateLegend(layerType);
}}

function updateLegend(layerType) {{
    const legendDiv = document.getElementById('legend');
    
    if (layerType === 'photos') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>📸 照片位置图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #FF6B6B; border-radius: 50%;'></div>
                <span>照片拍摄位置 (8个点)</span>
            </div>
        `;
    }} else if (layerType === 'property') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>💰 地价分布图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #ffffcc;'></div>
                <span>低价值 (< 150万)</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #fed976;'></div>
                <span>中等价值 (150-250万)</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #f03b20;'></div>
                <span>高价值 (> 250万)</span>
            </div>
        `;
    }} else if (layerType === 'landuse') {{
        legendDiv.innerHTML = `
            <div class='legend-title'>🏢 用地类型图例</div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #2E8B57;'></div>
                <span>住宅用地</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #4169E1;'></div>
                <span>商业用地</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #8B4513;'></div>
                <span>工业用地</span>
            </div>
            <div class='legend-item'>
                <div class='legend-color' style='background: #00FF00;'></div>
                <span>绿地公园</span>
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
            <div style='padding: 8px; min-width: 200px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>📸 照片位置</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>坐标:</strong> ${{coordinates[1].toFixed(6)}}, ${{coordinates[0].toFixed(6)}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>文件:</strong> ${{props.filename || '照片文件'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>时间:</strong> ${{props.timestamp || '未知时间'}}</p>
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
            <div style='padding: 8px; min-width: 200px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>💰 房产信息</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>地址:</strong> ${{props.address || '未知地址'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>评估价值:</strong> $${{props.value ? props.value.toLocaleString() : '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>业主:</strong> ${{props.owner || '未知业主'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>地块编号:</strong> ${{props.bbl || '未知'}}</p>
            </div>
        `)
        .addTo(map);
}}

function showLandusePopup(e) {{
    const props = e.features[0].properties;
    
    const landuseTypes = {{
        '01': '住宅-单户',
        '02': '住宅-多户', 
        '03': '住宅-混合',
        '04': '商业-办公',
        '05': '商业-零售',
        '06': '工业-制造',
        '07': '交通-运输',
        '08': '公共-教育',
        '09': '开放空间-绿地',
        '10': '公共-停车',
        '11': '公共-其他'
    }};
    
    const landuseType = landuseTypes[props.landuse] || '其他用地';
    
    new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(`
            <div style='padding: 8px; min-width: 200px;'>
                <h4 style='margin: 0 0 8px 0; color: #2d3748;'>🏢 用地信息</h4>
                <p style='margin: 4px 0; font-size: 13px;'><strong>用地类型:</strong> ${{landuseType}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>地块编号:</strong> ${{props.bbl || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>建筑年份:</strong> ${{props.yearbuilt || '未知'}}</p>
                <p style='margin: 4px 0; font-size: 13px;'><strong>建筑面积:</strong> ${{props.bldgarea ? props.bldgarea + ' sq ft' : '未知'}}</p>
            </div>
        `)
        .addTo(map);
}}

</script>

</body>
</html>"""
    
    # 保存最终HTML文件
    with open('final_photo_visualization.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 保存数据文件
    with open('property_values_final.geojson', 'w', encoding='utf-8') as f:
        json.dump(property_data, f, indent=2, ensure_ascii=False)
    
    print("✅ 最终可视化文件已创建:")
    print("   📄 final_photo_visualization.html")
    print("   📄 property_values_final.geojson")
    print(f"   📍 包含 {len(photo_data['features'])} 个照片数据点")
    print(f"   💰 包含 {len(property_data['features'])} 个地价数据点")
    print(f"   🏢 包含 {len(pluto_data.get('features', []))} 个PLUTO数据点")

if __name__ == "__main__":
    create_final_visualization()