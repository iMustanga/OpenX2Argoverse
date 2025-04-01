import os
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def print_red(text):
    """
    使用 ANSI 转义序列将文本以红色显示。
    """
    print(f"\033[91m{text}\033[0m")  # 91 是红色代码，0m 重置颜色

def visualize_ground_height(npy_file):
    """
    可视化地面高度矩阵
    :param npy_file: 输入 .npy 文件路径
    """
    try:
        ground_height = np.load(npy_file)
        plt.figure(figsize=(10, 10))
        plt.imshow(ground_height, cmap='terrain', origin='lower')
        plt.colorbar(label="Height (m)")
        plt.title("Ground Height Map")
        plt.xlabel("X-axis (Map Coordinate)")
        plt.ylabel("Y-axis (Map Coordinate)")
        plt.show()
    except Exception as e:
        print_red(f"Error visualizing {npy_file}: {e}")


def calculate_map_bounds(xodr_file):
    """
    计算地图的边界（最小 x, 最大 x, 最小 y, 最大 y）
    :param xodr_file: 输入 .xodr 文件路径
    :return: (min_x, max_x, min_y, max_y)
    """
    min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')

    try:
        tree = ET.parse(xodr_file)
        root = tree.getroot()

        for road in root.findall(".//road"):
            for geometry in road.findall(".//geometry"):
                x_start = float(geometry.get("x"))
                y_start = float(geometry.get("y"))
                length = float(geometry.get("length", 0))
                hdg = float(geometry.get("hdg", 0))

                x_end = x_start + length * np.cos(hdg)
                y_end = y_start + length * np.sin(hdg)

                min_x = min(min_x, x_start, x_end)
                max_x = max(max_x, x_start, x_end)
                min_y = min(min_y, y_start, y_end)
                max_y = max(max_y, y_start, y_end)

        return min_x, max_x, min_y, max_y

    except Exception as e:
        print_red(f"Error calculating bounds for {xodr_file}: {e}")
        return None


def xodr_to_ground_height(xodr_file, resolution=0.5):
    """
    将 .xodr 文件转换为地面高度矩阵 (.npy 格式)
    :param xodr_file: 输入 .xodr 文件路径
    :param resolution: 每个像素对应的实际距离 (单位: 米)
    :return: 地面高度矩阵
    """
    try:
        bounds = calculate_map_bounds(xodr_file)
        if bounds is None:
            return None

        min_x, max_x, min_y, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y

        grid_width = int(width / resolution)
        grid_height = int(height / resolution)

        ground_height = np.zeros((grid_height, grid_width), dtype=float)

        tree = ET.parse(xodr_file)
        root = tree.getroot()

        for road in root.findall(".//road"):
            for geometry in road.findall(".//geometry"):
                x_start = float(geometry.get("x"))
                y_start = float(geometry.get("y"))
                length = float(geometry.get("length", 0))
                hdg = float(geometry.get("hdg", 0))
                elevation = geometry.find(".//elevation")

                if elevation is not None:
                    for i in range(int(length / resolution)):
                        x = x_start + i * resolution * np.cos(hdg)
                        y = y_start + i * resolution * np.sin(hdg)
                        grid_x = int((x - min_x) / resolution)
                        grid_y = int((y - min_y) / resolution)

                        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                            height = float(elevation.get("a", 0))
                            ground_height[grid_y, grid_x] = height

        return ground_height

    except Exception as e:
        print_red(f"Error converting {xodr_file} to ground height: {e}")
        return None


def save_ground_height_to_npy(ground_height, output_file):
    """
    保存地面高度矩阵为 .npy 文件
    """
    np.save(output_file, ground_height)
    print(f"Saved ground height to {output_file}")


def batch_convert_xodr_to_ground_height(input_folder, output_folder, resolution=0.5):
    """
    批量转换.xodr文件并合并到单一高度矩阵
    :param input_folder: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    :param resolution: 空间分辨率 (米/像素)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 第一阶段：计算全局边界
    global_min_x = float('inf')
    global_max_x = float('-inf')
    global_min_y = float('inf')
    global_max_y = float('-inf')
    xodr_files = []

    # 递归扫描所有.xodr文件
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.xodr'):
                path = os.path.join(root, file)
                bounds = calculate_map_bounds(path)
                if bounds:
                    min_x, max_x, min_y, max_y = bounds
                    global_min_x = min(global_min_x, min_x)
                    global_max_x = max(global_max_x, max_x)
                    global_min_y = min(global_min_y, min_y)
                    global_max_y = max(global_max_y, max_y)
                    xodr_files.append(path)

    # 计算全局矩阵尺寸
    grid_cols = int(np.ceil((global_max_x - global_min_x) / resolution)) + 1
    grid_rows = int(np.ceil((global_max_y - global_min_y) / resolution)) + 1
    global_height = np.full((grid_rows, grid_cols), np.nan, dtype=np.float32)

    # 第二阶段：填充高度数据
    for path in xodr_files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            for road in root.findall(".//road"):
                for geometry in road.findall(".//geometry"):
                    x_start = float(geometry.get("x"))
                    y_start = float(geometry.get("y"))
                    length = float(geometry.get("length", 0))
                    hdg = float(geometry.get("hdg", 0))
                    elevation = geometry.find(".//elevation")

                    if elevation is None:
                        continue

                    # 沿道路方向采样
                    steps = int(length / resolution)
                    height_value = float(elevation.get("a", 0))

                    for step in range(steps + 1):
                        # 计算全局坐标
                        dx = step * resolution * np.cos(hdg)
                        dy = step * resolution * np.sin(hdg)
                        x = x_start + dx
                        y = y_start + dy

                        # 转换为矩阵索引
                        col = int((x - global_min_x) / resolution)
                        row = int((y - global_min_y) / resolution)

                        # 边界检查并更新高度值
                        if 0 <= row < grid_rows and 0 <= col < grid_cols:
                            # 保留最新测量的高度值
                            global_height[row, col] = height_value

        except Exception as e:
            print_red(f"Error processing {path}: {e}")

    # 处理未测量区域（填充nan值为0）
    global_height = np.nan_to_num(global_height, nan=0.0)

    # 保存合并结果
    output_path = os.path.join(output_folder, "MIA_10316_ground_height_mat_2019_05_28.npy")
    np.save(output_path, global_height)
    print(f"Saved merged height map ({grid_rows}x{grid_cols}) to {output_path}")

    # 返回结果路径供可视化
    return output_path


if __name__ == "__main__":
    output_file = batch_convert_xodr_to_ground_height(
        # input_folder="input_mia",
        input_folder="E:\\RLearning\\22.Onsite-3\\第一赛道_A卷",
        output_folder="output_mia",
        resolution=0.5
    )

    # # 可视化合并结果
    # if output_file:
    #     visualize_ground_height(output_file)
