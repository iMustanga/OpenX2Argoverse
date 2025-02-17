import json
import matplotlib.pyplot as plt


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
        print(f"Error loading or visualizing {json_file}: {e}")


if __name__ == "__main__":
    # 替换为实际 JSON 文件路径
    # json_file = "E:\Download\Chorme\map_files\MIA_10316_tableidx_to_laneid_map.json"
    json_file = "E:\\RLearning\\21.HiVT\\output_test\\0_409_merge_420_tableidx_to_laneid_map.json"

    # 加载并可视化映射关系
    load_and_visualize_mapping(json_file)
