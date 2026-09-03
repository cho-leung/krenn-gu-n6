# arXiv 投稿步骤(用你自己的 arXiv 账号)

## 文件准备(已完成)

- `main.tex` 可直接上传(xelatex + xeCJK,UTF-8;已含中文署名);
- 压缩包不含 `main.pdf` 之外的无用文件:上传前运行
  `cd paper && rm -f *.aux *.log *.out *.synctex.gz`
  (arXiv 自动生成 PDF,但带上 main.pdf 做对照也无妨)。

## 提交流程(arXiv.org → Submit)

1. 登录 → **New Submission**;
2. **File**: 上传 `main.tex`(选 "PDFLaTeX"... 注意:因为我们用了 xelatex 和 xeCJK,处理器要选 **"XeLaTeX"**;若上传界面只有 PDFLaTeX 选项,则先把 `\usepackage{xeCJK}` 和 `\setCJKmainfont{PingFang SC}` 两行注释掉,用 pdflatex 编译的纯 ASCII 版(作者行 "Junhao Liang (梁竣皓)" 会需要去掉中文) —— 优先试 XeLaTeX 处理器,arXiv 支持);
3. **Metadata**:
   - Title: *The Krenn–Gu conjecture holds for all simple graphs on six vertices*
   - Authors: Junhao Liang (primary name); 可在 Comments 写 "梁竣皓";
   - Abstract: 用 `main.tex` 里的 abstract 原文;
   - **Subjects: math.CO**(组合);可选交叉 cs.LO 或 quant-ph(此问题源自量子光学,加 quant-ph 交叉列表能多一个圈子的曝光——建议加);
   - Comments 栏建议写:
     `13 pages? no — 8 pages; settles eqSystem6_no_solution_d3/d4/d5/ge3 in google-deepmind/formal-conjectures; source at https://github.com/cho-leung/krenn-gu-n6`
4. **Submit**;等待处理(通常 1-2 天出编号,编号即刻可被引用);
5. 拿到编号后:把 arXiv 链接补进 GitHub README 和 MathOverflow 答案。

## 署名格式说明(arXiv 元数据)

- 元数据姓名填 **"Junhao Liang"**(纯 ASCII,国际索引友好);
- 中文名出现在:论文 PDF 首页(已含)、Comments 栏、ORCID 档案。

## 时间线建议

1. 今天:GitHub 仓库公开 ✓ + MathOverflow 回帖(等你发);
2. 今天/明天:arXiv 提交(你操作,我随时候命);
3. 拿到编号后:给 Krenn 发邮件/留言(赏金页面),附三样东西:
   arXiv 链接 + GitHub 链接 + 一句话"I'm working on the multigraph
   case (Q1) and n≥8; happy to collaborate"——这就是"入圈"的正式动作。
