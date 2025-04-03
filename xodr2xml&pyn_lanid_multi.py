import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import matplotlib.pyplot as plt

def print_red(text):
    """
    使用 ANSI 转义序列将文本以红色显示。
    """
    print(f"\033[91m{text}\033[0m")  # 91 是红色代码，0m 重置颜色


def visualize_vector_map(vector_map_file):
    """
    可视化 Argoverse 向量地图 XML 文件。
    :param vector_map_file: 输入的 XML 文件路径。
    """
    try:
        tree = ET.parse(vector_map_file)
        root = tree.getroot()

        # 提取节点信息
        nodes = {}
        for node in root.findall(".//node"):
            node_id = int(node.get("id"))
            x = float(node.get("x"))
            y = float(node.get("y"))
            nodes[node_id] = (x, y)

        # 绘制节点
        plt.figure(figsize=(10, 10))
        for x, y in nodes.values():
            plt.scatter(x, y, color='blue', s=10, label='Nodes' if 'Nodes' not in plt.gca().get_legend_handles_labels()[1] else "")

        # 绘制车道信息
        for way in root.findall(".//way"):
            points = []
            for point in way.findall(".//point"):
                point_id = int(point.get("id"))
                if point_id in nodes:
                    points.append(nodes[point_id])

            if points:
                xs, ys = zip(*points)
                plt.plot(xs, ys, color='red', linewidth=1, label='Lanes' if 'Lanes' not in plt.gca().get_legend_handles_labels()[1] else "")

        plt.title("Argoverse Vector Map Visualization")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.legend()
        plt.grid(True)
        plt.show()

    except Exception as e:
        print_red(f"Error visualizing {vector_map_file}: {e}")

def load_and_visualize_mapping(json_file):
    """
    加载并可视化 tableidx 到 lane_id 的映射关系
    :param json_file: 输入 JSON 文件路径
    """
    try:
        # 加载 JSON 文件
        with open(json_file, 'r') as f:
            mapping = json.load(f)

        # 打印映射关系
        print("Mapping (tableidx -> lane_id):")
        for tableidx, lane_id in mapping.items():
            print(f"  {tableidx} -> {lane_id}")

        # 可视化为条形图
        tableidx_list = list(mapping.keys())
        lane_id_list = list(mapping.values())

        plt.figure(figsize=(10, 6))
        plt.bar(tableidx_list, range(len(lane_id_list)), color='skyblue')
        plt.xticks(rotation=45)
        plt.xlabel("Table Index (tableidx)")
        plt.ylabel("Lane Index (lane_id)")
        plt.title("Table Index to Lane ID Mapping")
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print_red(f"Error loading or visualizing {json_file}: {e}")

def generate_unique_lane_id(existing_ids):
    """
    生成唯一的 7 位十进制数作为 lane_id
    """
    while True:
        lane_id = random.randint(1000000, 9999999)  # 生成 7 位十进制数
        if lane_id not in existing_ids:
            existing_ids.add(lane_id)
            return lane_id

