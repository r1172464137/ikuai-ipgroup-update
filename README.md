# iKuai CNIP组 更新脚本
这是原作者的介绍

1. Usage:
   1. `python3 main.py -h [iKuai IP] -u [Username] -p [Password] -gn [IP Group Name] -gid [IP Group ID]` (最好先在py文件里写好)
2. Requirements:
   1. Python3.6+
   2. Requests

# 修改说明

1. 增加了自动删除包含有设置好的IP Group Name的ip分组。
2. 因为爱块ip分组只支持最多1000个行，虽然原作者也能通过post的方式写入，但太别扭了，自动分组。
3. 自动识别ipv4和v6(爱块的ipv6端口分流功能还没实现)。
