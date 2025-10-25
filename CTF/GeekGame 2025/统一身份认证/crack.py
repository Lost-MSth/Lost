import requests
import json
from collections import deque
import sys
import ast


TARGET_FIELD = "flag2"
ROOT_QUERY_TYPE = "Secret"


with open('data.txt', 'r') as f:
    DATA = f.read().strip()


def build_schema_graph(types_data):
    """
    将从内省查询得到的类型列表转换成一个图（字典表示）。
    键是类型名，值是另一个字典，其中键是字段名，值是该字段对应的类型名。
    """
    graph = {}
    print("[*] 正在本地构建 Schema 关系图...")
    for type_def in types_data:
        if type_def.get('fields'):
            type_name = type_def['name']
            graph[type_name] = {}
            for field in type_def['fields']:
                field_name = field['name']

                final_type = field['type']
                graph[type_name][field_name] = final_type['name']
    print("[+] Schema 关系图构建完成。")
    return graph


def find_path_in_graph(graph, start_node, target_field):
    """
    在构建好的图中，使用广度优先搜索 (BFS) 查找从 start_node 到 target_field 的路径。
    """
    if start_node not in graph:
        print(f"[!] 错误：起始类型 '{start_node}' 在 Schema 中未找到。", file=sys.stderr)
        return None

    # 队列中存储元组 (当前类型名, 到达该类型的路径字符串)
    queue = deque([(start_node, '')])
    # 记录已访问的类型，防止在递归类型定义中无限循环
    visited = set([start_node])
    print(f"[*] 开始在本地图中搜索从 '{start_node}' 到 '{target_field}' 的路径...")
    while queue:
        current_type, path = queue.popleft()

        if current_type not in graph:
            continue
        # 遍历当前类型的所有字段
        for field_name, field_type_name in graph[current_type].items():
            new_path = f"{path}.{field_name}" if path else field_name

            # 检查是否找到目标字段
            if field_name == target_field:
                return new_path

            # 如果字段类型是一个新的、未访问过的对象类型，则将其加入队列继续搜索
            if field_type_name in graph and field_type_name not in visited:
                visited.add(field_type_name)
                queue.append((field_type_name, new_path))

    return None


if __name__ == "__main__":
    # 1. 获取 Schema 数据
    all_types = ast.literal_eval(DATA)

    # 2. 构建关系图
    schema_graph = build_schema_graph(all_types)

    # 3. 在图中搜索路径
    # 我们需要找到根查询对象的名字，它通常是'Query'
    # 内省查询结果本身会包含这个信息，但直接用 'Query' 通常是正确的
    final_path = find_path_in_graph(
        schema_graph, ROOT_QUERY_TYPE, TARGET_FIELD)
    if final_path:
        # 脚本找到的路径是从 'Query' 类型内部开始的，而实际查询需要从顶级字段开始
        # 比如脚本找到路径 login.user.name, 实际查询是 { login { user { name } } }
        # 在这个题目中，flag 在 `secret` 查询下，所以我们手动加上 `secret` 前缀
        # 脚本的输出会类似 `secret.secret_Bm4e...`，我们需要把它变成 `secret.{secret_Bm4e...}`
        # 为了方便，这里直接打印最终路径

        # 题目中的 Query 类型有两个字段 'login' 和 'secret'，flag 在 'secret' 下

        final_path = final_path.replace(
            '.', '{') + '}' * (final_path.count('.'))
        final_query_example = f"{{ {final_path} }}"
        print("\n" + "="*50)
        print(f"[+] 成功! 找到目标字段 '{TARGET_FIELD}'!")
        print(f"[+] 最终路径: {final_path.replace('{', '.').replace('}', '')}")
        print(f"[+] 可用于探索的 GraphQL 查询片段示例: \n{final_query_example}")
        print("="*50)

    else:
        print(
            f"\n[-] 在 Schema 中未找到从 '{ROOT_QUERY_TYPE}' 到 '{TARGET_FIELD}' 的路径。")
