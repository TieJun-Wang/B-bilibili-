# 📺 Bilibili 爬虫

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green?logo=selenium)](https://www.selenium.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

基于 Selenium 的 B 站视频数据爬取工具，支持自动抓取 UP 主全部视频信息，并通过 pandas + matplotlib 生成可视化分析报告。

---

## 功能

- 模拟浏览器自动登录，支持 cookies 持久化
- 抓取 UP 主基本信息（粉丝数、获赞数、总播放量）及全部视频列表分页采集
- 每条视频提取：标题、播放量、弹幕数、点赞、投币、收藏、转发、发布时间
- 数据清洗后输出 Excel 统计表 + 7 张分析图表 + Markdown 报告

## 依赖

| 包 | 用途 |
|---|---|
| `selenium` | 浏览器自动化，模拟登录与翻页 |
| `pandas` | 数据清洗、统计、导出 Excel |
| `matplotlib` | 7 张可视化图表 |
| `numpy` | 数值计算 |
| `xlsxwriter` | Excel 格式与样式 |

```bash
pip install selenium pandas matplotlib numpy xlsxwriter
```

> 需要 **Edge 浏览器**，脚本默认调用 Edge WebDriver。

---

## 项目结构

```
bilibili-crawler/
├── app/
│   ├── main/
│   │   ├── bilibili_selenium.py     # 爬虫主程序
│   │   ├── data_analyze.py          # 数据分析 + 画图
│   │   └── cookies.json             # 登录态缓存
│   └── data/
│       ├── raw/
│       │   └── UID_39279965/        # 示例：影石Insta360
│       └── output/
│           └── UID_39279965/
│               ├── video_data_stats.xlsx
│               ├── analysis_report.md
│               └── charts/          # 7 张 PNG 图表
```

---

## 快速开始

### 第一步：爬取数据

1. 打开 `app/main/bilibili_selenium.py`，修改第 13 行：

```python
UID = 'input_uid here'   # 替换为目标 UP 主的 UID
```

2. 运行脚本：

```bash
python app/main/bilibili_selenium.py
```

3. 浏览器自动打开 B 站首页，扫码或账号密码登录。登录成功后自动跳转目标主页，开始分页抓取。
5. 爬取完成后数据保存至 `app/data/raw/bilibili/UID_xxx/`。

### 第二步：生成报告

```bash
python app/main/data_analyze.py
```

输入 UID，脚本自动读取本地 JSON 数据，输出：

| 产出 | 内容 |
|---|---|
| `video_data_stats.xlsx` | 描述统计 / Top100 排行 / 月度趋势 / Top5 排行 |
| `charts/` 目录 | 7 张 PNG 图表（详见下方） |
| `analysis_report.md` | Markdown 格式分析报告 |

所有文件输出到 `app/data/output/bilibili/UID_xxx/`。

---

## 分析图表说明

| 编号 | 图表 | 说明 |
|:--:|------|------|
| 01 | 播放量分布 | 对数坐标下的密度曲线，标注均值与中位数 |
| 02 | 每月发布趋势 | 按月统计发布视频数量 |
| 03 | 每月平均播放量 | 月度平均播放量走势 |
| 04 | Top 10 播放量 | 播放量前十视频水平柱状图 |
| 05 | 互动率箱线图 | 弹幕率 / 投币率 / 收藏率 / 转发率分布 |
| 06 | 发布时间分布 | 24 小时发布热度 |
| 07 | 播放量 vs 投币率 | 散点图，颜色映射弹幕/评论数 |

---

## 示例数据

仓库 `app/data/` 中附带了 UP 主 **[影石Insta360](https://space.bilibili.com/39279965)** 的爬取数据与完整分析报告，可直接查看效果。
