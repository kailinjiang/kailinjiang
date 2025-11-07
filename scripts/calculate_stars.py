import os
import requests
import json
import sys

def get_all_repos_stars(account_name, token):
    """获取一个用户或组织的所有公开仓库的 Star 总数"""
    headers = {'Authorization': f'token {token}'}
    
    # 检查是用户还是组织
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
        # 使用 per_page=100 来减少 API 请求次数
        params = {'per_page': 100, 'page': page}
        try:
            r = requests.get(repos_url, headers=headers, params=params)
            r.raise_for_status() # 如果请求失败则抛出异常
            repos = r.json()
            
            if not repos: # 如果这一页没有数据，说明已经到底
                break
                
            for repo in repos:
                stars_count += repo.get('stargazers_count', 0)
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error: 请求 {account_name} 的仓库时出错: {e}")
            return stars_count # 返回已统计的星数
            
    print(f"账户 {account_name} 统计完毕, 共有 {stars_count} 颗星。")
    return stars_count

def main():
    # 从 GitHub Actions 的环境变量中读取需要统计的账户列表
    accounts_str = os.environ.get('ACCOUNTS_TO_CHECK')
    # 从环境变量中读取 GITHUB_TOKEN
    token = os.environ.get('GITHUB_TOKEN')

    if not accounts_str or not token:
        print("Error: 缺少 ACCOUNTS_TO_CHECK 或 GITHUB_TOKEN 环境变量。")
        sys.exit(1)

    accounts = accounts_str.split(',')
    total_stars = 0
    
    # 🔴 新增：创建一个字典来存储每个账号的星标数
    individual_stars = {}

    for account in accounts:
        if account: # 避免空字符串
            account_name = account.strip()
            
            # 🔴 修改：获取星标并存入两个变量
            stars = get_all_repos_stars(account_name, token)
            individual_stars[account_name] = stars
            total_stars += stars

    print(f"总 Star 数: {total_stars}")
    print(f"详细分项: {individual_stars}")

    # 准备 shields.io 需要的 JSON 数据
    data = {
        "schemaVersion": 1,
        "label": "Stars",  # 保持 "stars"
        "message": str(total_stars), # 徽章仍然显示总数
        "color": "brightgreen",
        "namedLogo": "github",
        
        # 🔴 新增：把详细分项数据添加到 JSON 中
        "breakdown": individual_stars
    }

    # 将 JSON 文件写入仓库根目录
    output_filename = "total-stars.json"
    with open(output_filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"成功写入 {output_filename}")

if __name__ == "__main__":
    main()
