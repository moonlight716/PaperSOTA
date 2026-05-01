# AGD20K 可供性定位相关方法对比

> 指标说明：
>  - KLD↓：衡量预测分布 $P$ 与真值分布 $Q$之间的差异，值越小表示两个分布越接近。
>  - SIM↑：计算预测图 $P$ 与连续真值图 $Q$ 逐像素最小值的总和，值越大表示相似度越高。
>  - NSS↑：将预测图 $P$ 标准化后，与二值或连续真值图 $Q$ 进行点乘并取平均，评估预测与真实注视点的一致性，值越大越好。
> 注意：Table 2 中部分方法采用 Easy/Hard split、dense annotation、one-shot setting 或额外数据训练，因此不宜与 Table 1 的弱监督 Seen/Unseen 设置直接做绝对数值比较。

## Table 1. AGD20K 原始基准与弱监督主线

| <font color="#4f81bd">Method</font> |                              <font color="#1f497d">Seen |       <font color="#1f497d"> Seen |         <font color="#1f497d">Seen</font> |      <font color="#1f497d">Unseen | </font> <font color="#1f497d">Unseen |      <font color="#1f497d">Unseen |
| ----------------------------------- | ------------------------------------------------------: | --------------------------------: | ----------------------------------------: | --------------------------------: | -----------------------------------: | --------------------------------: |
|                                     | <font color="#4f81bd"><font color="#4f81bd">KLD↓</font> | <font color="#4f81bd">SIM↑</font> | </font> <font color="#4f81bd">NSS↑</font> | <font color="#4f81bd">KLD↓</font> |    <font color="#4f81bd">SIM↑</font> | <font color="#4f81bd">NSS↑</font> |
| Cross-View-AG, CVPR2022 [1]         |                                                   1.538 |                             0.334 |                                     0.927 |                             1.787 |                                0.285 |                             0.829 |
| LOCATE, CVPR2023 [2]                |                                                   1.226 |                             0.401 |                                     1.177 |                             1.405 |                                0.372 |                             1.157 |
| WSMA, AAAI2024 [3]                  |                                                   1.176 |                             0.416 |                                     1.247 |                             1.335 |                                0.382 |                             1.220 |
| INTRA, ECCV2024 [4]                 |                                                   1.199 |                             0.407 |                                     1.239 |                             1.365 |                                0.375 |                             1.209 |
| R-Mamba, CVPR2025 [5]               |                                                   1.173 |                             0.414 |                                     1.247 |                             1.372 |                                0.380 |                             1.190 |
| WSMA + R-Mamba, CVPR2025 [5]        |                                                   1.143 |                             0.420 |                                     1.251 |                             1.310 |                                0.397 |                             1.279 |
| PLSP, ICLR2025 [6]                  |                                               **0.890** |                         **0.510** |                                 **1.547** |                         **1.153** |                            **0.437** |                         **1.418** |
| LoopTrans, ICCV2025 [7]             |                                                   1.088 |                             0.445 |                                     1.322 |                             1.247 |                                0.403 |                             1.315 |
| SelectiveCL, ICCV2025 [8]           |                                                   1.124 |                             0.433 |                                     1.280 |                             1.243 |                                0.405 |                             1.368 |
| BiT-Align, IROS2025 [9]             |                                                   1.105 |                             0.430 |                                     1.317 |                             1.331 |                                0.371 |                             1.302 |

## Table 2. VLM / LLM / 开放词汇与扩展任务方向

| Method                                       | Easy / Seen | Easy / Seen | Easy / Seen | Hard / Unseen | Hard / Unseen | Hard / Unseen |
| -------------------------------------------- | ----------: | ----------: | ----------: | ------------: | ------------: | ------------: |
|                                              |        KLD↓ |        SIM↑ |        NSS↑ |          KLD↓ |          SIM↑ |          NSS↑ |
| AffordanceLLM, CVPRW2024 [10]                |       1.463 |       0.377 |       1.070 |         1.661 |         0.361 |         0.947 |
| OOAL, CVPR2024 [11]                          |       1.070 |       0.461 |       1.503 |         1.302 |         0.410 |         1.119 |
| OOAL + C2F-Aff, CVPR2024 / 2025 setting [11] |       0.974 |       0.504 |       1.650 |         1.119 |         0.442 |         1.364 |
| WorldAfford, 2024 [12]                       |       1.201 |       0.406 |       1.255 |         1.393 |         0.380 |         1.225 |
| AffordanceSAM, 2025 [13]                     |       1.271 |       0.486 |       1.597 |         1.327 |         0.423 |         1.502 |
| AffordanceSAM + C2F-Aff, 2025 [13]           |       1.083 |   **0.543** |   **1.800** |         1.128 |     **0.514** |     **1.761** |

## References

[1] Hongchen Luo, Wei Zhai, Jing Zhang, Yang Cao, Dacheng Tao. **Learning Affordance Grounding from Exocentric Images**. CVPR, 2022.

[2] Gen Li, Varun Jampani, Deqing Sun, Laura Sevilla-Lara. **LOCATE: Localize and Transfer Object Parts for Weakly Supervised Affordance Grounding**. CVPR, 2023.

[3] Lingjing Xu, Yang Gao, Wenfeng Song, Aimin Hao. **Weakly Supervised Multimodal Affordance Grounding for Egocentric Images**. AAAI, 2024.

[4] Ji Ha Jang, Hoigi Seo, Se Young Chun. **INTRA: Interaction Relationship-aware Weakly Supervised Affordance Grounding**. ECCV, 2024.

[5] Haofei Wang et al. **Reasoning Mamba: Hypergraph-Guided Region Relation Calculating for Weakly Supervised Affordance Grounding**. CVPR, 2025.

[6] Peiran Xu, Yadong Mu. **Weakly-Supervised Affordance Grounding Guided by Part-Level Semantic Priors**. ICLR, 2025.

[7] Jin Tang et al. **Closed-Loop Transfer for Weakly-supervised Affordance Grounding**. ICCV, 2025.

[8] WonJun Moon, Hyun Seok Seong, Jae-Pil Heo. **Selective Contrastive Learning for Weakly Supervised Affordance Grounding**. ICCV, 2025.

[9] Yizhou Huang, Fan Yang, Guoliang Zhu, Gen Li, Hao Shi, Yukun Zuo, Wenrui Chen, Zhiyong Li, Kailun Yang. **Resource-Efficient Affordance Grounding with Complementary Depth and Semantic Prompts**. 2025.

[10] Shengyi Qian, Weifeng Chen, Min Bai, Xiong Zhou, Zhuowen Tu, Li Erran Li. **AffordanceLLM: Grounding Affordance from Vision Language Models**. CVPR Workshop, 2024.

[11] Gen Li, Deqing Sun, Laura Sevilla-Lara, Varun Jampani. **One-Shot Open Affordance Learning with Foundation Models**. CVPR, 2024.

[12] Changmao Chen, Yuren Cong, Zhen Kan. **WorldAfford: Affordance Grounding based on Natural Language Instructions**. 2024.

[13] Dengyang Jiang, Mengmeng Wang, Teli Ma, Hengzhuang Li, Yong Liu, Guang Dai, Lei Zhang. **AffordanceSAM: Segment Anything Once More in Affordance Grounding**. 2025.