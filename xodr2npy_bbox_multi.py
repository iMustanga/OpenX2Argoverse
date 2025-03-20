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
    批量转换.xodr文件并合并到单一输出文件
    :param input_folder: 输入文件夹路径，包含子文件夹和.xodr文件
    :param output_folder: 输出文件夹路径，保存合并后的.npy文件
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    all_bboxes = []  # 存储所有边界框数据

    # 递归遍历所有子目录
    for root_dir, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.xodr'):
                xodr_path = os.path.join(root_dir, file)
                print(f"Processing {xodr_path}")

                # 转换单个文件
                bbox_table = xodr_to_bbox_table(xodr_path)

                if bbox_table is not None and len(bbox_table) > 0:
                    # 追加数据到总列表
                    all_bboxes.append(bbox_table)

    if len(all_bboxes) > 0:
        # 合并所有边界框数据
        combined_bboxes = np.vstack(all_bboxes)

        # 生成输出路径
        output_file = os.path.join(output_folder, "MIA_10316_halluc_bbox_table.npy")

        # 保存合并后的数据
        np.save(output_file, combined_bboxes)
        print(f"Successfully merged {len(all_bboxes)} files into {output_file}")
    else:
        print_red("No valid bounding box data found in input files")


if __name__ == "__main__":
    input_folder = "input_mia"  # 替换为实际输入文件夹路径
    output_folder = "output_mia"  # 替换为实际输出文件夹路径

    # 批量转换并合并文件
    batch_convert_xodr_to_bbox_table(input_folder, output_folder)

    # 可视化合并结果
    # npy_file = os.path.join(output_folder, "combined_halluc_bbox_table.npy")
    # load_and_visualize_bbox_table(npy_file)
