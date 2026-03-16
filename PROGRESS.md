# Skiller 项目进展

## Step 1: 筛选场景 ✅
- 从 100 个 pilot_experiment 场景中选出 50 个
- 覆盖 14 个领域: astronomy, atmospheric, biology, chemistry, earth_science, ecology, engineering, environmental, materials, medical, neuroscience, oceanography, physics, social_science
- 输出: `selected_scenarios.json`, `data/requirements.csv`

## Step 2: 批量生成 Skill (进行中)
- 使用 Sonnet 生成 50 个 L4 skill 包
- 每个 skill 约 $0.33，2 次 API 调用（conversation + extraction）
- 质量评分平均 23/24
- 运行命令: `python -m skiller.generate --budget 20 --skip-existing`
- 后台运行中，预计 2.5 小时完成

## Step 3: 验证实验 (待开始)
- 4 模型 × 50 场景 × 2 条件 = 400 trials
- 模型: haiku, gpt4o_mini, gpt4o, sonnet
- 条件: L0 (无 skill) vs L4 (完整 skill)
- 运行命令: `python -m skiller.validate --budget 30`

## Step 4: 分析可视化 (待开始)
- 5 张图表: 热力图、散点图、模型响应、领域难度、案例分析
- 运行命令: `python analysis/generate_figures.py`

## Step 5: 推送 GitHub (待开始)
- 仓库: https://github.com/qishisuren123/skiller.git
