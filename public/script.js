/**
 * @fileoverview Main script for the GitHub Rank Leaderboard application.
 * Handles data fetching, rendering, pagination, and internationalization.
 * @license MIT
 */

document.addEventListener('DOMContentLoaded', () => {
  /**
   * Namespace for the CodeLegend application.
   * @namespace
   */
  const GitRank = {
    /** @type {Array<Object>} Holds the currently displayed dataset. */
    currentData: [],
    /** @type {number} Current page number for pagination. */
    currentPage: 1,
    /** @type {number} Number of items to display per page. */
    itemsPerPage: 100, // Default value, will be updated from select
    /** @type {string} The type of ranking currently displayed (e.g., 'daily_trending'). */
    currentRankType: 'top_users_list', // Default type
    /** @type {string} Current language ('zh' or 'en'). */
    currentLang: document.documentElement.lang.startsWith('zh') ? 'zh' : 'en',

    /** DOM element references */
    elements: {
      rankNavButtons: document.querySelectorAll('.rank-nav button'),
      rankListContainer: document.getElementById('rank-list-container'),
      paginationContainer: document.getElementById('pagination-container'),
      itemsPerPageSelect: document.getElementById('items-per-page'),
      updateTimeElement: document.getElementById('update-time'),
      fetchTimeFooterElement: document.getElementById('fetch-time-footer'), // Assuming this exists or is needed
      langLinks: document.querySelectorAll('.language-switch a.lang-select'),
      githubUserCountElement: document.getElementById('github-user-count'),
      mainTitleElement: document.querySelector('[data-i18n="mainTitle"]'),
      i18nElements: document.querySelectorAll('[data-i18n]'),
    },

    /** Translation strings */
    translations: {
      zh: {
        loading: '正在加载数据...', 
        fetchTimePrefix: '上次数据抓取时间: ',
        updateTimePrefix: '最近更新时间：',
        page: '页',
        prev: '上一页',
        next: '下一页',
        repoTitle: (name) => `${name} - 仓库详情`,
        userTitle: (login) => `${login} - 用户详情`,
        stars: '🌟总数',
        followers: '粉丝数',
        language: '语言',
        description: '描述',
        daily_trending: '🔥最近一天最热项目',
        weekly_trending: '🔥🔥最近一周最热项目',
        monthly_trending: '🔥🔥🔥最近一月最热项目',
        top_repos_list: '获的🌟最多的项目',
        top_users_list: '追随者最多的开发者🧑‍💻',
        mainTitle: 'GitHub 封神榜',
        langLabel: '语言',
        githubUserCount: 'GitHub 当前注册用户总数：',
        itemsPerPage: '每页显示:',
        dataSource: '数据来源: GitHub API',
        projectSource: '项目源码',
        noItems: '没有找到项目。',
        errorLoading: (type, message, url) => `加载 ${GitRank.i18n(type)} 数据时出错。详情: ${message}。请确保数据文件存在于 ${url} 且抓取脚本已运行。`,
        errorUpdateTime: '获取更新时间失败',
        title: 'GitHub 封神榜',
        stars_1d: '今日新增🌟',
        stars_7d: '本周新增🌟',
        stars_30d: '本月新增🌟',
      },
      en: {
        loading: 'Loading data...',
        fetchTimePrefix: 'Last data fetch time: ',
        updateTimePrefix: 'Last updated: ',
        page: 'Page',
        prev: 'Previous',
        next: 'Next',
        repoTitle: (name) => `${name} - Repository Details`,
        userTitle: (login) => `${login} - User Details`,
        stars: '🌟Stars',
        followers: 'Followers',
        language: 'Language',
        description: 'Description',
        daily_trending: '🔥Daily Trending',
        weekly_trending: '🔥🔥Weekly Trending',
        monthly_trending: '🔥🔥🔥Monthly Trending',
        top_repos_list: 'Top Repos',
        top_users_list: 'Top Coders🧑‍💻',
        mainTitle: 'GitHub Legend Leaderboard',
        langLabel: 'Language',
        githubUserCount: 'GitHub Registered Users:',
        itemsPerPage: 'Items per page:',
        dataSource: 'Data Source: GitHub API',
        projectSource: 'Project Source',
        noItems: 'No items found for this page.',
        errorLoading: (type, message, url) => `Error loading data for ${GitRank.i18n(type)}. Details: ${message}. Please ensure the data file exists at ${url} and the fetch script has run.`,
        errorUpdateTime: 'Failed to fetch update time',
        title: 'GitHub Legend Leaderboard',
        stars_1d: '🌟Stars (Today increased)',
        stars_7d: '🌟Stars (This Week increased)',
        stars_30d: '🌟Stars (This Month increased)',
      },
    },

    /**
     * Gets the translation for a given key in the current language.
     * @param {string} key The translation key.
     * @param {...*} args Arguments for function-based translations.
     * @returns {string} The translated string.
     */
    i18n(key, ...args) {
      const translation = GitRank.translations[GitRank.currentLang]?.[key];
      if (typeof translation === 'function') {
        return translation(...args);
      }
      // Fallback for keys not directly in translations but potentially in HTML
      if (!translation) {
        const element = document.querySelector(`[data-i18n="${key}"]`);
        if (element) {
          const raw = element.textContent.split('/');
          return (GitRank.currentLang === 'zh' ? raw[0] : raw[1] || raw[0])?.trim() || key;
        }
      }
      return translation || key;
    },

    /**
     * Fetches data for the specified ranking type.
     * @param {string} type The ranking type (e.g., 'daily_trending').
     */
    async fetchData(type) {
      GitRank.elements.rankListContainer.innerHTML = `<p>${GitRank.i18n('loading')}</p>`;
      GitRank.elements.paginationContainer.innerHTML = '';
      GitRank.currentRankType = type;
      GitRank.currentPage = 1;
      const dataUrl = `./data/${type}.json`;

      try {
        const response = await fetch(dataUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Determine the correct data array key
        const listData = data.top_repos || data.top_users || [];
        GitRank.currentData = listData.map((item, index) => ({ ...item, rank: index + 1 }));

        // Fetch update time separately
        GitRank.fetchUpdateTime();

        // Update GitHub user count
        GitRank.updateGitHubUserCount(data.meta);

      } catch (error) {
        console.error('Error fetching data:', error);
        GitRank.elements.rankListContainer.innerHTML = 
          `<p>${GitRank.i18n('errorLoading', type, error.message, dataUrl)}</p>`;
        GitRank.currentData = [];
        // Attempt to update user count to N/A on error
        GitRank.updateGitHubUserCount(null); 
        // Also clear update time on error
        GitRank.updateTimeDisplay('N/A', GitRank.i18n('errorUpdateTime'));
      }

      GitRank.renderList();
      GitRank.renderPagination();
    },

    /**
     * Fetches and displays the last update time.
     */
    async fetchUpdateTime() {
      const updateTimePath = './data/update_time.txt';
      try {
        const response = await fetch(updateTimePath);
        if (!response.ok) throw new Error(GitRank.i18n('errorUpdateTime'));
        const text = await response.text();
        GitRank.updateTimeDisplay(text);
      } catch (error) {
        console.error('Error fetching update time:', error);
        GitRank.updateTimeDisplay('N/A', error.message);
      }
    },

    /**
     * Updates the display for update time and fetch time.
     * @param {string} timeText The time text (or 'N/A').
     * @param {string} [errorText=''] Optional error text to display instead.
     */
    updateTimeDisplay(timeText, errorText = '') {
        const displayText = errorText || timeText;
        const updateTimeFullText = `${GitRank.i18n('updateTimePrefix')} ${displayText}`;
        const fetchTimeFullText = `${GitRank.i18n('fetchTimePrefix')} ${displayText}`;

        if (GitRank.elements.updateTimeElement) {
            GitRank.elements.updateTimeElement.textContent = updateTimeFullText;
        }
        // Ensure the footer element exists before trying to set its text content
        if (GitRank.elements.fetchTimeFooterElement) { 
            GitRank.elements.fetchTimeFooterElement.textContent = fetchTimeFullText;
        } else {
            // Optionally create the footer element if it's missing and needed
            // Or simply log a warning if it's expected but not found
            // console.warn('Fetch time footer element not found.');
        }
    },

    /**
     * Updates the GitHub user count display.
     * Tries to get the count from metadata, falls back to fetching top_users_list.json if needed.
     * @param {object | null} meta The metadata object from the fetched data, or null on error.
     */
    async updateGitHubUserCount(meta) {
      let count = null;
      if (meta && typeof meta.user_total_count === 'number') {
        count = meta.user_total_count;
      } else {
        // Attempt to fetch from top_users_list.json only if count wasn't in the primary data's meta
        try {
          const userCountResp = await fetch('./data/top_users_list.json');
          if (userCountResp.ok) {
            const userCountData = await userCountResp.json();
            if (userCountData.meta && typeof userCountData.meta.user_total_count === 'number') {
              count = userCountData.meta.user_total_count;
            }
          }
        } catch (userCountError) {
          console.warn('Could not fetch separate user count:', userCountError);
        }
      }

      if (GitRank.elements.githubUserCountElement) {
        GitRank.elements.githubUserCountElement.textContent = 
          `${GitRank.i18n('githubUserCount')} ${count ? count.toLocaleString() : 'N/A'}`;
      }
    },

    /**
     * Renders the list of items based on current data and pagination.
     */
    renderList() {
      GitRank.elements.rankListContainer.innerHTML = ''; // Clear previous list
      const startIndex = (GitRank.currentPage - 1) * GitRank.itemsPerPage;
      const endIndex = startIndex + GitRank.itemsPerPage;
      const itemsToDisplay = GitRank.currentData.slice(startIndex, endIndex);

      if (itemsToDisplay.length === 0) {
        const message = GitRank.currentData.length > 0 ? GitRank.i18n('noItems') : GitRank.i18n('loading');
        GitRank.elements.rankListContainer.innerHTML = `<p>${message}</p>`;
        return;
      }

      const listElement = document.createElement('ol');
      listElement.classList.add('rank-list');
      // listElement.start = startIndex + 1; // Use CSS counters or manual rank number instead

      itemsToDisplay.forEach((item, index) => {
        const displayRank = startIndex + index + 1;
        const listItem = GitRank.createListItem(item, displayRank);
        listElement.appendChild(listItem);
      });

      GitRank.elements.rankListContainer.appendChild(listElement);
    },

    /**
     * Creates a list item element for a given data item.
     * @param {object} item The data item (repository or user).
     * @param {number} displayRank The rank number to display.
     * @returns {HTMLLIElement} The created list item element.
     */
    createListItem(item, displayRank) {
      const listItem = document.createElement('li');
      listItem.classList.add('rank-item');

      // Check if it's a user item (presence of 'login' or 'followersCount' is a good indicator)
      const isUser = 'login' in item || 'followersCount' in item;

      if (isUser) {
        listItem.innerHTML = `
          <span class="rank-number">${displayRank}.</span>
          <div class="item-content">
            <div class="item-main">
              <img src="${item.avatarUrl || 'https://via.placeholder.com/40'}" alt="${item.login}" width="40" height="40" loading="lazy">
              <a href="${item.url}" target="_blank" title="${GitRank.i18n('userTitle', item.login)}">${item.login} ${item.name ? `(${item.name})` : ''}</a>
            </div>
            <div class="item-details">
              <span>${GitRank.i18n('followers')}: ${item.followersCount?.toLocaleString() || 'N/A'}</span>
            </div>
          </div>
        `;
      } else {
        // Assume repository item
        const languages = Array.isArray(item.language) ? item.language.join(', ').trim() : (item.language || '');
        listItem.innerHTML = `
          <span class="rank-number">${displayRank}.</span>
          <div class="item-content">
            <div class="item-main">
              <a href="${item.url}" target="_blank" title="${GitRank.i18n('repoTitle', item.name)}">${item.name}</a>
            </div>
            <div class="item-details">
              ${(() => {
                let starsLabel = GitRank.i18n('stars');
                let starsValue = item.accumulatedStars?.toLocaleString() || '0';
                let trendingStarsLabel = '';
                let trendingstarsValue = '';
                if (GitRank.currentRankType === 'daily_trending' && item.accumulatedStars_1d !== undefined) {
                  //Daily, weekly, or monthly trending
                  trendingStarsLabel = GitRank.i18n('stars_1d');
                  trendingstarsValue = item.accumulatedStars_1d?.toLocaleString() || '0';
                 
                } else if (GitRank.currentRankType === 'weekly_trending' && item.accumulatedStars_7d !== undefined) {
               
                  trendingStarsLabel = GitRank.i18n('stars_7d');
                  trendingstarsValue = item.accumulatedStars_7d?.toLocaleString() || '0';

                } else if (GitRank.currentRankType === 'monthly_trending' && item.accumulatedStars_30d !== undefined) {
                
                  trendingStarsLabel = GitRank.i18n('stars_30d');
                  trendingstarsValue = item.accumulatedStars_30d?.toLocaleString() || '0';
                }
                return `<span>${starsLabel}: ${starsValue}</span>   <span>${trendingStarsLabel}: ${trendingstarsValue}</span>`;
              })()}
              ${languages ? `<span>${GitRank.i18n('language')}: ${languages}</span>` : ''}
            </div>
            ${item.description ? `<p class="item-description">${item.description}</p>` : ''} 
          </div>
        `;
      }
      return listItem;
    },

    /**
     * Renders the pagination controls.
     */
    renderPagination() {
      GitRank.elements.paginationContainer.innerHTML = ''; // Clear previous pagination
      const totalPages = Math.ceil(GitRank.currentData.length / GitRank.itemsPerPage);

      if (totalPages <= 1) return; // No pagination needed

      // Previous Button
      const prevButton = document.createElement('button');
      prevButton.textContent = GitRank.i18n('prev');
      prevButton.disabled = GitRank.currentPage === 1;
      prevButton.addEventListener('click', () => {
        if (GitRank.currentPage > 1) {
          GitRank.currentPage--;
          GitRank.renderList();
          GitRank.renderPagination(); // Re-render pagination to update button states
        }
      });
      GitRank.elements.paginationContainer.appendChild(prevButton);

      // Page Number Indicator
      const pageInfo = document.createElement('span');
      pageInfo.textContent = `${GitRank.i18n('page')} ${GitRank.currentPage} / ${totalPages}`;
      pageInfo.classList.add('current-page');
      GitRank.elements.paginationContainer.appendChild(pageInfo);

      // Next Button
      const nextButton = document.createElement('button');
      nextButton.textContent = GitRank.i18n('next');
      nextButton.disabled = GitRank.currentPage === totalPages;
      nextButton.addEventListener('click', () => {
        if (GitRank.currentPage < totalPages) {
          GitRank.currentPage++;
          GitRank.renderList();
          GitRank.renderPagination(); // Re-render pagination to update button states
        }
      });
      GitRank.elements.paginationContainer.appendChild(nextButton);
    },

    /**
     * Updates all elements with data-i18n attributes based on the current language.
     */
    updateI18nTexts() {
      // Update static text elements
      GitRank.elements.i18nElements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        const text = GitRank.i18n(key);
        // Avoid updating if translation is function-based (handled elsewhere)
        if (key && typeof GitRank.translations[GitRank.currentLang]?.[key] !== 'function') {
            el.textContent = text;
        }
      });

      // Update dynamic elements like button text
      GitRank.elements.rankNavButtons.forEach(button => {
        const type = button.dataset.type;
        button.textContent = GitRank.i18n(type);
      });

      // Update pagination text (if pagination exists)
      GitRank.renderPagination();

      // Update time/fetch displays
      GitRank.fetchUpdateTime(); // Re-fetch to get potentially cached time in new language format
      
      // Update GitHub user count display
      GitRank.updateGitHubUserCount(null); // Re-fetch count or use cached value with new lang format

      // Update page title
      document.title = GitRank.i18n('title');
    },

    /**
     * Sets up event listeners for UI elements.
     */
    setupEventListeners() {
      // Rank type navigation
      GitRank.elements.rankNavButtons.forEach(button => {
        button.addEventListener('click', () => {
          GitRank.elements.rankNavButtons.forEach(btn => btn.classList.remove('active'));
          button.classList.add('active');
          GitRank.fetchData(button.dataset.type);
        });
      });

      // Items per page selection
      GitRank.elements.itemsPerPageSelect.addEventListener('change', (event) => {
        GitRank.itemsPerPage = parseInt(event.target.value, 10);
        GitRank.currentPage = 1; // Reset to first page
        GitRank.renderList();
        GitRank.renderPagination();
      });

      // Language switching
      GitRank.elements.langLinks.forEach(link => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          const selectedLang = link.getAttribute('data-lang');
          if (selectedLang === GitRank.currentLang) return;

          GitRank.currentLang = selectedLang;
          document.documentElement.lang = GitRank.currentLang;

          // Update active link style
          GitRank.elements.langLinks.forEach(l => l.classList.remove('active'));
          link.classList.add('active');

          // Update all internationalized text
          GitRank.updateI18nTexts();

          // Re-fetch data to potentially update list content if language affects it (though unlikely here)
          // And crucially, to update the user count display format
          GitRank.fetchData(GitRank.currentRankType);
        });
      });
    },

    /**
     * Initializes the application.
     */
    init() {
      // Set initial items per page from select
      GitRank.itemsPerPage = parseInt(GitRank.elements.itemsPerPageSelect.value, 10);

      // Set initial language and update UI accordingly
      document.documentElement.lang = GitRank.currentLang;
      GitRank.elements.langLinks.forEach(link => {
        link.classList.toggle('active', link.dataset.lang === GitRank.currentLang);
      });
      GitRank.updateI18nTexts(); // Set initial text based on detected language

      // Setup event listeners
      GitRank.setupEventListeners();

      // Initial data fetch for the default active type
      const initialActiveButton = document.querySelector('.rank-nav button.active');
      GitRank.currentRankType = initialActiveButton ? initialActiveButton.dataset.type : 'daily_trending';
      GitRank.fetchData(GitRank.currentRankType);
    }
  };

  // Initialize the application
  GitRank.init();
});
