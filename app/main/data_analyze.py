from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import time
import os
import re

#=====================================函数部分=====================================
#-----数据处理+转化为dataframe
def convert_count(value):  #用于处理video数据中含有万字的
    value_str = str(value).strip()
    #有万字的乘以10000转为数字
    if "万" in value_str:
        num_part = re.sub(r'[^\d.]','',value_str)
        return int(float(num_part)*10000) if num_part else 0
    else:
        try:
            return int(float(value_str))
        except:
            return 0
def fetch_data(uid:str,data_type:str): # --> return a dataframe
    allowed = {'video','basic'}
    if data_type not in allowed:
        raise ValueError('Please input correct data_type(basic or video)')
    data_path = os.path.join('.','app','data','raw','bilibili',f'UID_{uid}',f'{data_type}_data.json')
    try:
        with open(data_path,mode='r',encoding='utf-8') as f:
            data = pd.read_json(f)
            df = pd.DataFrame(data)
    except Exception as e:
        print(str(e))
        return None
    
    #转化类型
    if data_type == "video":
        columns = ['播放量','弹幕数','点赞量','投币数','收藏量','转发量']
        for col in columns:
            df[col] = df[col].apply(convert_count).astype(int)
        df['发布(更改)时间'] = pd.to_datetime(df['发布(更改)时间'])
    elif data_type == "basic":
        columns = ['关注数','粉丝数','获赞数','播放数']
        for col in columns:
            df[col] = pd.to_numeric(df[col],errors='coerce')
            df[col] = df[col].fillna(0)
    #处理完成返回dataframe类型
    return df


#=====================================读取数据=======================================
#读取数据
uid = input('请输入要分析的UP主UID: ').strip()
start_time = time.time()
data_dir = os.path.join('.','app','data','raw','bilibili',f'UID_{uid}')
if not os.path.isdir(data_dir):
    raise FileNotFoundError(f'没有UID:{uid}对应的信息,请先去爬取该用户数据')
data_type1 = 'basic'
data_type2 = 'video'
df_basic = fetch_data(uid,data_type1)
df_video = fetch_data(uid,data_type2)
#用于判断有没有读取到文件------文件不存在则报错
if not isinstance(df_basic,pd.DataFrame) or not isinstance(df_video,pd.DataFrame):
    raise FileNotFoundError(f'没有UID:{uid}所对应的信息,请先去爬取该用户数据')
#获取数据文件创建时间
basic_data_path = os.path.join('.','user_data',f'UID_{uid}','basic_data.json')
video_data_path = os.path.join('.','user_data',f'UID_{uid}','video_data.json')
basic_ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(basic_data_path))) if os.path.exists(basic_data_path) else '未知'
video_ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(video_data_path))) if os.path.exists(video_data_path) else '未知' 
#====================================分析数据处理======================================
row_num = df_video.shape[0]
axis_num = df_video.shape[1]
stats_file_path = os.path.join('.','app','data','output','bilibili',f'UID_{uid}','video_data_stats.xlsx')
charts_dir = os.path.join('.','app','data','output','bilibili',f'UID_{uid}','charts')
os.makedirs(charts_dir,exist_ok=True)

# 设置中文字体 & 符号兼容
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Microsoft YaHei'
plt.rcParams['mathtext.it'] = 'Microsoft YaHei:italic'

#----计算互动率
for col, rate_name in [('弹幕数','弹幕率'),('投币数','投币率'),('收藏量','收藏率'),('转发量','转发率')]:
    df_video[rate_name] = (df_video[col] / df_video['播放量']).round(5)

#----数据统计性展示
stats1 = df_video[['播放量','弹幕数','投币数','收藏量','转发量']].describe()

#----播放量前百条
if row_num >= 100:
    top_100 = df_video.sort_values('播放量',ascending=False).iloc[0:100].copy()
else:
    top_100 = df_video.sort_values('播放量',ascending=False).iloc[0:row_num+1].copy()
top_100.index = range(1,len(top_100)+1)
metric_keys = ['弹幕率','投币率','收藏率','转发率']

