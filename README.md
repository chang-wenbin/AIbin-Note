# ⚡ Ibin! 技术笔记库

> Ibin! 在 AI 推理引擎、GPU 优化与大模型加速领域的工作笔记与可视化文档集合

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://adux-user-0316.github.io/ibin-notes/)
![文档数量](https://img.shields.io/badge/文档-13篇-blue)
![持续更新](https://img.shields.io/badge/状态-持续更新-orange)

---

## 📖 项目简介

本仓库是 **Ibin!** 在日常工作与学习中积累的技术文档集合，以**交互式 HTML 可视化**的形式呈现复杂的 GPU 架构与 AI 算法原理。

所有文档均可通过 **GitHub Pages** 直接在浏览器中访问，无需任何安装。

**技术领域覆盖：**

- 🧠 **MLA (Multi-head Latent Attention)** — 多头潜在注意力机制的原理、矩阵吸收、GEMM 优化
- ⚙️ **Decode Attention 优化** — Flash Decoding、CuTe 算子、RoPE 位置编码对比
- 🔬 **SM80 Ampere 专项** — 针对 Ampere 架构的 Block Attention kernel 详解

---

## 🗂️ 目录结构

```
ibin-notes/
├── index.html              # 主页（自动生成）
├── update_index.py         # 一键更新主页脚本
├── docs_config.json        # 文档描述配置（可选）
├── README.md
├── .gitignore
│
├── MLA_DSA/                # MLA 与 DSA 相关笔记（7 篇）
│   ├── MLA_Best_Operators.html
│   ├── MLA_DSA_Inference_Guide.html
│   ├── MLA_GEMM_Visual.html
│   ├── MLA_Matrix_Absorption.html
│   ├── MLA_Prefix_Cache_ChunkedPrefill.html
│   ├── MLA_Simplified_Diagram.html
│   └── RoPE_Variants_Comparison.html
│
├── De_Attn/                # Decode Attention 优化（4 篇）
│   ├── flash_decoding_guide.html
│   ├── cute_divide_ops_v1.html
│   ├── cute_divide_ops_v2.html
│   └── rope_comparison_guide.html
│
└── De_Attn_sm80/           # SM80 架构专项（2 篇）
    ├── block_attn_kernel_guide.html
    └── block_attn_matrix_flow.html
```

---

## 🚀 部署到 GitHub Pages

### 第一次部署

```bash
# 1. 在 GitHub 新建仓库（例如：ibin-notes）

# 2. 初始化本地 git 仓库
cd Aibin_Note/
git init
git add -A
git commit -m "feat: initial commit"

# 3. 关联远程仓库并推送
git remote add origin https://github.com/chang-wenbin/AIbin-Note.git
git branch -M main
git push -u origin main

# 4. 在 GitHub 仓库设置中开启 GitHub Pages
#    Settings → Pages → Source: Deploy from a branch → Branch: main / (root)
```

### 访问地址

```
https://chang-wenbin.github.io/AIbin-Note/
```

---

## 🔄 更新主页（一键脚本）

每当新增 HTML 文档或修改目录结构后，运行：

```bash
# 扫描目录并更新 index.html
python3 update_index.py

# 更新并自动推送到 GitHub
python3 update_index.py --push

# 仅预览，不写入文件
python3 update_index.py --dry-run
```

脚本会自动：
1. 扫描所有子目录中的 `.html` 文件
2. 更新文档卡片与统计数字
3. 更新"最近更新"日期
4. （`--push` 模式）执行 `git add / commit / push`

---

## ➕ 新增文档

1. 将新的 `.html` 文件放入对应的子目录（如 `MLA_DSA/`）
2. （可选）在 `docs_config.json` 中添加描述
3. 运行 `python3 update_index.py --push`

### 新建文件夹

如需添加新的技术领域，编辑 `update_index.py` 顶部的 `FOLDER_CONFIG` 字典：

```python
FOLDER_CONFIG = {
    "MLA_DSA": { ... },
    "De_Attn": { ... },
    "Your_New_Folder": {
        "label":     "Your_New_Folder — 描述",
        "emoji":     "🚀",
        "css_class": "mla-section",
        "default_tag": "NewTag",
    },
}
```

---

## 📝 自定义文档描述

创建 `docs_config.json`，为新文档指定 emoji、标题和描述：

```json
{
  "MLA_DSA": {
    "my_new_doc.html": {
      "emoji": "🔥",
      "title": "我的新文档标题",
      "desc": "这是文档的简短描述。",
      "tag": "MLA · New"
    }
  }
}
```

---

## 📄 License

本仓库所有内容均为个人工作笔记，仅供学习参考。如需引用请注明出处。

---

<div align="center">Built with ❤️ by <strong>Ibin!</strong> | 持续学习，持续记录</div>
