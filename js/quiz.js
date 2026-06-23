const quizData = [
    // ==========================================
    // 1. 机器学习 (ml)
    // ==========================================
    {
        id: "ml_q1",
        category: "ml",
        question: "请对比随机森林 (Random Forest) 和 XGBoost 的异同，并说明它们分别在什么场景下表现更好？",
        difficulty: "medium",
        intent: "考察候选人对 Bagging 和 Boosting 两大集成学习家族核心差异的理解，以及实际场景下的模型选型能力。",
        key_points: "Bagging vs. Boosting, 偏差与方差的数学本质, 并行化原理, 对异常值敏感度",
        model_answer: "1. **算法机制**：Random Forest 基于 Bagging，树与树之间相互独立并行生成，最终通过投票或均值融合；XGBoost 基于 Boosting，采用串行递推，每棵新树都在拟合先前所有树的残差。\n2. **偏差与方差**：Random Forest 通过平均多棵树的结果，主要用于降低模型方差（Variance）；XGBoost 通过一步步逼近目标，主要用于降低模型偏差（Bias），配合正则项也较好地控制了方差。\n3. **并行计算**：Random Forest 天然支持样本和特征级的并行训练；XGBoost 虽然是串行的树生成，但在单棵树的分裂特征寻找上（直方图/预排序）实现了多线程并行计算。\n4. **数据敏感性**：Random Forest 对噪点和异常值极不敏感，不易过拟合；XGBoost 对噪点相对敏感，因为每一步都在拟合未被分类对的残差，需精细调节正则参数（lambda/gamma）和学习率。\n5. **选型场景**：数据含有较多噪点、标量缺失，且没有时间精力深度调参时，首选 Random Forest；若追求极致的预测精度，且数据清洗质量高、特征工程完善，首选 XGBoost 或 LightGBM。",
        traps: "避坑：误认为 XGBoost 的树是并行生成的。XGBoost 树是串行迭代的，并行仅体现在节点分裂寻找特征增益时的特征并行上。"
    },
    {
        id: "ml_q2",
        category: "ml",
        question: "什么是偏差-方差权衡 (Bias-Variance Tradeoff)？如何通过特征工程和模型设计进行优化？",
        difficulty: "easy",
        intent: "评估候选人对统计学习基础理论的掌握程度，以及解决过拟合（高方差）和欠拟合（高偏差）的实操经验。",
        key_points: "泛化误差分解, 过拟合与欠拟合, 正则化, 交叉验证",
        model_answer: "1. **定义**：模型的泛化误差可以分解为：误差 = 偏差² + 方差 + 噪声。偏差度量了模型期望预测与真实结果的偏离程度（代表拟合能力）；方差度量了在不同训练集上模型预测的变化波动（代表稳定性）。两者此消彼长。\n2. **高偏差（欠拟合）优化**：\n   - **特征层面**：增加特征维度，提取非线性交叉特征，做多项式扩展。\n   - **模型层面**：增加模型复杂度（如将线性模型换成神经网络/树模型），减少正则化惩罚参数。\n3. **高方差（过拟合）优化**：\n   - **特征层面**：进行特征选择（去噪），使用 PCA/LDA 降维。\n   - **数据层面**：增加训练样本量，或使用数据增强（如遥感影像翻转、缩放）。\n   - **模型层面**：引入 L1/L2 正则化，加入 Dropout，限制决策树深度，使用 Bagging 集成算法。",
        traps: "避坑：忽略噪声（Noise）这一不可消除的随机项。混淆 L1（产生稀疏权重）和 L2（使权重趋于均等的小值）在控制方差时的不同作用。"
    },
    {
        id: "ml_q3",
        category: "ml",
        question: "SVM 为什么要引入拉格朗日对偶性？核函数是如何将不可分问题转化为可分问题的？",
        difficulty: "hard",
        intent: "深入考察数学功底，特别是约束优化问题和核空间映射的数学本质。",
        key_points: "拉格朗日对偶, 强对偶性(KKT条件), 内积计算, 核函数高维映射",
        model_answer: "1. **引入对偶性的原因**：\n   - **简化约束**：原问题带有不等式约束，通过拉格朗日对偶性转化为无约束极值问题，更易求解。\n   - **引入核技巧**：对偶问题化简后，其优化目标和决策函数只包含样本向量之间的**内积（$x_i^T x_j$）**。这使得我们可以直接用核函数代替内积，而无需显式计算出高维空间映射后的向量，极大地节省了计算开销。\n   - **计算维度友好**：当样本维度 $d$ 远大于样本量 $N$ 时，对偶问题的求解效率更高。\n2. **核函数的作用**：根据 Cover 定理，将复杂的非线性不可分特征通过非线性映射 $\\Phi(x)$ 投影到更高维的空间中，数据变为线性可分的概率大幅提高。核函数 $K(x_i, x_j) = \\langle\\Phi(x_i), \\Phi(x_j)\\rangle$ 允许我们在低维空间直接算出高维投影的内积，避开了“维度灾难”。",
        traps: "避坑：不要背错对偶变换的极大极小值顺序（原问题是先 minimize w 再 maximize alpha；对偶问题是先 maximize alpha 再 minimize w，且需满足 KKT 条件）。"
    },
    {
        id: "ml_q4",
        category: "ml",
        question: "请对比三大主流梯度提升框架 XGBoost、LightGBM 和 CatBoost 的底层区别？",
        difficulty: "hard",
        intent: "考查大厂算法岗中，对常用树模型工具包内部优化算法和数学实现的横向辨析能力。",
        key_points: "直方图算法, GOSS与EFB, 对称树, 类别特征Target Encoding",
        model_answer: "1. **分裂寻找算法**：XGBoost 默认支持 Pre-sorted 算法，精度高但计算慢，后支持直方图；LightGBM 原生引入直方图（Histogram-based）算法将连续特征分桶，极大提升速度并降低内存。\n2. **样本/特征采样**：LightGBM 使用 GOSS（单边梯度采样，保留大梯度，对小梯度采样）和 EFB（互斥特征捆绑）减少计算维度；XGBoost 主要使用特征子抽样和样本行采样。\n3. **树结构生成**：XGBoost 采用 Level-wise 按层生长；LightGBM 采用 Leaf-wise 按叶子分裂，精度更高但需要配合最大深度以防过拟合；CatBoost 采用对称树（Oblivious Trees），同一层分裂特征相同，推理速度极快且防过拟合。\n4. **类别特征支持**：CatBoost 拥有最强类别特征支持，引入 Ordered Target Statistics（排序目标统计值）计算均值编码，并防止靶向泄露；而 XGBoost 需要 One-hot 或外部类别编码；LightGBM 采用基于直方图的分桶类别特征表达。",
        traps: "避坑：很多候选人只知道 CatBoost 快，实际上如果类别特征不多，LightGBM 和 XGBoost 训练速度可能反而更快。必须指出 CatBoost 最核心的贡献是对“类别特征目标泄露问题”的数学解决。"
    },
    {
        id: "ml_q5",
        category: "ml",
        question: "K-Means 聚类时，如何确定最优的 K 值？面对非凹形状地物数据，你会如何改进聚类方案？",
        difficulty: "medium",
        intent: "评估候选人对无监督学习模型诊断和应对非线性/复杂空间数据时的聚类设计思路。",
        key_points: "手肘法(SSE), 轮廓系数, 密度聚类DBSCAN, 谱聚类",
        model_answer: "1. **K值确定方法**：\n   - **手肘法 (Elbow Method)**：计算不同 K 值下的簇内误差平方和（SSE），绘制 K-SSE 曲线。当 K 增加到某值时，SSE 下降斜率突然变平缓，该转折点即为“手肘”，作为最优 K。\n   - **轮廓系数 (Silhouette Coefficient)**：计算样本与同簇和异簇的平均距离，范围为 $[-1, 1]$。轮廓系数越接近 1，代表聚类越合理，通常选取平均轮廓系数最大的 K。\n2. **处理非凹/非球状边界（如遥感带状河流、环状绿植分布）**：\n   - **改用 DBSCAN**：密度聚类不依赖球形假设，而是根据高密度连通性聚类，能自动拟合任意弯曲的复杂地物形态。\n   - **谱聚类 (Spectral Clustering)**：利用图论方法计算样本的邻接矩阵和拉普拉斯矩阵，将样本映射到低维特征空间再执行 K-Means，能有效分离流形数据。\n   - **使用核 K-Means**：引入核函数映射，使得在低维空间非线性的边界，映射到高维空间后可以用超平面分割。",
        traps: "避坑：不要只讲手肘法。在某些实际业务中，SSE 曲线手肘可能极不明显，必须补充轮廓系数法或结合实际业务先验来定 K。"
    },
    {
        id: "ml_q6",
        category: "ml",
        question: "对比主成分分析 (PCA) 与 t-SNE、UMAP 的底层降维逻辑，并说明为什么 t-SNE 不适合作为特征工程的降维器？",
        difficulty: "hard",
        intent: "深度考察候选人对特征工程中维度缩减算法的统计学和流形学习本质的理解。",
        key_points: "PCA 线性映射, t-SNE KL散度, 局部/全局拓扑, 归纳学习与转导学习",
        model_answer: "1. **底层降维逻辑**：\n   - **PCA** 是线性降维，寻找最大化全局投影方差的正交基，通过奇异值分解（SVD）解算。\n   - **t-SNE** 是非线性流形学习。高维空间采用高斯概率度量邻域，低维采用 t 分布，通过梯度下降最小化两者的 KL 散度（Kullback-Leibler Divergence），极其强调局部邻域的保真性。\n   - **UMAP** 基于拓扑结构，利用模糊单纯复形和交叉熵计算，兼顾局部和全局距离，比 t-SNE 快数倍。\n2. **t-SNE 不适合特征工程的原因**：\n   - **无法外推新数据**：t-SNE 是转导学习（Transductive Learning），没有学出一个显式的投影映射函数。当有新的测试数据到来时，你无法像 PCA 一样直接乘以矩阵降维，必须把所有数据拼在一起重新运行整个算法。\n   - **全局距离丢失**：t-SNE 中簇与簇之间的空间距离没有实际物理意义，因为它只保局部邻域，不能直接用来进行欧氏距离分类。\n   - **计算极其缓慢**：时间复杂度高达 $O(N^2)$，面对海量实时数据工程不可行。",
        traps: "避坑：不要忽略“转导学习”这一致命缺点。这是为什么 t-SNE 只被用于“降维可视化展示”，而极少用于“机器学习训练特征提取管线”的数学本质。"
    },

    // ==========================================
    // 2. 深度学习与Transformer (dl_transformer)
    // ==========================================
    {
        id: "dl_q1",
        category: "dl_transformer",
        question: "请详细解释 Self-Attention 中的 $Q$, $K$, $V$ 的物理含义，以及为什么计算点积相似度后要除以 $\\sqrt{d_k}$？",
        difficulty: "medium",
        intent: "这是深度学习面试中最高频的问题之一，用于测试候选人对 Transformer 核心数学机制的深度细节理解。",
        key_points: "$Q$/$K$/$V$ 投影空间, 点积相似度, 梯度消失, Softmax 饱和区",
        model_answer: "1. **物理含义**：\n   - $Q$ (Query)：当前 Token 主动发出的“寻回请求”，代表当前位置想寻找什么样的上下文信息。\n   - $K$ (Key)：每个 Token 暴露出来的“检索标签”，用于匹配其他 Token 的 Query。\n   - $V$ (Value)：Token 真正包含的“实质内容”。通过 $Q$ 和 $K$ 计算相似度权重后，对 $V$ 进行加权求和，实现信息汇聚。\n2. **为什么要除以 $\\sqrt{d_k}$**：\n   - 假设 $Q$ 和 $K$ 中的元素是独立同分布且均值为 0、方差为 1 的随机变量。它们点积 $q \\cdot k = \\sum_{i=1}^{d_k} q_i k_i$ 的均值为 0，方差会随着维度 $d_k$ 增长而增大到 $d_k$。\n   - 若不除以 $\\sqrt{d_k}$，当维度较大时，点积的值绝对值会非常大，送入 Softmax 函数后，大值对应的概率趋近于 1，其余趋近于 0。这导致 Softmax 的输出变成极端的 one-hot 向量，且该区域**导数极小（梯度饱和）**，从而引发梯度消失，导致模型无法训练。\n   - 除以 $\\sqrt{d_k}$ 能将方差缩回 1，使 Softmax 计算平滑，梯度流动稳定。",
        traps: "避坑：不要混淆 $d_k$（单个头的特征通道数）和 $d_{model}$（模型总隐藏维度）。计算缩放时，使用的是单头的维度 $d_k$。"
    },
    {
        id: "dl_q2",
        category: "dl_transformer",
        question: "LayerNorm 和 BatchNorm 的区别是什么？为什么 Transformer 架构选择 LayerNorm 而不是 BatchNorm？",
        difficulty: "medium",
        intent: "考察对归一化方法的透彻理解，以及在特定数据模态下算法选择的逻辑推理能力。",
        key_points: "归一化维度轴, 变长序列处理, 局部特征相关性, 训练推理一致性",
        model_answer: "1. **计算轴的区别**：\n   - **BatchNorm** 在一个 Batch 的单个特征通道内（跨样本，即沿 N, H, W 轴）计算均值方差；\n   - **LayerNorm** 在单个样本的所有通道上（跨特征，即沿 C, H, W 或 SeqLen, HiddenDim 轴）计算均值方差。\n2. **Transformer 选择 LayerNorm 的原因**：\n   - **文本变长问题**：NLP 任务中每个句子的长度通常不同。BatchNorm 跨样本归一化时，长句子后面的 Padding 部分会导致统计数据失真。而 LayerNorm 对每个样本独立归一化，与序列长度无关。\n   - **推理阶段的稳定性**：BatchNorm 推理时需要使用训练阶段累计的全局均值和方差，如果测试数据分布突变，预测就会失控。LayerNorm 在推理时依然只依赖当前样本自身计算均值方差，泛化更稳定。\n   - **语义独立性**：大模型中每个 Token 在不同句子中的语义是独立的，LayerNorm 有利于保持单个序列中各 Token 表示的特征缩放平衡。",
        traps: "避坑：要明确指出在三维 Tensor $(BatchSize, SeqLen, HiddenDim)$ 上，LayerNorm 归一化的具体计算维度是最后一个维度 $HiddenDim$。"
    },
    {
        id: "dl_q3",
        category: "dl_transformer",
        question: "如何解决极深神经网络中的梯度消失与梯度爆炸问题？从架构设计和训练策略两方面回答。",
        difficulty: "hard",
        intent: "测试候选人在深度学习系统优化上的综合技术积累。",
        key_points: "残差连接(Residual Connections), 门控机制, 梯度裁剪, 权重初始化, Pre-LN 结构",
        model_answer: "1. **架构设计层面**：\n   - **残差连接 (Residual Joint)**：通过 $y = x + F(x)$ 机制，使反向传播时的梯度项包含一个常数项 1，允许梯度越过复杂的非线性层直接回传，打通极深网络的训练路径。\n   - **Pre-LN 改进**：将 LayerNorm 移至残差分支内部（即对输入先归一化，再进 Attention/FFN，最后加残差）。这保证了梯度直接回传路径的畅通，防止了深层梯度随层数加深而呈指数衰减。\n   - **门控激活函数**：如 GeLU, SwiGLU，替代饱和激活函数（Sigmoid/Tanh）。\n2. **训练策略层面**：\n   - **权重初始化**：使用 Xavier 或 Kaiming 初始化，保证前向和反向传播时的方差稳定，避免初始化阶段就发生梯度爆炸。\n   - **梯度裁剪 (Gradient Clipping)**：设定阈值，当计算出的梯度 L2 范数超过阈值时，进行等比例缩放（`clip_grad_norm_`），这是防止训练崩塌的硬防线。\n   - **学习率 Warmup**：训练初期使用极小的学习率，随着模型逐步稳定再提升学习率，有效缓冲初始参数剧烈变化带来的数值不稳定。",
        traps: "避坑：误以为 Residual Connection 只能解决梯度消失。实际上，通过维持恒等梯度流，它同时对由于权重乘积链式累积导致的梯度爆炸也有极强的稳定作用。"
    },
    {
        id: "dl_q4",
        category: "dl_transformer",
        question: "为什么旋转位置编码 (RoPE) 在长文本外推上显著优于传统绝对绝对位置编码？",
        difficulty: "hard",
        intent: "考查候选人对大模型位置编码底层数学以及相对位置关联性的推导深度。",
        key_points: "复数空间旋转, 相对位置差, 线性外推性, 频率插值",
        model_answer: "1. **底层数学逻辑**：RoPE 通过构建 2D 旋转矩阵，将查询（Query）和键（Key）向量两两分组，按照位置 $m$ 和对应频率角度 $\\theta_i$ 进行旋转。它的精妙之处在于，旋转后计算 $Q_m^T K_n$ 时，通过复数内积的几何变换，绝对位置自变量 $m$ 和 $n$ 被抵消，最终点积只依赖于它们的相对位置差 $(m-n)$。\n2. **外推性优越的原因**：\n   - **绝对编码的限制**：传统的绝对位置编码（如正弦波形或可学习编码）在超出预训练长度（如 4k）后，超出部分的编码是未定义或模型从未见过的，网络会彻底混乱。\n   - **相对平滑性**：RoPE 具有天然的相对距离衰减性——即距离越远的 Token，旋转后的相似度内积分数趋向于 0。在长上下文外推时，我们可以通过“位置插值（Position Interpolation）”，把更大范围的位置坐标（如 0-32k）缩放到原预训练位置的频率范围（如 0-4k），配合少量微调即可支持数十倍的长文本外推。",
        traps: "避坑：答题时必须提到“内积空间中绝对位置被抵消，退化为仅包含相对位置 $(m-n)$”这一物理精髓，否则说明没有从数学公式层面理解 RoPE。"
    },
    {
        id: "dl_q5",
        category: "dl_transformer",
        question: "请详述 FlashAttention 优化显卡 HBM 和 SRAM 读写的底层逻辑，为什么它能节省大量显存？",
        difficulty: "hard",
        intent: "考察对硬件感知算法设计 (Hardware-aware Algorithm Design) 的认识，属于深度大模型工程优化的高级考点。",
        key_points: "SRAM与HBM吞吐限制, 分块计算(Tiling), 在线Softmax更新, 减少IO读写",
        model_answer: "1. **硬件底座痛点**：在传统注意力计算中，中间矩阵 $S = Q K^T \\in \\mathbb{R}^{L \\times L}$ 和 $A = softmax(S)$ 尺寸极大，必须写回到高延迟的 GPU 显存（HBM，高带宽显存）中。然后，计算加权 Value 时，又需要重新从 HBM 中读取 $A$。这种高频的内存 IO 读写速度（Bandwidth-bound）远远落后于显卡的算力（Compute-bound），限制了训练吞吐量。\n2. **优化核心：分块计算 (Tiling)**：\n   - FlashAttention 将 $Q, K, V$ 矩阵划分成多个小 Tiles（分块），加载到 GPU 内部的高速 SRAM 缓存中。\n   - **在线 Softmax (Online Softmax) 更新**：由于 Softmax 计算分母依赖全局指数累加和 $\\sum e^{x_i}$，传统的块计算会丢失全局分母。FlashAttention 引入了一个数学修正技巧：在分块读取计算时，维护并更新当前的局部最大值 $m^{(i)}$ 和累加和 $d^{(i)}$。当读取完下一分块时，将上一块的分数乘以归一化缩放系数 $e^{m^{(i-1)} - m^{(i)}}$ 自动修正。这使得它可以在不写回大矩阵 $A$ 的情况下，在线精确完成注意力求和计算。\n3. **结果**：中间矩阵 $A$ 的显存开销从 $O(L^2)$ 暴减为 $O(L)$（只保留块大小的内存），极大释放了显存，且计算耗时减半。",
        traps: "避坑：不要以为 FlashAttention 减少了计算量（FLOPs）。事实上，它的 FLOPs 数量由于需要在线修正更新 Softmax，甚至比传统 Attention 还要多一点。它的速度提升完全来自于“大幅减少了显存 HBM 与 SRAM 之间的数据拷贝 IO 延迟”。"
    },
    {
        id: "dl_q6",
        category: "dl_transformer",
        question: "多查询注意力 (MQA) 和分组查询注意力 (GQA) 的核心出发点是什么？它们如何降低大模型推理显存瓶颈？",
        difficulty: "hard",
        intent: "针对 LLM 推理优化和降本增效的核心工程考点，考查对 KV Cache 资源瓶颈的掌控。",
        key_points: "自回归推理, KV Cache, 显存带宽限制, GQA 架构优势",
        model_answer: "1. **核心出发点**：自回归解码（Generation）是逐个 Token 生成的，必须在内存中缓存历史所有 Token 的 $K$ 和 $V$ 向量以避免重复计算（KV Cache）。当并发用户数（Batch Size）较大且上下文较长时，KV Cache 会迅速吃光显存（例如 70B 模型单个并发 4k 上下文的 KV Cache 就达数 GB）。此时，GPU 算力过剩，但**显存读取带宽（Memory Bandwidth）成为瓶颈**。\n2. **架构优化机制**：\n   - **MHA (多头注意力)**：每个 $Q$ 头都有自己对应的 $K, V$ 头。数据搬运开销极大。\n   - **MQA (多查询)**：彻底精简，让所有 $Q$ 头共同使用仅有的 1 组 $K, V$ 头。这使得 KV Cache 的显存占用直接降低到原来的 $1/HeadNum$。但由于共享过多，导致模型损失了对复杂长文本的表达能力，容易出现事实胡说八道。\n   - **GQA (分组查询)**：折中黄金方案。将 $Q$ 头分成 $G$ 组（例如 8 组），每组内的几个 $Q$ 头共享该组的 1 组 $K, V$ 头。它比 MQA 具备更好的语义信息表达，同时能将 KV Cache 带宽读取开销缩减至原来的 $G/HeadNum$（通常为 1/8），QPS 并发量可提升数倍。",
        traps: "避坑：必须明确指出这一优化专门针对的是“自回归推理阶段（Autoregressive Decode）”，因为预训练阶段（Prefill）是可以并行计算的，KV Cache 显存瓶颈只在逐词生成的推理阶段爆发。"
    },

    // ==========================================
    // 3. 大模型与RAG (llm_rag)
    // ==========================================
    {
        id: "llm_q1",
        category: "llm_rag",
        question: "请设计一个完整的企业级 RAG 检索管线，如何解决向量检索“召回精度不足”和“大模型读取冗余上下文”的问题？",
        difficulty: "hard",
        intent: "评估候选人对生产级 RAG 方案的设计能力，而非套用简单 LangChain 教程的玩具项目。",
        key_points: "混合检索(Hybrid Search), Query 重写(HyDE), 交叉编码器重排(Rerank), 滑动窗口分块, Prompt 瘦身",
        model_answer: "1. **双阶段检索架构 (Retrieval + Rerank)**：\n   - **粗筛阶段**：采用 **混合检索 (Hybrid Search)**。一方面使用 Dense Embedding (如 OpenAI text-embedding-3 或 BGE-large) 提取语义特征，在 Qdrant 数据库中做 HNSW 检索；另一方面使用 Sparse Vector (BM25) 进行精确关键词匹配。两路结果使用倒数排名融合 (RRF) 合并，筛选前 50 个 Chunk，以防特定行业术语和代码型号漏检。\n   - **细筛与重排阶段**：使用 Cross-Encoder 重排器（如 **BGE-Reranker-Large**）对粗筛出的 50 个 Chunk 与原始 Query 计算深度交互相似度，输出得分最高的 5-10 个 Chunk。这有效滤除了检索器产生的语义噪音，极大提高了精确率。\n2. **Query 优化（降低语义偏差）**：\n   - **Query 重写**：通过 LLM 将用户多轮对话中的指代词、省略词重构为独立含义的查询句。\n   - **假设性文档生成 (HyDE)**：让 LLM 根据 Query 先盲写一篇“假回答”，用这个假回答去库里检索，利用回答与回答之间的相似度，往往能大幅提升检索精准度。\n3. **上下文瘦身（解决长文本大模型注意力稀释）**：\n   - **父子分块 (Parent-Child Chunking)**：检索时基于 200 字的小 Child 块匹配，送入大模型时，自动替换为包含它、且带有完整上下文的 1000 字 Parent 块。\n   - **Prompt 压缩**：使用 LLMLingua 等工具对检索出的 Chunk 进行语法熵计算，剔除停用词和冗余修饰，保留核心语义输入给 LLM，既节约 Token 又防止模型注意力分裂。",
        traps: "避坑：不要只讲 API 调用。必须指出单塔模型（Bi-Encoder，检索快精度一般）与双塔交叉模型（Cross-Encoder，检索慢但精度极高）在不同阶段的应用分工。"
    },
    {
        id: "llm_q2",
        category: "llm_rag",
        question: "什么是 Nous Hermes 3 架构？在 Agent 智能体开发中，如何基于它实现智能体的“自适应技能进化”？",
        difficulty: "hard",
        intent: "考察候选人对时下最新开源 Agent 架构以及 Hermes 3 模型特性的追踪和实战理解。",
        key_points: "Nous Hermes 特性, 智能体进化循环, Skill 抽象与持久化, ReAct 规划机制",
        model_answer: "1. **Nous Hermes 3 模型特性**：Nous Research 针对 Llama 3.1 等开源底座进行的深度对齐微调模型。其对复杂系统提示词（System Prompt）的遵从度极高，拥有原生强大的 XML Tag 级多步函数调用（Function Calling）以及极度诚实的拒绝回答机制，是目前最适合运行本地 AI Agent 的模型。\n2. **自适应技能进化 (Self-Evolution Skill Engine) 设计**：\n   - **闭环系统设计**：当 Agent 接收到复杂任务（如：'从遥感大图中提取目标并转成 CGCS2000 坐标系的 Shapefile'），它会通过 ReAct 循环分解步骤。\n   - **自主写码与执行**：Agent 在本地沙箱中编写 Python 脚本，调用 GDAL 和 Proj 库进行计算和格式转换，并自动通过 Terminal 执行与自我纠错。\n   - **技能抽象并归档 (Skill Saving)**：一旦任务成功跑通并通过验证，Agent 触发一个“技能提炼”动作，提取此任务中编写的最关键、高复用性的核心函数，自动为其编写注释和规范文档，以 `.py` 文件形式写入本地磁盘的 `skills/` 文件夹中。\n   - **重用与自增**：在未来的任务中，Agent 优先检索 `skills/` 目录下的元数据。一旦匹配，直接在内存中 `import` 动态加载，跳过重新构思和编码阶段，从而实现自我进化。",
        traps: "避坑：不要把 Hermes 混淆为只有 RAG 功能的模型。它是大语言模型，而自进化智能体架构是 Nous 社区基于该模型开发的 Agent 方法学，重点在于“将成功经验固化为 Skill 存盘”的记忆增长机制。"
    },
    {
        id: "llm_q3",
        category: "llm_rag",
        question: "请对比 GraphRAG 与传统向量 RAG (Naive RAG) 的优缺点，在处理不同类型的 Query 时应如何选择？",
        difficulty: "hard",
        intent: "考查大语言模型落地场景设计中，针对复杂文档全貌分析和细粒度片段分析的技术选型水平。",
        key_points: "非结构化图谱提取, 社区摘要(Leiden), Global Query vs. Local Query",
        model_answer: "1. **架构与原理对比**：\n   - **Naive RAG (经典向量检索)**：依靠文本分块和向量相似度。检索时只抓取语义匹配最贴近的几个局部 Chunk。\n   - **GraphRAG (图索引检索)**：在建库阶段通过 LLM 解析全部文本，提取“实体-关系-属性”三元组构建知识图谱，并利用 Leiden 图聚类将图分为多级社区，调用 LLM 对各社区生成预先总结好的社区报告（Community Summaries）。\n2. **优缺点与选型考量**：\n   - **处理全局/宏观 Query (选 GraphRAG)**：例如“这份项目文件所涵盖的全部潜在生态退化因素有哪些？”。传统 RAG 无法一次检索上百个分散的 Chunks（会超出 LLM 窗口且噪音极大），而 GraphRAG 通过直接调取顶层社区的总结性报告，能轻松给出全面的宏观总结。\n   - **处理具体/细粒度 Query (选 Naive RAG)**：例如“无人机搭载的近红外相机型号是什么？”。此时无需宏观总结，传统 RAG 可以在几毫秒内精准定位到含有该型号的那句话，耗费 Token 极少，且比 GraphRAG（检索图节点）更快更便宜。",
        traps: "避坑：不要把 GraphRAG 吹成“无脑平替”。必须指出 GraphRAG 的代价是**极高昂的建库成本**（由于需要用 LLM 批量读取提取图谱和总结社区，其 API 消耗和建库耗时是传统向量化 RAG 的 10 倍以上）。"
    },
    {
        id: "llm_q4",
        category: "llm_rag",
        question: "CLIP 和 LLaVA 是如何实现跨模态（图像与文本）特征对齐的？请阐述它们的投影层设计。",
        difficulty: "medium",
        intent: "评估候选人对多模态视觉-大语言模型（VLM）底座网络融合的理论扎实程度。",
        key_points: "对比学习, 双塔向量空间对齐, 视觉投影矩阵(MLP/Linear), 语言对齐Token化",
        model_answer: "1. **CLIP 对齐原理 (对比双塔)**：\n   - 采用 Vision Encoder (如 ViT-L/14) 提取图像特征，用 Text Encoder 提取文本特征。\n   - 训练阶段利用**对比学习 (Contrastive Learning)**。在一个有 $N$ 对图文样本的 Batch 内，最大化对应的正样本对的特征点积相似度，最小化其他 $N \\times (N-1)$ 个负样本对的相似度。使图像特征空间与文本特征空间整体对齐，输出的特征向量可以直接在统一空间内计算距离。\n2. **LLaVA 对齐原理 (投影层映射)**：\n   - LLaVA 并非双塔。它使用冻结的 CLIP-ViT 作为 Vision Encoder，对于一幅输入图，提取出其高维视觉 Patch 特征网格 $Z_v$。\n   - **投影层 (Projection Layer)**：为了让大语言模型（LLM，如 Llama/Qwen）读懂这组高维视觉特征，LLaVA 使用了一个可学习的线性映射层 (Linear Matrix) 或 2 层 MLP，将视觉特征向量的维度 $D_{vision}$ (如 1024) 投影转化为 LLM 的输入 Token 维度 $D_{llm}$ (如 4096)。这些投影后的向量被称为“视觉 Tokens”，在输入端与普通的文本嵌入 Tokens 进行直接拼接（Concat），最后一起灌入 LLM 中解码生成。",
        traps: "避坑：不要搞混。CLIP 是“将图和文拉近到同一坐标空间算相似度”（主要用于检索分类）；而 LLaVA 是“用映射矩阵把图像转换成大模型看得懂的视觉词向量”（主要用于文本生成和长文对话）。"
    },
    {
        id: "llm_q5",
        category: "llm_rag",
        question: "对比参数高效微调 (PEFT-LoRA) 与 RAG (检索增强) 的边界，如何针对具体的业务场景进行技术选型？",
        difficulty: "medium",
        intent: "考察对 LLM 两大最常用落地技术方案的边界分析与系统选型架构眼界。",
        key_points: "外部知识挂载, 模型行为/语气调整, 幻觉控制, 动态更新频率",
        model_answer: "1. **底层区别与边界**：\n   - **LoRA 微调** 是“往模型的大脑里做手术”。它通过外接低秩旁路矩阵，调整模型对特定语态、代码输出格式、垂直指令的依从能力，主要用于改变模型**“如何思考和表达 (How to speak)”**，虽能灌入部分新知识，但由于全连接的分布拟合限制，容易产生幻觉遗忘。\n   - **RAG** 是“给模型提供开卷考试”。模型本身没有改变，而是在 prompt 外部挂载实时检索出的私有资料，主要用于改变模型**“回答时的参考事实 (What to know)”**。\n2. **选型决策模型**：\n   - **选择 RAG 的场景**：数据高频更新（如股票实时数据、每日无人机外业日志）；要求回答有明确出处支持溯源；对幻觉零容忍。\n   - **选择 LoRA 的场景**：需要定制特定的输出格式（如输出严格的 JSON、特定遥感 XML 等）；需要扮演特定的人设/语气；数据量小且任务高度专一；大模型底座在专业垂直领域的常识能力不足，需要灌入基础垂直概念。",
        traps: "避坑：不要错误地认为“微调能完美解决模型的信息时效性”。灌入知识的最佳、最廉价手段是 RAG；LoRA 的第一优先级是调整模型的“指令格式依从性和语气风格”。"
    },
    {
        id: "llm_q6",
        category: "llm_rag",
        question: "在 QLoRA 微调大模型中，什么是双重量化 (Double Quantization) 和 NF4 (Normal Float 4) 数据类型？它们是如何减少显存的？",
        difficulty: "hard",
        intent: "考查对量化微调技术最前沿、最底层显卡物理表示机制的掌握。",
        key_points: "NF4 量化区间, 双重量化缩放系数, 分页优化器, 精度保留机制",
        model_answer: "1. **NF4 (Normal Float 4) 数据类型**：\n   - 传统 FP16 占用 2 字节，INT4 虽然省内存，但它是均匀划分的，对服从零均值高斯正态分布的模型权重表达极差。\n   - **NF4** 是一种**分位数非均匀量化方法**。它基于正态分布的累积分布函数（CDF），把四位空间（16个量化值）的间隔设定在正态分布分位数上。这确保了出现概率极高的大量“小权重值”获得更高的数值分辨率，而“极大极小值”分辨率变低，从而在 4-bit 量化下几乎**完全没有损失大模型原本的表达精度**。\n2. **双重量化 (Double Quantization)**：\n   - 量化时需要将大矩阵分成很多 block（如每64个权重一个块），每个块拥有一对 FP32 的缩放比例因子（Quantization Constants）。如果参数极大，这批因子也会占去约 0.5 bit/parameter 的显存。\n   - 双重量化对这批 FP32 比例因子本身进行二次 8-bit 量化。将这部分显存开销从 0.5 bit 压缩到 0.127 bit，使得 70B 模型可以仅消耗约 48GB 显存便可在单张显卡跑通微调。",
        traps: "避坑：指出量化仅针对“基座模型权重（Frozen Weights）”进行 NF4 压缩；而并联的可训练 LoRA 矩阵依然采用 FP16 精度进行高精度更新，否则会导致梯度更新崩溃。"
    },

    // ==========================================
    // 4. 计算机视觉与SAM (cv_sam)
    // ==========================================
    {
        id: "cv_q1",
        category: "cv_sam",
        question: "SAM (Segment Anything Model) 的 Image Encoder 和 Mask Decoder 分别是在哪里计算的？如何在 Web 前端实现毫秒级的交互式分割？",
        difficulty: "medium",
        intent: "考查候选人对 SAM 架构运行开销和边缘端（Edge Computing）落地优化方案的掌握。",
        key_points: "ViT 提取特征, 离线与在线计算分离, ONNX Runtime Web, 共享特征图",
        model_answer: "1. **计算分工**：\n   - **Image Encoder**：基于庞大的 Vision Transformer (ViT-H/L/B)，计算极其沉重。它在**服务器/显卡端**离线执行，将 $1024\\times1024$ 的图像转换为 $64\\times64\\times256$ 的高维特征图（Image Embedding），耗时通常在数百毫秒到数秒。\n   - **Prompt Encoder & Mask Decoder**：仅包含极少量的卷积和注意力机制，计算量极小（仅占总算力约 1%）。\n2. **Web 端毫秒级交互实现方案**：\n   - **特征图一次性提取**：当用户上传或打开一张图片时，在后端服务器（使用 GPU）一次性运行 Image Encoder，计算出该图像的 Embedding，并传输给前端网页。\n   - **前端边缘端推理**：前端使用 WebAssembly 或 **ONNX Runtime Web** 加载压缩导出后的轻量化 SAM Mask Decoder (ONNX 模型)。\n   - **毫秒响应**：当用户在前端进行鼠标点击、拖拽画框时，前端将点击的 $(x, y)$ 坐标即时转化为点提示（Point Prompt），与之前下载好的 Image Embedding 一起输入给前端的 ONNX Decoder，这一步仅需 **5 - 30 毫秒** 即可完成，从而达到完全实时的视觉反馈。",
        traps: "避坑：不要认为每次鼠标点击都需要将图片重新发回服务器计算。关键在于“一次提取，多次使用”和“前后端分离部署”的工程方案。"
    },
    {
        id: "cv_q2",
        category: "cv_sam",
        question: "如何针对非 RGB 模态（如遥感多光谱、热红外影像）微调 SAM 模型？需要修改模型的哪些部分？",
        difficulty: "hard",
        intent: "考察对 SAM 网络结构的剖析能力，以及对自定义模态进行微调的高级算法开发技巧。",
        key_points: "Patch Embedding 卷积核扩展, 参数冻结, LoRA 适配器注入, 权重初始化",
        model_answer: "1. **修改位置：Patch Embedding 层**：\n   - SAM 图像编码器入口是一个 $16\\times16$ 的卷积核（Patch Embedding），用于将 3 通道 (RGB) 图像切块并投影到 D 维空间。\n   - 针对遥感 5 通道（RGB + 红边 + 近红外）数据，需要将该卷积的输入通道数由 3 扩展为 5。具体操作是新建一个 $5 \\to D$ 维的卷积层，前 3 个通道复制 SAM 原有的权重，后 2 个通道用前 3 通道的权重均值进行初始化，以保留原模型的视觉特征感知能力。\n2. **参数微调策略 (LoRA 注入)**：\n   - 冻结 SAM 庞大的 ViT Encoder 和 Decoder 的绝大部分权重，避免破坏其强大的通用空间感知先验，并防止过拟合。\n   - 在 ViT 中每个 Self-Attention 层的 $W_q, W_v$ 线性层旁，并联低秩矩阵通道（LoRA Adapters，Rank=8 或 16）。\n   - 仅对 Patch Embedding 修改层和 LoRA 参数进行反向传播训练，使用遥感特定地物标注数据集（如水体、农田掩膜）进行端到端优化。\n3. **标签匹配与缩放**：由于卫星图像直方图与自然图像差异大，需预先对多光谱波段执行反射率归一化，使其分布调整为 $[0, 1]$ 之间，再送入微调网络。",
        traps: "避坑：切忌说“直接全参数微调”。SAM 参数量极其庞大（ViT-H 达 6.36 亿参数），遥感标注样本通常稀缺，直接全参微调会导致显存溢出（OOM）且破坏模型已有的泛化能力。"
    },
    {
        id: "cv_q3",
        category: "cv_sam",
        question: "SAM 2 是如何实现视频连续帧之间分割追踪的？请详述 Memory Bank 和 Memory Gate 机制。",
        difficulty: "hard",
        intent: "追踪视觉大模型最新前沿（SAM 2 于2024发布），考察候选人对时序注意力与记忆机制的掌握。",
        key_points: "Memory Bank, 门控自注意力(Memory Gate), 历史追踪, 目标遮挡找回",
        model_answer: "1. **视频追踪流程**：SAM 2 的图像和 Prompt 处理沿袭 SAM。当进入视频处理时，它通过引入 **Memory Bank (记忆库)** 来打破帧与帧之间的壁垒。处理第 $t$ 帧时，编码后的图像特征不仅与当前的 Prompt 交互，还要通过 **Memory Attention (记忆注意力层)** 与记忆库中的历史状态联合交互。\n2. **Memory Bank 组成**：\n   - 存储**短期局部记忆**：过去 6 帧的预测 Mask 和空间特征。\n   - 存储**长期全局记忆**：用户手动给出关键提示点的那几帧（通常为第 1 帧）的特征。\n3. **Memory Gate (记忆门控)**：\n   - 过去帧的记忆可能会带有大量漂移噪音。记忆门控引入了门控交叉注意力（Gated Cross-Attention）机制：对于历史记忆特征，模型会乘上一个自适应门控权重因子（Gate Value）。\n   - 如果模型判断过去某一帧的预测质量极差（IoU 估算偏低）或当前物体发生大面积遮挡，门控权重会自动缩减为 0，防止错误特征在帧间污染，从而在物体移出画面又重新返回时，能无缝实现目标的持续追踪。",
        traps: "避坑：指出 SAM 2 是流式处理视频的，无需像传统三维 CNN 一样一次性加载整个视频段。它像自回归大模型一样，逐帧消费、滚动更新记忆库，极大地减少了显卡内存开销。"
    },
    {
        id: "cv_q4",
        category: "cv_sam",
        question: "请对比 YOLOv8 与 YOLOv10 的网络架构差异？YOLOv10 是如何实现“免 NMS (NMS-free)”训练的？",
        difficulty: "hard",
        intent: "深度评估在目标检测落地优化和推理加速方向的技术沉淀。",
        key_points: "解耦头, Anchor-free, 双标签分配(Dual Label Assignment), 避开CPU端瓶颈",
        model_answer: "1. **网络架构演进**：\n   - YOLOv8 为解耦头、无锚框（Anchor-free）结构，使用 TaskAlignedAssigner 做正负样本匹配。\n   - YOLOv10 在 YOLOv8 基础上重构了骨干网络和颈部（启用大核卷积、优化通道设计），并全面移除了推理时的 NMS 模块。\n2. **免 NMS 实现原理：双标签分配 (Dual Label Assignment)**：\n   - **痛点**：传统 YOLO 训练时采用“一对多”正样本匹配（一个真实目标框对应多个检测器预测框），虽然能提供丰富梯度稳定训练，但推理时会产生大量重叠候选框，必须用 NMS（非极大值抑制）对重叠框进行排他性筛选，这在 CPU 端造成巨大延迟瓶颈。\n   - **双分支设计**：YOLOv10 在训练阶段并联了两个检测头：\n     1. **一对多分支 (One-to-many)**：使用传统分配方式计算损失，确保特征充分训练。\n     2. **一对一分支 (One-to-one)**：对每个真实目标只分配一个最佳预测框，计算分类和定位 Loss。\n     在训练时两路并行，共享骨干网络特征。在推理部署时，**直接将一对多分支砍掉**，只使用一对一分支的输出，天然保证每个目标只有一个输出框，完全避免了 NMS 耗时。",
        traps: "避坑：需要讲清“双标签分配”只发生在训练阶段，推理阶段仅运行一对一检测头，因此零计算开销提升速度。如果不知道双分支融合收敛机制，说明理解过于表面。"
    },
    {
        id: "cv_q5",
        category: "cv_sam",
        question: "在无人机/卫星遥感检测中，为什么要引入旋转框目标检测 (YOLO-OBB)？它面临的角度边界值问题如何解决？",
        difficulty: "hard",
        intent: "深入考察遥感特定场景算法优化及几何计算参数拟合方面的细节功底。",
        key_points: "定向边界框(OBB), 旋转矩形表示, 角度突变边界问题, 角度分类化",
        model_answer: "1. **引入 OBB 的核心原因**：\n   - 遥感影像为高空鸟瞰视角，目标（港口船舶、斜排车辆、跑道飞机）具有**任意方向旋转性**，且分布密集。\n   - 传统水平框（HBB）会将邻近倾斜排列的目标包裹在一起，计算重叠度时 IoU 极高。NMS 会误杀掉本属于不同物体的检测框。且水平框引入了太多无用的背景噪音，给分类器带来极大干扰。旋转框 $(x, y, w, h, \\theta)$ 能精准贴合目标边缘，避免重叠误杀。\n2. **角度边界值问题 (Boundary Problem) 的成因**：\n   - 使用 L1 损失回归角度 $\\theta$ 时，由于其具有周期性（如 $\\theta = -\\pi/2$ 与 $\\theta = \\pi/2$ 在几何形态上完全一致），但在数值轴上差了 $\\pi$。当预测框在临界点发生微小抖动时，L1 损失会产生极大的断崖式阶跃突变，导致网络梯度爆炸，训练无法收敛。\n3. **解决方案**：\n   - **角度分类法**：将连续角度转化为离散的分类标签（如把 180 度划分为 180 个离散类，使用 Softmax 预测角度类别）。\n   - **滑窗点表示法**：不直接回归角度，而是预测旋转矩形四个顶点的相对滑移距离，避开周期自变量 $\\theta$ 的显式计算。\n   - **Clipped / Smooth L1 Loss 周期截断**：在损失函数底层引入三角函数（如 $\\sin(\\theta_1 - \\theta_2)$）度量角度偏差，使其天然满足周期连通性性。",
        traps: "避坑：必须画出/描述出“角度周期性导致的边界损失突变”物理现象，并说出如何通过分类化或三角函数损失规避此缺陷。"
    },
    {
        id: "cv_q6",
        category: "cv_sam",
        question: "语义分割中，U-Net 的 Skip Connection (跳跃连接) 为什么对遥感细小地物提取至关重要？",
        difficulty: "medium",
        intent: "考察对深度学习基本架构在特定行业（空间遥感）落地时的特征融合机理理解。",
        key_points: "编码器-解码器, 跳跃连接, 底层高分细节特征, 特征通道拼接",
        model_answer: "1. **遥感数据痛点**：遥感影像分辨率高（单图动辄上万像素），其中地物（田垄、细渠、单条电网）在下采样多层后，其空间像素尺寸在极深特征图中会收缩到小于 1 像素，这导致解码器上采样时无法还原其空间边界，小物体彻底丢失。\n2. **跳跃连接的物理价值**：\n   - **特征对齐拼接**：U-Net 在解码端的每一层，强行将编码端对应分辨率的特征图通过通道拼接 (Concatenation) 引入进来。\n   - **信息互补**：编码端特征带有高分辨率的底层**几何细节特征**（如边缘、纹理、对比度），但缺乏语义信息；解码端特征具有高维**语义信息**（地物到底是什么），但丢失了细节。跳跃连接将两者无缝融合，使解码器在重建掩膜时，能依靠底层几何特征给出的精确定位“勾勒”出极细微的地物边缘。",
        traps: "避坑：区分 ResNet 的残差相加（Element-wise Add）和 U-Net 的跳跃通道拼接（Concat）。残差相加是为了让梯度流通防止退化，通道拼接是为了保留多尺度空间细节。"
    },

    // ==========================================
    // 5. 遥感算法与无人机 (rs_uav)
    // ==========================================
    {
        id: "rs_q1",
        category: "rs_uav",
        question: "请简述无人机航测内业三维重建中，空中三角测量 (空三/Aerotriangulation) 的物理意义与核心数学步骤。",
        difficulty: "medium",
        intent: "这是遥感和测绘算法岗位的核心专业课考点，检验候选人对摄影测量底层的几何物理模型掌握是否扎实。",
        key_points: "共线方程, 外方位元素, 光束法平差, 重投影误差最小化, GCP 控制点",
        model_answer: "1. **物理意义**：空三是指根据无人机飞行时拍摄的有重叠度的二维照片，通过数学几何约束，反求出拍摄每一张照片时相机在三维空间中的绝对位置和姿态（外方位元素），同时计算出地面同名特征点在地球三维坐标系下的世界坐标，为后续正射影像拼图和三维点云构建奠定几何基准。\n2. **核心数学步骤**：\n   - **特征点匹配**：通过 SIFT/ORB 算法寻找重叠照片间的同名点，利用对极约束估计相机间相对位置。\n   - **建立共线方程**：共线方程是摄影测量学的核心公式，描述了“投影中心（镜头中心）- 相片同名点 - 地面实际点”三点共线的几何关系：\n     $$x - x_0 = -f \\frac{a_1(X - X_S) + b_1(Y - Y_S) + c_1(Z - Z_S)}{a_3(X - X_S) + b_3(Y - Y_S) + c_3(Z - Z_S)}$$\n     其中 $(X_S, Y_S, Z_S)$ 是相机空间位置，旋转矩阵参数 $a_i, b_i, c_i$ 是相机姿态角，$(X, Y, Z)$ 是地面点坐标，相片坐标为 $(x, y)$。\n   - **光束法平差 (Bundle Adjustment)**：以共线方程为观测方程，以地面控制点（GCP）和 GNSS 坐标为约束条件，通过列文伯格-马夸尔特（LM）非线性最小二乘迭代算法，同时对数万个相机位姿和空间点坐标进行全局优化，使整体**重投影误差 (Reprojection Error) 达到最小**。",
        traps: "避坑：不要把空三仅当成“黑盒拼图”。必须说出共线方程这一理论模型，以及它是如何通过最小化重投影误差来实现内外参数迭代平差的。"
    },
    {
        id: "rs_q2",
        category: "rs_uav",
        question: "在无人机航测中，什么是正射影像 (DOM) 和数字表面模型 (DSM)？它们与数字高程模型 (DEM) 的区别是什么？",
        difficulty: "easy",
        intent: "考察航测核心概念的清晰度，确保外业及内业处理时的流程定义准确。",
        key_points: "DOM (正射纠正), DSM (包含地表附着物), DEM (纯地形表面)",
        model_answer: "1. **DOM (数字正射影像图)**：利用三维高程数据对原始航拍照片进行**正射纠正**（投影差改正），将中心投影（透视变形）转化为正射投影，然后进行影像拼接和色彩均衡生成的图像。它具有地图的几何精度和影像的丰富信息，可以直接测量距离和面积。\n2. **DSM (数字表面模型)**：代表包含地球表面自然物体和人工建筑物在内的最顶端高程模型。它保留了建筑物、森林冠层、桥梁等**所有地表附着物的高度**。\n3. **DEM (数字高程模型)**：则是剥离了植被、房屋等所有人工和自然地表附着物之后，仅代表**纯粹固体地球表面的高程模型**。\n4. **关系与区别**：\n   - **DSM 包含植被建筑，DEM 仅包含裸露地表**。\n   - 从 DSM 中提取建筑物和植被掩膜并利用插值方法“削平”，即可导出 DEM。\n   - 生成高精度 DOM 时，必须依赖 DSM 或 DEM 进行正射糾正，否则山体、高楼边缘会产生严重的拉伸和扭曲。",
        traps: "避坑：分清 DEM 和 DTM（数字地形模型，通常在DEM基础上包含特征线等更复杂的矢量信息）。不要把 DSM 和 DEM 搞混。"
    },
    {
        id: "rs_q3",
        category: "rs_uav",
        question: "请写出植被指数 NDVI 和 SAVI 的数学公式，说明它们在裸土环境下的表现差异，并说明为什么多光谱相机可以计算这些指数？",
        difficulty: "medium",
        intent: "考查地物光谱解译理论、以及多光谱影像的物理波段通道应用基础。",
        key_points: "红色与近红外反射率, 土壤背景噪声, SAVI 土壤调节因子",
        model_answer: "1. **数学公式**：\n   - **NDVI**：$NDVI = \\frac{\\rho_{NIR} - \\rho_{Red}}{\\rho_{NIR} + \\rho_{Red}}$，其中 $\\rho_{NIR}$ 为近红外反射率，$\\rho_{Red}$ 为红光反射率。\n   - **SAVI**：$SAVI = \\frac{\\rho_{NIR} - \\rho_{Red}}{\\rho_{NIR} + \\rho_{Red} + L} (1 + L)$，其中 $L$ 为土壤调整参数（常设为 0.5）。\n2. **裸土表现差异**：\n   - **NDVI 的局限性**：在低植被覆盖度（稀疏植被、农田苗期、荒漠化地区）下，地表裸土会产生强烈的土壤反射背景噪音。由于裸土在近红外和红光的比值与植被有重叠，NDVI 常常偏高或大幅度波动，失去长势诊断精度。\n   - **SAVI 的改进**：在分母端加入 $L$ 调节因子，并在整体乘上 $(1+L)$ 以抵消土壤光谱特征对指数的分母干涉，使裸土的 SAVI 数值趋于 0，精准把健康植物信号剥离出来。\n3. **多光谱相机计算机理**：多光谱相机拥有窄带滤光片，能独立记录特定窄波段（如近红外 840nm、红光 660nm、红边 705nm）的辐射亮度。经过辐射校正转化为地表反射率（Reflectance）后，即可带入公式运算。",
        traps: "避坑：强调公式中的项代表的是“反射率（Reflectance，通常在 0-1 之间）”，而不是多光谱图像的“原始 DN 亮度值（0-65535）”。带入原始 DN 值算出的 NDVI 是没有任何物理意义的。"
    },
    {
        id: "rs_q4",
        category: "rs_uav",
        question: "如何实现多源遥感影像（如高分二号光学影像与 Sentinel-1 卫星雷达影像）的配准？",
        difficulty: "hard",
        intent: "评估在复杂异源多源遥感图像对齐上的高级特征提取与算子改写经验。",
        key_points: "异源影像畸变, 梯度分布差异, 互信息法(Mutual Information), 结构化特征",
        model_answer: "1. **难点**：光学影像反映的是地物太阳辐射光谱反射，而雷达（SAR）反映的是电磁波回波散射（带有相干斑噪声且存在斜距投影变形）。它们的灰度分布几乎没有任何直接相关性，传统 SIFT 点匹配极易失效。\n2. **核心配准策略**：\n   - **基于结构描述子的匹配 (如 SAR-SIFT)**：不使用局部灰度，而是改用对相干斑噪声鲁棒的梯度算子（如罗盘梯度算子）计算高维多尺度直方图，在频域进行初粗筛定位。\n   - **最大互信息法 (Mutual Information, MI) 进行精细配准**：利用概率统计学中的信息熵度量两个随机变量的相似性：\n     $I(X, Y) = H(X) + H(Y) - H(X, Y)$\n     其中 $H(X, Y)$ 是图文联合信息熵。在配准迭代中，构建空间刚性或仿射变换矩阵，利用随机梯度下降优化变换参数，使两张图像的重合区域互信息值 $I(X, Y)$ 达到最大值。此时，虽然灰度值不相等，但它们的“空间边界排布规律”具有最高的相关一致性。\n   - **双线性重采样**：解算出最终参数后，对目标图像进行坐标逆变换与重采样插值，完成对齐。",
        traps: "避坑：必须指出“互信息法（MI）不依赖两图之间的灰度数值绝对一致，只依赖两图通道特征重合区域概率统计的一致性”，这是处理光学与SAR配准的核心理论底牌。"
    },
    {
        id: "rs_q5",
        category: "rs_uav",
        question: "在无人机航测作业中，已知目标地面采样距离 GSD=2cm/pixel，相机焦距 f=35mm，像元大小 a=4.4微米。请计算出无人机的设计飞行相对高度 H 应为多少？",
        difficulty: "medium",
        intent: "考查测绘工程师外业最基础的航线设计计算能力，数字必须严谨计算。",
        key_points: "GSD公式转化, 单位换算, 外业作业高度精算",
        model_answer: "1. **公式原理**：\n   地面采样距离 $GSD$ 的物理几何计算公式为：\n   $$GSD = \\frac{a \\cdot H}{f}$$\n   其中：\n   - $GSD$ 为地面采样距离，本题中 $GSD = 2\\text{cm} = 0.02\\text{m}$。\n   - $a$ 为像元尺寸，本题中 $a = 4.4\\mu\\text{m} = 4.4 \\times 10^{-6}\\text{m}$。\n   - $f$ 为像机焦距，本题中 $f = 35\\text{mm} = 0.035\\text{m}$。\n   - $H$ 为我们要计算的飞行高度。\n2. **计算过程**：\n   将公式变形求高度 $H$：\n   $$H = \\frac{GSD \\cdot f}{a}$$\n   代入数值：\n   $$H = \\frac{0.02 \\cdot 0.035}{4.4 \\times 10^{-6}} = \\frac{0.0007}{0.0000044} \\approx 159.09\\text{m}$$\n3. **结论**：设计飞行相对高度约为 **159 米**。",
        traps: "避坑：计算时像元大小 $a$ 的微米（$\\mu m$）和焦距的毫米（$mm$）必须统一换算为国际单位制中的米（$m$）。数字算错直接反映外业理论不关关。"
    },
    {
        id: "rs_q6",
        category: "rs_uav",
        question: "遥感中 WGS84 坐标系与 CGCS2000 坐标系之间有何区别？在几十米级误差敏感场景下需要执行投影转换吗？",
        difficulty: "easy",
        intent: "测绘坐标常识考点，评估候选人对大地坐标系统底层精度的认识。",
        key_points: "参考椭球体参数差异, 平移/漂移, 板块漂移修正, 厘米级投影转换",
        model_answer: "1. **定义与区别**：\n   - **WGS84** 是全球 GPS 采用的球心三维地理坐标系，其参考椭球体的偏心率与中国标准有极其微小的数学差异。\n   - **CGCS2000** 是中国国家大地坐标系，基准元时间设定在 2000.0 年。\n   - 在**定义定义上**，两者的参考椭球体扁率仅差约 $0.0000001$，这使得两者的球面几何差异仅在**毫米级**。\n2. **误差敏感场景下的投影考量**：\n   - 虽然椭球体参数差异极小，但由于板块运动以及地表基准站改正数的不同，在中国陆地版图上，原生的未校准 WGS84 原始定位点与 CGCS2000 精准标点之间，可能会有**几十厘米到两米左右的平移偏差**。\n   - 因此，在厘米级精度敏感业务（如地质滑坡形变监测、房地一体权属勘测）中，必须通过“三参数”或“七参数”空间相似变换进行绝对配准，否则无法保证多期时空数据的严格重合。",
        traps: "避坑：不要说“它们俩一模一样不用转”。在低精度民用手持机（精度10米）里确实可以忽略，但在高精度无人机 RTK 测绘中，必须通过参数平差实现统一。"
    },

    // ==========================================
    // 6. 数据工程 (data_eng)
    // ==========================================
    {
        id: "de_q1",
        category: "data_eng",
        question: "如何解决 Spark 在进行地理空间关联查询 (Spatial Join) 时由于空间聚集引起的数据倾斜问题？",
        difficulty: "hard",
        intent: "考查大体量空间大数据开发时的架构优化思维及 Sedona 等空间分布式框架的底层调优原理。",
        key_points: "空间非均匀分区, 四叉树/R树索引分区, 广播 Join (Broadcast), 两阶段聚合",
        model_answer: "1. **空间分区优化（治本）**：\n   - 传统哈希分区会将相同 Hash Key 的数据分到同分区，但地理空间数据在物理世界上分布极不均匀（如北上广深 GPS 数据极密，荒漠海面极稀疏）。\n   - 必须弃用默认分区器，改用 **R-Tree 或四叉树 (Quad-Tree) 空间分区器**。四叉树能够根据空间点数据的密度自动切分空间：数据密集的区域被切分为更小、更多的网格，稀疏区域则合并为大网格。这保证了每个 Spark Partitions 里的空间元素数量大致均等，从而根治 Shuffle 阶段的数据倾斜。\n2. **广播 Join 策略 (Broadcast Join)**：\n   - 如果其中一个表较小（如全省的环境保护红线多边形区，大小在数百MB以内），直接使用 `broadcast()` 算子将其广播到所有 Task 执行端。\n   - 这样 Spark 会采用 Map-Side Join，避免了大表（数亿条 GPS 轨迹点）的 Shuffle 过程，规避了数据倾斜的触发路径。\n3. **两阶段聚合 (加盐法适配)**：\n   - 对热点区域的多边形 ID 加上随机前缀（“加盐”），将大热点分散到多个分区并行 Join，最后再去除前缀进行二次聚合。",
        traps: "避坑：普通的哈希加盐无法直接应用在没有固定 Key、只依赖空间相交关系（`ST_Contains/ST_Intersects`）的空间 Join 上。必须强调使用“四叉树/R-Tree 物理空间网格重划分”这一针对空间数据特有的倾斜解决方案。"
    },
    {
        id: "de_q2",
        category: "data_eng",
        question: "在大模型向量化管道中，如何选择和优化向量数据库的索引？HNSW 相比 IVF_FLAT 索引在性能和成本上有什么考量？",
        difficulty: "hard",
        intent: "测试候选人在处理百万/千万级向量搜索时的系统设计眼界与数据库底层索引优化水平。",
        key_points: "HNSW (跳表图索引) 原理, IVF_FLAT (倒排聚类) 原理, QPS 与时延折衷, 内存占用计算",
        model_answer: "1. **对比考量**：\n   - **HNSW (层次导航小世界图)**：\n     - **原理**：将向量构建为多层图，利用类似跳表（Skip List）的结构实现高速搜索。\n     - **优点**：检索精度极高（Recall可达98%以上），检索延迟（Latency）极低且对高维向量支持极好，在高 QPS 场景下表现优异。\n     - **缺点**：内存消耗极其高昂。因为除了向量本体外，还需要在内存中存储图的拓扑连接结构（每个向量的 M 个邻居指针）。\n   - **IVF_FLAT (倒排扁平索引)**：\n     - **原理**：使用 K-Means 算法把向量空间聚类成 $N$ 个胞腔（Centroids）。检索时，先找出 Query 最近的几个聚类中心，再在这些聚类中心下的倒排列表中遍历计算相似度。\n     - **优点**：内存开销小，建库速度快。\n     - **缺点**：召回精度和检索延迟高度受聚类数量和搜索胞腔数（nprobe）的影响，在高并发时时延增加显著。\n2. **优化策略**：\n   - **内存预估与硬件匹配**：以 1000 万条 1536 维的向量为例，若采用 HNSW，内存开销通常达到约 1000万 * 1536 * 4字节 * 1.5 ≈ 90GB。若内存受限，需采用 **IVF_PQ (乘积量化)**，通过将高维向量压缩为一字节编码，可将内存缩减为 1/10，虽损失 2-5% 的精度，但能大幅降低硬件采购成本。\n   - **超参动态调优**：在线上服务中，通过压测动态调整 HNSW 的 `efSearch` 参数。在低谷期调大以保证召回率，在流量高峰期适当调小以释放系统吞吐量。",
        traps: "避坑：切忌泛泛而谈。需要给出具体的内存计算公式，以及针对物理资源的限制，如何通过 PQ（Product Quantization，乘积量化）和聚类参数的权衡来解决成本与精度的矛盾。"
    },
    {
        id: "de_q3",
        category: "data_eng",
        question: "请详述 Flink 配合 Kafka Sink 实现端到端 Exactly-Once 状态一致性的“两阶段提交”底层运行机制？",
        difficulty: "hard",
        intent: "高并发实时计算管线架构考点，测试候选人对分布式一致性事务与状态灾备的实战设计能力。",
        key_points: "屏障对齐(Barrier), Pre-commit 临时状态, JobManager 协调提交",
        model_answer: "1. **Checkpoint 阶段 (Pre-Commit)**：\n   - Flink 会在数据流中注入 Checkpoint Barrier。当算子处理完 Barrier 前的最后一条数据并将其写入 Kafka Sink 时，Kafka Sink 会**开启一个新的 Kafka 写入事务**，并向 Kafka 代理发送带有当前 Checkpoint ID 的预提交（Pre-commit）数据。\n   - 算子对自身内存状态执行快照持久化。此时数据已经写盘，但在 Kafka 中标记为“未提交”，下游开启 Read_Committed 的 Consumer 是读不到它的。\n2. **协调提交阶段 (Commit)**：\n   - 当 JobManager 协调器接收到所有算子的快照完成应答时，判定此次 Checkpoint 成功，广播发送 Commit 信号给所有算子。\n   - Kafka Sink 算子收到 Commit 信号，调用 Kafka API **正式 Commit 当前 Checkpoint ID 对应的事务**，修改事务状态为已提交，下游 Consumer 即刻能读到数据。\n3. **故障恢复机制**：\n   - 如果在 Pre-commit 后、正式 Commit 前系统崩溃重启，Flink 会将状态恢复到上一次成功 Checkpoint。由于那批预提交事务从未收到 Commit 信号，Kafka 事务会自动过期或回滚，防止了数据被重复消费或丢失。",
        traps: "避坑：强调下游 Kafka Consumer 必须将配置参数设为 `isolation.level = read_committed`。如果设为默认的 `read_uncommitted`，下游依然会读取到未提交事务的脏数据，Exactly-Once 语义在出口端宣告破产。"
    },
    {
        id: "de_q4",
        category: "data_eng",
        question: "对比 Delta Lake 和 Apache Iceberg 的元数据管理机制，它们各自在处理 PB 级小文件合并时有什么优势？",
        difficulty: "hard",
        intent: "深度大数据湖仓架构考点，考查对企业级非结构化与空间海量数据生命周期管理的设计。",
        key_points: "JSON Commit log, manifest 树状层级, OPTIMIZE 算子, 目录无关检索",
        model_answer: "1. **元数据管理差异**：\n   - **Delta Lake** 采用 **Transaction Log (JSON 文件链)** 记录每一次 commits。读取当前快照时，需要按照版本号顺序从头构建文件系统列表视图。分区修剪依赖于 JSON 日志里的元数据指标。\n   - **Apache Iceberg** 采用 **多层 Manifest 元数据树** 结构（Manifest List -> Manifest File -> Data File）。Iceberg 直接把每个 Parquet 文件的统计数据（列最大最小值、Null数量）写入 Manifest 中。最重要的是，Iceberg 完全脱离了物理文件夹目录的定义，只依靠元数据树查询。这使得它能实现**秒级的分区进化（Partition Evolution）**。\n2. **PB级小文件合并 (Compaction) 优势**：\n   - **Delta Lake** 提供原生 `OPTIMIZE` 语法。它可以并行使用 Spark，读取历史 JSON 链中标记的大量小 Parquet 文件，并在后台将它们重写合并为单个 1GB 的规范 Parquet，然后写入一条新的 Commit 记录指向新文件，标记老文件为“已删除”。非常易用，与 Spark 结合极其紧密。\n   - **Apache Iceberg** 在合并小文件时更为优雅，它允许配置 **Copy-on-Write (CoW)** 或 **Merge-on-Read (MoR)**。在 PB 级并发写入极密时，使用 MoR 将更新写到小 delta 文件；在非高峰期，自动调度后台任务进行 Compact，合并元数据 Manifest 树的枝干，从而在极大规模下查询性能受小文件影响的波动性明显小过 Delta Lake。",
        traps: "避坑：指出在对象存储（如 AWS S3 或阿里云 OSS）上，传统的 Hadoop HDFS 目录遍历性能极差，Iceberg 依靠 manifest 树避开了 S3 `listStatus` 目录调用，这是它在大规模对象存储上速度超越 Delta 的关键。"
    },
    {
        id: "de_q5",
        category: "data_eng",
        question: "在 Spark Executor 中，当底层 C++ 库（如 GDAL 影像解译引擎）报错 Out of Memory (OOM) 时，你应如何调整 Spark 的 JVM 内存分配参数？",
        difficulty: "hard",
        intent: "考察在 AI 影像算法落地中，多模态/空间栅格大文件内存越界诊断的生产解决能力。",
        key_points: "Executor Memory Overhead, 堆外内存(Off-Heap), 垃圾回收, C++指针泄露",
        model_answer: "1. **诊断本质**：Spark 默认的 `spark.executor.memory` 仅控制 **JVM 堆内内存 (On-Heap)**。而 GDAL 或是 PyTorch 编译出的 C++ 模块，是在 JVM 之外的 **堆外内存 (Off-Heap / OS Memory)** 中分配空间。如果遥感大图切割开销超限，YARN 协调器检测到该进程占用的物理总内存超出限定，就会强行发送 `SIGKILL` 信号终止 Executor，导致任务报错 OOM 并崩塌。\n2. **调整参数方案**：\n   - **调大堆外内存超限比例**：配置 `spark.executor.memoryOverhead` 参数。默认仅为 Executor 内存的 10%，在处理遥感/CV大算力时，必须提高到 **30% - 50%** 以上。例如给 Executor 分配 20GB，Overhead 建议分配 6GB - 10GB。\n   - **启用堆外执行内存**：设置 `spark.memory.offHeap.enabled = true`，并分配 `spark.memory.offHeap.size = 8g`，让 Spark SQL 在做排序和哈希 Shuffle 时直接借用堆外，给 JVM 堆内腾出垃圾回收空间。\n   - **GC调优**：选用 G1GC 垃圾回收器，限制停顿时间以防大数据量下 Full GC 导致 Task 触发超时心跳丢失。",
        traps: "避坑：发生这种 OOM 时，**无脑调大 `spark.executor.memory`（堆内内存）是没有任何用的**，反而会因为挤压了 OS 物理机空闲空间，加速 YARN 发送 kill 信号的阈值临界。必须调大 `memoryOverhead`。"
    },
    {
        id: "de_q6",
        category: "data_eng",
        question: "当实时空间数据管线中出现 Kafka 消息积压 (Data Backlog)，且消费组频繁发生 Rebalance 抖动时，你应该如何诊断和调优？",
        difficulty: "hard",
        intent: "大系统高可用吞吐调优核心，考查对流处理中反压（Backpressure）和消费阻塞排查经验。",
        key_points: "消费吞吐QPS, max.poll.interval.ms, 心跳超时, 粘性分配(Sticky)",
        model_answer: "1. **诊断步骤**：\n   - 检查 Kafka Lag 积压指标，定位是单个 Partition 积压（存在数据倾斜）还是整体积压。\n   - 观察消费端报错日志，若出现 `CommitFailedException`，说明 Consumer 发生了 Rebalance。\n   - **根本成因诊断**：消费组频繁 Rebalance 往往是因为单个 Batch 的遥感地物数据解析耗时过长，超出了配置的 `max.poll.interval.ms`（最大拉取间隔）。Kafka 协调器判定此 Consumer 已经挂掉，强行踢出消费组并触发重分区。重分区又会导致消费停顿，形成恶性循环。\n2. **调优与解决措施**：\n   - **调整超时参数**：调大 `max.poll.interval.ms`（给长耗时解译任务留足处理时间）；或调小 `max.poll.records`（限制单次 poll 拉取的消息条数）。\n   - **改用 CooperativeSticky 分配器**：在 Consumer 侧设置 `partition.assignment.strategy = org.apache.kafka.clients.consumer.CooperativeStickyAssignor`。支持渐进式增量重平衡，停止消费停顿，只对变动的分区进行移交。\n   - **多线程解耦**：Consumer 只负责快拉消息放入内存队列，使用本地线程池（ThreadPoolExecutor）多并发执行算法解译，使拉取与解译彻底解耦，防止阻塞 Heartbeat 线程。",
        traps: "避坑：不要说“直接增加 Consumer 实例”。如果 Consumer 数量已经等于 Partition 数量，继续加实例只会有闲置浪费，无法提高并发。必须首先排查并优化单次 Poll batch 的处理耗时和超时参数匹配。"
    }
];