#----时间维度分析
df_video['发布年月'] = df_video['发布(更改)时间'].dt.to_period('M')
monthly_stats = df_video.groupby('发布年月').agg(
    发布视频数=('标题','count'),
    平均播放量=('播放量','mean'),
    平均弹幕=('弹幕数','mean'),
    平均投币=('投币数','mean'),
    平均收藏=('收藏量','mean'),
    播放量中位数=('播放量','median')
).reset_index()
monthly_stats['发布年月'] = monthly_stats['发布年月'].astype(str)
monthly_stats['平均播放量'] = monthly_stats['平均播放量'].round(0).astype(int)
monthly_stats['平均弹幕'] = monthly_stats['平均弹幕'].round(1)
monthly_stats['平均投币'] = monthly_stats['平均投币'].round(1)
monthly_stats['平均收藏'] = monthly_stats['平均收藏'].round(1)
monthly_stats['播放量中位数'] = monthly_stats['播放量中位数'].astype(int)

#----各指标TOP5
top_view = df_video.nlargest(5,'播放量')[['标题','播放量']]
top_dm = df_video.nlargest(5,'弹幕率')[['标题','弹幕率','弹幕数']]
top_coin = df_video.nlargest(5,'投币率')[['标题','投币率','投币数']]
top_fav = df_video.nlargest(5,'收藏率')[['标题','收藏率','收藏量']]

#=====================================Matplotlib可视化（分图）===================================

# ---- 图1: 播放量分布密度曲线 ----
views = df_video['播放量'][df_video['播放量'] > 0]
log_min, log_max = np.log10(views.min()), np.log10(views.max())
bins = np.logspace(log_min, log_max, 31)
counts, bin_edges = np.histogram(views, bins=bins)
centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])  # 对数中点在几何中点
fig1, ax1 = plt.subplots(figsize=(16, 9))
ax1.plot(centers, counts, 'o-', color='#00a1d6', linewidth=2.5, markersize=8)
ax1.fill_between(centers, counts, alpha=0.15, color='#00a1d6')
ax1.set_xscale('log')
ax1.set_title('播放量分布', fontsize=26)
ax1.set_xlabel('播放量 (对数刻度)', fontsize=21)
ax1.set_ylabel('视频数', fontsize=21)
ax1.axvline(views.mean(), color='red', linewidth=2.5, linestyle='--', label=f"均值:{views.mean():.0f}")
ax1.axvline(views.median(), color='orange', linewidth=2.5, linestyle='--', label=f"中位数:{views.median():.0f}")
ax1.legend(fontsize=17)
ax1.tick_params(axis='both', labelsize=19)
fig1.tight_layout(pad=2)
fig1.savefig(os.path.join(charts_dir, '01_播放量分布.png'), dpi=150, bbox_inches='tight')
plt.close(fig1)

# ---- 图2: 每月发布视频数趋势 ----
monthly_data = df_video.groupby('发布年月').size()
n_months = len(monthly_data)
fig2, ax2 = plt.subplots(figsize=(18, 9))
bars = ax2.bar(range(n_months), monthly_data.values, color='#fb7299', width=0.6)
ax2.set_title('每月发布视频数', fontsize=26)
ax2.set_xlabel('月份', fontsize=21)
ax2.set_ylabel('视频数', fontsize=21)
if n_months > 0:
    step = max(1, n_months // 15) if n_months > 15 else 1
    tick_positions = range(0, n_months, step)
    tick_labels = [str(monthly_data.index[i]) for i in tick_positions]
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels, rotation=30, ha='right', fontsize=19)
    ax2.tick_params(axis='y', labelsize=19)
    ax2.margins(x=0.02)
fig2.tight_layout(pad=2)
fig2.savefig(os.path.join(charts_dir, '02_每月发布趋势.png'), dpi=150, bbox_inches='tight')
plt.close(fig2)

