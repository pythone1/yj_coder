import sys
import snappy

def readS1ZipFile(filename):
    '''
    将压缩包的原始文件读取为snap里的 product对象
    :param filename: str 原始数据文件 *.zip
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tReading Sentinel-1 zip file...')
    s1_product = snappy.ProductIO.readProduct(filename)

    return s1_product

def subsetToGeoRegion(product,wkt):
    '''
    按地理坐标范围裁剪
    :param product: org.esa.snap.core.datamodel.Product
    :param wkt: The subset region in geographical coordinates using WKT-format,
    e.g. POLYGON((<lon1> <lat1>, <lon2> <lat2>, ..., <lon1> <lat1>))
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tSubset...')
    params = snappy.HashMap()
    params.put('copyMetadata', True)
    params.put('geoRegion', wkt)
    results = snappy.GPF.createProduct('Subset', params, product)

    return results

def subsetToRectangle(product, rectangle):
    '''
    按矩形框裁剪
    :param product:
    :param rectangle: list [起始列坐标,起始行坐标,宽度,高度]
    :return:
    '''
    print('\tSubset...')
    x, y, width, height = rectangle
    params = snappy.HashMap()
    params.put('copyMetadata', True)
    params.put('region', '%s,%s,%s,%s' % (x, y, width, height))

    # 执行裁剪操作
    results = snappy.GPF.createProduct('Subset', params, product)

    return results

def applyOrbitFile(product):
    '''
    轨道校正
    :param product: org.esa.snap.core.datamodel.Product
    :return: orb org.esa.snap.core.datamodel.Product 处理后的对象
    '''
    print('\tApply orbit file...')
    # 参数设置
    params = snappy.HashMap()
    params.put('orbitType', 'Sentinel Precise (Auto Download)')
    params.put('continueOnFail', True)
    params.put('polyDegree', 3)

    # 执行轨道校正操作
    results = snappy.GPF.createProduct('Apply-Orbit-File', params, product)

    return results

def removeThermalNoise(product):
    '''
    去除热噪声
    :param product: org.esa.snap.core.datamodel.Product
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tRemove thermal noise...')
    # 参数设置
    params = snappy.HashMap()
    params.put('removeThermalNoise', True)

    # 执行热噪声剔除
    results = snappy.GPF.createProduct('ThermalNoiseRemoval', params, product)

    return results

def radioCalibration(product):
    '''
    辐射校正
    :param product: org.esa.snap.core.datamodel.Product
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tRadio calibration...')
    params = snappy.HashMap()
    params.put('outputSigmaBand', True)
    params.put('sourceBands', 'Intensity_VH,Intensity_VV')
    params.put('selectedPolarisations', 'VH,VV')

    # 执行操作
    results = snappy.GPF.createProduct('Calibration', params, product)

    return results

def speckleFilter(product):
    '''
    斑点滤波（相干斑滤波）
    :param product: org.esa.snap.core.datamodel.Product
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tSpeckle filtering...')
    params = snappy.HashMap()
    params.put('filter', 'Lee Sigma')
    params.put('filterSizeX', 5)  # The kernel x/y dimension
    params.put('filterSizeY', 5)

    results = snappy.GPF.createProduct('Speckle-Filter', params, product)

    return results

def terrainCorrection(product):
    '''
    地形校正
    :param product: org.esa.snap.core.datamodel.Product
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tTerrain correction...')
    params = snappy.HashMap()
    params.put('demName', 'SRTM 3Sec')
    params.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    params.put('pixelSpacingInMeter', 10.0)
    params.put('mapProjection', 'WGS84(DD)')
    params.put('nodataValueAtSea', False)
    params.put('saveSelectedSourceBand', True)

    results = snappy.GPF.createProduct('Terrain-Correction', params, product)

    return results

def linearToFromdB(product):
    '''
    分贝化
    :param product: org.esa.snap.core.datamodel.Product
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tLining_to_db...')
    params = snappy.HashMap()

    results = snappy.GPF.createProduct('LinearToFromdB', params, product)

    return results

def write2File(filename,product,format='GeoTIFF'):
    '''
    写出
    :param filename: str
    :param product: org.esa.snap.core.datamodel.Product
    :param format: str
    :return: None
    '''
    print("Writing...")
    # 不支持更新数据
    incremental = False
    snappy.GPF.writeProduct(product, snappy.File(filename), format, incremental, snappy.ProgressMonitor.NULL)

def sliceMosaic(product_list):
    '''
    多幅图像镶嵌/拼接
    :param product_list: list[org.esa.snap.core.datamodel.Product]
    :return: org.esa.snap.core.datamodel.Product
    '''
    # 创建一个product数组
    products = snappy.jpy.array('org.esa.snap.core.datamodel.Product',len(product_list))
    for i in range(len(product_list)):
        products[i] = product_list[i]

    params = snappy.HashMap()
    results = snappy.GPF.createProduct('SliceAssembly',params,products)

    return results

def GRDPreprocess(file_list,savefile,subsetregion=None):
    '''
    GRD产品预处理，保存为geotiff文件
    :param file_list: list[str]
    :param savefile: str 保存文件
    :param subsetregion: wkt格式的文本 或 [起始列,起始行,宽度,高度] 或None
    :return: None
    '''
    # 开始预处理
    product_list = []
    for i in range(len(file_list)):
        # 读
        print(file_list[i])
        s1_read = readS1ZipFile(file_list[i])
        if subsetregion:
            # 裁剪
            if isinstance(subsetregion,list):
                s1_read = subsetToRectangle(s1_read,subsetregion)
            elif isinstance(subsetregion,str):
                s1_read = subsetToGeoRegion(s1_read,subsetregion)
        # 去除热噪声
        thermalremoved = removeThermalNoise(s1_read)
        # 轨道校正
        applyorbit = applyOrbitFile(thermalremoved)
        # 辐射定标
        calibrated = radioCalibration(applyorbit)
        product_list.append(calibrated)
    # 镶嵌
    if len(product_list) == 1:
        assembly = product_list[0]
    else:
        assembly = sliceMosaic(product_list)
    del thermalremoved, applyorbit, calibrated
    # 斑点滤波
    filtered = speckleFilter(assembly)
    # 地形校正
    terrain_corrected = terrainCorrection(filtered)
    del filtered
    # 分贝化
    db = linearToFromdB(terrain_corrected)
    del terrain_corrected
    # 写为tif
    write2File(savefile,db,format='GeoTIFF')


filegroup = sys.argv[1]
savefile = sys.argv[2]
subsetregion = sys.argv[3]

# file_list = filegroup.split(',')
# GRDPreprocess(file_list, savefile, subsetregion)

# filegroup = 'P:\\imgdata\\GRD\\S1A_IW_GRDH_1SDV_20230409T095531_20230409T095556_048018_05C585_7246.zip'
# savefile = 'P:\\imgdata\\DB\\s1_csar_grd_20230409_20230409_20230421T154957_E121N32.tif'
# subsetregion = 'POLYGON ((121.505449 32.016585, 121.513942 31.983291, 121.555128 31.996425, 121.552314 32.028828, 121.505449 32.016585))'

# file_list = filegroup.split(',')
# GRDPreprocess(file_list, savefile, subsetregion)

















