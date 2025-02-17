import numpy as np
import matplotlib.pyplot as plt

def load_and_visualize_se2_mapping(npy_file):
    """
    加载并可视化 SE2 映射数据
    :param npy_file: 输入 .npy 文件路径
    """
    try:
        # 加载 .npy 文件
        data = np.load(npy_file, allow_pickle=True)

        # 打印数据结构和内容
        print("Data type:", type(data))
        print("Data shape:", data.shape)
        print("Sample data:")
        print(data)

        # 可视化解析内容
        if isinstance(data, np.ndarray):
            if data.ndim == 2 and data.shape[1] == 3:  # 假设为 [R | t] 矩阵
                print("SE2 transformation matrices detected.")

                # 假设每行是一个变换矩阵，将其绘制为箭头表示变换效果
                plt.figure(figsize=(10, 10))
                for row in data:
                    x, y, theta = row  # 解析二维坐标和旋转
                    dx = np.cos(theta)  # 方向向量
                    dy = np.sin(theta)

                    plt.arrow(
                        x, y, dx, dy,
                        head_width=0.5, head_length=1.0,
                        fc='blue', ec='blue', label=f"Rotation: {theta:.2f} rad"
                    )

                plt.xlabel("X (city coordinates)")
                plt.ylabel("Y (city coordinates)")
                plt.title("SE2 Mapping Visualization")
                plt.axis("equal")
                plt.legend()
                plt.grid()
                plt.show()

            elif data.ndim == 1:  # 单独存储一个矩阵
                print("Single SE2 matrix detected.")
                print(data)
            else:
                print("Unknown data format. Please check the data structure.")

    except Exception as e:
        print(f"Error loading or visualizing {npy_file}: {e}")


if __name__ == "__main__":
    # 替换为实际文件路径
    # npy_file = "E:\Download\Chorme\map_files\MIA_10316_npyimage_to_city_se2_2019_05_28.npy"
    npy_file = "E:\\RLearning\\21.HiVT\\output\\4_57_straight_in_opposite_left_58_npyimage_to_city_se2.npy"

    # 加载并可视化
    load_and_visualize_se2_mapping(npy_file)