def parse_xodr_to_vector_map(xodr_file, existing_lane_ids):
    """
    解析 .xodr 文件并生成向量地图格式数据，包括唯一的 lane_id
    """
    try:
        tree = ET.parse(xodr_file)
        root = tree.getroot()

        nodes = []  # 用于存储节点数据
        ways = []  # 用于存储车道信息
        node_id = 0
        mapping = {}  # 存储 tableidx 到 laneid 的映射
        table_idx = 0

        # 遍历道路和车道信息
        for road in root.findall(".//road"):
            road_geometry = []

            # 提取道路的几何信息
            for geometry in road.findall(".//geometry"):
                x = float(geometry.get("x"))
                y = float(geometry.get("y"))
                road_geometry.append({"id": node_id, "x": x, "y": y})

                # 保存节点
                nodes.append({"id": node_id, "x": x, "y": y})
                node_id += 1

            # 遍历车道信息
            for lane_section in road.findall(".//laneSection"):
                for lane in lane_section.findall(".//lane"):
                    unique_lane_id = generate_unique_lane_id(existing_lane_ids)
                    mapping[str(table_idx)] = unique_lane_id
                    lane_type = lane.get("type", "driving")  # 默认类型为 driving
                    width = lane.get("width", "3.5")  # 默认宽度为 3.5 米

                    # 提取前继和后继关系
                    predecessor = road.find(".//link/predecessor")
                    successor = road.find(".//link/successor")

                    predecessor_id = predecessor.get("elementId") if predecessor is not None else None
                    successor_id = successor.get("elementId") if successor is not None else None

                    # 确保 predecessor_id 和 successor_id 是有效值
                    if predecessor_id == "None" or predecessor_id is None:
                        predecessor_id = None
                    else:
                        predecessor_id = int(predecessor_id)  # 转换为整数

                    if successor_id == "None" or successor_id is None:
                        successor_id = None
                    else:
                        successor_id = int(successor_id)  # 转换为整数

                    # 保存车道数据，使用唯一的 lane_id
                    ways.append({
                        "lane_id": unique_lane_id,
                        "lane_type": lane_type,
                        "width": width,
                        "geometry": road_geometry,
                        "tags": {
                            "predecessor": [predecessor_id] if predecessor_id else [],
                            "successor": [successor_id] if successor_id else [],
                            "l_neighbor_id": lane.get("l_neighbor_id", "None"),
                            "r_neighbor_id": lane.get("r_neighbor_id", "None")
                        }
                    })

                    table_idx += 1

        return nodes, ways, mapping

    except Exception as e:
        print_red(f"Error processing {xodr_file}: {e}")
        return [], [], {}

def save_vector_map_to_xml(nodes, ways, output_file):
    """
    将节点和车道信息保存为格式化的 XML 文件，使用唯一的 lane_id
    """
    root = ET.Element("ArgoverseVectorMap")

    # 添加节点信息
    for node in nodes:
        ET.SubElement(root, "node", id=str(node["id"]), x=str(node["x"]), y=str(node["y"]))

    # 添加车道信息
    for way in ways:
        way_elem = ET.SubElement(root, "way", lane_id=str(way["lane_id"]))

        # 添加额外的标签信息
        ET.SubElement(way_elem, "tag", k="has_traffic_control", v="False")
        ET.SubElement(way_elem, "tag", k="turn_direction", v="NONE")
        ET.SubElement(way_elem, "tag", k="is_intersection", v="False")
        ET.SubElement(way_elem, "tag", k="l_neighbor_id", v=way["tags"].get("l_neighbor_id", "None"))
        ET.SubElement(way_elem, "tag", k="r_neighbor_id", v=way["tags"].get("r_neighbor_id", "None"))

        # 添加节点引用
        for geom in way["geometry"]:
            ET.SubElement(way_elem, "nd", ref=str(geom["id"]))

        # 添加继承关系标签
        if "tags" in way and isinstance(way["tags"], dict):
            for predecessor in way["tags"].get("predecessor", []):
                if "None" not in str(predecessor):
                    # print(predecessor)
                    ET.SubElement(way_elem, "tag", k="predecessor", v=str(predecessor))
            for successor in way["tags"].get("successor", []):
                if "None" not in str(successor):
                    # print(successor)
                    ET.SubElement(way_elem, "tag", k="successor", v=str(successor))

    # 格式化 XML 并写入文件
    xml_str = ET.tostring(root, encoding="unicode")
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"Saved vector map to {output_file}")

