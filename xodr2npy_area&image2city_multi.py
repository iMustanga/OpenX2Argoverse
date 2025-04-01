import os
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def print_red(text):
    """
    使用 ANSI 转义序列将文本以红色显示。
    """
    print(f"\033[91m{text}\033[0m")  # 91 是红色代码，0m 重置颜色

def calculate_map_bounds(xodr_file):
    """
    计算地图的边界（最小 x, 最大 x, 最小 y, 最大 y），包括车道偏移量和长度的影响。
    """
    min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')

    try:
        tree = ET.parse(xodr_file)
        root = tree.getroot()

        for road in root.findall(".//road"):
            for geometry in road.findall(".//geometry"):
                x_start = float(geometry.get("x"))
                y_start = float(geometry.get("y"))
                hdg = float(geometry.get("hdg", 0))
                length = float(geometry.get("length", 0))

                x_end = x_start + length * np.cos(hdg)
                y_end = y_start + length * np.sin(hdg)

                min_x = min(min_x, x_start, x_end)
                max_x = max(max_x, x_start, x_end)
                min_y = min(min_y, y_start, y_end)
                max_y = max(max_y, y_start, y_end)

            for lane_section in road.findall(".//laneSection"):
                for lane in lane_section.findall(".//lane"):
                    lane_offset = 0
                    lane_width = 0

                    lane_offset_element = lane_section.find(".//laneOffset")
                    if lane_offset_element is not None:
                        lane_offset = float(lane_offset_element.get("a", 0))

                    width_element = lane.find(".//width")
                    if width_element is not None:
                        lane_width = float(width_element.get("a", 0))

                    total_width = abs(lane_offset) + abs(lane_width)
                    min_x -= total_width
                    max_x += total_width
                    min_y -= total_width
                    max_y += total_width

        if min_x == float('inf') or max_x == float('-inf') or min_y == float('inf') or max_y == float('-inf'):
            print_red(f"No valid map bounds found in {xodr_file}. Setting default bounds.")
            return 0, 1, 0, 1

        print(f"Bounds: min_x={min_x}, max_x={max_x}, min_y={min_y}, max_y={max_y}")
        return min_x, max_x, min_y, max_y

    except Exception as e:
        print_red(f"Error processing {xodr_file}: {e}")
        return 0, 1, 0, 1


def calculate_transform_matrix(min_x, min_y):
    """
    计算从地图坐标到栅格坐标的变换矩阵
    :param min_x: 地图最小 x 值
    :param min_y: 地图最小 y 值
    :return: 3x3 变换矩阵
    """
    # 直接根据平移量设置变换矩阵
    transform_matrix = np.array([
        [1, 0, -min_x],  # X 方向单位缩放和平移
        [0, 1, -min_y],  # Y 方向单位缩放和平移
        [0, 0, 1]        # 齐次坐标行
    ])
    return transform_matrix



def parse_xodr_to_driveable_area(xodr_file, grid_size=None, resolution=0.5):
    """
    解析 .xodr 文件并生成可行驶区域矩阵，同时生成地图到栅格的变换矩阵
    """
    try:
        # 计算地图边界
        min_x, max_x, min_y, max_y = calculate_map_bounds(xodr_file)
        width = max_x - min_x
        height = max_y - min_y

        grid_width = int(width / resolution)
        grid_height = int(height / resolution)
        grid_size = (grid_height, grid_width)

        # 初始化可行驶区域矩阵
        driveable_area = np.zeros(grid_size, dtype=int)

        tree = ET.parse(xodr_file)
        root = tree.getroot()

        offset_x = -min_x
        offset_y = -min_y

        for road in root.findall(".//road"):
            for geometry in road.findall(".//geometry"):
                x_start = float(geometry.get("x")) + offset_x
                y_start = float(geometry.get("y")) + offset_y
                hdg = float(geometry.get("hdg", 0))
                length = float(geometry.get("length", 0))

                for lane_section in road.findall(".//laneSection"):
                    for lane in lane_section.findall(".//lane"):
                        width_element = lane.find(".//width")
                        lane_width = float(width_element.get("a", 0)) if width_element is not None else 0

                        if lane_width == 0 or lane.get("type") != "driving":
                            continue

                        for i in range(int(length / resolution)):
                            x = x_start + i * resolution * np.cos(hdg)
                            y = y_start + i * resolution * np.sin(hdg)

                            for w in np.arange(-lane_width, lane_width + resolution, resolution):
                                grid_x = int((x + w * np.sin(hdg)) / resolution)
                                grid_y = int((y - w * np.cos(hdg)) / resolution)

                                if 0 <= grid_x < grid_size[1] and 0 <= grid_y < grid_size[0]:
                                    driveable_area[grid_y, grid_x] = 1

        # 生成变换矩阵
        transform_matrix = calculate_transform_matrix(min_x, min_y)
        return driveable_area, transform_matrix

    except Exception as e:
        print_red(f"Error processing {xodr_file}: {e}")
        return None, None


