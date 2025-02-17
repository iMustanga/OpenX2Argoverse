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
    批量转换 .xodr 文件为地面高度矩阵 (.npy 格式)
    :param input_folder: 输入文件夹路径，包含子文件夹和 .xodr 文件
    :param output_folder: 输出文件夹路径，保存 .npy 文件
    :param resolution: 每个像素对应的实际距离 (单位: 米)
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

                ground_height = xodr_to_ground_height(xodr_path, resolution)
                if ground_height is not None:
                    output_file = os.path.join(output_folder, f"{dir_name}_ground_height_mat.npy")
                    save_ground_height_to_npy(ground_height, output_file)


if __name__ == "__main__":
    input_folder = "input_mia"  # 替换为实际输入文件夹路径
    output_folder = "output_mia"  # 替换为实际输出文件夹路径

    # 解析并可视化 .npy 文件
    # npy_file = "E:\Download\Chorme\map_files\MIA_10316_ground_height_mat_2019_05_28.npy"  # 替换为实际 .npy 文件路径
    # npy_file = "E:\\RLearning\\21.HiVT\\output\\mixed_952_32_0_height.npy"
    # visualize_ground_height(npy_file)

    # 批量转换 .xodr 文件
    resolution = 0.5
    batch_convert_xodr_to_ground_height(input_folder, output_folder, resolution)
