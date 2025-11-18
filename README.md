# 项目 Python 文件用途一览

| 序号 | 类名 | 用途 |
| ---- | ---- | ---- |
| 1 | PointElevationUpdater | 为点要素批量赋予DEM高程(Z值)，支持文件夹批处理多个Shapefile，自动处理坐标系不一致并重投影，输出三维Shapefile与GeoJSON，内置日志系统与tqdm进度条，使用rasterio.sample进行高性能栅格采样。 |
