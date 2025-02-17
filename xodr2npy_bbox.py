import os
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def print_red(text):
    """
    使用 ANSI 转义序列将文本以红色显示。
    """
    print(f"\033[91m{text}\033[0m")  # 91 是红色代码，0m 重置颜色

def load_and_visualize_bbox_table(npy_file):
    """
    加载并可视化边界框数据
    :param npy_file: 输入 .npy 文件路径
    """
    try:

        bbox_data = np.load(npy_file, allow_pickle=True)

        if isinstance(bbox_data, np.ndarray) and bbox_data.ndim == 2:
            print("Bounding Box Data:")
            print(bbox_data)

            # 获取字段数
            num_fields = bbox_data.shape[1]
            print(f"Number of fields per entry: {num_fields}")

            plt.figure(figsize=(10, 10))
            for bbox in bbox_data:
                x_center, y_center = bbox[0], bbox[1]
                width = bbox[2] if num_fields > 2 else 1.0  # 默认宽度
                height = bbox[3] if num_fields > 3 else 1.0  # 默认高度
                angle = bbox[4] if num_fields > 4 else 0.0   # 默认角度
                label = bbox[5] if num_fields > 5 else "unknown"  # 默认标签

                # 绘制边界框
                rect = plt.Rectangle(
                    (x_center - width / 2, y_center - height / 2),  # 左下角
                    width,
                    height,
                    angle=angle,
                    edgecolor="red",
                    facecolor="none",
                    label=f"Label: {label}" if num_fields > 5 else None,
                )
                plt.gca().add_patch(rect)

            plt.title("Bounding Box Visualization")
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.axis("equal")
            plt.legend()
            plt.show()

        else:
            print_red("Unexpected format in .npy file.")

    except Exception as e:
        print_red(f"Error visualizing {npy_file}: {e}")



def xodr_to_bbox_table(xodr_file):
    """
    将 .xodr 文件转换为边界框角点数据
    :param xodr_file: 输入 .xodr 文件路径
    :return: 边界框角点数据
    """
    try:
        tree = ET.parse(xodr_file)
        root = tree.getroot()

        bbox_table = []

        # 提取道路几何信息
        for road in root.findall(".//road"):
            road_id = road.get("id", "unknown")
            for geometry in road.findall(".//geometry"):
                x_start = float(geometry.get("x", 0))
                y_start = float(geometry.get("y", 0))
                length = float(geometry.get("length", 0))
                hdg = float(geometry.get("hdg", 0))

                # 计算角点
                x_end = x_start + length * np.cos(hdg)
                y_end = y_start + length * np.sin(hdg)
                width = 3.5  # 假设车道宽度

                # 左下角和右上角
                x_min = x_start - width / 2
                y_min = y_start - width / 2
                x_max = x_end + width / 2
                y_max = y_end + width / 2

                bbox_table.append([x_min, y_min, x_max, y_max])

        return np.array(bbox_table, dtype=float)

    except Exception as e:
        print_red(f"Error converting {xodr_file}: {e}")
        return None


def save_bbox_table_to_npy(bbox_table, output_file):
    """
    保存边界框角点数据为 .npy 文件
    :param bbox_table: 边界框角点数据
    :param output_file: 输出 .npy 文件路径
    """
    try:
        np.save(output_file, bbox_table)
        print(f"Saved bounding box table to {output_file}")
    except Exception as e:
        print_red(f"Error saving {output_file}: {e}")


def batch_convert_xodr_to_bbox_table(input_folder, output_folder):
    """
    批量转换 .xodr 文件为边界框角点数据 (.npy 格式)
    :param input_folder: 输入文件夹路径，包含子文件夹和 .xodr 文件
    :param output_folder: 输出文件夹路径，保存 .npy 文件
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

                bbox_table = xodr_to_bbox_table(xodr_path)
                if bbox_table is not None:
                    output_file = os.path.join(output_folder, f"{dir_name}_halluc_bbox_table.npy")
                    save_bbox_table_to_npy(bbox_table, output_file)

if __name__ == "__main__":
    input_folder = "input_mia"  # 替换为实际输入文件夹路径
    output_folder = "output_mia"  # 替换为实际输出文件夹路径

    # 可视化示例 .npy 文件
    # npy_file = "E:\Download\Chorme\map_files\MIA_10316_halluc_bbox_table.npy"
    # npy_file = "E:\\RLearning\\21.HiVT\\output\\8_5_1_377_halluc_bbox_table.npy"
    # load_and_visualize_bbox_table(npy_file)

    # 批量转换 .xodr 文件
    batch_convert_xodr_to_bbox_table(input_folder, output_folder)
