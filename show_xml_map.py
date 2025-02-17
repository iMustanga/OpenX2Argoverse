import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def parse_argoverse_map(xml_file):
    """
    解析 XML 格式的 Argoverse1 地图文件
    :param xml_file: XML 地图文件路径
    :return: 道路中心线、车道边界点
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        road_centers = []  # 道路中心线
        lane_boundaries = []  # 车道边界点

        # 解析道路中心线
        for road in root.findall(".//road"):
            for geometry in road.findall(".//geometry"):
                x = float(geometry.get("x", 0))
                y = float(geometry.get("y", 0))
                road_centers.append((x, y))

        # 解析车道边界
        for lane_section in root.findall(".//laneSection"):
            for lane in lane_section.findall(".//lane"):
                boundary_points = []
                for width in lane.findall(".//width"):
                    x = float(width.get("sOffset", 0))
                    y = float(width.get("a", 0))
                    boundary_points.append((x, y))
                lane_boundaries.append(boundary_points)

        return road_centers, lane_boundaries

    except Exception as e:
        print(f"Error parsing XML map file: {e}")
        return [], []


def visualize_map(road_centers, lane_boundaries):
    """
    可视化地图
    :param road_centers: 道路中心线
    :param lane_boundaries: 车道边界点
    """
    plt.figure(figsize=(12, 8))
    plt.title("Argoverse Map Visualization")
    plt.xlabel("X (meters)")
    plt.ylabel("Y (meters)")

    # 绘制道路中心线
    if road_centers:
        x, y = zip(*road_centers)
        plt.plot(x, y, label="Road Centers", color="blue")

    # 绘制车道边界
    for boundary in lane_boundaries:
        if boundary:
            x, y = zip(*boundary)
            plt.plot(x, y, label="Lane Boundary", linestyle="--", color="red")

    plt.legend()
    plt.axis("equal")
    plt.grid()
    plt.show()


if __name__ == "__main__":
    # 输入 XML 文件路径
    # xml_file = "E:\Download\Chorme\map_files\pruned_argoverse_PIT_10314_vector_map.xml"  # 替换为实际的 XML 地图文件路径
    # xml_file = "E:\\RLearning\\21.HiVT\\input\\7_253_merge_271\\7_253_merge_271.xodr"

    # 解析地图
    road_centers, lane_boundaries = parse_argoverse_map(xml_file)

    # 可视化地图
    visualize_map(road_centers, lane_boundaries)
