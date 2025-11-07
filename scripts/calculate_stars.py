import os
import requests
import json
import sys

def get_repo_stars(repo_name, token):
    """获取一个特定仓库的 Star 数 (例如 'owner/repo')"""
    headers = {'Authorization': f'token {token}'}
    repo_url = f"https://api.github.com/repos/{repo_name}"
    
    try:
        r = requests.get(repo_url, headers=headers)
        r.raise_for_status() # 如果请求失败则抛出异常
        repo_data = r.json()
        
        stars_count = repo_data.get('stargazers_count', 0)
        print(f"仓库 {repo_name} 统计完毕, 共有 {stars_count} 颗星。")
        return stars_count
        
    except requests.exceptions.RequestException as e:
        print(f"Error: 请求 {repo_name} 的仓库时出错: {e}")
        return 0

def get_all_repos_stars(account_name, token):
    """获取一个用户或组织的所有公开仓库的 Star 总数"""
    headers = {'Authorization': f'token {token}'}
    
    account_type_url = f"https://api.github.com/users/{account_name}"
    response = requests.get(account_type_url, headers=headers)
    if response.status_code != 200:
        print(f"Error: 无法获取账户 {account_name} 的信息。")
        return 0
        
    account_type = response.json().get('type', 'User').lower()
    
    if account_type == 'organization':
        repos_url = f"https://api.github.com/orgs/{account_name}/repos"
    else:
        repos_url = f"https://api.github.com/users/{account_name}/repos"
        
    page = 1
    stars_count = 0
    
    while True:
        params = {'per_page': 100, 'page': page}
        try:
            r = requests.get(repos_url, headers=headers, params=params)
            r.raise_for_status() 
            repos = r.json()
            
            if not repos: 
                break
                
            for repo in repos:
                stars_count += repo.get('stargazers_count', 0)
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error: 请求 {account_name} 的仓库时出错: {e}")
            return stars_count
            
    print(f"账户 {account_name} 统计完毕, 共有 {stars_count} 颗星。")
    return stars_count

def main():
    # 从 GitHub Actions 的环境变量中读取需要统计的条目列表
    items_str = os.environ.get('ACCOUNTS_TO_CHECK')
    token = os.environ.get('GITHUB_TOKEN')

    if not items_str or not token:
        print("Error: 缺少 ACCOUNTS_TO_CHECK 或 GITHUB_TOKEN 环境变量。")
        sys.exit(1)

    items_to_check = items_str.split(',')
    total_stars = 0
    individual_stars = {}

    for item in items_to_check:
        item_name = item.strip()
        if not item_name: # 避免空字符串
            continue
            
        stars = 0
        
        # 🔴 核心逻辑修改：检查是否有斜杠
        if '/' in item_name:
            # 这是一个仓库, 比如 "bigai-ai/ICE"
            stars = get_repo_stars(item_name, token)
        else:
            # 这是一个账户/组织, 比如 "kailinjiang"
            stars = get_all_repos_stars(item_name, token)
            
        individual_stars[item_name] = stars
        total_stars += stars

    print(f"总 Star 数: {total_stars}")
    print(f"详细分项: {individual_stars}")

    # 准备 shields.io 需要的 JSON 数据
    data = {
        "schemaVersion": 1,
        "label": "Stars",
        "message": str(total_stars),
        "color": "brightgreen",
        "namedLogo": "github",
        "breakdown": individual_stars
    }

    # 将 JSON 文件写入仓库根目录
    output_filename = "total-stars.json"
    with open(output_filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"成功写入 {output_filename}")

if __name__ == "__main__":
    main()
