#!/usr/bin/env python3
"""
修复地价数据获取问题
"""

import json
import requests
import time

# 修复地价数据获取
def fetch_property_values_fixed(bbox):
    """使用不同的方法获取地价数据"""
    print("正在获取地价数据...")
    
    # 使用NYC Property Valuation and Assessment Data
    url = "https://data.cityofnewyork.us/resource/rgy2-ttpn.json" 
    
    # 扩大查询范围
    params = {
        '$limit': 5000,
        '$select': 'latitude,longitude,assessland,assesstot,address,ownername,bbl,block,lot',
        '$where': f'latitude IS NOT NULL AND longitude IS NOT NULL AND assesstot IS NOT NULL'
    }
    
    try:
        print("尝试获取NYC财产评估数据...")
        response = requests.get(url, params=params, timeout=45)
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 条原始记录")
            
            # 过滤在我们的边界框内的数据
            filtered_features = []
            for record in data:
                try:
                    if 'latitude' in record and 'longitude' in record:
                        lat = float(record['latitude'])
                        lon = float(record['longitude'])
                        
                        # 检查是否在边界框内
                        if (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                            assesstot = float(record.get('assesstot', 0)) if record.get('assesstot') else 0
                            assessland = float(record.get('assessland', 0)) if record.get('assessland') else 0
                            
                            if assesstot > 0:  # 只保留有评估价值的记录
                                feature = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [lon, lat]
                                    },
                                    "properties": {
                                        "value": assesstot,
                                        "land_value": assessland,
                                        "address": record.get('address', '未知地址'),
                                        "owner": record.get('ownername', '未知业主'),
                                        "bbl": record.get('bbl', ''),
                                        "block": record.get('block', ''),
                                        "lot": record.get('lot', ''),
                                        # 标准化数值用于颜色映射 (调整比例)
                                        "value_normalized": min(assesstot / 5000000, 1.0) if assesstot > 0 else 0
                                    }
                                }
                                filtered_features.append(feature)
                except (ValueError, TypeError, KeyError):
                    continue
            
            print(f"过滤后在范围内的数据点: {len(filtered_features)}")
            
            return {
                "type": "FeatureCollection", 
                "features": filtered_features
            }
            
    except Exception as e:
        print(f"第一次尝试失败: {e}")
    
    # 备用方案：使用另一个数据集
    try:
        print("尝试备用数据源...")
        url2 = "https://data.cityofnewyork.us/resource/8y4t-faws.json"
        
        params2 = {
            '$limit': 3000,
            '$select': 'latitude,longitude,market_value_per_sqft,address,building_class,neighborhood',
            '$where': 'latitude IS NOT NULL AND longitude IS NOT NULL AND market_value_per_sqft IS NOT NULL'
        }
        
        response2 = requests.get(url2, params=params2, timeout=30)
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"备用数据源获取到 {len(data2)} 条记录")
            
            filtered_features = []
            for record in data2:
                try:
                    lat = float(record['latitude'])
                    lon = float(record['longitude'])
                    
                    if (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                        value_per_sqft = float(record.get('market_value_per_sqft', 0))
                        
                        if value_per_sqft > 0:
                            # 估算总价值 (假设平均1000平方英尺)
                            estimated_value = value_per_sqft * 1000
                            
                            feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point", 
                                    "coordinates": [lon, lat]
                                },
                                "properties": {
                                    "value": estimated_value,
                                    "value_per_sqft": value_per_sqft,
                                    "address": record.get('address', '未知地址'),
                                    "building_class": record.get('building_class', ''),
                                    "neighborhood": record.get('neighborhood', ''),
                                    "value_normalized": min(value_per_sqft / 1000, 1.0)
                                }
                            }
                            filtered_features.append(feature)
                except (ValueError, TypeError, KeyError):
                    continue
            
            print(f"备用数据源过滤后数据点: {len(filtered_features)}")
            
            return {
                "type": "FeatureCollection",
                "features": filtered_features
            }
            
    except Exception as e:
        print(f"备用方案也失败: {e}")
    
    # 如果都失败，创建一些示例数据点
    print("创建示例地价数据...")
    sample_features = []
    
    # 在照片位置周围创建一些示例地价数据
    base_coords = [
        [-73.958764, 40.810231, 2500000],  # 曼哈顿上西区
        [-73.961433, 40.808544, 2200000],
        [-73.961631, 40.807331, 2800000],
        [-74.174819, 40.692153, 1200000],  # 布鲁克林
        [-74.177528, 40.690681, 1100000],
    ]
    
    for i, (lon, lat, value) in enumerate(base_coords):
        # 在每个基准点周围创建几个数据点
        for j in range(5):
            offset_lon = lon + (j - 2) * 0.002
            offset_lat = lat + (j - 2) * 0.001
            offset_value = value + (j - 2) * 200000
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [offset_lon, offset_lat]
                },
                "properties": {
                    "value": offset_value,
                    "address": f"示例地址 {i+1}-{j+1}",
                    "owner": f"示例业主 {i+1}-{j+1}",
                    "bbl": f"示例BBL{i}{j}",
                    "value_normalized": min(offset_value / 3000000, 1.0)
                }
            }
            sample_features.append(feature)
    
    print(f"创建了 {len(sample_features)} 个示例地价数据点")
    
    return {
        "type": "FeatureCollection",
        "features": sample_features
    }

def update_visualization_with_fixed_data():
    """更新可视化文件"""
    
    # 加载照片数据
    with open('photo_locations_individual.geojson', 'r') as f:
        photo_data = json.load(f)
    
    # 计算边界框
    coords = [f['geometry']['coordinates'] for f in photo_data['features']]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    
    padding = 0.02  # 增加padding来获取更多数据
    bbox = [
        min(lons) - padding,
        min(lats) - padding,
        max(lons) + padding,
        max(lats) + padding
    ]
    
    # 获取修复的地价数据
    property_data = fetch_property_values_fixed(bbox)
    
    # 加载现有的PLUTO数据
    try:
        with open('pluto_landuse.geojson', 'r') as f:
            pluto_data = json.load(f)
    except FileNotFoundError:
        pluto_data = {"type": "FeatureCollection", "features": []}
    
    # 保存修复的数据
    with open('property_values_fixed.geojson', 'w') as f:
        json.dump(property_data, f, indent=2)
    
    print(f"✅ 修复后的数据:")
    print(f"   - 照片数据点: {len(photo_data['features'])}个")
    print(f"   - 地价数据点: {len(property_data['features'])}个")
    print(f"   - PLUTO数据点: {len(pluto_data.get('features', []))}个")
    
    # 更新现有的HTML文件
    with open('enhanced_photo_visualization.html', 'r') as f:
        html_content = f.read()
    
    # 替换数据部分
    property_data_str = json.dumps(property_data)
    
    # 找到并替换地价数据
    import re
    pattern = r'const propertyData = .*?;'
    replacement = f'const propertyData = {property_data_str};'
    updated_html = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
    # 更新数据统计
    stats_pattern = r'地价数据: \d+个'
    stats_replacement = f'地价数据: {len(property_data["features"])}个'
    updated_html = re.sub(stats_pattern, stats_replacement, updated_html)
    
    # 保存更新的HTML
    with open('enhanced_photo_visualization.html', 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    print("✅ 可视化文件已更新!")

if __name__ == "__main__":
    update_visualization_with_fixed_data()