# ---- 图3: 每月平均播放量趋势 ----
monthly_avg = df_video.groupby('发布年月')['播放量'].mean()
fig3, ax3 = plt.subplots(figsize=(18, 9))
ax3.plot(range(len(monthly_avg)), monthly_avg.values, marker='o', color='#00a1d6', linewidth=2.5, markersize=10)
ax3.set_title('每月平均播放量趋势', fontsize=26)
ax3.set_xlabel('月份', fontsize=21)
ax3.set_ylabel('平均播放量', fontsize=21)
ax3.fill_between(range(len(monthly_avg)), monthly_avg.values, alpha=0.15, color='#00a1d6')
if len(monthly_avg) > 0:
    step = max(1, len(monthly_avg) // 15) if len(monthly_avg) > 15 else 1
    tick_positions = range(0, len(monthly_avg), step)
    tick_labels = [str(monthly_avg.index[i]) for i in tick_positions]
    ax3.set_xticks(tick_positions)
    ax3.set_xticklabels(tick_labels, rotation=30, ha='right', fontsize=19)
    ax3.tick_params(axis='y', labelsize=19)
    ax3.margins(x=0.02)
fig3.tight_layout(pad=2)
fig3.savefig(os.path.join(charts_dir, '03_每月平均播放量.png'), dpi=150, bbox_inches='tight')
plt.close(fig3)

# ---- 图4: Top10播放量柱状图 ----
top10_view = df_video.nlargest(10, '播放量')
fig4, ax4 = plt.subplots(figsize=(18, 10))
colors = ['#00a1d6'] * 10
if len(top10_view) >= 1:
    colors[0] = '#fb7299'
bars = ax4.barh(range(10), top10_view['播放量'].values[::-1], color=colors[::-1], height=0.8)
ax4.set_title('Top 10 播放量视频', fontsize=26)
ax4.set_xlabel('播放量', fontsize=21)
ax4.set_yticks(range(10))
ax4.set_yticklabels([t[:28]+'...' if len(t)>28 else t for t in top10_view['标题'].values[::-1]], fontsize=19)
ax4.ticklabel_format(axis='x', style='plain')
for bar, val in zip(bars, top10_view['播放量'].values[::-1]):
    ax4.text(bar.get_width() + top10_view['播放量'].max() * 0.02, bar.get_y() + bar.get_height()/2, f'{val:,}', va='center', fontsize=19)
ax4.set_xlim(right=top10_view['播放量'].max() * 1.25)
fig4.tight_layout(pad=2)
fig4.savefig(os.path.join(charts_dir, '04_Top10播放量.png'), dpi=150, bbox_inches='tight')
plt.close(fig4)

# ---- 图5: 互动率箱线图 ----
rate_data = [df_video['弹幕率'].dropna(), df_video['投币率'].dropna(), df_video['收藏率'].dropna(), df_video['转发率'].dropna()]
fig5, ax5 = plt.subplots(figsize=(14, 9))
bp = ax5.boxplot(rate_data, labels=['弹幕率','投币率','收藏率','转发率'], patch_artist=True, widths=0.4)
for patch, color in zip(bp['boxes'], ['#00a1d6','#fb7299','#ffb81c','#6dc781']):
    patch.set_facecolor(color)
ax5.set_title('互动率分布', fontsize=26)
ax5.set_ylabel('比率', fontsize=21)
ax5.tick_params(axis='both', labelsize=19)
fig5.tight_layout(pad=2)
fig5.savefig(os.path.join(charts_dir, '05_互动率箱线图.png'), dpi=150, bbox_inches='tight')
plt.close(fig5)

# ---- 图6: 发布时间分布（按小时） ----
if '发布(更改)时间' in df_video.columns:
    hour_dist = df_video['发布(更改)时间'].dt.hour.value_counts().sort_index()
    fig6, ax6 = plt.subplots(figsize=(18, 9))
    ax6.bar(hour_dist.index, hour_dist.values, color='#fb7299', width=0.7)
    ax6.set_title('发布时间分布（按小时）', fontsize=26)
    ax6.set_xlabel('小时', fontsize=21)
    ax6.set_ylabel('视频数', fontsize=21)
    ax6.tick_params(axis='both', labelsize=19)
    ax6.set_xticks(range(0, 24))
    ax6.set_xlim(-1, 24)
    ax6.margins(x=0.01)
    fig6.tight_layout(pad=2)
    fig6.savefig(os.path.join(charts_dir, '06_发布时间分布.png'), dpi=150, bbox_inches='tight')
    plt.close(fig6)

# ---- 图7: 播放量 vs 投币率 散点图 ----
fig7, ax7 = plt.subplots(figsize=(15, 10))
purple_red = LinearSegmentedColormap.from_list('purple_red', ['#8b00ff', '#e74c3c'])
scatter = ax7.scatter(df_video['播放量'], df_video['投币率'], alpha=0.85, c=df_video['评论数'] if '评论数' in df_video.columns else df_video['弹幕数'], cmap=purple_red, s=90)
ax7.set_title('播放量 vs 投币率', fontsize=26)
ax7.set_xlabel('播放量', fontsize=21)
ax7.set_ylabel('投币率', fontsize=21)
cbar = fig7.colorbar(scatter, ax=ax7)
cbar.set_label('评论数', fontsize=17)
ax7.tick_params(axis='both', labelsize=19)
cbar.ax.tick_params(labelsize=19)
fig7.tight_layout(pad=2)
fig7.savefig(os.path.join(charts_dir, '07_播放量vs投币率.png'), dpi=150, bbox_inches='tight')
plt.close(fig7)

chart_files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
print(f'图表已保存至 {charts_dir}/ ({len(chart_files)} 张)')

#=====================================写进Excel表=====================================
with pd.ExcelWriter(stats_file_path,engine='xlsxwriter') as writer:
    workbook = writer.book
    # 通用格式
    center_format = workbook.add_format({"align":"center","valign":"vcenter"})
    percent_format = workbook.add_format({'num_format':'0.000%','align':'center'})
    int_format = workbook.add_format({'num_format':'#,##0','align':'center'})
    # 浅蓝配色格式
    header_fmt = workbook.add_format({
        'align':'center','valign':'vcenter','bold':True,
        'fg_color':'#7BC4E8','font_color':'#FFFFFF','border':1
    })
    row_even_fmt = workbook.add_format({
        'align':'center','valign':'vcenter',
        'fg_color':'#E8F4FD','border':1
    })
    row_odd_fmt = workbook.add_format({
        'align':'center','valign':'vcenter',
        'fg_color':'#F5FAFE','border':1
    })
    section_fmt = workbook.add_format({
        'align':'center','valign':'vcenter','bold':True,
        'fg_color':'#5BA3D9','font_color':'#FFFFFF','border':1
    })
    # 带浅蓝背景的数值格式
    percent_fmt_even = workbook.add_format({'num_format':'0.000%','align':'center','fg_color':'#E8F4FD','border':1})
    percent_fmt_odd = workbook.add_format({'num_format':'0.000%','align':'center','fg_color':'#F5FAFE','border':1})
    int_fmt_even = workbook.add_format({'num_format':'#,##0','align':'center','fg_color':'#E8F4FD','border':1})
    int_fmt_odd = workbook.add_format({'num_format':'#,##0','align':'center','fg_color':'#F5FAFE','border':1})

    #----表一: 描述统计
    stats1.to_excel(writer, sheet_name='Data_Describe', index=True, index_label='Metrics', float_format='%.0f')
    ws1 = writer.sheets['Data_Describe']
    nrows1, ncols1 = stats1.shape
    ws1.set_column(0, ncols1, 12, center_format)
    # 表头 + 数据行上色
    ws1.set_row(0, None, header_fmt)
    for r in range(nrows1):
        ws1.set_row(r + 1, None, row_even_fmt if r % 2 == 0 else row_odd_fmt)

    #----表二: 播放量Top排行+互动率
    stats2 = top_100[['播放量','弹幕数','投币数','收藏量','转发量','弹幕率','投币率','收藏率','转发率']]
    stats2.to_excel(writer, sheet_name='top_100', index=True, index_label='播放量排名')
    ws2 = writer.sheets['top_100']
    nrows2, ncols2 = stats2.shape
    ws2.set_column(0, 1, 12, center_format)
    ws2.set_column(1, 5, 14, int_format)
    for col_name in metric_keys:
        if col_name in stats2.columns:
            col_idx = stats2.columns.get_loc(col_name) + 1
            ws2.set_column(col_idx, col_idx, 12, percent_format)
    ws2.set_row(0, None, header_fmt)
    for r in range(nrows2):
        ws2.set_row(r + 1, None, row_even_fmt if r % 2 == 0 else row_odd_fmt)

    #----表三: 月度统计
    monthly_stats.to_excel(writer, sheet_name='Monthly_Stats', index=False)
    ws3 = writer.sheets['Monthly_Stats']
    nrows3, ncols3 = monthly_stats.shape
    ws3.set_column(0, ncols3, 14, center_format)
    ws3.set_row(0, None, header_fmt)
    for r in range(nrows3):
        ws3.set_row(r + 1, None, row_even_fmt if r % 2 == 0 else row_odd_fmt)

    #----表四: 各指标TOP5（合并为一个sheet）
    top_sheet_name = 'Top5_排行榜'
    top5_data = [
        ('播放量 Top 5', top_view, False),
        ('弹幕率 Top 5', top_dm, True),
        ('投币率 Top 5', top_coin, True),
        ('收藏率 Top 5', top_fav, True),
    ]
    ws_top = workbook.add_worksheet(top_sheet_name)
    current_row = 0
    for sec_title, df_top, has_rate in top5_data:
        ncols = len(df_top.columns)
        # 段标题行
        ws_top.merge_range(current_row, 0, current_row, ncols - 1, sec_title, section_fmt)
        for c in range(ncols):
            ws_top.write(current_row, c, sec_title if c == 0 else '', section_fmt)
        current_row += 1
        # 表头行
        for c, col_name in enumerate(df_top.columns):
            ws_top.write(current_row, c, col_name, header_fmt)
        current_row += 1
        # 数据行
        for r in range(len(df_top)):
            row_fmt = row_even_fmt if r % 2 == 0 else row_odd_fmt
            pf = percent_fmt_even if r % 2 == 0 else percent_fmt_odd
            inf = int_fmt_even if r % 2 == 0 else int_fmt_odd
            ws_top.write(current_row, 0, df_top.iloc[r, 0], row_fmt)
            if has_rate:
                ws_top.write(current_row, 1, df_top.iloc[r, 1], pf)
            else:
                ws_top.write(current_row, 1, int(df_top.iloc[r, 1]), inf)
            if ncols >= 3:
                ws_top.write(current_row, 2, int(df_top.iloc[r, 2]), inf)
            current_row += 1
        current_row += 1  # 表间间隔
    ws_top.set_column(0, 0, 50, center_format)
    ws_top.set_column(1, 1, 14, center_format)
    ws_top.set_column(2, 2, 14, center_format)

#=====================================控制台摘要输出===================================
print('\n' + '='*60)
print('                数据分析摘要')
print('='*60)
print(f'数据获取日期:{video_ctime}')
print(f'总视频数: {row_num}')
print(f'播放量 -- 均值: {df_video["播放量"].mean():.0f}  |  中位数: {df_video["播放量"].median():.0f}  |  最高: {df_video["播放量"].max()}')
print(f'平均弹幕率: {df_video["弹幕率"].mean():.4%}  |  平均投币率: {df_video["投币率"].mean():.4%}  |  平均收藏率: {df_video["收藏率"].mean():.4%}')
print(f'\n--- 播放量最高的视频 ---')
for _, row in top_view.iterrows():
    print(f'  [{row["播放量"]}] {row["标题"]}')
print(f'\n--- 投币率最高的视频 ---')
for _, row in top_coin.iterrows():
    print(f'  [{row["投币率"]:.2%}] {row["标题"]}')

#=====================================写入Markdown报告===================================
md_path = os.path.join('.','app','data','output','bilibili',f'UID_{uid}','analysis_report.md')
with open(md_path, 'w', encoding='utf-8') as md:
    md.write(f'# UID:{uid} 数据分析报告\n\n')
    md.write(f"**数据获取日期**:{video_ctime}\n")
    md.write(f'**总视频数**: {row_num}\n\n')
    md.write(f'## 基础数据\n\n')
    for _, row in df_basic.iterrows():
        md.write(f'- 昵称: {row.get("昵称","")}\n')
        md.write(f'- 粉丝数: {row.get("粉丝数",0):,}\n')
        md.write(f'- 获赞数: {row.get("获赞数",0):,}\n')
        md.write(f'- 播放数: {row.get("播放数",0):,}\n')
    md.write(f'\n## 播放量统计\n\n')
    md.write(f'| 指标 | 数值 |\n|------|------|\n')
    md.write(f'| 均值 | {df_video["播放量"].mean():.0f} |\n')
    md.write(f'| 中位数 | {df_video["播放量"].median():.0f} |\n')
    md.write(f'| 最高 | {df_video["播放量"].max()} |\n')
    md.write(f'| 最低 | {df_video["播放量"].min()} |\n')
    md.write(f'\n## 播放量 Top 5\n\n')
    for i, (_, row) in enumerate(top_view.iterrows(), 1):
        md.write(f'{i}. **{row["标题"]}** — {row["播放量"]:,} 播放\n')
    md.write(f'\n## 月度趋势\n\n')
    md.write(f'| 月份 | 发布数 | 平均播放量 |\n|------|--------|------------|\n')
    for _, row in monthly_stats.iterrows():
        md.write(f'| {row["发布年月"]} | {row["发布视频数"]} | {row["平均播放量"]:,} |\n')
    md.write(f'\n## 图表\n\n')
    for fname in sorted(chart_files):
        label = fname.replace('.png','').replace('_',' ')
        md.write(f'![{label}](charts/{fname})\n\n')
print(f'Markdown报告已保存: {md_path}')

end_time = time.time()
print(f'\n程序执行完毕, 总用时:{end_time-start_time:.2f}s')