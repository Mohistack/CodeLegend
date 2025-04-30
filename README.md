# CodeLegend (GitHub 封神榜)

![visitor badge](https://visitor-badge.laobi.icu/badge?page_id=Mohistack.CodeLegend)
[![Update GitHub Code Legend LeaderBoards](https://github.com/Mohistack/CodeLegend/actions/workflows/github-code_legend.yml/badge.svg)](https://github.com/Mohistack/CodeLegend/actions/workflows/github-code_legend.yml)

## 项目介绍

本项目通过 GitHub Actions 定时抓取 GitHub 最新数据，自动生成并展示各类排行榜单。榜单数据基于 GitHub API 自动抓取存储并计算，每日更新一次。

## 榜单类别

### 已实现榜单

- **每日最热门项目 TOP100**  
  统计最近24小时内新获得 Star 数最多的100个项目。

- **每周最热门项目 TOP100**  
  统计最近7天内新获得 Star 数最多的100个项目。

- **每月最热门项目 TOP100**  
  统计最近30天内新获得 Star 数最多的100个项目。

- **Star 总数最多项目 TOP100**  
  统计历史上 Star 总数最多的100个项目。

- **粉丝最多的开发者 TOP100**  
  统计粉丝（followers）数量最多的100个 GitHub 用户。

### 计划实现榜单

- **每日最活跃用户 TOP100**  
  统计最近24小时内提交代码最多的100个 GitHub 用户。

- **每周最活跃用户 TOP100**  
  统计最近7天内提交代码最多的100个 GitHub 用户。

- **每月最活跃用户 TOP100**  
  统计最近30天内提交代码最多的100个 GitHub 用户。

- **每月最热语言**  
  统计最近30天新建项目使用最多的语言，并统计每种语言的仓库数。

## 数据更新

榜单数据最近更新时间见各榜单页面顶部，或查看 [update_time.txt](data/update_time.txt)。

## 快速开始

### 1. 安装依赖

需要 Python 3 环境：

```bash
pip install -r requirements.txt
```

### 2. 获取 GitHub Token

- 访问 [GitHub 个人设置](https://github.com/settings/tokens) 生成一个具有 public_repo 权限的 Token
- 建议将 Token 保存为环境变量 `GH_TOKEN`，以便后续脚本调用

### 3. 配置环境变量

- 在本地终端执行：
  ```bash
  export GH_TOKEN=你的token
  ```

### 4. 数据抓取

运行数据抓取脚本：

```bash
python scripts/fetch_github_main.py
```

脚本会自动抓取最新榜单数据并生成到 `public/` 目录下对应 html 文件。

### 5. 本地预览

使用任意静态服务器（如 Python 自带 http.server）预览页面：

```bash
cd public
python3 -m http.server 8080
```

在浏览器访问 [http://localhost:8080](http://localhost:8080) 查看榜单页面。

### 6. 自动化部署

项目已配置 GitHub Actions，推送到主分支后会自动定时抓取并部署最新榜单。工作流配置见 `.github/workflows/github-code_legend.yml`。

## GitHub Actions 配置环境变量

### 1. 进入仓库设置

- 访问你的 GitHub 仓库页面
- 点击顶部菜单的 Settings
- 在左侧边栏选择 Secrets and variables > Actions

### 2. 添加新 Secret

- 点击 New repository secret 按钮
- 输入 Secret 名称（如 GH_TOKEN）
- 输入 Secret 值（如你的 GitHub Token）
- 点击 Add secret 保存

## 其他说明

- 如需自定义抓取范围或榜单数量，可修改 `scripts/fetch_github_main.py` 脚本参数
- 如遇 API 限流，请更换 Token 或修改config.py中的 `WAIT_TIME_PER_REQUEST`参数，建议设置为10秒稍后重试
