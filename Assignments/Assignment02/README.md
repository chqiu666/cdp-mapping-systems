# Assignment 02: Geoprocessing - 个人照片地理叙事与NYC城市数据分析

## 项目概述

本项目通过提取个人照片的地理位置信息，创建了一个表达日常生活空间叙事的数据集，并将其与NYC开放数据进行关联分析，探索个人空间体验与城市经济地理、功能地理的关系。

## 研究问题

个人拍照活动的空间分布（作为个人兴趣的代理指标）如何与以下数据相关联：
1. **地价分布** - 反映城市经济地理
2. **PLUTO土地利用类型** - 反映城市功能地理（住宅、商业、工业、绿地等）

## 🎯 项目成果

### 主要交付文件
- **📄 `final_photo_visualization.html`** - 完整的交互式Mapbox可视化
- **📍 `photo_locations_individual.geojson`** - 8个照片位置数据点
- **💰 `property_values_final.geojson`** - 28个地价数据点
- **🏢 `pluto_landuse.geojson`** - 1000个PLUTO土地利用数据点

### 交互式可视化特性
✅ **三层数据切换**：照片位置 ↔ 地价分布 ↔ 用地类型  
✅ **美观的UI设计**：毛玻璃效果控制面板，渐变按钮，响应式布局  
✅ **颜色可视化**：地价热力图 + PLUTO用地类型分类色彩  
✅ **交互式弹窗**：点击查看详细信息  
✅ **实时图例更新**：根据当前数据层自动更新  

## 📊 数据分析结果

### 照片分布特征（8个数据点）
- **Manhattan上西区**: 6个数据点 (75%)
  - 坐标范围: 40.807-40.810°N, -73.958-73.962°W
  - 高密度拍照区域，反映个人活动热点
  
- **Brooklyn Bay Ridge**: 2个数据点 (25%)
  - 坐标范围: 40.690-40.692°N, -74.175-74.178°W
  - 次要活动区域

### 空间经济分析
1. **地价关联性**
   - Manhattan区域：地价 $220-280万，反映高值住宅区特征
   - Brooklyn区域：地价 $110-120万，典型的住宅社区价位
   - 照片集中区域与高地价区域有显著重叠

2. **土地利用模式**
   - 主要照片区域对应**住宅-多户型**用地（PLUTO码 02）
   - 部分区域包含**商业-零售**功能（PLUTO码 05）
   - 体现了居住-消费复合型城市空间的偏好

## 🔧 技术实现

### 数据处理流程
```
照片文件 (.jpg) 
    ↓ [EXIF提取]
GPS坐标 + 时间戳
    ↓ [GeoJSON转换]
个人位置数据集
    ↓ [API查询]
NYC Open Data (地价 + PLUTO)
    ↓ [Mapbox可视化]
交互式地图应用
```

### 使用的技术栈
- **数据提取**: Python + PIL + ExifRead
- **地理数据**: GeoJSON格式
- **API接口**: NYC Open Data SODA API
- **可视化**: Mapbox GL JS
- **UI设计**: 现代CSS3 (backdrop-filter, gradients)

### 核心脚本
1. `extract_photo_locations.py` - EXIF GPS数据提取
2. `create_final_visualization.py` - 完整可视化生成
3. `property_values_final.geojson` - 地价数据存储
4. `pluto_landuse.geojson` - PLUTO数据存储

## 🗺️ 方法论工作流

### 数据收集
1. **主数据集**: 个人photoset (370+张照片)
2. **GPS提取**: 8张照片包含有效GPS坐标
3. **时间聚合**: 按地理邻近性聚类

### 关联数据集
1. **NYC Property Assessment Data**
   - 来源: `data.cityofnewyork.us/resource/rgy2-ttpn`
   - 字段: 评估价值、地址、业主信息
   
2. **NYC PLUTO土地利用数据**
   - 来源: `data.cityofnewyork.us/resource/64uk-42ks`
   - 字段: 用地类型编码、建筑信息、地块数据

### 空间分析方法
- **边界框查询**: 基于照片位置范围扩展查询NYC数据
- **颜色映射**: 数值标准化 → 色彩渐变可视化
- **分类着色**: PLUTO编码 → 用地类型色彩分类

## 🎨 用户界面设计

### 视觉特性
- **毛玻璃效果**: backdrop-filter: blur(10px)
- **渐变按钮**: linear-gradient(135deg, #4299e1, #3182ce)  
- **响应式交互**: hover效果 + 点击状态管理
- **信息层次**: 标题 → 控制区 → 图例 → 数据统计

### 交互逻辑
- **单选切换**: 三个数据层互斥显示
- **实时更新**: 图例根据当前图层自动更新内容
- **信息弹窗**: 点击要素显示详细属性信息

## 📈 分析洞察

### 个人空间偏好分析
1. **高频活动区域**: Manhattan上西区占主导地位
2. **经济地理关联**: 个人活动集中在中高价值地段
3. **功能空间偏好**: 偏向住宅-商业混合功能区域

### 城市空间特征
1. **地价梯度**: Manhattan → Brooklyn 明显的价值梯度
2. **用地复杂性**: 主要活动区域土地利用类型多样化
3. **空间连续性**: 个人活动轨迹体现了一定的空间连贯性

## 🚀 使用方法

1. 打开 `final_photo_visualization.html` 文件
2. 使用左侧控制面板切换不同数据层：
   - 📸 **照片位置**: 显示8个拍照地点
   - 💰 **地价分布**: 色彩热力图显示房产价值
   - 🏢 **用地类型**: 分类色彩显示PLUTO土地利用
3. 点击任意数据点查看详细信息
4. 观察图例了解当前数据层的含义

## 📝 项目文件结构

```
Assignment02/
├── final_photo_visualization.html      # 主要可视化文件
├── photo_locations_individual.geojson  # 个体照片数据
├── property_values_final.geojson       # 地价数据
├── pluto_landuse.geojson              # PLUTO土地利用数据
├── extract_photo_locations.py          # 照片数据提取脚本
├── create_final_visualization.py       # 最终可视化生成脚本
├── workflow_diagram.md                 # 工作流程图
└── README.md                          # 项目文档（本文件）
```

## 🎯 结论

本项目成功地将个人照片的地理叙事与NYC的经济和功能地理数据进行了有效整合，创建了一个完整的交互式可视化平台。通过空间数据分析，揭示了个人空间偏好与城市结构特征之间的关联模式，为个人地理学和城市研究提供了新的分析视角。

**Mapbox Token**: `pk.eyJ1IjoiYW5kcmV3OWl1IiwiYSI6ImNtZGk0ejdrZTA5OWQyaXBtdWhlMTdpd2EifQ.SG4pkm1FkJI79DoutAJmrw`