def save_driveable_area_to_npy(driveable_area, output_file):
    """
    保存可行驶区域矩阵为 .npy 文件
    """
    np.save(output_file, driveable_area)
    print(f"Saved driveable area to {output_file}")


def save_transform_matrix_to_npy(transform_matrix, output_file):
    """
    保存变换矩阵为 .npy 文件
    """
    np.save(output_file, transform_matrix)
    print(f"Saved transform matrix to {output_file}")


def batch_convert_xodr_to_driveable_area(input_folder, output_folder, resolution=0.5):
    """
    批量转换.xodr文件并合并到单一输出文件
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 第一阶段：收集所有文件路径并计算全局边界
    xodr_paths = []
    global_min_x = float('inf')
    global_max_x = float('-inf')
    global_min_y = float('inf')
    global_max_y = float('-inf')

    # 递归遍历所有子目录
    for root_dir, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.xodr'):
                full_path = os.path.join(root_dir, file)
                xodr_paths.append(full_path)

                # 计算单个文件边界
                min_x, max_x, min_y, max_y = calculate_map_bounds(full_path)
                global_min_x = min(global_min_x, min_x)
                global_max_x = max(global_max_x, max_x)
                global_min_y = min(global_min_y, min_y)
                global_max_y = max(global_max_y, max_y)

    # 计算全局栅格尺寸
    global_width = global_max_x - global_min_x
    global_height = global_max_y - global_min_y
    grid_cols = int(np.ceil(global_width / resolution)) + 1  # 列数对应x方向
    grid_rows = int(np.ceil(global_height / resolution)) + 1  # 行数对应y方向
    global_driveable = np.zeros((grid_rows, grid_cols), dtype=np.uint8)

    # 第二阶段：处理每个文件并合并到全局矩阵
    for path in xodr_paths:
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            for road in root.findall(".//road"):
                for geometry in road.findall(".//geometry"):
                    # 原始坐标转换到全局偏移坐标系
                    x_start = float(geometry.get("x")) - global_min_x
                    y_start = float(geometry.get("y")) - global_min_y
                    hdg = float(geometry.get("hdg", 0))
                    length = float(geometry.get("length", 0))

                    # 车道处理
                    for lane_section in road.findall(".//laneSection"):
                        for lane in lane_section.findall(".//lane"):
                            if lane.get("type") != "driving":
                                continue

                            # 车道宽度处理
                            width_element = lane.find(".//width")
                            if width_element is None:
                                continue
                            lane_width = float(width_element.get("a", 0))

                            # 生成离散化点集
                            steps = int(length / resolution)
                            for step in range(steps + 1):
                                # 计算中心线坐标
                                dx = step * resolution * np.cos(hdg)
                                dy = step * resolution * np.sin(hdg)
                                x_center = x_start + dx
                                y_center = y_start + dy

                                # 横向偏移采样
                                offsets = np.arange(-lane_width, lane_width + resolution, resolution)
                                for offset in offsets:
                                    # 计算全局栅格坐标
                                    x = x_center + offset * np.sin(hdg)
                                    y = y_center - offset * np.cos(hdg)

                                    col = int(x / resolution)
                                    row = int(y / resolution)

                                    # 边界检查
                                    if 0 <= row < grid_rows and 0 <= col < grid_cols:
                                        global_driveable[row, col] = 1

        except Exception as e:
            print_red(f"Error processing {path}: {e}")

    # 生成全局变换矩阵
    global_transform = np.array([
        [1, 0, -global_min_x],
        [0, 1, -global_min_y],
        [0, 0, 1]
    ])

    # 保存结果
    np.save(os.path.join(output_folder, "MIA_10316_driveable_area_mat_2019_05_28.npy"), global_driveable)
    np.save(os.path.join(output_folder, "MIA_10316_npyimage_to_city_se2_2019_05_28.npy"), global_transform)
    print(f"Merged {len(xodr_paths)} maps into combined files")


if __name__ == "__main__":
    # input_folder = "input_mia"  # 替换为实际输入文件夹路径
    input_folder = "E:\\RLearning\\22.Onsite-3\\第一赛道_A卷"
    output_folder = "output_mia"  # 替换为实际输出文件夹路径
    resolution = 0.5  # 每个像素对应 0.5 米
    batch_convert_xodr_to_driveable_area(input_folder, output_folder, resolution)
