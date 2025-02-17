import os
import json
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def visualize_json_mapping(json_file):
    """
    可视化 JSON 文件中 tableidx 与 laneid 的映射关系。
    :param json_file: JSON 文件路径。
    """
    with open(json_file, 'r') as f:
        mapping = json.load(f)

    # 绘制映射关系图
    plt.figure(figsize=(10, 6))
    keys = list(mapping.keys())
    values = list(mapping.values())

    plt.scatter(keys, values, c='blue', label='Lane Mapping')
    plt.title('TableIdx to LaneId Mapping')
    plt.xlabel('TableIdx')
    plt.ylabel('LaneId')
    plt.grid(True)
    plt.legend()
    plt.show()


def xodr_to_json_mapping(xodr_file, output_file):
    """
    将 xodr 文件转换为 JSON 格式的 tableidx 到 laneid 的映射。
    :param xodr_file: 输入 .xodr 文件路径。
    :param output_file: 输出 JSON 文件路径。
    """
    tree = ET.parse(xodr_file)
    root = tree.getroot()

    mapping = {}
    table_idx = 0

    # 遍历车道信息
    for road in root.findall(".//road"):
        for lane_section in road.findall(".//laneSection"):
            for lane in lane_section.findall(".//lane"):
                lane_id = lane.get("id")
                if lane_id:
                    mapping[str(table_idx)] = lane_id
                    table_idx += 1

    # 保存为 JSON 文件
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=4)
    print(f"Mapping saved to {output_file}")


def batch_convert_xodr_to_json(input_folder, output_folder):
    """
    批量转换 .xodr 文件为 JSON 格式的 tableidx 到 laneid 映射。
    :param input_folder: 输入文件夹路径，包含子文件夹和 .xodr 文件。
    :param output_folder: 输出文件夹路径，保存 JSON 文件。
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, dirs, files in os.walk(input_folder):
        for dir_name in dirs:
            subfolder_path = os.path.join(root, dir_name)
            xodr_files = [f for f in os.listdir(subfolder_path) if f.endswith('.xodr')]

            for xodr_file in xodr_files:
                xodr_path = os.path.join(subfolder_path, xodr_file)
                print(f"Processing {xodr_path}")

                output_file = os.path.join(output_folder, f"{dir_name}_tableidx_to_laneid_map.json")
                xodr_to_json_mapping(xodr_path, output_file)


if __name__ == "__main__":
    # 输入和输出目录
    input_folder = "input_test"  # 替换为实际输入文件夹路径
    output_folder = "output_test"  # 替换为实际输出文件夹路径

    # 批量转换
    # batch_convert_xodr_to_json(input_folder, output_folder)

    # 可视化示例
    # sample_json = os.path.join(output_folder, "sample_tableidx_to_laneid_map.json")
    sample_json = "E:\Download\Chorme\map_files\MIA_10316_tableidx_to_laneid_map.json"
    if os.path.exists(sample_json):
        visualize_json_mapping(sample_json)
