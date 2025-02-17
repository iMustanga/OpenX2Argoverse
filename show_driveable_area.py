import numpy as np
import matplotlib.pyplot as plt

def visualize_driveable_area(npy_file_path):
    """
    读取并可视化 Argoverse 可行驶区域文件 (.npy)
    """
    # 读取 .npy 文件
    driveable_area = np.load(npy_file_path)
    print(f"Driveable area shape: {driveable_area.shape}")

    # 可视化
    plt.figure(figsize=(10, 10))
    plt.imshow(driveable_area, cmap='gray', origin='lower')
    plt.title("Driveable Area")
    plt.xlabel("X-axis (Map Coordinate)")
    plt.ylabel("Y-axis (Map Coordinate)")
    plt.colorbar(label="Driveability")
    plt.show()
# 示例路径
# npy_file_path = "E:\Download\Chorme\map_files\MIA_10316_driveable_area_mat_2019_05_28.npy"
# npy_file_path = 'E:\\RLearning\\21.HiVT\\output\\4_57_straight_in_opposite_left_58_driveable_area.npy'
npy_file_path = "E:\\RLearning\\21.HiVT\\test_mia_9\\map\\MIA_10316_driveable_area_mat_2019_05_28.npy"
# npy_file_path = "E:\\RLearning\\21.HiVT\\output_test\\intersection_12_61_5.npy"
visualize_driveable_area(npy_file_path)
