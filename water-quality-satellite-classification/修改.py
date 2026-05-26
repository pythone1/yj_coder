def Main_Classify(tifdata,pixelnum,bufdist):
    """
    对图像进行分块预测
    :param im: 图像的矩阵np.float
    :param pixelnum: 分块的大小int
    :param model: 用户选择的模型str
    :param outpath_visual: 可视化路径str
    :return: 存储预测结果只含0，1值的矩阵 np.int
    """
    rows, cols, _ = tifdata.dataarray.shape
    #向上取整
    xnum = math.ceil(cols / pixelnum)
    ynum = math.ceil(rows / pixelnum)
    for i in range(ynum):
        # 防止输入的图像过小裁剪行数只有1行（rows<=pixelnum）
        if ynum == 1:
            ylim = [0, rows]
            kernel_y = [0, rows]
        # 裁剪行数大于1行
        else:
            if i == 0:
                ylim = [0, pixelnum + bufdist]  # 向一定方向扩展按照缓冲距延伸 再进行分类
                kernel_y = [0, pixelnum]  # 在分类结果上只取核心范围kernel_x/y
            elif i == ynum - 1:
                ylim = [i * pixelnum - bufdist, rows]
                kernel_y = [i * pixelnum, rows]
            else:
                ylim = [i * pixelnum - bufdist, (i + 1) * pixelnum + bufdist]
                kernel_y = [i * pixelnum, (i + 1) * pixelnum]
        for j in range(xnum):
            # 防止输入的图像过小裁剪行数只有1行（rows<=pixelnum）
            if xnum == 1:
                xlim = [0, cols]
                kernel_x = [0, cols]
            else:  # 裁剪行数大于1列
                if j == 0:
                    xlim = [0, pixelnum + bufdist]  # 向一定方向扩展按照缓冲距延伸 再进行分类
                    kernel_x = [0, pixelnum]  # 在分类结果上只取核心范围kernel_x/y
                elif j == xnum - 1:
                    xlim = [j * pixelnum - bufdist, cols]
                    kernel_x = [j * pixelnum, cols]
                else:
                    xlim = [j * pixelnum - bufdist, (j + 1) * pixelnum + bufdist]
                    kernel_x = [j * pixelnum, (j + 1) * pixelnum]
            subdata = im[ylim[0]:ylim[1], xlim[0]:xlim[1], :]

            if np.max(subdata) > 0:

                #调用模型进行预测，'label_map'存储预测结果灰度图
                visual_result=model.predict(subdata)
                #多类识别
                result = visual_result['label_map']

                # #单类识别
                # bands = visual_result['score_map'].shape[2]
                # treshould = 0.6
                # #设置阈值
                # for i in range(bands):
                #     if i != 0:
                #         result = visual_result['score_map'][:, :, i]
                #         result[score > treshould] = 1
                #         result[score < treshould] = 0


                pdx.seg.visualize(subdata, visual_result, weight=0.5, save_dir=outpath_visual)

                result1[kernel_y[0]:kernel_y[1], kernel_x[0]:kernel_x[1]] = result[kernel_y[0] - ylim[0]:(kernel_y[0] - ylim[
                    0]) + (kernel_y[1] - kernel_y[0]), kernel_x[0] - xlim[0]:(kernel_x[0] - xlim[0]) + (
                            kernel_x[1] - kernel_x[0])]

    return result1