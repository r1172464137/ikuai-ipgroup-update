import requests
import hashlib
import sys
import re

def main():
    # 默认值
    iKuaiHostIP = "192.168.5.1"
    username = "admin"
    password = "518126zz"
    groupName = "CN_ip_list"
    groupID = "15"

    # 解析命令行参数
    parse_arguments()

    # 使用MD5对密码进行哈希处理
    md5passwd = hashlib.md5(password.encode()).hexdigest()

    # 从指定的URL获取IP列表
    ipv4_lines, ipv6_lines = fetch_ip_list("https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/text/cn.txt")

    # 创建用于进行请求的会话
    session = requests.Session()
    # 登录到 iKuai 主机
    login_to_ikuai(session, iKuaiHostIP, username, md5passwd)

    # 删除包含指定组名的现有IP组
    ip_groups = get_ip_groups(session, iKuaiHostIP, "IPv4")
    delete_ip_groups(session, iKuaiHostIP, ip_groups, groupName, "IPv4")
    ipv6_groups = get_ip_groups(session, iKuaiHostIP, "IPv6")
    delete_ip_groups(session, iKuaiHostIP, ipv6_groups, groupName, "IPv6")

    # 每1000个IP确认一次后上传IP组
    upload_and_confirm(session, iKuaiHostIP, int(groupID), groupName, ipv4_lines, "IPv4")
    upload_and_confirm(session, iKuaiHostIP, int(groupID), groupName, ipv6_lines, "IPv6")

def parse_arguments():
    # 解析命令行参数
    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if arg == "-h":
            iKuaiHostIP = sys.argv[i + 1]
        elif arg == "-u":
            username = sys.argv[i + 1]
        elif arg == "-p":
            password = sys.argv[i + 1]
        elif arg == "-gn":
            groupName = sys.argv[i + 1]
        elif arg == "-gid":
            groupID = sys.argv[i + 1]

def fetch_ip_list(url):
    # 从指定的URL获取IP列表
    ip_list = requests.get(url).text

    # 使用正则表达式查找包含IPv4和IPv6地址的整行
    ipv4_lines = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:\/[0-9]+)?\b', ip_list)
    ipv6_lines = re.findall(r'\b(?:[0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}(?:\/[0-9]+)?\b', ip_list)

    return ipv4_lines, ipv6_lines

def login_to_ikuai(session, iKuaiHostIP, username, md5passwd):
    # 登录到 iKuai 主机
    session.post("http://{}/Action/login".format(iKuaiHostIP), json={
        "username": username,
        "passwd": md5passwd
    })

def del_ipgroup_function(session, iKuaiHostIP, groupID, ip_type):
    # 调用 'ipgroup' 函数删除IP组
    json_data ={"action": "del","param": {"id": groupID}}
    if ip_type == "IPv4":
        json_data["func_name"] = "ipgroup"
    if ip_type == "IPv6":
        json_data["func_name"] = "ipv6group"
    session.post("http://{}/Action/call".format(iKuaiHostIP), json=json_data)

def upload_ip_group(session, iKuaiHostIP, ipgroup):
    # 上传IP组信息
    files = {'ipgroup.txt': ipgroup.encode()}
    session.post("http://{}/Action/upload".format(iKuaiHostIP), files=files)

def call_ipgroup_function(session, iKuaiHostIP, ip_type):
    # 调用 'ipgroup' 函数导入IP组
    json_data = {"action": "IMPORT", "param": {"filename": "ipgroup.txt", "append": 1}}
    if ip_type == "IPv4":
        json_data["func_name"] = "ipgroup"
    if ip_type == "IPv6":
        json_data["func_name"] = "ipv6group"

    session.post("http://{}/Action/call".format(iKuaiHostIP), json=json_data)

def upload_and_confirm(session, iKuaiHostIP, start_group_id, start_group_name, ip_list, ip_type):
    if ip_type == "IPv4":
        start_group_name = "CN_ip_list"
    if ip_type == "IPv6":
        start_group_name = "CN_ipv6_list"
    # 确定所需的组数
    num_groups = (len(ip_list) + 999) // 1000

    for group_num in range(num_groups):
        start_idx = group_num * 1000
        end_idx = (group_num + 1) * 1000
        current_ip_list = ip_list[start_idx:end_idx]

        # 格式化IP组信息
        current_group_id = start_group_id + group_num
        current_group_name = "{}_{}".format(start_group_name, group_num + 1)
        ipgroup = "id={} comment=, group_name={} addr_pool={}".format(current_group_id, current_group_name, ','.join(current_ip_list))

        # 上传IP组信息
        upload_ip_group(session, iKuaiHostIP, ipgroup)

        # 根据IP类型调用 'ipgroup' 函数导入IP组
        call_ipgroup_function(session, iKuaiHostIP, ip_type)

def get_ip_groups(session, iKuaiHostIP, ip_type):
    # 获取IP组列表
    json_data = {
        "action": "show",
        "param": {"TYPE": "total,data", "limit": "0,100", "ORDER_BY": "", "ORDER": ""}
    }
    if ip_type == "IPv4":
        json_data["func_name"] = "ipgroup"
    if ip_type == "IPv6":
        json_data["func_name"] = "ipv6group"
    response = session.post(f"http://{iKuaiHostIP}/Action/call", json=json_data).json()

    if response["Result"] == 30000:
        return response.get("Data", {}).get("data", [])
    else:
        print(f"获取IP组时出错: {response['ErrMsg']}")
        return []

def delete_ip_groups(session, iKuaiHostIP, ip_groups, group_name, ip_type):
    # 删除指定组名的IP组
    if ip_type == "IPv4":
        group_name = "CN_ip_list"
    if ip_type == "IPv6":
        group_name = "CN_ipv6_list"
    for ip_group in ip_groups:
        gname = ip_group.get("group_name", "")
        if group_name in gname:
            group_id = ip_group.get("id", "")
            del_ipgroup_function(session, iKuaiHostIP, group_id, ip_type)
            print(f"已删除ID为 {ip_group['id']}，名称为 {ip_group['group_name']} 的IP组。")

if __name__ == "__main__":
    main()
