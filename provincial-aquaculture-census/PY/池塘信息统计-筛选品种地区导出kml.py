import geopandas as gpd
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import pandas as pd
import json


def _safe_to_str(val):
	"""把各种值安全地转成字符串（避免把对象/NaN 放入 description）"""
	if pd.isna(val):
		return ""
	if isinstance(val, (list, tuple, dict)):
		return json.dumps(val, ensure_ascii=False)
	return str(val)


def _create_description_text(row, skip=('geometry',)):
	"""把行的属性做成纯文本描述：每字段一行
    - 如果值为空则在前面空一行（特定字段会有空行）
    - 但"包保人员"字段例外，不加空行
    """
	cols = [c for c in row.index if c not in skip]
	lines = []
	# 定义需要添加空行的字段
	fields_with_blank = ['基础信息', '养殖情况', '上市计划', '养殖或退养计划']
	for c in cols:
		val = row[c]
		val_str = _safe_to_str(val).strip()  # 去掉空格
		# 判断是否需要空一行
		if val_str == "" and c not in ["包保人员"] and c in fields_with_blank:
			lines.append("")  # 空一行（对于特定字段）
		lines.append(f"{c}：{val_str}")  # 字段名保留
	return "\n".join(lines)


def _poly_to_kml_polygon(poly):
	"""把 shapely Polygon（含内环）转为 KML.Polygon"""
	outer = " ".join(f"{x},{y},0" for x, y in poly.exterior.coords)
	outer_el = KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(outer)))
	inner_els = []
	for interior in poly.interiors:
		inner = " ".join(f"{x},{y},0" for x, y in interior.coords)
		inner_els.append(KML.innerBoundaryIs(KML.LinearRing(KML.coordinates(inner))))
	return KML.Polygon(
		KML.extrude(0),
		KML.tessellate(1),
		KML.altitudeMode("clampToGround"),
		outer_el,
		*inner_els
	)


def writePolygons2kml(outfile, gdf, doc_name, fld_field, lbr_field):
	"""
    写出多边形 KML（只输出面，不生成点）
    outfile: 输出 kml 路径
    gdf: GeoDataFrame
    doc_name: 文档名称
    fld_field: 按哪个字段分文件夹
    lbr_field: 标签字段（例如 '图斑编号'）
    """
	print(f"写出kml多边形数量：{len(gdf)}")
	# 强制投影到 WGS84（KML 要经纬度）
	if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
		gdf = gdf.to_crs(epsg=4326)
	gdf = gdf.copy()
	geom_col = gdf.geometry.name
	attr_cols = [c for c in gdf.columns if c != geom_col]
	doc = KML.Document(KML.name(doc_name))
	# 定义两种样式：红色（退养）和亮蓝色（正常）
	# 红色样式（AABBGGRR格式）
	red_fill = "FF0000FF"  # 红色（不透明）
	red_line = "FF0000FF"  # 红色（不透明）
	style_red = KML.Style(
		KML.PolyStyle(KML.color(red_fill), KML.fill(1), KML.outline(1)),
		KML.LineStyle(KML.color(red_line), KML.width(1.2)),
		id="style_red"
	)
	doc.append(style_red)
	# 亮蓝色样式（AABBGGRR格式）
	blue_fill = "FFFFBF00"  # 亮蓝色（不透明）
	blue_line = "FFFFBF00"  # 亮蓝色（不透明）
	style_blue = KML.Style(
		KML.PolyStyle(KML.color(blue_fill), KML.fill(1), KML.outline(1)),
		KML.LineStyle(KML.color(blue_line), KML.width(1.2)),
		id="style_bright_blue"
	)
	doc.append(style_blue)
	# 按 fld_field 分文件夹
	for fld_value, sub in gdf.groupby(fld_field):
		folder = KML.Folder(KML.name(str(fld_value)))
		for _, row in sub.iterrows():
			geom = row.geometry
			if geom is None or geom.is_empty:
				continue
			# 只处理 Polygon / MultiPolygon
			polys = []
			if geom.geom_type == "Polygon":
				polys = [geom]
			elif geom.geom_type == "MultiPolygon":
				polys = list(geom.geoms)
			else:
				continue
			# 预生成 description 文本与 ExtendedData（每个属性一个 Data）
			desc_text = _create_description_text(row, skip=(geom_col,))
			extdata_children = []
			for c in attr_cols:
				extdata_children.append(KML.Data(KML.value(_safe_to_str(row[c])), name=str(c)))
			extdata_el = KML.ExtendedData(*extdata_children) if extdata_children else None
			# 根据"是否退养"列选择样式
			is_retired = _safe_to_str(row.get("是否退养", "")).strip()
			style_id = "#style_red" if is_retired == "退养" else "#style_bright_blue"
			for poly in polys:
				kml_poly = _poly_to_kml_polygon(poly)
				# Placemark：name（图斑编号）、description（纯文本换行）、ExtendedData、样式、Polygon
				elements = [
					KML.name(_safe_to_str(row.get(lbr_field, ""))),
					KML.description(desc_text),
				]
				if extdata_el is not None:
					elements.append(extdata_el)
				elements.append(KML.styleUrl(style_id))  # 动态选择样式
				elements.append(kml_poly)
				placemark = KML.Placemark(*elements)
				folder.append(placemark)
		doc.append(folder)
	# 写出文件
	with open(outfile, "wb") as f:
		f.write(etree.tostring(doc, pretty_print=False, xml_declaration=False, encoding="utf-8"))


if __name__ == "__main__":
	gdf = gpd.read_file(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\output.gpkg')
	writePolygons2kml(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\ponds2.kml", gdf, "池塘分布",
	                  "所在镇村（镇街+村）", "图斑编号")