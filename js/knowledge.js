const knowledgeData = [
    {
        id: "ml",
        name: "机器学习算法",
        icon: "cpu",
        items: [
            {
                term: "支持向量机 (SVM) 深度数学原理",
                desc: "SVM 是一种基于最大化几何间隔与对偶优化的经典监督学习分类算法。",
                details: [
                    "**几何间隔与目标函数**：给定训练集，SVM 试图寻找一个分割超平面 $w^T x + b = 0$。为了最大化支持向量到超平面的几何间隔 $\\gamma = \\frac{2}{||w||}$，优化目标转化为最小化二次函数：$min \\frac{1}{2} ||w||^2$，满足不等式约束：$y_i(w^T x_i + b) \\ge 1$。",
                    "**拉格朗日对偶化 (Lagrange Duality)**：引入拉格朗日乘子 $\\alpha_i \\ge 0$，将原约束问题转化为无约束目标函数。通过令 $w$ 和 $b$ 对偏导数为 0，得到对偶形式：$max \\sum_{i=1}^N \\alpha_i - \\frac{1}{2}\\sum_{i=1}^N\\sum_{j=1}^N \\alpha_i \\alpha_j y_i y_j x_i^T x_j$，约束条件为 $\\sum_{i=1}^N \\alpha_i y_i = 0$ 且 $\\alpha_i \\ge 0$。求解出 $\\alpha$ 后，权重向量为支持向量的线性组合 $w = \\sum_{i=1}^N \\alpha_i y_i x_i$。",
                    "**核技巧与对偶性的价值**：① 对偶问题中样本只以**内积形式 $x_i^T x_j$** 出现。这使得我们可以直接定义核函数 $K(x_i, x_j) = \\langle\\Phi(x_i), \\Phi(x_j)\\rangle$ 替代内积，从而避开显式计算高维空间映射，轻松处理非线性可分问题。② 当特征维度很高时，通过对偶求解往往更高效。",
                    "**KKT 条件**：支持向量对应 $\\alpha_i > 0$。对于非支持向量，$\\alpha_i = 0$，对最终超平面无贡献，这赋予了 SVM 极强的稀疏性与鲁棒性。"
                ],
                code: `from sklearn.svm import SVC
# 核心超参数调优：
# C: 惩罚系数。C越大对误分类容忍度越低，易过拟合；C越小容忍度越高，易欠拟合。
# gamma: RBF核的宽度参数。gamma越大高斯分布越窄，模型只关注支持向量附近，决策边界极度复杂（易过拟合）。
model = SVC(C=1.0, kernel='rbf', gamma='scale')`,
                analogy: "这就像是在两个敌对部落之间修建一条防护公路，马路越宽越安全（最大几何间隔）。为了保证马路绝对宽，我们在两边离得最近的房屋（支持向量）处立桩子，其他更远的房子我们根本不需要关心（稀疏性）。如果遇到高低起伏的山丘挡路（非线性），就使用核函数把地面“弹射”到三维甚至更高维空间，在立体空间切一刀就轻松分开了。",
                interview_script: "1. 先指明SVM的核心是寻找能够最大化几何间隔的超平面，以保证模型泛化性。\n2. 解释拉格朗日乘子法的作用：将带约束的二次规划问题通过对偶化转为无约束问题。强调对偶化之后，样本计算只依赖内积 $x_i^T x_j$，这正是引入核技巧的前提。\n3. 说明KKT条件决定了只有极少数边界样本（支持向量）决定决策面，具备天然的防噪声鲁棒性。\n4. 避坑指南：面试官常问核函数的计算开销。答：核函数是在低维直接计算内积，从而免去了显式投影到高维的计算，这才是核技巧的关键。"
            },
            {
                term: "随机森林 (Random Forest) 架构与方差控制",
                desc: "基于自助采样法 (Bootstrap) 和决策树 (CART) 的 Bagging 代表集成算法。",
                details: [
                    "**双重随机性控制方差**：\n  1. **样本随机性**：使用 Bootstrap 方法从原始样本集有放回抽取 $N$ 个样本构建子树训练集，约有 36.8% 的数据不会被抽到（称为 Out-of-Bag，袋外数据，可直接用于模型无偏评估）。\n  2. **特征随机性**：CART 决策树在节点分裂时，只随机从全部 $D$ 个特征中选取 $d = \\sqrt{D}$ 个特征子集，再从中选择最优分裂属性。\n  这种双重随机性降低了单棵树的过拟合风险，使得各子树相关性极大降低，集成后的方差（Variance）呈指数级下降。",
                    "**偏差-方差表现**：Bagging 架构中，基评估器并行训练。集成结果是多棵树的平均值或多数表决。这保持了模型的偏差（Bias）与单棵树相似，但大幅度**压制了方差（Variance）**，表现出极强的泛化稳定度。"
                ],
                code: `from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(
    n_estimators=200,   # 决策树个数
    max_depth=12,        # 限制树高以防单树过拟合
    max_features='sqrt', # 每节点考虑的特征子集大小
    oob_score=True,      # 启用袋外数据评估
    n_jobs=-1
)`,
                analogy: "这就像去医院确诊一个复杂疾病，如果只听一个医生的意见很容易误诊（单棵决策树容易过拟合，方差高）。所以我们找 200 个医生进行联合会诊（集成）。为了让医生们的专业视角多样化，我们给每个医生只看随机抽样的一部分病历（样本随机），且限制他们诊断时只能问某几个特定维度的问题（特征随机），最后大家投票。这能极大地消除个人偏见，降低误诊率（方差）。",
                interview_script: "1. 表明随机森林是基于Bagging架构的，它的核心目标是通过引入“双重随机性”（自助样本重采样和随机特征子集）来降低单树之间的相关性，从而在集成时显著降低方差。\n2. 提及袋外数据（OOB）可以代替验证集进行泛化能力评估，提高数据利用率。\n3. 强调随机森林的偏差和基树差不多，因此基树要尽量生长的深一些（低偏差、高方差）。\n4. 避坑指南：面试官常问RF与GBDT区别。答：RF是并行Bagging，侧重降方差；GBDT是串行Boosting，侧重降偏差。"
            },
            {
                term: "XGBoost 梯度提升树与二阶泰勒展开",
                desc: "XGBoost 是对 GBDT 算法在效率与泛化性能上的极致优化版 Boosting 实现。",
                details: [
                    "**目标函数二阶展开**：XGBoost 优化目标包含损失函数与控制复杂度的正则项：$\\mathcal{L}^{(t)} = \\sum_{i=1}^n l(y_i, \\hat{y}_i^{(t-1)} + f_t(x_i)) + \\Omega(f_t)$。\n  对其在 $\\hat{y}^{(t-1)}$ 处进行二阶泰勒级数展开：\n  $\\mathcal{L}^{(t)} \\approx \\sum_{i=1}^n [l(y_i, \\hat{y}_i^{(t-1)}) + g_i f_t(x_i) + \\frac{1}{2} h_i f_t^2(x_i)] + \\gamma T + \\frac{1}{2} \\lambda \\sum_{j=1}^T w_j^2$\n  其中 $g_i$ 为一阶导数，$h_i$ 为二阶导数。二阶信息的引入使得算法能够更精确、快速地逼近局部最优。",
                    "**分裂增益度量**：XGBoost 采用以下公式评估节点分裂价值：\n  $Gain = \\frac{1}{2} [\\frac{(\\sum_{i \\in I_L} g_i)^2}{\\sum_{i \\in I_L} h_i + \\lambda} + \\frac{(\\sum_{i \\in I_R} g_i)^2}{\\sum_{i \\in I_R} h_i + \\lambda} - \\frac{(\\sum_{i \\in I} g_i)^2}{\\sum_{i \\in I} h_i + \\lambda}] - \\gamma$\n  其中 $\\gamma$ 为叶子分裂惩罚项，相当于树剪枝的阀值，只有增益大于 $\\gamma$ 时才执行分裂。"
                ],
                code: `import xgboost as xgb
# 调参重点：
# min_child_weight: 叶子节点最小二阶导数和（类似于样本数）。值过大防过拟合，过小易过拟合。
# gamma: 控制分裂阈值惩罚。
params = {
    'max_depth': 6,
    'learning_rate': 0.1,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'tree_method': 'hist' # 启用直方图算法提速
}`,
                analogy: "这就像射箭比赛。第一支箭射偏了，第二支树就去修正第一支箭偏离靶心的距离和方向（拟合残差，降偏差）。为了让修正极其精准，我们不仅看偏了多少（一阶导数 $g$），还要计算风速和拉弓加速度的变动趋势（二阶导数 $h$），并且在弓上加了防震稳定器（正则化项 $\\gamma, \\lambda$），防止过度发力导致动作变形（过拟合）。",
                interview_script: "1. 明确XGBoost是Boosting架构，通过串行迭代生成决策树去拟合先前累加模型的伪残差，逐步降低偏差。\n2. 核心讲清泰勒二阶展开的优势：引入一阶梯度 $g$ 和二阶梯度 $h$，使目标函数能更精确、快速地逼近极值，且使得XGBoost支持自定义损失函数（只要能求一二阶导）。\n3. 说明正则化项的意义：在目标函数中直接加入了控制叶子数和叶子权重的罚项，这是它相比传统GBDT不易过拟合的底层数学保障。\n4. 避坑指南：必须主动提到直方图搜索算法和稀疏感知分裂，这是大规模计算提速的核心。"
            },
            {
                term: "LightGBM 优化机制 (GOSS & EFB)",
                desc: "针对大规模特征与大样本量，微软对经典树分裂算法进行的低开销高速演进。",
                details: [
                    "**GOSS (单边梯度采样)**：为了减少样本计算量，GOSS 保留所有一阶梯度绝对值较大的样本（这部分样本拟合不充分），而对梯度较小的样本进行随机下采样（乘以缩放系数以保持数据分布一致）。这使得模型只关注“难训练”的样本，减少了 80%+ 的计算开销且精度不减。",
                    "**EFB (互斥特征捆绑)**：在许多稀疏特征空间中，许多特征是互斥的（即极少同时为非零值）。EFB 算法将这些互斥特征捆绑合并为一个连续特征，极大缩减了特征维度，消除了无效特征扫描开销。",
                    "**Leaf-wise 与 Level-wise**：传统 XGBoost 默认采用 Level-wise（按层分裂），而 LightGBM 采用 Leaf-wise（按叶子分裂，每次只找分裂增益最大的叶子节点）。Leaf-wise 能生成更深的非对称树，偏差更低，但需配合 `max_depth` 限制深度以防过拟合。"
                ],
                code: `import lightgbm as lgb
# 核心超参：
# num_leaves: 决定单树复杂度的最重要参数。必须小于 2^max_depth。
# min_data_in_leaf: 叶子节点最少数据量，调大可防止过拟合。
train_data = lgb.Dataset(X, y)
params = {'num_leaves': 31, 'learning_rate': 0.05, 'boosting_type': 'gbdt'}`,
                analogy: "这就像老师改作业。如果把全班所有人的所有题都仔仔细细改一遍，效率太低。老师的做法是：重点关注成绩差、容易错的这部分学生作业（梯度大），而对成绩优异、基本全对的学生（梯度小）只随机抽查 20%（GOSS）。同时，把班级里从不重叠的职务（如语文课代表和体育课代表不可能同一人担任）捆绑成一个职务（EFB），登记分数时直接合并成一列，改作业速度暴涨。",
                interview_script: "1. 明确LightGBM是为了突破XGBoost在海量特征和样本下，频繁扫描直方图带来的时间和内存开销。\n2. 深入阐述GOSS原理：基于样本梯度进行启发式采样，既减少了样本，又通过权重补偿保留了原始分布的无偏性。\n3. 说明EFB原理：利用互斥特征的稀疏性，将互斥特征安全合并，减少特征维度。\n4. 阐述Leaf-wise的优缺点：效率高、偏差低，但树过深易过拟合，需要严控 `num_leaves` 参数。"
            },
            {
                term: "CatBoost 类别特征与对称树设计",
                desc: "专门针对类别特征进行深度优化，防靶向泄漏与过拟合的梯度提升框架。",
                details: [
                    "**Ordered Boosting (排序提升)**：经典 GBDT 使用相同样本计算梯度并更新权重，易导致目标泄漏（Target Leakage）。CatBoost 引入时间序列思维，计算当前样本的梯度时只使用之前的样本，避免了预测偏移。",
                    "**Symmetric Trees (对称树)**：CatBoost 的基分类器采用对称决策树（Oblivious Trees），即同一层的所有节点都使用相同的特征和分裂条件。对称树结构极其简单，能够有效对抗过拟合，且推理速度比普通决策树快数倍。"
                ],
                code: `from catboost import CatBoostClassifier
# 原生支持类别特征，无需手动One-Hot
model = CatBoostClassifier(
    iterations=500,
    depth=6,
    cat_features=['gender', 'city_id'] # 指定类别特征索引
)`,
                analogy: "这就像公司做业绩考核。如果用每个人的考核成绩去当场修正所有人的评价标准，容易形成裙带关系和主观偏见（目标泄漏）。CatBoost 采用的方法是“按入职顺序考核”：计算你的指标时，只参考在你之前入职员工的业绩数据（Ordered Boosting）。此外，考核条件极度标准化，每一层的提问条件全班统一（对称树），就像制式的问卷调查，这极大避免了树结构走偏（抗过拟合）。",
                interview_script: "1. 突出CatBoost的两大王牌：完美处理类别型特征（Categorical Features）和独创的Ordered Boosting算法。\n2. 解释目标偏移（Prediction Shift）和目标泄漏：在传统树模型中，用于计算梯度的样本与用于训练树的样本重合，导致过拟合；Ordered Boosting通过随机排列和历史样本估计，实现梯度计算的无偏性。\n3. 说明对称决策树（Symmetric Trees）的作用：每层使用相同分裂特征，简化树结构，支持并行且推理时仅用哈希查表，执行极其迅速。"
            },
            {
                term: "聚类算法对比: K-Means vs. DBSCAN",
                desc: "基于中心距离的划分聚类与基于密度连通的密度聚类对比。",
                details: [
                    "**K-Means (划分聚类)**：① **原理**：随机初始化 K 个质心，交替执行样本分配与质心更新，最小化簇内平方误差（SSE）。② **局限性**：必须预先指定 K 值；对噪声点和离群值极敏感；只能发现凸包状（圆形/球形）的簇，无法处理非线性复杂边界。",
                    "**DBSCAN (密度聚类)**：① **原理**：基于邻域半径 $Eps$ 和最少样本数 $MinPts$ 扫描密度可达关系，将紧密连接的区域归为一个簇。② **优势**：无需指定簇数；能自动识别并过滤噪声离群点；可以发现任意形状的簇（弯曲地物、河流、道路等）。③ **局限性**：对参数 $Eps$ 和 $MinPts$ 极其敏感，在数据密度分布极不均匀时表现不佳。"
                ],
                code: `from sklearn.cluster import KMeans, DBSCAN
# K-Means 调优：使用 K-Means++ 改进初始质心选择，避免陷入局部最优
kmeans = KMeans(n_clusters=5, init='k-means++')
# DBSCAN 调优：对于高维数据，Eps半径通常使用 K-distance 图进行拐点估计
dbscan = DBSCAN(eps=0.5, min_samples=10)`,
                analogy: "K-Means 就像在广场上摆 K 个摊位，让所有人就近排队（基于距离），如果有人捣乱（噪点），摊位中心就会被迫往他那边挪。DBSCAN 就像在人群里找小团体，只要一个人周围一米内有超过 10 个人（高密度），就把他们划为团伙成员，大家手拉手不断延伸。即使队伍弯弯曲曲（非线性形状）也无所谓，而孤零零站在远处的人会被当做路人（噪点）直接过滤掉。",
                interview_script: "1. 从底层逻辑划分聚类与密度聚类，指出 K-Means 以欧氏距离最小化为优化目标，DBSCAN 以局部高密度区域连通性为收敛目标。\n2. 详细对比两者对于噪声、K值确定、形状提取的差异。\n3. 避坑指南：面试官喜欢问K-Means如何选K值，答：肘部法（Elbow Method）看SSE饱和拐点，或者轮廓系数（Silhouette Coefficient）看内聚性与分离度。"
            },
            {
                term: "降维技术: PCA vs. t-SNE vs. UMAP",
                desc: "线性全局投影与非线性局部拓扑保持降维算法的深度剖析。",
                details: [
                    "**PCA (主成份分析)**：线性降维。核心思想是通过正交变换，将原高维特征投影到方差最大的前几个正交方向（主成分），只保留全局最大方差结构，丢失非线性流形特征。",
                    "**t-SNE (t分布邻域嵌入)**：非线性降维。在高维空间用高斯分布度量邻域相似度，低维空间用 t 分布度量相似度，利用 **KL 散度**最小化两者的概率分布差异。极大保留局部邻域结构，利于可视化，但无法保留全局距离，计算开销极高（$O(N^2)$）。",
                    "**UMAP (统一流形逼近与投影)**：基于黎曼几何与代数拓扑。通过模糊单纯复形构建拓扑图，计算比 t-SNE 快数倍，且不仅保留了局部拓扑，还较好保留了全局结构关系。"
                ],
                code: `from umap import UMAP
# UMAP 调优：
# n_neighbors: 邻域大小。越小越关注局部微观结构，越大越关注全局宏观结构。
# min_dist: 投影后点之间的最小距离，控制低维分布的紧密程度。
reducer = UMAP(n_neighbors=15, min_dist=0.1, n_components=2)`,
                analogy: "PCA 就像从正上方用强光照一个立体雕塑，只看打在地面上的阴影（全局最大方差线性投影），把复杂的弯曲细节全压扁了。t-SNE 就像把高维的面膜撕下来铺平，只保证紧挨着的皮肤细胞相对位置不变（局部邻域相似性），但面膜的额头到下巴的宏观距离全乱了。UMAP 就像在充气气球上画图，放气后按拓扑结构精密折叠，既保住了局部挨着的点，宏观拓扑轮廓也没散，而且折叠速度飞快。",
                interview_script: "1. 分类对比线性与非线性降维。说明PCA是无监督线性映射，目标是投影后方差最大化以保留信息，但无法拟合非线性高维流形。\n2. 剖析t-SNE的核心：利用复t分布解决拥挤问题（Crowding Problem），通过KL散度约束距离，是可视化利器，但无法用于特征预处理，因为新样本无法增量投影。\n3. 指出UMAP的数学底座（黎曼几何），强调它兼顾全局与局部拓扑特征，是高维向量可视化的最新SOTA。"
            },
            {
                term: "分类基石: 逻辑回归与朴素贝叶斯",
                desc: "经典判别式分类模型与基于贝叶斯定理的生成式模型对比。",
                details: [
                    "**逻辑回归 (Logistic Regression)**：判别式模型。使用 Sigmoid 函数 $P(y=1|x) = \\frac{1}{1 + e^{-(w^Tx+b)}}$ 直接对条件概率建模，通过最大似然估计求解权重。不要求特征独立分布，适合高维稀疏特征线性建模。",
                    "**朴素贝叶斯 (Naive Bayes)**：生成式模型。基于贝叶斯定理 $P(Y|X) = \\frac{P(X|Y)P(Y)}{P(X)}$，并**强假设特征之间条件独立**。通过计算联合概率分布建模，在文本分类（如垃圾邮件分类）及小样本上表现优异，但特征关联强时性能退化严重。"
                ],
                code: `from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
# 逻辑回归正则化：L1正则化产生稀疏特征（特征选择），L2正则化控制权重大小防止过拟合
lr = LogisticRegression(penalty='l2', C=1.0)
nb = MultinomialNB()`,
                analogy: "逻辑回归就像是相亲时的直接打分表，不管你爸是谁，只看你的各项硬件条件（特征），赋予不同的权重（如学历乘 0.4 加收入乘 0.6），最后算个总分过不过（条件概率直接建模）。朴素贝叶斯就像是通过统计大数据进行画像：先统计程序员里单身的概率，再假定发型秃、喜欢穿格子衫这两个特征互相无关（条件独立假设），算出“既秃又穿格子衫”的程序员里单身和脱单的比例来做决策。",
                interview_script: "1. 区分判别式与生成式：逻辑回归是判别式，直接学习 $P(Y|X)$，建立分类超平面；朴素贝叶斯是生成式，学习联合分布 $P(X, Y)$，通过贝叶斯定理逆推条件概率。\n2. 说明朴素贝叶斯的核心假设——特征条件独立性。虽然能极快计算出概率并克服小样本，但在高相关性特征下，独立假设被破坏，分类效果会急剧恶化。\n3. 避坑指南：面试官常问LR的损失函数。答：交叉熵损失函数（Cross Entropy Loss），使用梯度下降或L-BFGS求解优化。"
            }
        ]
    },
    {
        id: "dl_transformer",
        name: "深度学习与Transformer",
        icon: "layers",
        items: [
            {
                term: "自注意力机制 (Self-Attention) 与多头数学",
                desc: "Transformer 架构的核心计算组件，通过关联相似度聚合全局上下文信息。",
                details: [
                    "**单头自注意力推导**：\n  对于输入矩阵 $X \\in \\mathbb{R}^{L \\times d}$，通过投影矩阵得到 $Q = X W_Q$, $K = X W_K$, $V = X W_V$（其中 $W \\in \mathbb{R}^{d \\times d_k}$）。\n  计算相似度分布：$Attention(Q, K, V) = softmax(\\frac{Q K^T}{\\sqrt{d_k}}) V$。\n  **缩放因子 $\\sqrt{d_k}$ 推导**：设 $q \\in \mathbb{R}^{d_k}$ 且 $q_i, k_i$ 独立且服从均值 0 方差 1 独立同分布。则两向量内积 $q \\cdot k = \\sum_{i=1}^{d_k} q_i k_i$ 的方差为 $Var(q \\cdot k) = d_k Var(q_i)Var(k_i) = d_k$。为了避免 Softmax 输入方差过大进入饱和区梯度消失，必须除以 $\\sqrt{d_k}$ 将方差归一化为 1。",
                    "**多头注意力 (MHA)**：\n  将隐藏维度分裂为 $h$ 个小维度 $d_k = d_{model}/h$，在 $h$ 个独立的投影子空间计算注意力，最后拼接输出：\n  $MultiHead(Q,K,V) = Concat(head_1, ..., head_h) W^O$。\n  多头注意力的本质是允许模型在不同的表示子空间并行获取不同位置的特征关联性。"
                ],
                code: `import torch
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.out_linear = nn.Linear(d_model, d_model)
        
    def forward(self, x):
        B, L, D = x.shape
        Q = self.q_linear(x).view(B, L, self.num_heads, self.d_k).transpose(1, 2)
        K = self.k_linear(x).view(B, L, self.num_heads, self.d_k).transpose(1, 2)
        V = self.v_linear(x).view(B, L, self.num_heads, self.d_k).transpose(1, 2)
        
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.d_k ** 0.5)
        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, L, D)
        return self.out_linear(out)`,
                analogy: "自注意力机制就像是一场鸡尾酒会。你（Query）想找到共同话题，便向全场人发放你的个人名片（Key）。每个人根据你的名片计算出你们之间的话题重合度（Softmax相似度），根据重合度大小，他们把各自的话题干货信息（Value）分享给你。多头注意力就像是你长出了多对耳朵，一对耳朵只听谁聊足球，另一对耳朵只听谁聊八卦，最后综合出全场信息流。",
                interview_script: "1. 先写出Attention的经典公式，重点强调其三个矩阵 Q, K, V 的物理意义：Query是当前的查询，Key是信息索引，Value是包含特征的原始向量。\n2. 深入推导为什么除以 $\\sqrt{d_k}$。当维度极高时，Query和Key的内积数值很容易被放大，进入Softmax的饱和区，导致反向传播梯度为0（梯度消失）。除以 $\\sqrt{d_k}$ 能将内积方差归一化为1，确保梯度平稳回传。\n3. 说明多头注意力的好处：多组 $Q, K, V$ 能投影到不同的低维子空间，捕捉更细粒度、多维度的序列相关特征（比如句法关系与指代关系）。"
            },
            {
                term: "DeepSeek v3 MLA (多头潜在注意力机制) 推理优化",
                desc: "MLA 是 DeepSeek 提出的低秩 Key-Value 联合压缩注意力机制，极大缓解了推理时的 KV Cache 显存瓶颈。",
                details: [
                    "**低秩投影压缩**：MLA 将输入的 Key 和 Value 向量联合投影到一个低维潜在向量 $c_t^{KV}$（秩为 $d_c \\ll d_{model}$），在显存中只需缓存这个低维的潜在向量。当前 Step 计算注意力时，再通过解压矩阵将其临时还原到多头 Key-Value 空间，从而将 KV Cache 显存占用降低至原先的 $1/6$ 左右。",
                    "**解耦旋转位置编码 (RoPE Decoupling)**：传统的 RoPE 位置编码与 Key 向量相乘，这与低秩解压矩阵冲突（因为旋转矩阵无法直接合并进解压矩阵）。MLA 将 Q 和 K 的特征维度拆分出一部分专门用于注入 RoPE 位置编码（单独计算内积），而未注入位置编码的部分则直接在低秩潜在空间中进行计算，完美解决了低秩压缩与旋转位置编码的兼容性难题。"
                ],
                code: `# DeepSeek MLA (Multi-Head Latent Attention) 核心流程伪代码
class MLA(nn.Module):
    def __init__(self, d_model, num_heads, d_c, d_k):
        super().__init__()
        self.compress_kv = nn.Linear(d_model, d_c) # 压缩至潜在空间
        self.decompress_k = nn.Linear(d_c, num_heads * d_k) # 解压Key
        self.decompress_v = nn.Linear(d_c, num_heads * d_k) # 解压Value
        # 旋转位置编码单独处理分支，注入RoPE位置特征`,
                analogy: "这就像出国旅游带行李。如果把所有衣服鞋子（K、V向量）直接原样塞进皮箱，显存箱子很快就装满了。DeepSeek 的办法是：把衣服全部放进真空压缩袋里抽气，缩减成一个小纸包（潜在压缩表示 $c_t^{KV}$），到酒店（计算单元）后再拆袋充气还原（解压矩阵还原多头）。至于带有精密防震要求的定位表针（RoPE），我们单独拎在手里，绝不装进压缩袋（解耦位置编码）。",
                interview_script: "1. 指出 MLA 是针对大语言模型自回归解码（Generation）阶段，KV Cache 占用显存带宽过高这一痛点进行的系统级优化。\n2. 解释它是如何通过低秩分解，对 Key 和 Value 建立联合压缩矩阵，使推理卡只需要缓存压缩后的低维特征，而将原本的多头展开在计算时原位进行解压，极大降低了 IO 带宽负载。\n3. 说明解耦位置编码（RoPE Decoupling）的设计：由于旋转位置编码矩阵无法通过结合律嵌入到低秩解压矩阵中，MLA 将 K 和 Q 解耦，分裂为位置无关和位置相关两部分，前者走低秩压缩计算，后者单独做复数相乘，实现了低秩缓存与RoPE的完美融合。"
            },
            {
                term: "三维归一化对比: LN vs. BN vs. GN",
                desc: "神经网络正则化在批处理（Batch）、通道（Channel）及序列长度（SeqLen）维度的设计差异。",
                details: [
                    "**BatchNorm (批归一化)**：沿批量 $N$ 计算均值方差，保留 $C, H, W$ 轴。极大依赖 Batch Size；训练与推理行为不一致（推理使用滑动平均）；变长序列易失效。",
                    "**LayerNorm (层归一化)**：沿特征通道 $C$ 计算均值方差，保留批量 $N$ 轴。不依赖 Batch Size，适用于 NLP 序列动态长度特征归一化，训练推理行为一致。",
                    "**GroupNorm (组归一化)**：将通道 $C$ 划分为 $G$ 个组，在每个样本的每组内计算均值方差。介于 BN 与 LN 之间，在 CV 目标检测大图训练（Batch Size=1 或 2）时完美替代 BatchNorm，具有更强健的超小 Batch 鲁棒性。",
                    "**Pre-LN 与 Post-LN 稳定性**：Pre-LN：$x_{l+1} = x_l + F(LN(x_l))$。Post-LN：$x_{l+1} = LN(x_l + F(x_l))$。Pre-LN 让梯度直接流通残差干线，训练大模型不易崩塌，无需过长 Warmup。"
                ],
                code: `# PyTorch 中的调用演示
import torch.nn as nn
# LayerNorm: NLP标准，归一化特定样本的所有通道特征
ln = nn.LayerNorm(normalized_shape=512)
# GroupNorm: 将512个通道分成32个组，每组16通道，独立计算归一化
gn = nn.GroupNorm(num_groups=32, num_channels=512)`,
                analogy: "这就像学校做体检统计。BatchNorm 是把全国所有班级的 1 号学生（同一通道的整个 Batch）拉出来称体重算平均分，高度依赖抽样人数（Batch Size）。LayerNorm 是把每个班级自己的所有人（单样本的所有特征）拉出来称重统计，各个班级各算各的，不受别的班影响。GroupNorm 是嫌整个班人数太多不好算，把全班分成 4 个课外小组（通道分组），每个组单独称重算平均分。",
                interview_script: "1. 先用三维张量 $(N, C, L)$（Batch, Channel, Length）阐述三者的计算方向差异：BN跨样本算通道；LN跨通道算样本；GN在单样本内按通道分组算归一化。\n2. 指出BN之所以不适合NLP，是因为文本长度是动态的，且Batch Size在微调时往往很小，会导致计算的均值方差抖动剧烈。\n3. 主动提及Pre-LN与Post-LN的演进：现代大模型（如Llama）均将Post-LN改为了Pre-LN，以保护残差通道（Identity Map）上的梯度不被归一化层过度缩放，从而使上百层的大模型能稳定训练。"
            },
            {
                term: "优化器进阶: AdamW vs. SGD vs. Lion",
                desc: "深度模型训练的参数更新动力学及解耦权重衰减机制。",
                details: [
                    "**AdamW (解耦权重衰减自适应优化)**：经典 Adam 在更新方向上混合了梯度正则化项。为了使 L2 正则化的缩放完全不被自适应一阶/二阶动量偏差干涉，AdamW 将权重衰减直接从梯度梯度项剥离，改为在最后参数更新时直接减去衰减：$w_{t+1} = w_t - \\eta_t(\\lambda w_t + \\frac{m_t}{\\sqrt{v_t} + \\epsilon})$。这是 Transformer 训练的绝对标配。",
                    "**Lion (符号化自适应优化)**：谷歌 2023 提出，仅使用一阶动量的**符号（Sign）**决定更新方向，内存开销减少一半（无需存储二阶动量 $v_t$），且在多类 foundation models 训练中显示出优于 AdamW 的收敛速度。"
                ],
                code: `from torch.optim import SGD, AdamW
# AdamW 的调用：将 weight_decay 解耦传入，防止与梯度动量混淆
optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=0.01, eps=1e-8)`,
                analogy: "SGD 就像下山，哪一步陡（梯度大）就迈大步，遇到小坑就容易陷进去。AdamW 就像带GPS和阻尼器的平衡滑板车，不仅记住刚才冲下来的速度（一阶动量），还看脚下路面有多抖（二阶动量），而且把阻力（L2正则化）直接接在轮刹上，而不是接在发动机上（解耦）。Lion 就像是极简主义滑板，它根本不在乎山坡到底有多陡，只用眼睛看方向是上还是下，用 1 或 -1（符号函数）直接滑行，省了一半内存卡。",
                interview_script: "1. 讲清为什么L2正则化在Adam中会失效：传统Adam直接把L2正则加入梯度计算，由于二阶动量分母的存在，会导致正则项被非正常缩放，使大权重的参数衰减不足，小权重参数衰减过度。AdamW的贡献在于将权重衰减（Weight Decay）完全从动量梯度中解耦出来，使得L2正则项真正起到限制权重大小的作用。\n2. 提及Lion的创新：通过 `torch.sign` 极大降低显存开销，减少了超大模型预训练时的成本。"
            },
            {
                term: "旋转位置编码 (RoPE) 数学原理",
                desc: "旋转位置编码是目前 Llama, Qwen 等主流开源大模型绝对统配的相对位置编码机制。",
                details: [
                    "**旋转算子推导**：RoPE 期望通过在复数空间对向量进行旋转来注入绝对位置信息，使得投影后的内积包含相对位置差 $(m - n)$。对于 2 维向量 $x = (x_1, x_2)^T$，赋予位置 $m$ 时的旋转操作为乘上 2D 旋转矩阵：\n  $R_{\\Theta, m}^d x = \\begin{pmatrix} \\cos m\\theta & -\\sin m\\theta \\\\ \\sin m\\theta & \\cos m\\theta \\end{pmatrix} \\begin{pmatrix} x_1 \\\\ x_2 \\end{pmatrix}$\n  这相当于将 2D 向量在复数空间乘以 $e^{i m \\theta}$。在高维空间中，RoPE 将隐藏维度两两分组，执行不同频率的 2D 坐标系旋转。",
                    "**线性外推优势**：由于旋转运算具有高度的相对位置对称性，模型在长上下文测试时，只需通过调整基本频率参数 $\\theta$ 的底数（如将 $10000$ 扩展为 $1000000$），就能在外推到 128k 甚至更长窗口时保持低困惑度 (Perplexity)。"
                ],
                code: `# RoPE 核心操作伪代码
def apply_rotary_emb(x, cos, sin):
    # 将输入向量x按照隐藏维度两两切分并旋转
    x1, x2 = x[..., 0::2], x[..., 1::2]
    # 按照三角函数旋转公式：[x1*cos - x2*sin, x1*sin + x2*cos]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)`,
                analogy: "传统的绝对位置编码就像是在每个位置上贴一个特制邮戳。旋转位置编码（RoPE）就像是在钟表盘上拨指针。第 $m$ 个字进入网络时，它的特征向量就像是一只被旋转了 $m$ 次固定角度（$m\\theta$）的指针。当计算两个指针的相似度时，我们只需要看它们的夹角差（相对距离 $m-n$）。要延长上下文窗口，我们只需要将钟表刻度调细一点（调整基底频率参数 $\\theta$）。",
                interview_script: "1. 阐明RoPE的根本价值是：通过绝对位置编码的形式，在注意力矩阵的乘法计算中，自然导出相对位置关系，完美契合Transformer只关注相关性这一底层逻辑。\n2. 解释其如何将 $D$ 维向量两两拆分成 $D/2$ 个二维复数子空间，对每一个二维子空间乘以具有特定旋转角度的位置复数 $e^{i m \\theta}$。\n3. 说明线性外推性：讲解在超长文本微调时，如何通过NTK-aware Scaled RoPE等插值算法扩展基本频率底数，使得原本只能处理4k长度的模型，在零训练下外推至32k甚至更高。"
            },
            {
                term: "FlashAttention IO 瓶颈与在线 Softmax",
                desc: "针对 GPU 显存层次设计的高速注意力加速机制，解决了长序列 O(L²) 的显存限制。",
                details: [
                    "**硬件限制背景**：传统 Attention 需要将 $L \\times L$ 的注意力矩阵写回高延迟的显存 HBM，再读取回高速的 SRAM 计算 Softmax，频繁的 GPU 读写 IO 延迟远大于实际浮点运算开销。",
                    "**核心改进：Tiling (分块计算)**：\n  FlashAttention 将输入矩阵分割成块，调入 SRAM。核心难点在于 Softmax 的全局指数归一化。它采用**在线 Softmax 更新算法 (Online Softmax)**，在分块读取时，维护并不断更新局部最大值 $m^{(i)}$ 和累加和 $d^{(i)}$。当所有分块处理完，结果能精确还原全局 Softmax 的加权和，从而实现 $O(L)$ 的额外显存开销，速度提升 2 至 4 倍。\n  **FlashAttention-2** 进一步优化了分块并行顺序，提升了 GPU 乘加计算单元（Tensor Cores）的利用率。"
                ],
                code: `# FlashAttention-2 核心思想是减少共享内存（SRAM）与寄存器之间的冗余数据加载
# 并在序列长度方向（Q的块级别）实现高效的多WARP并行调度
# 推理调用：from flash_attn import flash_attn_func`,
                analogy: "这就像厨师做菜。大容量显存（HBM）是远处的仓库，高频缓存（SRAM）是手边的砧板。传统的 Attention 就像切完一个番茄就要跑去大仓库登记一次（写入 $L \\times L$ 矩阵），再跑回来切下一样，来回搬运耗费了 90% 的时间。FlashAttention 则是把大材料切成小丁装进小碗（Tiling），在手边砧板上一次性完成调味加和（在线Softmax更新），只把最后做好的菜（Attention Output）送回大仓库。",
                interview_script: "1. 明确指出FlashAttention不是修改了Attention的数学公式，而是修改了其在GPU上的内存读写（IO）实现机制，属于系统级算子融合。\n2. 讲清核心概念——在线Softmax更新：由于Softmax分母需要知道所有元素的指数和，传统方法必须全局扫描。在线Softmax通过巧妙公式变形，使得每次新来一个局部块，都可以用旧的局部最大值与当前局部最大值进行缩放对齐，从而实现了单向分块流式计算。\n3. 说明它将空间复杂度从 $O(L^2)$ 降低到 $O(L)$（只保存块级别的中间标量），让显卡能训练更长上下文的模型。"
            },
            {
                term: "KV Cache 机制与 GQA / MQA 降本",
                desc: "大模型自回归解码（Generation）阶段显存吞吐量优化的绝对关键技术。",
                details: [
                    "**KV Cache 痛点**：在大模型推理的自回归阶段，前一步算好的 Token 的 $Key$ 和 $Value$ 向量在未来的 Step 中是固定不变的。如果不保存，每次生成新 Token 都要重算之前所有 Token，导致计算开销呈平方级暴增。因此，将先前所有 $K$ 和 $V$ 缓存到显存中，当前 Step 只需计算新 Token 的 $Q$ 并与历史 $K, V$ 进行点积，称为 **KV Cache**。但这带来了极大的显存带宽瓶颈。",
                    "**注意力架构演进**：\n  - **MHA (Multi-Head Attention)**：每个 $Q$ 头都有对应独立的 $K$ 头和 $V$ 头。当 Batch Size 和序列很长时，KV 显存巨大，内存带宽极度受限。\n  - **MQA (Multi-Query Attention)**：所有 $Q$ 头共享单一的一组 $K$ 头 and $V$ 头。KV 显存暴减至 $1/HeadNum$，但由于信息压缩过于极端，会导致模型表达能力和生成质量有一定降级。\n  - **GQA (Grouped-Query Attention)**：折中方案（Llama 3, Qwen 2 标配）。将 $Q$ 头分为 $G$ 个组，每组内的 $Q$ 头共享一组 $K$ 和 $V$ 头。既大幅降低了 KV Cache 显存读写带宽开销，又几乎完全保持了 MHA 的生成效果。"
                ],
                code: `# KV Cache 的理论大小计算（以FP16/BF16为例）：
# Size = 2 * 2 * n_layers * n_heads * d_head * seq_len * batch_size (Bytes)
# 针对 GQA，需要将 n_heads 替换为 n_kv_heads (通常为 n_heads/8)`,
                analogy: "这就像玩解密游戏。每回答一个问题，都需要查看之前所有的线索卡。KV Cache 就是把看过的线索卡（KV向量）全部平铺在桌上，回答下一题时直接拿手里的新卡（Query）去配对，不需重新查阅档案（免去重算）。MHA 就像是每个侦探都有一套专属的线索卡，桌子很快堆不下。MQA 就像是 32 个侦探共享一张桌子和一套卡片，容易看花眼（精度降级）。GQA 则是把侦探分 4 人一组，每组共用一张小桌子，速度和精度达到平衡。",
                interview_script: "1. 能够清晰给出自回归解码的数学推导，解释每次新生成一个词，它的 $K$ 和 $V$ 是对过去上下文的提炼，具有独立性，如果不做缓存就会导致 $O(L^2)$ 计算量。\n2. 深入探讨MHA、MQA和GQA之间的异同，强调GQA之所以是目前大模型的主流，是因为它在降低KV Cache带宽延迟（Memory-Bound问题）的同时，保留了模型的多头空间建模能力。\n3. 给出一个典型的KV Cache占用大小计算公式，证明其在大批量长上下文下会直接吃干GPU显存，需配合PagedAttention（Page机制）进行显存池化管理。"
            },
            {
                term: "激活函数演进: ReLU, GeLU 与 SwiGLU",
                desc: "神经网络非线性变换函数的发展历程及 SwiGLU 的底层表达优势。",
                details: [
                    "**ReLU (修正线性单元)**：$f(x) = max(0, x)$。计算极快，有效缓解梯度消失，但由于负半区导数完全为 0，会导致部分神经元“永久死亡”（Dead ReLU 问题）。",
                    "**GeLU (高斯误差线性单元)**：$GeLU(x) = x P(X \\le x)$。它引入了随机正则化思想，让输入值根据自身大小概率性地决定是否通过。其数学公式常用近似公式：$0.5x(1 + \\tanh[\\sqrt{\\frac{2}{\\pi}}(x + 0.044715x^3)])$。在正负半区平滑可导，是 BERT 和 GPT-3 的标配。",
                    "**SwiGLU (门控双线性激活函数)**：现代开源 LLM 的基准选择（如 Llama）。其公式为：$SwiGLU(x) = (x W \cdot Swish_1(x V))$。SwiGLU 相当于一个门控机制，利用 Swish 函数作为门控开关，配合双线性乘积。大量消融实验表明，SwiGLU 虽增加了少量参数，但其非线性拟合与梯度流动能力明显强于单一激活函数。"
                ],
                code: `# PyTorch 实现 Llama 中的 SwiGLU 激活层
import torch.nn.functional as F

class SwiGLU(nn.Module):
    def __init__(self, in_features, hidden_features):
        super().__init__()
        self.w = nn.Linear(in_features, hidden_features)
        self.v = nn.Linear(in_features, hidden_features)
        
    def forward(self, x):
        # 门控分支使用 Swish(x) = x * sigmoid(beta*x)
        return F.silu(self.w(x)) * self.v(x)`,
                analogy: "ReLU 就像是一扇普通的声控门，声音大于 0 分贝就全开，小于 0 分贝就死死关着，容易造成门锁损坏（Dead ReLU）。GeLU 就像是防夹自动门，根据你走过来的速度（高斯分布概率），以一种平滑的曲线自动开闭，负区间也有微弱的缝隙。SwiGLU 则是豪华的“指纹双通道门”：通道 A 计算数据特征（$xV$），通道 B 计算授权门禁（$Swish(xW)$），两个通道相乘做双线性融合，只有授权通过且有实体特征时才能通过，安全性（表示能力）极高。",
                interview_script: "1. 简单说明激活函数的演进是为了克服不可导性及Dead神经元问题。\n2. 解释GLU（门控线性单元）引入了双线性投影的优势。说明SwiGLU作为GLU与Swish（SiLU）的结合，其最核心的数学优势是具备平滑的一阶/二阶梯度，使得网络在深层训练时能以更平稳的曲率收敛。\n3. 说明SwiGLU虽然将前馈神经网络（FFN）的线性映射层数量从两层增加到三层（W1, W2, W3），增加了参数量，但其带来的模型泛化能力提升非常显著，因此被Llama等几乎所有现代大模型广泛采纳。"
            },
            {
                term: "深层网络梯度流稳定方案",
                desc: "深入参数初始化与残差连接的数学机制，控制万亿级参数训练的边界波动。",
                details: [
                    "**初始化控制 (Kaiming / He 初始化)**：\n  如果权重过大，信号经过多层传播会呈指数放大（梯度爆炸）；如果权重过小，信号会快速衰减至 0（梯度消失）。Kaiming 初始化针对 ReLU 激活函数，设定权重初始化方差为 $Var(W) = \\frac{2}{n_{in}}$，保证输入和输出在统计层面的方差守恒，避免了深层网络的数学崩溃。",
                    "**残差干线与常数梯度回传**：\n  残差公式 $x_{l+1} = x_l + F(x_l, W_l)$，在反向传播计算对当前层输入 $x_l$ 的导数时：\n  $\\frac{\\partial \\mathcal{L}}{\\partial x_l} = \\frac{\\partial \\mathcal{L}}{\\partial x_{l+1}} \\frac{\\partial x_{l+1}}{\\partial x_l} = \\frac{\\partial \\mathcal{L}}{\\partial x_{l+1}} (1 + \\frac{\\partial F(x_l, W_l)}{\\partial x_l})$。\n  由于括号中存在常数项 1，即使残差分支的导数趋于 0，全局梯度依然能够无损传回输入端，这在数学上为极深层网络训练提供了铁壁般的保障。"
                ],
                code: `# PyTorch 中的 Kaiming 初始化调用
import torch.nn.init as init
linear = nn.Linear(512, 512)
init.kaiming_normal_(linear.weight, mode='fan_in', nonlinearity='relu')`,
                analogy: "这就像是铺设一条超长的海底光缆（上百层的神经网络）。信号（梯度）在传播时很容易因为长距离损耗而彻底消失。为此，我们做两件事：一是在源头发射端，根据光缆粗细精算初始发射功率（Kaiming初始化），既不能烧断也不能太小；二是在整条光缆中额外铺设一条超导备用铜线（残差连接的直连通道），即使信号放大器（卷积/注意力分支）全部断电没信号，最核心的信息依然可以通过备用铜线无损流回起点。",
                interview_script: "1. 阐述深层网络训练的头号大敌是梯度消失和梯度爆炸，核心解决手段就是“科学的初始化”加上“残差直连结构”。\n2. 深入剖析残差块反向传播的数学公式，核心指明对当前输入求偏导时，会自然包含一个“+1”的常数项。正是这个常数项，将乘法链条转化为了加法求和，使梯度能绕过权重衰减，稳定传递回浅层。\n3. 说明在训练大模型时，初始化权重的缩放因子往往要除以层数的平方根（如 $1/\\sqrt{2 N_{layers}}$），是为了控制随着层数加深，输出残差累加导致的方差爆炸问题。"
            }
        ]
    },
    {
        id: "llm_rag",
        name: "大模型、RAG与Agent",
        icon: "message-square",
        items: [
            {
                term: "高级提示词工程与 DSPy 自动编译",
                desc: "从经验性 Prompt 撰写走向工程化、系统化大模型指令自动优化的演进路径。",
                details: [
                    "**CoT / ReAct / Reflexion 交互范式**：\n  - **CoT (思维链)**：显式促使 LLM 生成中间推理步骤。在数学和逻辑推理中，引入 Few-shot CoT 模板可大幅提升逻辑链条正确率。\n  - **ReAct (推理-行动)**：模型在决策时交替输出 Thought -> Action -> Observation，形成闭环。\n  - **Reflexion (反思环)**：智能体将先前的失败执行记录和评估指标输入给自身的“评判器”，生成反思日志，并在下一轮执行中将反思日志作为上下文以修正行为路径。",
                    "**DSPy (声明式自提高提示语言)**：\n  - **核心痛点**：传统的 Prompt 工程高度依赖人工微调，当底座大模型更换或数据集改变时，之前的 Prompt 往往失效。\n  - **DSPy 原理**：将 Prompt 开发转变为模块化编程（类似于 PyTorch 写网络）。用户只需定义输入/输出签名（Signatures）和逻辑管道（Modules），DSPy 编译器会针对给定的评测指标（Metric），使用优化器（如 BootstrapFewShot）自动在训练集上寻找、组合并微调最优的提示语和少样本示例，免去了人工调试 Prompt 的繁杂工作。"
                ],
                code: `import dspy
# 定义输入输出签名，无需在Prompt中写大段说明
class QA(dspy.Signature):
    question = dspy.InputField(desc="用户的算法提问")
    answer = dspy.OutputField(desc="专业的公式推导与原理解释")

# 构建基于多路检索的 RAG 管道模块
module = dspy.RetrieveThenRead(signature=QA)
# 自动编译微调 Prompt
# optimizer = dspy.teleprompt.BootstrapFewShot(metric=my_metric)
# compiled_module = optimizer.compile(module, trainset=train_set)`,
                analogy: "手写提示词就像是用各种古怪的手势和语气去驯服一只野生大象（LLM），每次换大象手势都得重练。DSPy 就像是为大象装了一套“自动驾驭系统”。我们程序员只需用代码定义好方向和终点（签名Signature，如输入问题输出代码），优化器就会在跑道（评估集）上进行几百次尝试，自动摸索出大象最听得懂的震动信号（生成最完美的few-shot和提示语），大象换了，系统自动重新编译适应。",
                interview_script: "1. 介绍CoT和ReAct的区别，强调ReAct将推理和外部环境接口交互融合起来，是Agent实现函数调用（Tool Calling）的基础。\n2. 讲清DSPy的划时代意义：它提出了“Prompt即代码”的声明式编程理念。传统方法手工调参Prompt，一旦大模型迭代就前功尽弃。DSPy将输入/输出声明解耦，利用强化学习或少样本自助生成器，把Prompt优化变成了一个在约束指标下自动编译和微调的过程，是工业级Agent提示词维护的未来方向。"
            },
            {
                term: "企业级高可靠 RAG 检索管线设计",
                desc: "解决大模型企业知识落地“语义鸿沟”与“信息冗余”的生产级架构设计。",
                details: [
                    "**语义切割 (Semantic Chunking)**：弃用粗暴的字符长度截断。使用 Embedding 模型计算句子之间的余弦相似度，当相似度突变时才执行切割，保持切片内语义的连续和完整。",
                    "**多路混合检索与 RRF 融合**：\n  - **Dense Retrieval**：通过向量模型捕捉长文本深层语义相关性。\n  - **Sparse Retrieval (BM25)**：通过词频 TF-IDF 匹配专有名词、设备代码（如无人机型号、卫星代号）。\n  - **RRF (Reciprocal Rank Fusion) 融合**：使用公式 $RRF\\_Score(d) = \\sum_{m \\in M} \\frac{1}{k + r_m(d)}$（通常 $k=60$），将两路粗筛排序无参融合，筛选出 Recall 最优的前 100 个 Chunk。",
                    "**Cross-Encoder 重排 (Rerank)**：\n  向量检索模型（双塔模型）为了检索速度，将 Query 和 Doc 独立编码，损失了两者之间的高阶交叉特征。Rerank 采用单塔交叉模型，将 Query 和 Doc 拼接后共同送入网络，全方位计算细粒度语义相关性得分。测试表明，通过重排只保留 Top 5 送入大模型，能将幻觉率降低 40% 以上并大幅减少输入 Token。"
                ],
                code: `# 混合检索倒数排名融合 (RRF) 算法实现
def rrf(dense_ranks, sparse_ranks, k=60):
    rrf_scores = {}
    for doc, rank in dense_ranks.items():
        rrf_scores[doc] = rrf_scores.get(doc, 0.0) + 1.0 / (k + rank)
    for doc, rank in sparse_ranks.items():
        rrf_scores[doc] = rrf_scores.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)`,
                analogy: "这就像企业招聘人才。第一步是海选（混合检索），HR部门既看综合素质得分（向量模型语义查找），又硬性筛学历和证书（BM25关键词检索）。两份名单合并（RRF融合）筛选出 100 个人。第二步是专业笔试与面试（Reranker重排），由于面试成本高（LLM上下文限制），不能让这 100 人全上，只能由专业技术总监把他们和岗位描述放在一块仔细对比打分（交叉模型），最后只挑出最匹配的前 5 个人去见老板（送入大模型）。",
                interview_script: "1. 深入阐述从天真RAG（Naive RAG）到高级RAG（Advanced RAG）的升级路径。说明天真RAG在面对长文本时，会因为生硬的分块导致检索丢失上下文。\n2. 解释混合检索的互补性：Dense对语义理解好但容易漏掉专有名词和型号；Sparse（BM25）专门精准咬合型号和专属词汇。RRF作为无参融合算法，能将两者的排名字数差异进行缩放加和，表现出极佳的粗筛效果。\n3. 说明Reranker的作用：双塔模型（如SentenceTransformers）只做局部内积，Cross-Encoder进行全局Self-Attention交互，计算虽慢但极准，适合在候选集较小时做临门一脚的精筛。"
            },
            {
                term: "微软 GraphRAG 拓扑索引与社区总结",
                desc: "利用知识图谱技术解决宏观、全局性、多文档联合分析的 RAG 创新范式。",
                details: [
                    "**构建索引阶段 (Index Phase)**：\n  1. **实体与关系抽取**：利用大模型遍历非结构化文本，抽取文本中的实体（如地名、设备、指标）、关系（如意图、所属）和声明，构建异构图。\n  2. **图聚类 (Graph Partitioning)**：利用 Leiden 算法对构建的图进行多层级拓扑聚类，将图划分成多个相互紧密连接的“社区 (Communities)”。\n  3. **社区摘要生成 (Community Summaries)**：调用大模型为每一个社群自动生成包含核心议题、结论的总结性报告，并将这些报告持久化为文档向量。",
                    "**查询阶段 (Global Query vs. Local Query)**：\n  - **Global Query**（全局查询，如“近三年来航测报告反映的水体变化趋势是什么？”）：系统不直接检索单个 Chunk，而是并行检索图中的多个相关社区摘要，再由 LLM 将多份摘要融合成最终报告。这解决了传统向量 RAG 只能见树木（聚焦局部 Chunk）不能见森林（系统总结）的软肋。"
                ],
                code: `# GraphRAG Pipeline的核心是用Leiden图聚类算法进行社区发现
# 构建多层级的社区索引：社区(0)->社区(1)->社区(2)
# 全局检索时，生成各层级摘要的并联合并问答`,
                analogy: "传统的向量 RAG 就像是在图书馆里搜论文，只搜包含某些句子的那几页（局部Chunk匹配），这导致当你问“这个作者的所有书的核心思想是什么”时，大模型无法给出一个完整的答案。GraphRAG 则是派大模型通读所有书，拉出一张人物和事件的关系网（图谱），然后用社团划分算法，把经常互动的角色聚堆成不同的“朋友圈”（Leiden社区），并为每个朋友圈写一份活动汇报（社区总结）。你提问时，直接找朋友圈报告，立马洞悉全局。",
                interview_script: "1. 指出传统向量RAG的根本短板——“见树不见林”，无法处理全局性的横向归纳提问。\n2. 阐述GraphRAG的构建核心是：大模型抽取三元组建立实体关系图，加上Leiden图聚类算法。解释Leiden算法能以非层级网络为基础寻找图的社群模块度最大化，切分出密集的拓扑群落。\n3. 说明查询模式：Local Query适合精准细节定位（查找具体实体周边的一阶和二阶关联信息）；Global Query适合主题性归纳（检索图层级较高处的社区报告并并行融合），这在处理企业审计、全局报告分析中是颠覆性提升。"
            },
            {
                term: "LoRA vs. DoRA 权重高效微调原理",
                desc: "LoRA 是基于低秩矩阵乘积的微调，DoRA 则是将其进一步分解为幅度和方向进行优化。",
                details: [
                    "**LoRA (低秩自适应) 原理**：\n  冻结原权重 $W_0 \\in \\mathbb{R}^{d \\times k}$，旁路并联两个低秩矩阵 $A \\in \\mathbb{R}^{d \\times r}$ 与 $B \\in \\mathbb{R}^{r \\times k}$ ($r \\ll d$)。微调时只训练 $A, B$，前向传播为：$W = W_0 + \\frac{\\alpha}{r} BA$。这样使得训练显存消耗下降 60% 以上，且推理时可直接把 $BA$ 合并回主权重，零额外时延。",
                    "**DoRA (权重分解低秩适应) 原理**：\n  DoRA 认为 LoRA 在微调时将参数的幅度和方向绑定更新，限制了表达能力。DoRA 将原权重矩阵进行**幅度 (Magnitude)** $m \\in \\mathbb{R}^{1 \\times k}$ 和**方向 (Direction)** $V \\in \\mathbb{R}^{d \\times k}$ 的解耦分解：$W = m \\frac{V}{||V||_c}$。微调时，幅度 $m$ 直接更新，而对于方向矩阵的微调量 $\\Delta V$，则通过 LoRA 低秩矩阵 $BA$ 来近似，从而在不增加推理参数的前提下，使微调效果极其逼近 Full Fine-tuning。"
                ],
                code: `# DoRA 的权重更新公式实现思想
# 引入缩放因子和幅度分量 m 
# W = m * (W_0 + B @ A) / norm(W_0 + B @ A)
# 通过解耦幅度m和方向分量，使微调的梯度更新方向更加稳定`,
                analogy: "LoRA 就像是你要修改一幅画，但画作本身（主权重）被锁在玻璃柜里，你只能在玻璃柜外层覆一张薄膜（低秩矩阵A、B），在薄膜上画改动。DoRA 则是把画笔分解为两个分量：笔触的力度大小（幅度 $m$）和下笔的方向角度（方向 $V$）。你只在薄膜上修改画笔的方向（对 $V$ 施加 LoRA），而把力度大小单独写在画布外直接调。由于方向和力度分开了，画出来的画细节极为细腻，无限逼近直接在画作上动笔（全量微调）。",
                interview_script: "1. 熟练写出LoRA的低秩相乘公式，讲明初始化时 $A$ 用高斯分布，$B$ 用 0，以确保初始微调增量 $\\Delta W = 0$。\n2. 深入探讨DoRA与LoRA的区别。DoRA的核心创新在于引入了权重矩阵的“幅度-方向分解（Weight Decomposition）”。研究表明，在全参数微调时，参数的方向和幅度更新是弱相关的；而LoRA的更新中，方向和幅度存在高度正相关。DoRA通过解耦两者的更新，恢复了网络在方向上的优化自由度。\n3. 说明DoRA在训练中会带来轻微的显存开销（因为需要计算范数），但训练完毕后同样可以完全融合（Merge）回原权重中，推理时没有任何额外开销。"
            },
            {
                term: "多模态对齐架构: CLIP & LLaVA 底层机制",
                desc: "图文多模态特征空间对齐以及视觉-语言大模型构建原理。",
                details: [
                    "**CLIP 双塔对比预训练**：\n  使用 Image Encoder (如 ViT) 和 Text Encoder (如 Transformer) 分别提取图片和文本向量。在一个 Batch 内，最大化对角线上正样本对的相似度，最小化非对角线上负样本对的相似度。通过对比学习将图片和文本投射到了同一个共享的语义向量空间，为后续多模态图文检索打下坚实基础。",
                    "**LLaVA 视觉-大语言模型架构**：\n  - **图像编码器**：使用 CLIP-ViT 提取图像的高维特征网格 $Z_v$。\n  - **投影层 (Projection Matrix)**：使用一个简单的线性层（Linear Projection）或两层 MLP（多层感知机），将视觉特征空间向量映射到与 LLM 的文本 Token Embedding 相同的维度空间，得到视觉 Tokens $H_v$。\n  - **LLM 解码**：将视觉 Tokens 与用户输入的文本 Token 直接拼接，一并送入 LLM（如 Llama）中进行自回归解码生成。训练分为两阶段：① 预训练阶段只训练 Projection 层进行对齐；② 微调阶段冻结 Vision Encoder，对 Projection 和 LLM 执行指令微调。"
                ],
                code: `# LLaVA 前向流伪代码
class LLaVA(nn.Module):
    def __init__(self, clip_vit, projection, llama_llm):
        super().__init__()
        self.vision_tower = clip_vit
        self.multi_modal_projector = projection
        self.llm = llama_llm
        
    def forward(self, images, text_input_ids):
        # 1. 提取图像特征 [B, Grid, D_vision]
        image_features = self.vision_tower(images)
        # 2. 对齐维度投影到 LLM 隐藏维度 [B, Grid, D_llm]
        image_tokens = self.multi_modal_projector(image_features)
        # 3. 提取文本 Embedding [B, L, D_llm]
        text_embeddings = self.llm.embed_tokens(text_input_ids)
        # 4. 拼接多模态 Tokens 并送入大模型
        inputs_embeds = torch.cat([image_tokens, text_embeddings], dim=1)
        return self.llm(inputs_embeds=inputs_embeds)`,
                analogy: "这就像是一个懂英语的盲人（LLM）和一个懂画画的法国人（Vision Encoder）合作。为了让他们沟通，我们找了一位双语翻译官（Projection对齐矩阵）。法国画家画了一幅画（提取图像特征），翻译官将这幅画转化为英语单词（视觉Tokens），并将这些单词直接塞到盲人听到的英文句子中。盲人听到了整段英文（画的英语描述+提示词），便能自然地自言自语回答出画里有什么。",
                interview_script: "1. 讲清多模态大模型的核心不是从头训练一个图文大模型，而是“桥接两组预训练成熟的单模态网络”。\n2. 剖析LLaVA的构造：CLIP ViT做Encoder，中间用MLP作Projector。强调Projector的本质是矩阵缩放变换，把图像网格块转化成大语言模型能理解的“虚拟Token”。\n3. 阐述二阶段训练法：第一阶段（对齐阶段）完全冻结LLM和视觉Encoder，只用海量图文对（Captioning）训练Projector，实现“看图识字”；第二阶段（指令微调）联合微调Projector与LLM，使模型具备多模态指令交互与逻辑推理能力。"
            },
            {
                term: "Nous Hermes 3 与自进化智能体架构",
                desc: "基于高依从度 LLM 的智能体自主规划与本地“技能（Skill）”进化引擎。",
                details: [
                    "**Nous Hermes 3 的底座优势**：针对系统提示词和结构化规范有极强的执行精度。在 Agent 调试中，它支持精确地利用特定 XML 标记（如 `<tool_call>`）进行函数调用，并在检测到错误时自主捕获 Stack Trace 并输出修正指令。",
                    "**自进化 Skill Engine 环路设计**：\n  1. **自主编程求解**：接收复杂物理计算或遥感转换任务，Agent 无法一次性输出正确答案时，它会自发编写 Python 代码并调用本地 Sandbox 里的编译器执行。\n  2. **异常捕获与自我纠偏**：若执行失败，Agent 将编译器返回的 Traceback 报错信息作为 Observation 输入给自己，重新评估代码逻辑并修改，直到程序正确运行并得出验证结果。\n  3. **技能沉淀与持久化 (Skill Archiving)**：验证成功后，Agent 将这段编写成功的 Python 代码提取出来，包装成一个标准的、带有输入输出类型定义和说明文档的方法，将其写入磁盘 `skills/` 目录下（如 `coordinate_transform.py`）。\n  4. **后续调用**：未来的任务中，Agent 会首先对 `skills/` 库进行检索。一旦匹配，直接在内存中 `import` 使用，无需二次构思编码，智能体借此实现了“用得越久、积累技能越多、越聪明”的自进化机制。"
                ],
                code: `# Agent 捕获异常并编写 Skill 写入磁盘的过程
# 异常捕获机制：
try:
    exec(agent_generated_code)
except Exception as e:
    tb = traceback.format_exc()
    # 反射传回 LLM，由 LLM 生成修正版本
    agent_corrected_code = call_agent_to_fix(code, tb)
# 验证通过后写入本地 skill_pool 库`,
                analogy: "这就像一个新手木匠。当顾客要一个奇形怪状的柜子时，木匠第一次做失败了（写代码运行报错）。但他不放弃，看着木屑和断裂处（Traceback报错信息），琢磨出问题所在并做出了改进，终于做出了合格的模具（代码运行成功）。为了以后省事，他把这个模具命名挂在墙上（保存到本地Skill库）。下次再有类似要求，他直接摘下模具套用（Skill复用），日积月累，他成了墙上挂满工具的宗师级木匠。",
                interview_script: "1. 指出 Nous Hermes 3 是专为 Agent 任务微调的开源基座，其在结构化格式依从（XML解析）、反思（Self-Reflection）以及工具调用（Tool Use）上的准确率接近闭源的 GPT-4。\n2. 详细拆解自进化技能引擎的闭环：LLM生成代码 -> 编译环境运行 -> 异常捕获 -> 梯度外自我纠正 -> 技能打包持久化。强调这是解决复杂、长链条推理任务（如空间数据库自动解算）的业界最佳实践。\n3. 说明技能持久化的长远价值：它通过把高频计算逻辑转化为“确定性代码”离线化，避免了未来调用时 LLM 每次都做随机规划产生的幻觉和高昂 Token 费用。"
            }
        ]
    },
    {
        id: "cv_sam",
        name: "计算机视觉与SAM",
        icon: "eye",
        items: [
            {
                term: "Segment Anything Model (SAM) 深度解析",
                desc: "Meta 提出的零样本交互式图像分割大模型，打通了通用的视觉掩膜提取管线。",
                details: [
                    "**三大核心模块架构**：\n  1. **Image Encoder (图像编码器)**：基于 Vision Transformer (ViT) 并引入 Masked Autoencoder (MAE) 预训练。输入 $1024 \\times 1024$ 图像，经过一系列 Transformer Blocks 处理，最终下采样并转化为 $64 \\times 64 \\times 256$ 的图像 Embedding。这是模型最沉重的部分，通常在服务器 GPU 端一次性提取。\n  2. **Prompt Encoder (提示词编码器)**：接收不同交互输入。\n    - **稀疏提示（点、框）**：使用位置编码（Positional Encoding）机制投影为 256 维的嵌入表示，每个点击类型用专门的标记向量相加区分。\n    - **密集提示（先前输出的低分辨率 Mask）**：通过 4 层跨通道卷积下采样，与图像 Embedding 执行逐像素按通道相加。\n  3. **Mask Decoder (掩膜解码器)**：\n    基于双向 Transformer 交叉注意力块。一方面使 Prompt Tokens 去关联图像特征，另一方面图像特征也反向融合 Prompt Tokens。最后通过转置卷积（Transposed Convolution）将特征还原，利用两层 MLP 输出掩膜分类概率和 IoU 质量预测得分。",
                    "**消除多歧义语义设计**：如果用户点击叶子边缘，这可能代表“叶绿体”、“整片叶子”或“整盆绿植”。SAM 设计在解码端并行输出 3 个尺度的掩膜（子部分、部分、整体），结合 IoU 分数进行内部过滤，成功解决了无监督交互式分割中常遇到的歧义难题。"
                ],
                code: `# 使用 segment_anything 调用 SAM 进行点/框分割推理
from segment_anything import sam_model_registry, SamPredictor
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
predictor = SamPredictor(sam)
predictor.set_image(image_rgb)
masks, scores, logits = predictor.predict(point_coords=np.array([[500, 375]]), point_labels=np.array([1]))`,
                analogy: "SAM 就像是一个极度聪明的全能剪刀手。首先，他要把整张画仔细端详半天，把画里的颜色、纹理提炼成一张高维特征图（Image Encoder，最费时间）。接着，你在画上点一下或者画个方框（Prompt），剪刀手就会以极快的速度（Mask Decoder，仅需几十毫秒）根据特征图和你点的位置，把对应轮廓抠出来。即使你的点击有多种抠法（歧义），他也能同时剪出“大、中、小”三种规格的补丁供你挑选。",
                interview_script: "1. 重点写出SAM的结构：ViT Image Encoder（占计算量90%以上，单张耗时上百毫秒）、Prompt Encoder（轻量）、Mask Decoder（超轻量，极速交互）。\n2. 指出其在工业级部署时的关键：由于Image Encoder计算极慢，在实时交互界面中，通常将Image Encoder放在GPU服务器上跑一次，把生成的图像Embedding传回前端，用户前端点击时只调用轻量级Decoder，实现毫秒级“即点即看”响应。\n3. 说明SAM消除多重歧义机制：并行预测三个不同层级的Mask（细粒度、中粒度、粗粒度），并输出IoU质量估计分，过滤低质图像块。"
            },
            {
                term: "SAM 2 记忆机制与时序分割追踪",
                desc: "将静态图像分割无缝外推到时序动态视频分割的核心技术改进。",
                details: [
                    "**核心演进：流式记忆系统**：\n  SAM 2 为了解决视频分割中物体被遮挡、镜头移动和移出画面的高难度追踪问题，引入了**记忆机制 (Memory System)**：\n  1. **Memory Bank (记忆库)**：包含短期空间记忆（过去 6 帧的预测掩膜）和长期全局记忆（关键提示帧的特征），记忆库最多存储 $N$ 帧特征。\n  2. **Memory Attention (记忆注意力)**：当处理当前帧时，使用 Transformer 交叉注意力机制，强行让当前帧的特征与记忆库中保存的历史各帧进行跨时间、跨空间对齐。这使得模型能“记住”物体过去的运动轨迹和形态特征。\n  3. **Memory Encoder (记忆编码器)**：当前帧分割完，其生成的掩膜和当前帧特征送入轻量级记忆编码器生成记忆 Tokens，并将其压入记忆库，滚动挤占掉最老的一帧，实现流式快速运行。"
                ],
                code: `# SAM 2 视频推理基本流程
# predictor = build_sam2_video_predictor("sam2_hiera_l.yaml", "sam2_hiera_large.pt")
# state = predictor.init_state(video_path="my_video_folder")
# predictor.add_new_points(state, frame_idx=0, obj_id=1, points=np.array([[200, 300]]), labels=np.array([1]))
# for frame_idx, out_mask in predictor.propagate_in_video(state): pass # 时序传播追踪`,
                analogy: "静态的 SAM 1 就像是个盲人剪纸，只看一张图，换张图就要重新打量。SAM 2 升级成了“带脑子的摄像师”。他在追踪跑动的小狗时，手里有个“历史备忘录”（Memory Bank），记着前几帧小狗的轮廓，以及开头你圈定它时的特写（关键帧）。当小狗跑过树后被挡住（遮挡）再出来时，摄像师用当前画面对比备忘录里的特征（Memory Attention），瞬间再次认出它，实现了不跟丢的丝滑时序分割。",
                interview_script: "1. 明确指出SAM 2的核心改进是：从单图静态分割飞跃到“时序视频分割追踪（VOS）”，解决了物体快速运动、遮挡、出框再入框的对齐痛点。\n2. 讲清记忆模块（Memory System）的三要素：Memory Bank（滑窗缓存空间与提示特征）、Memory Attention（在当前帧提取特征时，对先前多帧进行跨时间交叉注意）、Memory Encoder（将本帧掩膜压缩成新记忆滑入缓存，踢出旧记忆）。\n3. 强调其在遥感视频流分析（如无人机实时监控、船只动态轨迹划分）中的工业价值。"
            },
            {
                term: "DINOv2 (视觉自监督大模型) 底层机制",
                desc: "Meta 提出的基于 ViT 的视觉自监督预训练算法，能够输出无需微调的鲁棒密集表征。",
                details: [
                    "**自监督学习架构 (DINO)**：\n  DINO 采用学生-教师网络（Student-Teacher Network）的双重蒸馏架构。输入同一张图像的不同裁剪视图（大尺度全局视图给 Teacher，小尺度局部视图给 Student），最大化学生与教师输出概率分布的交叉熵。利用指数移动平均（EMA）在不训练的情况下从学生网络动态更新教师参数，并通过中心化（Centering）和锐化（Sharpening）操作防止坍塌（Mode Collapse）。",
                    "**DINOv2 的核心演进**：\n  1. **iBOT 损失集成**：引入了屏蔽图像建模（Masked Image Modeling, MIM）损失。在学生网络输入时遮蔽部分 Patches，要求模型在 Patch 级别重建教师网络的特征，具备极其精细的密集定位表征能力。\n  2. **免微调的特征泛化**：由于训练时不使用任何人工标签，其提取的 Vision Feature 包含了最纯粹的空间结构、边缘和纹理。其特征具有极强的泛化度，直接用线性分类器（Linear Probe）或无监督 KNN 聚类，就能在语义分割、深度估计、地物解译上达到 SOTA。"
                ],
                code: `# 使用 PyTorch Hub 直接载入 DINOv2 骨干网络提取图像高维特征
import torch
dinov2_vitl14 = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14')
dinov2_vitl14.cuda().eval()
with torch.no_grad():
    # 输入为 [B, 3, 224, 224]
    features = dinov2_vitl14(image_tensor) # 提取的全局特征向量
    # 亦可调用 get_intermediate_layers 提取中间每个 Patch 的精细特征，用于语义分割`,
                analogy: "这就像教一个小孩子认字认地物。我们不用带文字的卡片教他（无标签数据自监督）。而是带他看世界，让他自己摸索规律：给他看全景图（全局视图）和局部放大图（局部视图），让他自己把两个视角的画面在脑子里拼起来，寻找“相似的内在规律”（对比学习）。如果蒙住他的一部分眼睛（Masked Patch），要求他根据露出的部分猜出被遮住部分的材质。这样培养出来的孩子，空间触觉极其灵敏，即使去到一个完全陌生的丛林（泛化领域），他也一眼就能分辨出树木和石头。",
                interview_script: "1. 讲清DINOv2的本质是自监督（Self-Supervised Learning, SSL）的视觉表征大模型，是目前CV领域的超级Backbone。\n2. 阐述核心优化：将DINO的“自蒸馏对比学习（Self-distillation）”与iBOT的“Masked Image Modeling（掩膜特征重建）”结合，使ViT不仅学到了全局语义，还学到了Patch级别的密集空间细节（对于稠密预测任务如深度估计、地物解译至关重要）。\n3. 强调其“免微调直接用于下游任务”的特性。可以直接用无监督KNN进行图像检索，或者加一层Linear层做分类，避开传统监督学习过拟合训练集的宿命。"
            },
            {
                term: "YOLO 系列演进 (YOLOv8 vs. YOLOv10)",
                desc: "经典单阶段目标检测网络在架构和免 NMS 优化方面的最新演进。",
                details: [
                    "**YOLOv8 核心设计**：\n  - **Anchor-free (无锚框检测)**：抛弃了 YOLOv5 时代繁琐的 Anchor 聚类参数，直接预测物体的中心点和边界框偏移。大幅提高了小目标检测的泛化精度。\n  - **Decoupled Head (解耦头)**：将分类分支和回归分支彻底剥离，独立计算损失，解决了分类和定位关注特征不同导致的冲突。\n  - **Task-Aligned Assigner (任务对齐分配器)**：基于分类得分与定位 IoU 的联合矩阵，动态挑选正样本，避免了分类高但定位差的样本被选为正样本的问题。",
                    "**YOLOv10 核心创新：免 NMS 训练**：\n  - **非极大值抑制 (NMS) 的动因与短板**：目标检测在推理时会生成海量重叠候选框，必须在 CPU 端执行 NMS 根据置信度过滤掉重叠框，这造成了极大的推理延迟阻碍。\n  - **双标签分配 (Dual Label Assignment)**：YOLOv10 在训练阶段，使用了一路“一对多分配”（用于提供强梯度保证收敛）和一路“一对一分配”（用于无重叠候选框生成）。在推理时，只需直接输出“一对一分支”的预测框，从而完全**抛弃了 NMS 步骤**，推理延迟暴降，吞吐量翻倍。"
                ],
                code: `# 使用 ultralytics 运行 YOLO 检测
from ultralytics import YOLO
model = YOLO("yolov10n.pt") # 默认推理不使用 NMS 算子，直接输出唯一边界框
results = model("orthophoto.jpg")
results[0].show()`,
                analogy: "这就像是特种部队去排雷。YOLOv8 是给雷区划分不同的网格直接预测雷点（Anchor-free），并且让探雷手（分类）和爆破手（回归）分工明确各干各的（解耦头）。但最后由于每个人都报告了大量重合的疑似雷区，队长必须在后台花大量时间查重过滤（NMS）。YOLOv10 则是进行了双轨特训：训练时允许大家广泛上报（一对多），但同时考核其中一个尖兵，要求他必须做到精准报告且绝不报重（一对一）。推理时只听这个尖兵的报告，彻底取消了后台查重过滤关卡（免NMS），效率翻倍。",
                interview_script: "1. 对比YOLOv8和v10的本质差别。指出YOLOv10的核心突破在于消除了单阶段检测器长年以来在推理端对NMS的依赖。\n2. 深入讲解双标签分配机制（Dual Label Assignment）：训练时，“一对多分配”使用分类和IoU得分矩阵进行正样本丰富匹配以保障收敛；“一对一分配”利用匈牙利匹配类似的一对一约束，强行让检测头在没有NMS干预下也只能输出一个最优框。两者在训练时共享 Backbone 和 Neck，推理时抛弃“一对多”分支。\n3. 强调该改进在大规模嵌入式测绘设备（如无人机机载边缘端芯片）上落地时的低时延硬件友好性。"
            },
            {
                term: "YOLO-OBB (旋转目标检测) 遥感算法",
                desc: "解决俯视视角下密集分布、斜角排列目标的特殊目标检测技术。",
                details: [
                    "**旋转框表达与遥感痛点**：在遥感卫星/无人机影像中，港口的船舶、机场的飞机、停车场的车辆往往密集且倾斜排列。若使用传统水平边界框（Horizontal Bounding Box, HBB），重叠度会极高，导致 NMS 误杀邻近目标，且包含大量地物背景噪声。YOLO-OBB (Oriented Bounding Box) 将预测框表示为 5 维参数：$(x, y, w, h, \\theta)$，其中 $\\theta$ 代表偏转角弧度，使其紧密包裹倾斜的船体和机身。",
                    "**边界值突变（Boundary Problem）的数学解决**：\n  由于角度 $\\theta$ 具有周期性（如 $-\\pi/2$ 与 $\\pi/2$ 在几何上相同，但在数学数值上突变），这会导致回归损失在边界处产生梯度爆炸。YOLO-OBB 通常将角度预测转换为分类问题（Angle Classification）或采用滑窗距离表示法，确保模型在任意旋转角度下稳定收敛。"
                ],
                code: `# 遥感旋转框数据集 DOTA 的标注格式
# 通常为八个坐标值表示旋转四边形的顶点: x1, y1, x2, y2, x3, y3, x4, y4, class_name
# 模型内部转换为 (x_ctr, y_ctr, w, h, theta) 进行回归计算`,
                analogy: "这就像给斜着停靠的豪华邮轮套救生圈。如果是水平救生圈（水平框），由于邮轮是斜着的，救生圈必须画得非常大才能套住它，这会把旁边并排停着的邮轮也圈进去，导致救生圈大量重叠，电脑查重时会误以为是多余的圈而把旁边的邮轮判定为噪声删掉（NMS误杀）。旋转救生圈（OBB）则是给救生圈加了一个旋转把手（角度 $\\theta$），刚好歪过来紧紧卡在邮轮身上，即使排得再密也各套各的，绝不穿帮。",
                interview_script: "1. 明确遥感图像特有的“鸟瞰图视角（Bird's-eye view）”和“目标密集且方向任意”的特点，说明传统水平检测框在遥感解译上的局限性（重叠高、背景噪声大）。\n2. 讲清OBB的五参数表示法 $(x, y, w, h, \\theta)$。\n3. 重点阐述如何解决角度边界突变问题（Boundary Problem）：讲解L1损失在 $-\\pi/2$ 临界点角度突变时，会导致较大的损失跃变，引起训练震荡。一般答复使用角度分类（将角度切分为180个类做分类损失）或者使用GWD（高斯瓦瑟斯坦距离）将倾斜四边形转换为2D高斯分布，用分布相似度算损失，彻底避开角度突变。"
            },
            {
                term: "地物语义分割基线: U-Net vs. FCN",
                desc: "遥感大图语义解译最经典的编码器-解码器与全卷积网络基准对比。",
                details: [
                    "**U-Net 架构与 Skip Connections**：\n  经典的对称“V字形”结构。左侧下采样提取高维抽象语义，右侧上采样逐步恢复空间分辨率。最关键的是引入了**跳跃连接 (Skip Connections)**：将左侧特征图直接与右侧对应分辨率的特征图进行通道拼接（Concat）。这使解码端拥有丰富的底层细节特征（边界、纹理），在遥感大图细小地物（如田垄、水渠、细小道路）分割上精度极高。",
                    "**FCN (全卷积网络)**：\n  开创了图像语义分割的先河。将 VGG/ResNet 等分类网络最后的连结层全部换成卷积层，实现输入任意尺寸图片输出对应掩膜。但由于其直接通过步长为 32 的转置卷积进行粗暴恢复，缺乏多级跳跃连接，其边界分割通常非常平滑、模糊，小地物易丢失。"
                ],
                code: `# U-Net Skip Connection 实现核心
# 沿 Channel 轴拼接编码器特征与解码器上采样特征
x_concat = torch.cat([encoder_feature, decoder_upsampled], dim=1)`,
                analogy: "这就像是画一副高精度的地图。FCN 就像是一个记性差的画师，他把原图缩小成草图（下采样），画好后再粗暴地用放大机放大 32 倍（上采样反卷积），画出来的公路和河流边界就像浆糊一样模糊。U-Net 则是一个聪明的画师，他在把原图缩小的同时，把每一级分辨率的精细线稿（纹理特征）保留在草稿本左侧。当他在右侧逐步放大绘制细节时，直接翻开左侧对应的分辨率草纸贴过来（Skip Connection）参考边界，画出来的田垄水沟边缘锐利清晰。",
                interview_script: "1. 区分U-Net和FCN的设计哲学。指出FCN是全卷积的开山鼻祖，但其在第32层做32倍上采样，空间位置信息丢失极多，边缘分割粗糙。\n2. 深入解析U-Net的对称编码-解码（U-shape）结构以及Skip Connection。说明Skip Connection是通过 `torch.cat` 拼接高分辨率的浅层细节特征（关注在哪）与低分辨率的深层语义特征（关注是什么），这对医学影像和高分辨率遥感细碎地物的边界保持至关重要。"
            },
            {
                term: "经典 CNN 现代化改造: ResNet vs. ConvNeXt",
                desc: "CNN 吸收 Transformer 设计思想，重夺视觉主导权的架构改造实践。",
                details: [
                    "**ResNet (残差网络)**：提出 Bottleneck Block，打通超深层 CNN 的训练壁垒，长年作为 CV 的骨干网络 Backbone。",
                    "**ConvNeXt 的现代化重构步骤**：\n  2022 年，Meta 对经典 ResNet 进行了一系列“现代化”改造，使其不仅具备 Transformer 的优势，更保留了 CNN 的高效计算：\n  1. **改变宏观设计**：调整各阶段 Block 堆叠比例，从 $3:4:6:3$ 改为 $3:3:9:3$（仿照 Swin Transformer）。\n  2. **深度可分离卷积 (Depthwise Conv)**：将卷积核大小从 $3\\times3$ 提升至 $7\\times7$（模拟自注意力的全局感受野），使用深度可分离卷积解耦空间与通道计算。\n  3. **倒置瓶颈设计 (Inverted Bottleneck)**：通道数呈 $1 \\to 4 \\to 1$ 变化，将参数量集中在低频高维特征表达。\n  4. **微观改动**：用 GeLU 代替 ReLU，减少 Normalization 频率并用 LayerNorm 代替 BatchNorm。结果表明，改造后的 ConvNeXt 在多项 CV 任务上击败了同级别 Swin Transformer。"
                ],
                code: `# ConvNeXt Block 结构包含 LayerNorm 与 Depthwise 卷积
# x -> DepthwiseConv2D(7x7) -> LayerNorm -> Conv2D(1x1) -> GeLU -> Conv2D(1x1) -> x_out`,
                analogy: "这就像是传统老武侠门派（CNN）吸收了西洋击剑（Transformer）的力量。ResNet 是老拳师，招式扎实（残差块）。而 ConvNeXt 则是把老拳师全方位升级：把原本 3*3 小快拳改成了 7*7 的大开大合拳法（大感受野）；把复杂的内功运算法改为一招一式通道拆开分算（深度可分离卷积）；同时去掉了繁多的中间繁杂套路，换成了轻量级的呼吸调整（用LayerNorm代替BatchNorm，GeLU激活）。最后，老拳师打败了洋枪队，而且功耗更低。",
                interview_script: "1. 讲清ConvNeXt的核心逻辑是：在保留CNN简单高效结构（不使用自注意力矩阵那样的 $O(L^2)$ 计算）的前提下，通过模仿Swin Transformer的宏观和微观设计，极大提升CNN在各大视觉任务上的上限。\n2. 详述四步改造：宏观阶段配比（3:3:9:3）、大卷积核（7x7 depthwise）、逆瓶颈结构（FFN结构的通道放大）、微观算子精简（减少激活和归一化层，换用LN和GeLU）。这代表了工业级神经网络骨干网络设计的高级理解。"
            },
            {
                term: "核心 CV 指标: mAP 计算与 Precision-Recall 曲线",
                desc: "全面透析目标检测与分割模型性能的最核心评测方法。",
                details: [
                    "**交并比 (IoU)**：$IoU = \\frac{Area(A \\cap B)}{Area(A \\cup B)}$。通常设定一个阈值（如 0.5），当预测框与真实框的 IoU 大于该阈值且分类正确时，判定为真阳性（TP），否则为假阳性（FP）。未检出的真实框为假阴性（FN）。",
                    "**Precision-Recall 曲线与 AP 计算**：\n  - **Precision (精准率)**：$P = \\frac{TP}{TP + FP}$。代表预测为正的样本中真正正样本比例。\n  - **Recall (召回率)**：$R = \\frac{TP}{TP + FN}$。代表所有真实正样本中被模型找出的比例。\n  - **AP (平均精度)**：在不同的置信度阈值下计算一组 $(P, R)$，绘制 PR 曲线，AP 是该曲线下的面积（积分）：$AP = \\int_0^1 P(R) dR$。\n  - **mAP**：所有类别的 AP 平均值。**mAP@0.5** 代表 IoU 阈值设为 0.5 时的平均精度；**mAP@0.5:0.95** 代表在 IoU 从 0.5 递增到 0.95（步长 0.05）的一组 mAP 的平均值，是衡量定位精度最严苛的指标。"
                ],
                code: `# 混淆矩阵判定规则
# IoU >= threshold: TP (若类别也对)
# IoU < threshold: FP
# GroundTruth未被检测到: FN`,
                analogy: "这就像在果园挑好苹果（目标检测）。Precision（精准率）是指你挑出的这一篮子果里，好苹果占了多少，如果你只挑最有把握的 1 个绝世好果，Precision 就是 100%。Recall（召回率）是指树上所有的好苹果里，被你摘下来了多少，如果你把整棵树无论好坏全部摇下来，Recall 就是 100%，但坏果（FP）也全装进去了。AP 就是我们在不断挑剔和放宽筛选条件时，精准和召回所围成的“面积”，面积越大说明挑得越好。",
                interview_script: "1. 给出 Precision 和 Recall 的严格公式，讲清真阳性（TP）、假阳性（FP）、假阴性（FN）与 IoU 阈值的判定联动。\n2. 阐述AP是PR曲线下的积分面积（AUC），代表了模型对单类别的综合检测能力；mAP是多类别的平均得分。\n3. 解释 mAP@0.5 与 mAP@0.5:0.95 的物理差异。mAP@0.5 只关注分类和大概的检测位置（比如大致框中就算对），而 mAP@0.5:0.95 强迫预测框与真实框极致贴合，是工业级算法交付的刚性定位指标。"
            },
            {
                term: "视觉自监督模型: MAE (Masked Autoencoders) 机制",
                desc: "何恺明提出基于掩膜重建的视觉基础模型预训练范式。",
                details: [
                    "**计算不对称架构设计**：\n  1. **掩膜处理**：将输入图片划分为不重叠的 Patches，并随机遮盖掉大部分（高频遮盖率，通常为 75%）。\n  2. **轻量化 ViT Encoder**：只将未被遮盖的 25% 的 Patches 输入到重型 Transformer 编码器中，计算开销暴减 3/4。\n  3. **Mask Tokens 填充**：将编码后的特征与可学习的共享 Mask 标记拼接回完整图像网格。\n  4. **轻量化 Decoder 像素重建**：通过一个很浅的 Decoder 重建被遮盖 Patches 的原始像素值，损失函数采用 MSE 损失。预训练成功后的 Encoder 具备极强的空间先验认知，能完美迁移至遥感和缺陷检测分类任务中。"
                ],
                code: `# MAE 核心流程伪代码
# patches = patchify(images) # 切块
# x_keep, x_masked = random_masking(patches, mask_ratio=0.75) # 掩膜75%
# latent = encoder(x_keep) # 仅编码剩余的25%
# x_all = cat(latent, mask_tokens) # 还原顺序拼接
# reconstructed_pixels = decoder(x_all) # 重建图像`,
                analogy: "这就像做英语阅读理解填空。传统的自监督拼图很慢。何恺明的方法是：拿出一张图，用黑墨水把 75% 的画面全涂黑（Mask处理），只留下 25% 支离碎屑。我们让一个大专家（Encoder）去仔细端详这 25% 的零碎碎片提取特征。接着把特征和黑墨水块拼接回原位置，让一个助理（轻量Decoder）根据专家的指点，把涂黑的 75% 像素全部画出来。由于专家只看了 25% 的内容，画画速度暴增，且被迫学会了极其强大的“见微知著”空间脑补本领。",
                interview_script: "1. 重点突出MAE的“不对称架构设计”：将 75% 的图像掩膜，且让重型的 Encoder 只计算剩下的 25% 区域，这使得图像 Transformer 的计算开销骤降一个数量级，支持超大模型预训练。\n2. 解释为什么图像的掩膜比例（75%）要远高于文本的掩膜比例（BERT的15%）：图像的信息冗余度极高，如果只蒙住15%，模型直接复制邻近像素就能蒙对，学不到深层的几何空间先验；只有蒙住75%，才能强迫模型学到深刻的语义三维拓扑特征。\n3. 说明预训练完毕后，直接丢弃 Decoder，保留 Encoder 迁移到下游分类、检测任务中，可显著提升收敛效率。"
            }
        ]
    },
    {
        id: "rs_uav",
        name: "遥感算法与无人机",
        icon: "navigation",
        items: [
            {
                term: "摄影测量学 SfM 重建与 Bundle Adjustment 细节",
                desc: "从倾斜航拍图像重构地面三维空间场景的核心计算管线。",
                details: [
                    "**空三与 SfM 的数学基础**：\n  1. **特征提取**：利用 SIFT 提取每张图像尺度与旋转不变特征点，利用 KD-Tree 进行两两照片匹配，通过 RANSAC 算法计算基础矩阵并剔除误匹配。\n  2. **初值解算**：选择重叠度最高的照片对，计算本质矩阵并分解出相机位姿 $(R, T)$，利用三角化计算稀疏点云，随后使用 PNP 算法逐步将新相机的相对位姿迭代接入系统。\n  3. **光束法平差 (Bundle Adjustment)**：\n    这是全局精度的决定性步骤。建立共线方程方程，目标函数是最小化所有特征点在所有相机相片上的**重投影误差 (Reprojection Error)**：\n    $min_{a_j, X_i} \\sum_{i=1}^M \\sum_{j=1}^N \\rho(||x_{ij} - P(a_j, X_i)||^2)$\n    其中 $a_j$ 为相机 $j$ 的内参及外方位元素，$X_i$ 为空间点 $i$ 的三维世界坐标，$x_{ij}$ 为观测值。利用 Levenberg-Marquardt (LM) 算法求解稀疏对称矩阵（利用舒尔补 Schur Complement 提速），实现百万级未知数的高速平差迭代。"
                ],
                analogy: "SfM 就像是从几百张不同角度拍摄的照片里还原出犯罪现场的 3D 模型。我们首先在所有照片中找相同的特征记号（同名点，SIFT），然后猜相机是在什么角度按的快门（相机位姿 PNP）。最后的全局平差（Bundle Adjustment）就像是找一把拉尺：由于每张照片估出的距离都有细微偏差，我们建立共线方程，让所有视线光束穿过快门汇聚到地面三维点上，通过拉紧所有线（最小化重投影误差），把相机的拍摄位置和地面的每一个点全部矫正归位到最真实的位置。",
                interview_script: "1. 全面讲述SfM的三步法：SIFT特征提取与RANSAC粗筛特征点匹配、PNP迭代增量建图、以及最后的全局光束法平差（BA）。\n2. 深入探讨重投影误差的本质：利用解算出的相机内外参，将解算出的三维空间点 $X_i$ 重新投影回相机平面上，与其在照片上的实际像素坐标作差求范数。平差的目标就是通过非线性最小二乘（LM算法）让所有重投影误差之和达到最小。\n3. 说明平差计算中的加速手段：利用相机和路标点的稀疏矩阵特性，使用舒尔补（Schur Complement）消元计算，将大矩阵求逆降低为对角矩阵求逆，这才是航测空三处理能支撑数万张照片建图的技术关键。"
            },
            {
                term: "坐标系变换与控制点平差 (GCP/RTK)",
                desc: "高精度航测系统所涉及的地理坐标与投影平面坐标变换原理。",
                details: [
                    "**椭球体地理坐标 (GCS) 与投影面坐标 (PCS)**：\n  - **WGS84 / CGCS2000**：以地球质量中心为原点的三维椭球体空间坐标系，位置以经度、纬度、椭球高表达。\n  - **UTM / 高斯-克吕格投影**：将椭球体通过圆柱套合按度带展平的平面直角坐标系，投影计算后坐标表示为 $(East, North)$。高斯投影采用分带（如我国常用的 3 度带），在中央子午线处变形为 0。\n  - **坐标投影公式（高斯投影正解）**：将经纬度 $(L, B)$ 展开为以偏心率、子午线弧长为主导的泰勒级数，转化为高斯直角坐标 $(x, y)$。GDAL/Proj 库底层即执行此计算。",
                    "**外业控制点 (GCP) 配准数学模型**：\n  内业空三初步解算的点云坐标只具有相对空间尺寸（Relative CRS）。必须通过手动或自动刺点，导入 RTK 静态测量的地面控制点绝对坐标，执行 **七参数三维空间相似变换 (Bursa-Wolf 模型)**：\n  $\\begin{pmatrix} X_A \\\\ Y_A \\\\ Z_A \\end{pmatrix} = \\begin{pmatrix} \\Delta X \\\\ \\Delta Y \\\\ \\Delta Z \\end{pmatrix} + (1 + m) \\begin{pmatrix} 1 & -\\epsilon_Z & \\epsilon_Y \\\\ \\epsilon_Z & 1 & -\\epsilon_X \\\\ -\\epsilon_Y & \\epsilon_X & 1 \\end{pmatrix} \\begin{pmatrix} X_R \\\\ Y_R \\\\ Z_R \\end{pmatrix}$\n  通过 3 个平移参数 $\\Delta$、3 个旋转角 $\\epsilon$、1 个缩放因子 $m$，将点云刚性对齐到真实地球，定位偏差从米级缩减至厘米级。"
                ],
                analogy: "地球是个扁球体，经纬度坐标（WGS84）就像是按橘子皮标记位置。但在做工程图纸时我们必须用平整的直角网格（UTM投影），这就好比把橘子皮撕开在桌上摊平，不可避免会产生拉伸变形。刚解算出来的三维模型就像是个积木，尺寸对但不知道放在地球的哪个角落。我们去现场用 RTK 测几个钢钉的绝对经纬度作为控制点（GCP），然后运行 Bursa-Wolf 模型，给这个三维积木整体进行“平移、旋转、缩放”（共7个参数），啪地一下卡到真实的 CGCS2000 投影坐标系中，精度误差不超过 3 厘米。",
                interview_script: "1. 清晰解释地理坐标系（GCS，经纬度三维）与投影坐标系（PCS，平面二维带高程）的区别，指出测量图纸必须使用高精度PCS。\n2. 阐明为什么需要 Bursa-Wolf 七参数模型：空三模型在无控制点时只有相对比例和位置。七参数包含 3 个平移量（dX, dY, dZ）、3 个旋转角（Rx, Ry, Rz）和 1 个缩放因子（m）。\n3. 说明当测区较小且高差不大时，也可以使用简化版的三参数（仅平移）或四参数进行二维变换，但精密航测必须刺控制点解算七参数配准。"
            },
            {
                term: "植被与水体光谱指数 (NDVI, SAVI, NDWI)",
                desc: "利用遥感图像地物反射光谱的特征通道运算公式提取物性特征。",
                details: [
                    "**NDVI (归一化植被指数)**：\n  $$NDVI = \\frac{\\rho_{NIR} - \\rho_{Red}}{\\rho_{NIR} + \\rho_{Red}}$$\n  物理机理：健康植物叶绿素吸收红光，而细胞壁多孔结构强烈反射近红外光。取值范围 $[-1, 1]$，大于 0.2 代表有植被覆盖。主要缺点：在高密度植被区容易饱和，对土壤背景噪声敏感。\n  - **SAVI (土壤调节植被指数)**：\n    $$SAVI = \\frac{\\rho_{NIR} - \\rho_{Red}}{\\rho_{NIR} + \\rho_{Red} + L} (1 + L)$$\n    其中 $L$ 为土壤调整参数（常设为 0.5）。通过在分母引入 $L$ 并进行整体缩放，有效抑制了裸土、反射率高低起伏对植被系数计算的干扰。\n  - **EVI (增强植被指数)**：\n    $$EVI = 2.5 \\frac{\\rho_{NIR} - \\rho_{Red}}{\\rho_{NIR} + C_1 \\rho_{Red} - C_2 \\rho_{Blue} + 1}$$\n    利用蓝光波段对大气气溶胶散射的敏感性校正红光波段，解决了 NDVI 的高密植被饱和痛点，广泛用于森林盖度解译。\n  - **NDWI (归一化水体指数)**：\n    $$NDWI = \\frac{\\rho_{Green} - \\rho_{NIR}}{\\rho_{Green} + \\rho_{NIR}}$$\n    水体在近红外波段反射率极低接近于0，在绿光波段稍高。NDWI 能够完美凸显水体边界并抑制土壤和植被信号。"
                ],
                analogy: "这就像是用地物的“光谱指纹”来辨别地物。健康绿叶有两张面孔：它疯狂吞噬红光（Red）作为光合作用能量，却对近红外光（NIR）极度嫌弃全部反弹。所以通过红光和近红外的差值比例（NDVI）一眼就能看出是不是绿色植物。如果地上长草不密，泥土露出来了，我们就加个土壤调整阀门 $L$（SAVI）把泥土反射干涉过滤掉。如果是找湖泊水库，由于水在近红外下就像黑洞一样把光吸光，而绿光段有一点反射，所以用绿光减去近红外（NDWI），水体就亮如白昼了。",
                interview_script: "1. 给出各个核心光谱指数公式，阐明其物理机理：绿植对红光强吸收、对近红外强反射；水体对近红外极强吸收。\n2. 解释NDVI的痛点：① 饱和效应（植被郁闭度高时，红光吸收达到瓶颈，NDVI不再上涨）；② 土壤背景效应（稀疏植被区受背景反射干扰大）。\n3. 指出EVI通过引入蓝光波段校正气溶胶，并引入常数分量解决饱和问题；SAVI通过 $L$ 因子抵消土壤基质的反射梯度，是在复杂荒漠农田交界测绘时的首选。"
            },
            {
                term: "遥感旋转目标检测: Oriented R-CNN 架构",
                desc: "在保持极佳推理速度的同时，实现高精度遥感旋转物体提取的两阶段网络。",
                details: [
                    "**Oriented R-CNN 设计特色**：\n  传统的旋转检测模型（如 RoI Transformer）通常有多步复杂对齐，计算开销巨大。Oriented R-CNN 提出了一种极其优美的一阶段旋转建议框网络（Oriented RPN）：\n  - **轻量旋转 Proposal 生成**：传统的 RPN 预测水平框。Oriented RPN 将建议框表示为 6 维中点偏移法：$(x, y, w, h, \\Delta\\alpha, \\Delta\\beta)$。它只需使用很少的 Anchor，就能直接在 FPN（特征金字塔）上生成高质量的定向候选框（Oriented Proposals）。\n  - **Rotated RoI Align**：在第二阶段，利用 Rotated RoI Align 算子，根据定向 Proposal 的偏转角将高维特征图上的区域进行双线性插值重采样，恢复为无偏转的规则特征网格输入给 FC 分类器。实验表明，该算法在 DOTA 数据集上取得了 SOTA 的精度，且速度达到 20+ FPS。"
                ],
                analogy: "这就像在一张密密麻麻的航拍图上抓斜着停的卡车。传统的两阶段模型像是一个繁杂的筛子，先猜出一万个方框，再费力去扭转对齐（RoI Transformer，速度极慢）。Oriented R-CNN 则是直接给第一阶段派了一支轻骑兵（Oriented RPN），直接用极简的“中点偏移法”画出带倾角的长条纸片框（旋转候选区）。到第二阶段，直接用一张歪着的“印泥网格”顺着倾斜角盖下去重采样特征（Rotated RoI Align），一步到位，既快又准。",
                interview_script: "1. 说明Oriented R-CNN是目前遥感影像旋转目标检测的代表性SOTA，相比传统的RoI Transformer和Rotated RetinaNet在召回和时延上有巨大优势。\n2. 详细解释中点表示法（Midpoint Offset）：不同于复杂的角度正弦回归，它用水平包络框加上四个中点的相对位移偏差 $(\\Delta\\alpha, \\Delta\\beta)$ 直接表示旋转多边形，不仅完全避免了回归数值突变，还极易由普通RPN层直接生成。\n3. 说明 Rotated RoI Align 的机理：根据建议框的角度，将特征图网格执行仿射变换（坐标旋转），再做双线性插值，将定向RoI转化为规则输出，输入全连接层做精确分类与边界回归。"
            }
        ]
    },
    {
        id: "data_eng",
        name: "数据工程",
        icon: "database",
        items: [
            {
                term: "Spark 空间分布式 Join 与 Apache Sedona 调优",
                desc: "处理海量地理空间几何计算的分布式内存引擎底层调优。",
                details: [
                    "**R-Tree 空间索引与非均匀分区**：\n  在大规模空间 Join（例如统计全国一亿个定位轨迹点 ST_Contains 在哪些商圈多边形内）中，传统的 HashPartitioner 划分数据会导致 Shuffle 后极度的数据倾斜（因为人流高度聚集在北上广深，而海洋荒漠分区几乎为空）。\n  - **解决机制**：Apache Sedona 抛弃了 HashPartitioner，改用 **Quad-Tree（四叉树）或 K-D Tree 空间划分算法**。它首先在大数据集的抽样集上构建空间网格，对热点高密区域不断细分，稀疏区域进行合并，保证每个网格内的几何元素数量均匀。然后，将这个网格分配作为 RDD 分区界线，使各 Task 计算负载完美均衡，空间 Range Join 性能提升 5 - 10 倍。\n  - **点面空间索引**：每个分区内部使用 Java 拓扑套件（JTS）在内存中构建 R-Tree 树状索引，将点点匹配的 $O(M \\times N)$ 高复杂度降为 $O(M \\log N)$。"
                ],
                analogy: "这就像把全国的轨迹点按省份划片派给不同的派递员（Hash分区）。由于上海北京的快递量（数据量）是青海西藏的一万倍，上海派递员会被活活累死，青海派递员闲得喝茶（数据倾斜）。Apache Sedona 的做法是改用“空间四叉树网格划分”：看哪里快件多，就把那条街不断切细，切成 100 个小网格；看哪里快件少（如大沙漠），就把几个省合成一个大网格，保证每个派递员拿到的快件数几乎一模一样，大家齐头并进，速度快了几十倍。",
                interview_script: "1. 明确指出传统大数据分区算子（如Hash, Range）完全不感知地理几何的空间局部性，直接用于空间 Join 会因为人口高聚敛导致Shuffle数据倾斜 OOM。\n2. 讲清Sedona调优的核心是：① 空间分区器（Quad-Tree/KDB-Tree Partitioning），基于空间数据密度的分级剖分，确保空间负载均衡；② 分区内空间索引（Partition R-Tree Index），将点面匹配从暴力循环优化为对数级树搜索。\n3. 说明在做 Sedona Join 时，要善用 Broadcast Broadcast Join（如广播较小的多边形数据集），避免点和多边形双重 Shuffle 带来的网络带宽灾难。"
            },
            {
                term: "Flink 状态管理与端到端 Exactly-Once 机制",
                desc: "实时空间物联网与监控数据流处理中的状态持久化与事务提交保证。",
                details: [
                    "**Chandy-Lamport 快照算法与 Barrier 机制**：\n  Flink 在流通道中异步注入名为 **Checkpoint Barrier (屏障)** 的特殊标记。当算子从各个输入流接收到序号相同的 Barrier 时，会触发**对齐 (Barrier Alignment)**，并将算子当前的内存状态（如滑动窗口统计、滑动平均NDVI值）进行快照，异步写入 RocksDB 分布式存储。对齐保证了当上游崩溃重启时，系统能回溯到所有算子状态完全同步的历史点，这是 Exactly-Once 状态一致性保证的基石。\n  - **双阶段提交 (Two-Phase Commit, 2PC) 事务写入**：\n    实现端到端的 Exactly-Once，不仅需要 Flink 内部状态一致，还要保证下游 Sink 输出不重复。Flink 与 Kafka Sink 结合采用两阶段提交：\n    1. **Pre-commit 阶段**：算子在接收到 Barrier 执行快照时，向 Kafka 发送预提交事务，写入数据但标记为未提交。\n    2. **Commit 阶段**：当所有算子 Checkpoint 均宣告成功，JobManager 协调器向所有 Sink 发出 Commit 信号，将 Kafka 事务状态标记为已提交，下游消费者即可读取。若中途崩溃，预提交事务将被 Kafka 回滚，彻底避免了重复写入。"
                ],
                analogy: "这就像是多人网络联机游戏自动存档。游戏服务器每隔 10 秒在所有人的通信包里插一张“存档卡”（Barrier）。当所有人都在同一时刻收到了这张存档卡（Barrier对齐），服务器就自动把大家当前的血量和位置存入数据库（Checkpoint）。Exactly-Once 写入下游就像是在刷卡消费：你先向系统提交“准备刷卡申请”（预提交），一旦确认所有人存档完成，协调器大喊一声“执行”（提交阶段），钱才真正扣掉；如果中途网络断了，刚才的刷卡申请直接撤销（回滚），防止多刷一次卡。",
                interview_script: "1. 重点解释 Chandy-Lamport 分布式快照算法在Flink中的具体实现——Barrier 对齐流机制。解释对齐屏障如何确保流的局部有序性和状态快照的一致性。\n2. 详述端到端 Exactly-Once 的核心支柱——双阶段提交协议（2PC）。讲清 Pre-commit 和 Commit 两个阶段在 Sink 算子（如 FlinkKafkaProducer）中的生命周期配合，以及协调器 JobManager 的两阶段决策机制。\n3. 说明如果下游存储（如 MySQL）不支持事务回滚，就无法实现Exactly-Once，只能通过幂等写入（Idempotent Write）退而求其次地保证最终一致性。"
            },
            {
                term: "向量数据库索引优化: Milvus HNSW 调优",
                desc: "在高并发 RAG 和多模态大模型应用中，如何精确调试向量索引提升检索效能。",
                details: [
                    "**HNSW 图结构超参的物理意义与调优建议**：\n  - **M**：构建多层图时，为每个新节点建立的最大单向连接边数。取值范围 $[4, 64]$。针对高维密集嵌入（如 1536 维的 OpenAI 向量或多模态 CLIP 向量），建议将 M 设为 $16$ 到 $32$。M 越大，高维检索精度（Recall）越好，但建库速度显著放缓，内存消耗增大。\n  - **efConstruction**：构建索引阶段近邻搜索范围的限制长度。推荐设为 $200$。efConstruction 越大，图连接关系越合理，虽然建库耗时，但在极高精度检索时有优势。\n  - **efSearch**：在线查询检索时动态评估邻居列表的范围（Search Window）。这是**调节 QPS 和 Latency 的终极开关**。增加 `efSearch`（如从 16 调到 64）可显著提升 Recall，但会导致单次检索时延增加、QPS 下降。生产线上需通过动态压测，在召回率与并发量之间寻找帕累托最优解。",
                    "**Scalar-Vector 混合过滤优化**：\n  当查询带有过滤条件时：\n  - **Post-filtering (后过滤)**：先用 HNSW 筛出 Top 100 向量，再按标量条件过滤。若符合条件的报告很少，过滤后可能只剩 2-3 个甚至为空，造成“检索消失”问题。\n  - **Pre-filtering / Single-stage (单阶段混合检索)**：Milvus 在沿着 HNSW 图遍历跳转节点时，利用标量索引同步判定该节点是否符合标量条件。如果不满足，直接跳过该节点不进行向量距离计算。这需要向量库底层具备优秀的标量-向量联合联合计算。"
                ],
                analogy: "HNSW 就像是修建全国公路网。$M$ 相当于每个立交桥（节点）能伸出多少条高速路（单向边），如果路修得很多，交通网就极度四通八达（召回率高），但筑路费和占地面积（建库耗时和内存）会飙升。`efSearch` 就像是探路车的雷达扫描范围：雷达开得越大（`efSearch`值大），越不可能迷路，能找到最完美的近路（高召回），但开雷达很耗电，探路车跑得慢（时延增加、QPS下降）。",
                interview_script: "1. 表明HNSW（分层导航可收缩世界图）是目前高维向量实时检索最常用的图索引格式，其通过多层跳表结构实现了 $O(\\log N)$ 级搜索。\n2. 准确说出三个核心超参 $M$、`efConstruction`、`efSearch` 的实际物理意义和权衡（Trade-off）。指出 `efSearch` 是唯一可以在线动态调优而不需要重新建库的参数，是线上应对流量高峰和召回指标的终极杠杆。\n3. 指出混合检索（标量过滤+向量搜索）时，后过滤（Post-filtering）在稀疏标量分布下的致命缺陷（检索漏失），并说明Milvus的单阶段混合检索（Pre-filtering）在遍历图节点时同步进行标量位图（Bitset）剪枝的底层运作，显示出深厚的实战大数据背景。"
            }
        ]
    },
    {
        id: "frontier_ai",
        name: "前沿 AI 工程",
        icon: "sparkles",
        items: [
            {
                term: "Loop Engineering：Agent 闭环工程",
                desc: "把 Agent 设计成生成、执行、观察、评估、修正的持续闭环，而不是一次性 prompt。",
                details: [
                    "**核心定义**：Loop Engineering 关注 Agent 的循环控制结构。典型闭环包括 Planner 生成计划、Executor 调用工具、Observer 收集外部结果、Evaluator 评估质量、Controller 决定继续、重试、回滚或交给人工。",
                    "**工程价值**：商用 Agent 失败通常不是模型不会回答，而是缺少状态管理、错误检测、反馈修正和人工接管。闭环设计能把模型从“文本生成器”升级为“可监督的任务执行系统”。",
                    "**在求职系统中的落地**：JD 匹配可以形成 loop：解析岗位 -> 匹配简历 -> 找证据项目 -> 生成修改建议 -> 评分 -> 人工确认 -> 更新版本。每一轮都有输入、输出、评分和审计记录。"
                ],
                analogy: "一次性 prompt 像只让人写一版草稿；Loop Engineering 像完整编辑流程：先写、再检查、再改、再审核，直到达到标准或交给人工决定。",
                interview_script: "1. 先说明 Agent 工程的重点是闭环控制，不是单轮对话。\n2. 拆出 Planner、Executor、Observer、Evaluator、Controller 五个角色。\n3. 结合项目讲落地：简历/JD/作品集匹配都可以做成可回滚、可评分、可人工确认的闭环。"
            },
            {
                term: "Context Engineering：上下文工程",
                desc: "系统管理模型可见的信息，包括指令、工具、记忆、检索证据、任务状态和 token 预算。",
                details: [
                    "**不是更长 prompt**：Context Engineering 不是把所有材料塞进上下文，而是决定哪些信息该进入、以什么顺序进入、如何压缩、如何隔离不可信内容、何时刷新。",
                    "**关键机制**：上下文来源分层（系统指令、用户目标、工具结果、RAG 证据、长期记忆）、优先级排序、token 预算、证据引用、过期策略和冲突处理。",
                    "**求职场景**：针对某个 JD 生成简历时，应优先加载岗位要求、目标岗位版本、相关项目证据和事实约束，低优先级历史聊天不应污染输出。"
                ],
                analogy: "模型上下文像面试前放在桌上的资料袋。不是资料越多越好，而是要把最相关、最新、可信的材料放在最前面。",
                interview_script: "1. 把 prompt engineering 升级为 context engineering：输入不只是文本，而是一套上下文编排系统。\n2. 说明核心控制点：来源、优先级、token 预算、可信度和时效性。\n3. 强调外部 JD/网页/文档只能作为数据，不能覆盖系统规则。"
            },
            {
                term: "EvalOps 与 AgentOps：AI 应用评测和可观测性",
                desc: "为 LLM/RAG/Agent 建立评测集、回归测试、执行 trace、成本、延迟和失败分析。",
                details: [
                    "**EvalOps**：把 AI 输出质量变成可测试对象。常见指标包括准确性、证据一致性、格式合规、召回质量、幻觉率、拒答边界、延迟和成本。没有评测集的 AI 功能很难稳定迭代。",
                    "**AgentOps**：记录 Agent 的每一步执行，包括模型输入输出、工具参数、工具返回、耗时、token、费用、错误、重试和人工确认。它解决的是“出了问题能不能定位”的生产化问题。",
                    "**求职系统落地**：简历润色需要事实一致性评测；JD 匹配需要关键词覆盖和项目证据评分；面试训练需要评分 rubric 和历史趋势。"
                ],
                analogy: "EvalOps 像考试卷，告诉你答案质量好不好；AgentOps 像行车记录仪，告诉你系统每一步怎么走到这个结果。",
                interview_script: "1. 说明 AI 应用不能只靠主观感觉验收，必须有评测样例和回归测试。\n2. 区分 EvalOps 和 AgentOps：前者评质量，后者看过程。\n3. 给出落地指标：准确率、证据一致性、格式合规、延迟、成本、失败率和人工接管率。"
            },
            {
                term: "LLM Gateway 与模型路由",
                desc: "在多个模型和供应商之间统一做鉴权、路由、降级、预算、限流和日志。",
                details: [
                    "**为什么需要 Gateway**：生产系统不会把业务代码直接写死到一个模型接口上。不同任务对速度、质量、成本、隐私和稳定性的要求不同，需要统一入口来管理模型选择和失败处理。",
                    "**核心能力**：模型路由、fallback、重试、缓存、限流、预算控制、密钥隔离、日志审计和 A/B 测试。比如 JD 粗分类可走小模型，最终简历润色走强模型，敏感本地材料优先走本地模型。",
                    "**求职系统落地**：岗位解析、简历改写、面试评分、知识问答可以配置不同模型策略，并在输出里记录模型、成本、延迟和版本，便于后续评测和回滚。"
                ],
                analogy: "LLM Gateway 像机场调度塔。不同飞机飞不同航线，遇到天气不好要改降、备降、限流和记录日志，不能让每个乘客自己决定起降规则。",
                interview_script: "1. 先说明模型调用生产化不能直接耦合单一供应商。\n2. 讲清模型路由依据：任务难度、成本、延迟、隐私、稳定性和上下文长度。\n3. 给出工程能力：fallback、重试、预算、限流、缓存、日志和 A/B 测试。"
            },
            {
                term: "OpenTelemetry GenAI 与标准化可观测性",
                desc: "用标准化 telemetry 记录模型请求、token、延迟、错误和工具调用链。",
                details: [
                    "**GenAI 可观测性目标**：让 LLM 请求像普通微服务一样可追踪。一次 Agent 执行可能包含模型调用、检索、工具调用、重试和人工确认，每一步都需要 span、属性和错误信息。",
                    "**关键指标**：模型名、供应商、输入/输出 token、延迟、费用、调用状态、错误类型、工具参数、工具返回、trace id、用户会话和版本号。",
                    "**工程价值**：当简历生成错误、JD 匹配慢、RAG 引用不准时，可以从 trace 反查是哪一步出了问题，而不是只看到一个最终答案。"
                ],
                analogy: "没有可观测性的 Agent 像黑箱面试官，只告诉你结果；有 trace 的系统像全程录像，能看到每一步怎么判断、调用了什么工具、哪里失败。",
                interview_script: "1. 说明 GenAI 应用同样需要日志、指标和 trace。\n2. 说出关键字段：token、延迟、成本、模型名、工具调用、错误和会话。\n3. 强调这能支撑排障、成本优化、质量回归和审计。"
            },
            {
                term: "SWE Agent 与真实代码库评测",
                desc: "面向真实仓库 issue 的代码定位、修改、测试和回归验证能力。",
                details: [
                    "**从代码生成到代码修复**：SWE Agent 的重点不是写一个孤立函数，而是在真实仓库里读结构、定位 bug、修改相关文件、运行测试，并解释风险。",
                    "**SWE-bench 类评测价值**：真实 issue、真实代码上下文、真实失败测试和可验证 patch 更接近软件工程岗位，比算法题更能衡量工程能力。",
                    "**本项目落地**：后续拆分 app.js/resume.js 时，应先写模块边界和 smoke test，再让 Agent 辅助重构，最后用脚本验证页面挂载和语法检查。"
                ],
                analogy: "普通代码生成像让人现场写一小段函数；SWE Agent 像接手一个正在运行的项目，要先读代码、复现问题、改最小补丁、跑测试再交付。",
                interview_script: "1. 区分 coding assistant 和 SWE agent：前者帮写代码，后者能围绕真实 issue 完成修复闭环。\n2. 说明真实仓库能力包括检索、定位、补丁、测试和回归。\n3. 结合本项目讲：模块化重构必须有验收标准和自动检查，不能只靠生成代码。"
            },
            {
                term: "MCP 与 A2A：Agent 工具协议和跨 Agent 协作",
                desc: "把大模型从聊天框接到真实工具、数据源和多 Agent 网络的关键协议层。",
                details: [
                    "**MCP (Model Context Protocol)** 解决的是“模型如何安全、标准化地连接外部工具和上下文”。它把文件、数据库、浏览器、业务系统等能力封装成可发现、可调用的工具，降低每个应用都单独写插件适配层的成本。",
                    "**A2A (Agent-to-Agent)** 关注 Agent 之间如何交换任务、状态和结果。面试里可以把 MCP 解释成“模型到工具”的接口，把 A2A 解释成“Agent 到 Agent”的协作接口。两者共同支撑多 Agent 工作流、企业内知识系统和复杂任务编排。"
                ],
                analogy: "MCP 像给模型配统一插座，任何工具只要按接口接入就能用；A2A 像给多个智能体配对讲机，让它们能分工、交接和汇报。",
                interview_script: "1. 先区分 MCP 与 A2A：MCP 是模型调用工具和上下文，A2A 是 Agent 之间交换任务。\n2. 结合项目讲落地：RAG 系统可用 MCP 接数据库、文档和搜索工具；复杂求职助手可让简历 Agent、岗位分析 Agent、面试 Agent 通过 A2A 协作。\n3. 强调安全边界：工具白名单、参数校验、权限隔离、审计日志和人工确认是 Agent 工程的核心。"
            },
            {
                term: "Responses API / Agents SDK / Tool Calling 工程栈",
                desc: "新一代 LLM 应用从单次补全走向状态管理、工具调用、结构化输出和可观测执行。",
                details: [
                    "现代大模型应用不再只是 prompt + completion，而是由模型、工具、状态、文件、向量检索、函数调用和执行轨迹组成。Responses API 类接口适合统一文本、多模态输入、工具调用和流式输出。",
                    "Agents SDK 侧重把工具、任务步骤、handoff、trace 和 guardrail 工程化。面试表达重点不是“会调 API”，而是能设计工具 schema、失败重试、权限控制、输出校验和日志追踪。"
                ],
                analogy: "传统调用像给模型发短信；Agent 工程栈像给模型配了工单系统、工具箱、操作日志和质检员。",
                interview_script: "1. 说明自己会把 LLM 应用拆成输入规范、工具 schema、检索层、模型决策、执行层和审计层。\n2. 举例：知识库问答中，模型先调用检索工具，再基于证据回答，最后输出引用和置信度。\n3. 强调线上可靠性：超时、重试、幂等、结构化输出校验和人工兜底。"
            },
            {
                term: "GraphRAG 与 Agentic RAG",
                desc: "从“向量召回片段”升级到“图谱关系 + 多步检索 + 任务规划”的知识增强范式。",
                details: [
                    "GraphRAG 会把文档中的实体、关系、社区结构和摘要组织成图，使模型能回答跨文档、跨实体、跨层级的问题。它适合政策、论文、企业知识库、项目资料这类关系密集场景。",
                    "Agentic RAG 让模型根据问题动态规划检索步骤：先拆问题、选择数据源、调用检索/搜索/SQL 工具，再综合证据。关键指标包括召回质量、证据覆盖率、幻觉率、延迟和成本。"
                ],
                analogy: "普通 RAG 像在一堆便签里找相似句子；GraphRAG 像先画出人物关系图和章节地图，再顺着关系查证据。",
                interview_script: "1. 先讲普通向量 RAG 的短板：长链条问题、跨文档关系和全局摘要能力弱。\n2. 再讲 GraphRAG 用实体关系和社区摘要补足全局结构，Agentic RAG 用计划式检索提升复杂问题命中率。\n3. 落到工程：需要离线抽取图谱、在线检索融合、证据引用和评测集。"
            },
            {
                term: "Test-Time Compute：验证器、PRM 与推理扩展",
                desc: "通过增加推理时搜索、采样、评估和验证步骤提升复杂问题正确率。",
                details: [
                    "Test-Time Compute 指在推理阶段投入更多计算，让模型生成多个候选思路、用 verifier 或 process reward model 评分，再选择更可靠的答案。它常用于数学、代码、规划和多步推理。",
                    "工程权衡是准确率、延迟和成本。适合在高价值任务中按风险分层启用，例如重要报告、代码修改、数据分析结论，而不是所有问题都暴力多采样。"
                ],
                analogy: "普通推理是一次交卷；Test-Time Compute 是先打草稿、做多套解法，再让阅卷器挑最稳的一份。",
                interview_script: "1. 解释推理扩展不是单纯加大模型，而是在推理阶段增加候选生成、验证和选择。\n2. 说明 verifier/PRM 的作用：评价最终答案或中间步骤。\n3. 讲工程策略：按任务风险开关，控制延迟预算，并记录验证轨迹。"
            },
            {
                term: "MLA、GQA、KV Cache 量化与长上下文推理",
                desc: "长上下文模型的核心瓶颈是注意力计算和 KV Cache 显存，优化重点在结构和缓存。",
                details: [
                    "GQA/MQA 通过减少 Key/Value 头数量降低 KV Cache 占用；MLA 通过低秩潜变量表示进一步压缩注意力缓存。它们都服务于更长上下文、更低显存和更高吞吐。",
                    "KV Cache 量化、分页缓存、连续批处理和前缀缓存是推理服务常见优化。面试里应结合显存公式讲清楚：上下文越长、batch 越大，KV Cache 越容易成为瓶颈。"
                ],
                analogy: "长上下文像把整本书摊在桌上做笔记。GQA/MLA/KV 量化就是把笔记本压缩、合并和分页，否则桌面很快被占满。",
                interview_script: "1. 先指出长上下文成本主要来自注意力和 KV Cache。\n2. 对比 MHA、MQA、GQA、MLA 的缓存压缩思路。\n3. 结合部署讲：量化、prefix cache、paged attention 和 batch 调度决定实际吞吐。"
            },
            {
                term: "Speculative Decoding 与推理吞吐优化",
                desc: "用小模型草拟、大模型验证的方式提升生成速度，适合低延迟 LLM 服务。",
                details: [
                    "Speculative Decoding 通常由 draft model 先生成若干 token，再由 target model 并行验证。若草稿被接受，就能一次前进多个 token；若不接受，则回退到大模型结果。",
                    "它的收益取决于草稿模型速度、接受率、目标模型大小和 batch 调度。工程上还会结合量化、连续批处理、KV cache 管理、tensor parallel 和算子融合。"
                ],
                analogy: "像让实习生先写草稿，资深工程师快速批改；草稿靠谱时整体速度很快，不靠谱时也能回到资深工程师答案。",
                interview_script: "1. 说明核心机制：draft model 预测，target model 验证。\n2. 讲收益条件：草稿足够快且接受率高。\n3. 扩展到服务优化：量化、批处理、KV cache 和并行策略共同决定延迟。"
            },
            {
                term: "Discrete Diffusion Language Model",
                desc: "离散扩散语言模型尝试用非自回归或半自回归方式生成文本，是语言建模的新路线之一。",
                details: [
                    "传统 LLM 多按 token 自左向右生成。离散扩散模型把文本生成看成从噪声离散状态逐步去噪的过程，理论上更适合并行生成、编辑式生成和全局约束。",
                    "它仍处在快速研究阶段。面试中适合表达为“关注中的前沿方向”，不要把它夸成已经替代 Transformer 自回归范式的工业标准。"
                ],
                analogy: "自回归像一字一句往后写；离散扩散像先拿到一张模糊草稿，再一轮轮把词改清楚。",
                interview_script: "1. 先说明它与自回归生成的区别：逐步去噪而不是严格从左到右。\n2. 讲潜在优势：并行生成、编辑能力和全局一致性。\n3. 明确边界：目前仍是前沿研究，工业主流仍是自回归 Transformer。"
            },
            {
                term: "VLM / VLA 与 OpenVLA 具身智能",
                desc: "从看图问答扩展到视觉-语言-动作，让模型理解环境并输出可执行动作。",
                details: [
                    "VLM 处理图像、视频与语言；VLA 进一步把动作纳入输出空间，用于机器人、无人系统和工业操作。OpenVLA 等路线体现了开源具身模型从感知到控制的趋势。",
                    "求职表达可结合遥感和工业视觉：VLM 负责理解场景，检测/分割模型负责精确定位，业务规则或控制策略负责可靠执行。"
                ],
                analogy: "VLM 是能看图说话；VLA 是看懂现场后还能告诉机械臂下一步怎么动。",
                interview_script: "1. 区分 VLM 与 VLA：前者理解视觉语言，后者输出动作。\n2. 结合工业场景讲多层架构：视觉识别、语义理解、动作规划、规则安全。\n3. 强调生产系统仍需传感器冗余、权限约束和安全停机。"
            },
            {
                term: "SAM 2 与视频/遥感交互式分割",
                desc: "从单图分割扩展到视频时序对象分割，适合遥感变化检测、目标标注和工业质检提效。",
                details: [
                    "SAM 2 强化了视频对象分割能力，能利用提示在多帧中保持目标一致性。对遥感和无人机数据，价值在于减少标注成本、提升交互式解译效率。",
                    "工程落地要注意尺度差异、小目标、云影遮挡、跨传感器域偏移和地理坐标回写。它更像高效标注/解译助手，不应替代完整质量控制流程。"
                ],
                analogy: "SAM 2 像给标注员一支会跟踪目标的笔，第一帧点一下，后面多帧能自动帮你延续轮廓。",
                interview_script: "1. 说明 SAM 2 的价值是视频级交互分割和标注提效。\n2. 结合遥感讲挑战：尺度、小目标、域偏移、地理配准。\n3. 落地时要接入人工复核、质检抽样和 GIS 坐标体系。"
            },
            {
                term: "Prithvi-EO / TerraTorch 地理空间基础模型",
                desc: "面向遥感和地球观测的基础模型，把多光谱、时序和空间任务统一到预训练-微调范式。",
                details: [
                    "地理空间基础模型通过大规模遥感数据预训练，迁移到土地覆盖、变化检测、洪水识别、农作物监测等任务。Prithvi-EO 和 TerraTorch 代表了遥感 AI 工程化生态的推进方向。",
                    "面试里可以把它和通用 CV 模型区分开：遥感有多光谱、时间序列、投影坐标、分辨率差异和地理泛化问题，不能只套普通 ImageNet 视觉经验。"
                ],
                analogy: "普通视觉模型像看生活照片长大；地理空间基础模型像从小读卫星影像地图长大，更懂地物、季节和空间尺度。",
                interview_script: "1. 说明遥感基础模型的预训练数据和任务特性。\n2. 讲迁移流程：预训练权重、任务头、少样本微调、地理区域验证。\n3. 强调遥感工程细节：CRS、分辨率、时序、云影和跨区域泛化。"
            },
            {
                term: "Prithvi-EO-2.0：多时相地球观测基础模型",
                desc: "IBM、NASA 与 Juelich 推出的第二代 EO foundation model，重点补强多时相、时空位置和多光谱遥感任务。",
                details: [
                    "**模型结构**：Prithvi-EO-2.0 仍以 ViT + MAE 为核心，但把 2D patch/position embedding 升级为 3D patch/position embedding，使模型能直接处理按时间排列的影像序列。TL 版本还把经纬度、年份和年内日序编码进模型，帮助它学习地理位置和季节性。",
                    "**数据与任务**：官方模型卡说明其使用 NASA HLS V2 产品预训练，包含 Blue、Green、Red、NIR、SWIR1、SWIR2 六个波段，并提供 5M、100M、300M、600M 等规模。微调任务覆盖作物分割、滑坡分割、碳通量回归等，和遥感算法工程师岗位高度相关。",
                    "**落地价值**：它不是简单替代 UNet/DeepLabv3，而是作为 backbone 提供更强的遥感表征。实际项目可先用传统模型建立 baseline，再用 Prithvi-EO-2.0 做少样本微调、跨区域泛化和多时相变化分析对比。"
                ],
                code: `# TerraTorch 中加载 Prithvi-EO-2.0 backbone 的典型方式
from terratorch.registry import BACKBONE_REGISTRY

backbone = BACKBONE_REGISTRY.build(
    "ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL"
)

# 后续接 segmentation / regression head 做下游微调`,
                analogy: "如果普通遥感模型像只看一张照片判断地物，Prithvi-EO-2.0 更像同时看多期影像、季节和地理位置的判读员，能把“这里是什么”和“它随时间怎么变”一起理解。",
                interview_script: "1. 先讲结构升级：3D patch embedding 处理多时相影像，TL 版本加入时间和位置编码。\n2. 说明它的遥感特异性：HLS 多光谱、时间序列、地理位置、跨分辨率任务，而不是 ImageNet 迁移。\n3. 落到项目：池塘、水体、农田、变化检测可用它做 backbone，对比 UNet/DeepLabv3/SAM 后处理。"
            },
            {
                term: "Clay Foundation Model：开源 Earth Embedding 底座",
                desc: "面向地球观测的开源 AI 模型和接口，可作为遥感下游任务的通用 embedding/backbone。",
                details: [
                    "**定位**：Clay 官方仓库将其定义为面向 Earth 的开源 AI 模型和接口，源码与模型权重采用 Apache-2.0 许可。它适合被包装成遥感项目里的统一特征提取层，而不是只做单一分类器。",
                    "**工程使用**：Clay 提供 pip 安装和 Python 包接口，核心模块包括 `ClayDataModule` 与 `ClayMAEModule`，训练和验证通过 PyTorch Lightning 风格配置运行。对作品集而言，它能体现你会把学术模型接成可复现实验管线。",
                    "**简历表达**：可以把 Clay 放在“关注并能迁移的 GeoAI 基础模型”里：用其 embedding 做水体/池塘/滩涂场景的特征抽取，再与传统指数、UNet、SAMGeo 后处理结果进行对照。"
                ],
                code: `# Clay 官方仓库的典型安装和导入方式
# pip install git+https://github.com/Clay-foundation/model.git

from claymodel.datamodule import ClayDataModule
from claymodel.module import ClayMAEModule

# 通过配置文件组织数据、backbone 和训练过程`,
                analogy: "Clay 像给地球观测数据做了一套通用底片。你不必每个任务都从零训练眼睛，而是先拿到更懂 Sentinel、DEM、地物纹理的 embedding，再接自己的分类、分割或检索头。",
                interview_script: "1. 说明 Clay 是开源地球观测 foundation model，适合做遥感 embedding/backbone。\n2. 强调工程化：pip 安装、配置驱动训练、可复现实验，而不是只会说模型名。\n3. 结合求职项目：用 Clay 与传统遥感指数、UNet、SAMGeo 对比，证明自己能跟进 GeoAI 前沿。"
            },
            {
                term: "ColPali / ColQwen：视觉文档检索与多模态 RAG",
                desc: "把 PDF 页面直接作为图像嵌入，绕开脆弱的 OCR/版面解析链路，适合投标文件、报告和图表知识库。",
                details: [
                    "**核心机制**：ColPali 系列用 VLM 视觉 patch 输出构造多向量表示，再沿用 ColBERT 式 late interaction 计算查询和页面之间的 MaxSim 相似度。它能同时利用文字、版式、表格、图表和页面视觉结构。",
                    "**为什么重要**：传统 RAG 常依赖 OCR + layout parser + chunking，遇到扫描件、复杂表格、图文混排时容易丢信息。ColPali/ColQwen 直接检索页面图像，适合投标书、项目报告、遥感制图说明、PPT 截图和检测报告。",
                    "**工程权衡**：多向量视觉检索通常比纯文本 embedding 更重，需要 GPU、向量压缩、rerank 和缓存策略。生产系统可用文本 BM25 做粗筛，再用 ColPali 对关键页面做视觉重排。"
                ],
                code: `# ColQwen 检索的核心调用形态
image_embeddings = model(**processor.process_images(page_images).to(device))
query_embeddings = model(**processor.process_queries(queries).to(device))
scores = processor.score_multi_vector(query_embeddings, image_embeddings)`,
                analogy: "普通文档 RAG 像先把报告抄成纯文字再搜索；ColPali 像直接看整页报告，能注意到表格位置、图例、标题层级和截图内容。",
                interview_script: "1. 先说它解决 OCR/版面解析脆弱的问题，直接做页面级视觉检索。\n2. 讲 late interaction：页面和查询都是多向量，最后用 MaxSim 汇总相关性。\n3. 结合项目：投标文件、遥感报告、PPT、图表证据库适合用视觉文档 RAG，不只做纯文本检索。"
            },
            {
                term: "SGLang / RadixAttention：结构化生成与 KV Cache 复用",
                desc: "面向多轮、多分支、结构化输出和 Agent/RAG 管线的高吞吐 LLM 推理框架。",
                details: [
                    "**系统定位**：SGLang 把前端的结构化语言模型程序和后端高吞吐 runtime 结合起来，支持生成、选择、并行控制流、结构化输出和服务化推理。",
                    "**RadixAttention**：复杂 Agent、RAG、few-shot 和多轮对话会反复共享长前缀。RadixAttention 用类似 radix tree 的方式复用 KV cache，减少重复 prefill 计算；压缩 FSM 则用于加速 JSON/约束输出这类结构化解码。",
                    "**求职系统落地**：JD 分析、简历改写、作品集报告、RAG 问答会共享候选人资料和项目证据。若后续接后端服务，可用 prefix cache / RadixAttention 思路降低重复上下文成本，并用结构化解码保证输出 JSON 可解析。"
                ],
                code: `# 工程思路：共享长上下文前缀，结构化输出单独约束
shared_context = candidate_profile + portfolio_evidence
tasks = ["JD匹配", "简历改写", "面试问答"]

# 推理服务层应复用 shared_context 的 KV cache，
# 并对每个任务的 JSON schema 做约束解码。`,
                analogy: "如果每次生成都重新读一遍整份简历和作品集，就像每个问题都重新背书。RadixAttention 像把共同前缀做成缓存书签，后面不同任务直接从书签处继续。",
                interview_script: "1. 说明 SGLang 不只是模型，而是结构化生成程序 + 高吞吐 runtime。\n2. 讲 RadixAttention 的价值：多请求共享前缀时复用 KV cache，减少重复 prefill。\n3. 结合系统设计：RAG、Agent、JD 分析和报告生成要考虑结构化输出、缓存、吞吐和成本。"
            },
            {
                term: "Prompt Injection、工具沙箱与 Agent 权限边界",
                desc: "Agent 能调用工具后，安全问题从文本幻觉升级为真实操作风险。",
                details: [
                    "Prompt Injection 会把恶意指令藏在网页、文档、邮件或检索结果里，诱导模型泄露数据、越权调用工具或改变任务目标。RAG 和浏览器 Agent 尤其需要防护。",
                    "工程防线包括系统指令隔离、工具权限最小化、参数白名单、沙箱执行、敏感操作二次确认、检索内容不可信标记、审计日志和回滚机制。"
                ],
                analogy: "让 Agent 上网和读文件，就像让员工处理陌生邮件附件；不能因为内容写着“请忽略公司规则”就真的照做。",
                interview_script: "1. 说明 Prompt Injection 是外部内容对模型行为的攻击，不只是 prompt 写得不好。\n2. 列出防护：最小权限、工具白名单、沙箱、参数校验、人工确认和日志审计。\n3. 强调高风险动作必须可追踪、可回滚、可审批。"
            }
        ]
    }
];
