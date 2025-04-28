### 角色

你是一名资深全栈工程师，擅长python开发和前端UI设计

### 任务

你要根据我的需求完成一个项目名称为GitRank的展示github项目和开发者排行榜单的项目

### 主要目标

借助GitHub Action pages, 通过每日爬虫抓取仓库和开发者信息, 设计美观的静态页面展示榜单, 榜单包括

### 主要技术栈

python sqlite3 sql json html5 javascript css 等等

### 开发流程

- 通过爬虫脚本按条件爬取当天github开发者users列表, user列表数据中有user 的id name url  avatar_url  followers_total_count update_at 等等数据

- 通过爬虫脚本按条件爬取当天github 仓库列表信息, 包括id name url stargazerCount  description update_at 等等数据

- 将爬取到信息存入sqlite数据库(要注意sqlite 文件不能大于100m, github不支持大于100m, 当文件大于100m需要github action报错)

- 将当天爬取的所有数据存入sqlite 数据库后, 立即 生成需要的json文件(daily_trending.json weekly_trending.json monthly_trending.json top_repos.json top_users.json), 同时到 data/archive 按日期归档所有生成的json数据

- 用html5 css javascript 等 技术开发展示界面, 数据直接读取data下面的json 数据, 所有页面要支持中英文查看, 并且可以指定日期查看历史数据, 比如 查看 2025/04/20 的top_users.json , 当前页面 就会去archive下对应目录下的数据

### 核心关键

如果对需求不是很清楚,不要执行后续步骤, 可以向我提问, 直到清楚后再执行