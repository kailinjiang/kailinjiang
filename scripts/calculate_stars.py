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

    # 文件 1: 准备 徽章 (badge) 专用 JSON 数据
    badge_data = {
        "schemaVersion": 1,
        "label": "stars",
        "message": str(total_stars),
        "color": "brightgreen",
        "namedLogo": "github"
    }
    
    # 文件 2: 准备 详细分类 (breakdown) 专用 JSON 数据
    breakdown_data = {
        "total": total_stars,
        "breakdown": individual_stars
    }

    # 写入 两个 文件
    badge_filename = "total-stars.json"
    breakdown_filename = "stars-breakdown.json"

    try:
        with open(badge_filename, 'w') as f:
            json.dump(badge_data, f, indent=2)
        print(f"成功写入徽章文件: {badge_filename}")

        with open(breakdown_filename, 'w') as f:
            json.dump(breakdown_data, f, indent=2)
        print(f"成功写入分类文件: {breakdown_filename}")

    except IOError as e:
        print(f"Error: 写入 JSON 文件时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