def batch_convert_xodr_to_vector_map_and_json(input_folder, output_folder):
    """
    批量转换.xodr文件并合并到单一输出文件，添加数据去重功能
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 使用字典存储全局数据用于去重
    global_nodes = {}  # {node_key: node_data}
    global_ways = {}  # {way_hash: way_data}
    global_mapping = {}  # 全局映射表
    existing_lane_ids = set()  # 全局唯一ID集合
    table_idx_counter = 0  # 全局tableidx计数器

    # 第一阶段：递归处理所有.xodr文件
    for root_dir, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.xodr'):
                xodr_path = os.path.join(root_dir, file)
                print(f"Processing {xodr_path}")

                try:
                    tree = ET.parse(xodr_path)
                    root = tree.getroot()

                    # 处理道路几何信息
                    for road in root.findall(".//road"):
                        # 处理几何节点并去重
                        road_nodes = []
                        for geometry in road.findall(".//geometry"):
                            x = round(float(geometry.get("x")), 4)  # 精度控制
                            y = round(float(geometry.get("y")), 4)
                            node_key = f"{x}_{y}"  # 基于坐标的哈希键

                            if node_key not in global_nodes:
                                # 生成新节点ID为当前全局节点数量
                                new_node_id = len(global_nodes)
                                global_nodes[node_key] = {
                                    "id": new_node_id,
                                    "x": x,
                                    "y": y
                                }
                            road_nodes.append(global_nodes[node_key])

                        # 跳过空几何的道路
                        if not road_nodes:
                            continue

                        # 处理车道信息
                        for lane_section in road.findall(".//laneSection"):
                            for lane in lane_section.findall(".//lane"):
                                # 生成车道特征哈希
                                lane_hash = hash(
                                    (tuple((n["x"], n["y"]) for n in road_nodes),
                                     lane.get("type", "driving"),
                                     lane.get("width", "3.5")
                                     ))

                                # 如果车道已存在，复用现有数据
                                # if lane_hash in global_ways:
                                #     # existing_lane_id = global_ways[lane_hash]["lane_id"]
                                #     # global_mapping[str(table_idx_counter)] = existing_lane_id
                                #     # table_idx_counter += 1
                                #     continue
                                if lane_hash not in global_ways:

                                    # 生成新lane_id
                                    new_lane_id = generate_unique_lane_id(existing_lane_ids)
                                    global_mapping[str(table_idx_counter)] = new_lane_id

                                    # 构建车道数据
                                    way_data = {
                                        "lane_id": new_lane_id,
                                        "lane_type": lane.get("type", "driving"),
                                        "width": lane.get("width", "3.5"),
                                        "geometry": road_nodes.copy(),
                                        "tags": {
                                            "predecessor": [],
                                            "successor": [],
                                            "l_neighbor_id": "None",
                                            "r_neighbor_id": "None"
                                        }
                                    }

                                    # 处理邻居关系
                                    neighbors = lane.find("neighbors")
                                    if neighbors is not None:
                                        way_data["tags"]["l_neighbor_id"] = neighbors.get("left", "None")
                                        way_data["tags"]["r_neighbor_id"] = neighbors.get("right", "None")

                                    # 添加到全局数据
                                    global_ways[lane_hash] = way_data
                                    table_idx_counter += 1

                except Exception as e:
                    print_red(f"Error processing {xodr_path}: {e}")

    # 第二阶段：保存合并结果
    if global_nodes and global_ways:
        # 转换节点数据结构
        final_nodes = list(global_nodes.values())

        # 生成最终向量地图文件
        vector_map_file = os.path.join(output_folder, "pruned_argoverse_MIA_10316_vector_map.xml")
        save_vector_map_to_xml(
            nodes=final_nodes,
            ways=list(global_ways.values()),
            output_file=vector_map_file
        )

        # 保存映射文件
        json_file = os.path.join(output_folder, "MIA_10316_tableidx_to_laneid_map.json")
        with open(json_file, 'w') as f:
            json.dump(global_mapping, f, indent=4)
        print(f"Saved combined mapping to {json_file}")

    else:
        print_red("No valid data found in input files")


if __name__ == "__main__":
    # input_folder = "input_mia"
    input_folder = "E:\\RLearning\\22.Onsite-3\\第一赛道_A卷"
    # input_folder = "E:\\RLearning\\22.Onsite-3\\第一赛道_B卷\\replay"
    output_folder = "output_mia"

    # 设置随机种子保证lane_id生成可复现
    random.seed(42)

    # 执行合并转换
    batch_convert_xodr_to_vector_map_and_json(input_folder, output_folder)



