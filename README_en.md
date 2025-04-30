# CodeLegend
![visitor badge](https://visitor-badge.laobi.icu/badge?page_id=Mohistack.CodeLegend)

[![Update GitHub Code Legend LeaderBoards](https://github.com/Mohistack/CodeLegend/actions/workflows/github-code_legend.yml/badge.svg)](https://github.com/Mohistack/CodeLegend/actions/workflows/github-code_legend.yml)

This project uses GitHub Actions to periodically fetch GitHub data and automatically generate the following rankings:

## Rankings Introduction
Ranking data is automatically fetched and calculated based on GitHub API, updated daily.

### Ranking Categories
- **Daily Top 100 Trending Repositories**  
  Top 100 repositories with the most new stars in the last 24 hours.  

- **Weekly Top 100 Trending Repositories**  
  Top 100 repositories with the most new stars in the last 7 days.  

- **Monthly Top 100 Trending Repositories**  
  Top 100 repositories with the most new stars in the last 30 days.  

- **All-Time Top 100 Most Starred Repositories**  
  Top 100 repositories with the highest total stars in history.  

- **Top 100 Most Followed Users**  
  Top 100 GitHub users with the most followers.

### TODO LIST
- **Daily Top 100 Most Active Users**  
  Top 100 GitHub users with the most commits in the last 24 hours.

- **Weekly Top 100 Most Active Users**  
  Top 100 GitHub users with the most commits in the last 7 days.

- **Monthly Top 100 Most Active Users**  
  Top 100 GitHub users with the most commits in the last 30 days.

- **Monthly Most Popular Languages**  
  Statistics of most used languages in new projects created in last 30 days, with repository count for each language.  

## Last Updated

See the top of each ranking page for the last update time, or check [update_time.txt](data/update_time.txt).

## Quick Start

1. Install dependencies (Python 3 required)  
   ```bash
   pip install -r requirements.txt
   ```
2. Get GitHub Token  
   - Visit [GitHub Personal Settings](https://github.com/settings/tokens) to generate a token with public_repo permissions.
   - Recommended to save the token as environment variable `GITHUB_TOKEN` for script usage.
3. Configure environment variables  
   - Run in local terminal:
     ```bash
     export GITHUB_TOKEN=your_token
     ```
4. Data fetching  
   - Run the data fetching script:
     ```bash
     python scripts/fetch_github_main.py
     ```
   - The script will automatically fetch the latest ranking data and generate HTML files in `public/` directory.
5. Local preview  
   - Use any static server (e.g. Python built-in http.server) to preview:
     ```bash
     cd public
     python3 -m http.server 8080
     ```
   - Visit [http://localhost:8080](http://localhost:8080) in browser to view the rankings.
6. Automated deployment  
   - The project is configured with GitHub Actions to automatically fetch and deploy latest rankings when pushed to main branch.
   - Workflow configuration can be found at `.github/workflows/github-code_legend.yml`.

## Additional Notes

- To customize the fetching scope or ranking count, modify parameters in `scripts/fetch_github_main.py`.
- If encountering API rate limits, try changing the token or retry later.