const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'cloud_native_geospatial_stack',
    name: 'Cloud-native Geospatial Stack',
    domain: '遥感数据工程',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 95,
    summary: '以 STAC、COG、Zarr、GeoParquet、DuckDB Spatial 和动态瓦片服务构成云原生遥感数据处理底座。',
    why: '遥感算法工程师不只训练模型，还要能把影像、矢量、索引、瓦片和接口组织成可复用的数据产品。',
    actions: ['补一张云原生遥感架构图', '把池塘项目映射到 STAC/COG/GeoParquet', '设计本地轻量数据湖目录'],
    interview: '我会把遥感数据底座设计成云原生栈：STAC 做资产目录，COG/Zarr 做栅格访问，GeoParquet 做矢量分析，TiTiler 做在线瓦片。',
    sources: [
      { label: 'STAC specification', url: 'https://stacspec.org/en' },
      { label: 'OGC Cloud Optimized GeoTIFF', url: 'https://docs.ogc.org/is/21-026/21-026.html' },
      { label: 'GeoParquet', url: 'https://geoparquet.org/' }
    ]
  },
  {
    id: 'stac_catalog_api',
    name: 'STAC Catalog / STAC API',
    domain: '遥感数据工程',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 94,
    summary: '用统一 JSON 结构描述时空资产、集合、链接、时间和空间范围，让多源遥感数据可发现、可索引、可检索。',
    why: '你会处理 Sentinel、无人机、天地图和项目成果，STAC 能把这些影像和图斑产物纳入统一资产目录。',
    actions: ['给项目成果定义 STAC Item', '记录 datetime/bbox/assets/properties', '预留 STAC API 查询入口'],
    interview: 'STAC 的价值是把遥感资产描述标准化，避免每个数据源都写一套下载和解析逻辑。',
    sources: [
      { label: 'STAC overview', url: 'https://stacspec.org/en' }
    ]
  },
  {
    id: 'cloud_optimized_geotiff',
    name: 'Cloud Optimized GeoTIFF (COG)',
    domain: '遥感数据工程',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 93,
    summary: '把 GeoTIFF 组织成支持 HTTP Range Request、内部瓦片和概览金字塔的云端可流式读取格式。',
    why: '养殖池塘、断面溯源和水色专题图都需要快速预览、局部读取和在线制图，COG 是工程交付关键格式。',
    actions: ['把输出影像转 COG', '生成 overview 和 tiling', '用局部读取替代整图下载'],
    interview: 'COG 的关键是让大影像像网页资源一样按需读取，配合瓦片服务能显著提升遥感产品浏览和部署效率。',
    sources: [
      { label: 'OGC COG Standard', url: 'https://docs.ogc.org/is/21-026/21-026.html' }
    ]
  },
  {
    id: 'zarr_xarray_datacube',
    name: 'Zarr / Xarray Data Cube',
    domain: '时空数据',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 89,
    summary: '用分块、压缩、N维数组格式承载多时相、多波段遥感和气象水文数据，适合 xarray/dask 并行分析。',
    why: '水质、气象、遥感时序和模型预测天然是多维数据，Zarr 比一堆散文件更适合时空立方体分析。',
    actions: ['把水质/影像时间序列抽象为 cube', '记录 chunk 策略', '比较 GeoTIFF 栈与 Zarr 读取性能'],
    interview: '当数据从单景影像变成多时相、多波段、多变量时，我会考虑 Zarr + xarray，把处理逻辑变成数据立方体计算。',
    sources: [
      { label: 'Zarr overview', url: 'https://zarr.dev/' }
    ]
  },
  {
    id: 'geoparquet_vector_lake',
    name: 'GeoParquet Vector Lake',
    domain: '空间数据工程',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 92,
    summary: '用 Parquet 列式存储和地理空间元数据组织图斑、排口、断面、道路、水系等矢量数据。',
    why: '你的项目有大量 shapefile/geojson/gpkg/excel 成果，GeoParquet 适合做高性能、可版本化、可分析的矢量数据湖。',
    actions: ['把池塘图斑导出 GeoParquet', '记录 CRS 和 geometry 类型', '用 DuckDB 做面积/叠加统计'],
    interview: '传统 shapefile 适合交换，但生产分析我会优先考虑 GeoParquet，列式压缩、批量查询和数据湖生态更好。',
    sources: [
      { label: 'GeoParquet', url: 'https://geoparquet.org/' }
    ]
  },
  {
    id: 'duckdb_spatial_analytics',
    name: 'DuckDB Spatial Analytics',
    domain: '空间数据工程',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 90,
    summary: '在本地用 DuckDB Spatial 直接查询 Parquet/GeoParquet/CSV，完成轻量级空间统计和数据质检。',
    why: '求职软件和项目证据库都偏本地工作流，DuckDB Spatial 能在不搭 PostGIS 的情况下快速做空间数据分析。',
    actions: ['写一个 GeoParquet 面积统计 demo', '替换部分 Excel 空间统计脚本', '建立矢量质检 SQL 模板'],
    interview: '我会按规模选工具：轻量本地分析用 DuckDB Spatial，团队级服务再上 PostGIS 或云数仓。',
    sources: [
      { label: 'DuckDB Spatial extension', url: 'https://duckdb.org/docs/stable/core_extensions/spatial/overview' }
    ]
  },
  {
    id: 'titiler_dynamic_tiles',
    name: 'TiTiler Dynamic Raster Tiles',
    domain: '遥感服务化',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 88,
    summary: '把 COG、STAC 和栅格算法封装成动态瓦片服务，实现在线预览、渲染、指数计算和产品发布。',
    why: '遥感成果不能只停留在离线图件，在线瓦片服务能让养殖池塘、水色指数和断面溯源产品更像商用系统。',
    actions: ['设计 COG + TiTiler 预览链路', '增加指数渲染参数', '把专题图推送变成 URL 产品'],
    interview: '我会用 TiTiler 把遥感影像服务化：前端只请求瓦片，后端按需读取 COG 并动态渲染指数或分类结果。',
    sources: [
      { label: 'TiTiler docs', url: 'https://developmentseed.org/titiler/' }
    ]
  },
  {
    id: 'overture_maps_gers',
    name: 'Overture Maps / GERS',
    domain: '地图数据',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 83,
    summary: '开放地图数据和 Global Entity Reference System，为道路、建筑、POI 等实体提供稳定 ID 和统一 schema。',
    why: '遥感结果要和建筑、道路、行政区、兴趣点等底图实体联动，稳定实体 ID 有助于做数据融合和变化追踪。',
    actions: ['补建筑/道路底图融合卡', '研究 GERS 稳定 ID', '对接遥感提取图斑与开放地图实体'],
    interview: '遥感识别结果要进入业务系统，关键不只是检测到对象，还要和稳定地图实体、行政区和业务属性关联。',
    sources: [
      { label: 'Overture Maps', url: 'https://overturemaps.org/' }
    ]
  },
  {
    id: 'pmtiles_static_tile_delivery',
    name: 'PMTiles Static Tile Delivery',
    domain: '地图服务化',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 82,
    summary: '把矢量或栅格瓦片打包成单文件，通过静态对象存储分发，降低地图服务部署复杂度。',
    why: '求职作品集和遥感产品展示需要低成本部署，PMTiles 适合静态托管专题图和项目演示。',
    actions: ['把一个矢量图层转成 PMTiles', '测试静态托管地图展示', '比较 MBTiles/PMTiles/在线服务'],
    interview: '如果只是展示专题成果，我会考虑 PMTiles 这类静态瓦片方案，避免为一个演示系统维护完整地图服务器。',
    sources: [
      { label: 'PMTiles', url: 'https://pmtiles.io/' }
    ]
  },
  {
    id: 'spatiotemporal_feature_store',
    name: 'Spatiotemporal Feature Store',
    domain: '特征工程',
    horizon: '下一批',
    maturity: '新兴',
    relevance: 91,
    summary: '把水质、气象、影像指数、空间邻域、时间滞后和业务标签统一管理，服务预测、分类和溯源模型。',
    why: '你的水质 LSTM、污水厂优化、池塘识别和断面溯源都依赖时空特征；特征管理能把项目经验复用起来。',
    actions: ['定义时空特征 schema', '记录特征血缘和窗口', '把 LSTM 与遥感指数特征统一入库'],
    interview: '我会把模型前的数据准备沉淀成时空特征库，管理时间窗口、空间邻域、数据血缘和训练/推理一致性。',
    sources: [
      { label: 'STAC assets context', url: 'https://stacspec.org/en' },
      { label: 'GeoParquet', url: 'https://geoparquet.org/' }
    ]
  }
];

let added = 0;
for (const item of additions) {
  if (!seen.has(item.id)) {
    current.push(item);
    seen.add(item.id);
    added += 1;
  }
}

const prefix = 'const knowledgeRadar = ';
const start = source.indexOf(prefix);
const renderMarker = '\nconst radarFilterState =';
const renderStart = source.indexOf(renderMarker, start);
const end = renderStart === -1 ? -1 : source.lastIndexOf('\n]', renderStart);
if (start === -1 || end === -1 || renderStart === -1) {
  throw new Error('Unable to locate knowledgeRadar array boundary');
}

const beforeArray = source.slice(0, start);
const afterArray = source.slice(end + 2);
const nextSource = `${beforeArray}${prefix}${JSON.stringify(current, null, 4)};${afterArray}`;
fs.writeFileSync(path, nextSource, 'utf8');
console.log(JSON.stringify({ added, total: current.length }, null, 2));
