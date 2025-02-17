import xml.etree.ElementTree as ET
import json
import sys
import os

def parse_xodr_map(file_path):
    """
    从 OpenDRIVE 文件提取道路地图信息。
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    map_data = {"lanes": {}, "lane_connections": {}}

    for road in root.findall("road"):
        road_id = road.get("id")

        # 提取参考线
        reference_line = []
        for geometry in road.findall("planView/geometry"):
            x = float(geometry.get("x"))
            y = float(geometry.get("y"))
            reference_line.append({"x": x, "y": y})

        # 假设每个 road 为单条车道，添加车道
        lane_id = f"lane_{road_id}"
        map_data["lanes"][lane_id] = {
            "center_line": reference_line,
            "left_boundary": [{"x": p["x"] - 1.75, "y": p["y"]} for p in reference_line],
            "right_boundary": [{"x": p["x"] + 1.75, "y": p["y"]} for p in reference_line]
        }

        # 车道拓扑（基于 OpenDRIVE 的前驱和后继）
        for connection in road.findall("link"):
            predecessor = connection.find("predecessor")
            successor = connection.find("successor")
            if predecessor is not None or successor is not None:
                map_data["lane_connections"][lane_id] = {
                    "predecessors": [f"lane_{predecessor.get('id')}"] if predecessor else [],
                    "successors": [f"lane_{successor.get('id')}"] if successor else []
                }
    return map_data


def parse_xosc_scenario(file_path):
    """
    从 OpenSCENARIO 文件提取场景动态信息。
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    dynamic_data = {"trajectories": []}

    for entity in root.findall(".//Entities/ScenarioObject"):
        agent_id = entity.get("name")

        # 初始状态
        init_state = entity.find(".//Init/Actions/PrivateAction/Position/WorldPosition")
        if init_state is not None:
            x = float(init_state.get("x"))
            y = float(init_state.get("y"))
            heading = float(init_state.get("h"))
            dynamic_data["trajectories"].append({
                "agent_id": agent_id,
                "initial_state": {"x": x, "y": y, "heading": heading},
                "trajectory": []
            })

        # 时间步轨迹（可解析动作或事件生成轨迹）
        trajectory = []
        for step in entity.findall(".//Route/Waypoint"):
            px = float(step.get("x"))
            py = float(step.get("y"))
            trajectory.append({"x": px, "y": py})

        if trajectory:
            dynamic_data["trajectories"][-1]["trajectory"] = trajectory
    return dynamic_data

def merge_to_argoverse_format(map_data, dynamic_data, output_path):
    """
    合并地图和动态数据为 Argoverse 格式。
    """
    argoverse_data = {
        "lanes": map_data["lanes"],
        "lane_connections": map_data["lane_connections"],
        "agent_trajectories": {}
    }

    for agent in dynamic_data["trajectories"]:
        agent_id = agent["agent_id"]
        argoverse_data["agent_trajectories"][agent_id] = {
            "initial_state": agent["initial_state"],
            "trajectory": agent["trajectory"]
        }

    with open(output_path, "w") as f:
        json.dump(argoverse_data, f, indent=2)
    print(f"Argoverse data saved to: {output_path}")


if __name__ == "__main__":

    # if len(sys.argv) != 4:
    #     print("Usage: python convert_xodr_xosc_to_argoverse.py <input_xodr> <input_xosc> <output_json>")
    #     sys.exit(1)

    xodr_file = '8_5_3_503.xodr'  # sys.argv[1]
    xosc_file = '8_5_3_503.xosc'  # sys.argv[2]
    output_json = '8_5_3_503.json'  # sys.argv[3]

    if not os.path.exists(xodr_file):
        print(f"Error: File {xodr_file} does not exist.")
        sys.exit(1)
    if not os.path.exists(xosc_file):
        print(f"Error: File {xosc_file} does not exist.")
        sys.exit(1)

    print("Parsing OpenDRIVE file...")
    map_data = parse_xodr_map(xodr_file)

    print("Parsing OpenSCENARIO file...")
    dynamic_data = parse_xosc_scenario(xosc_file)

    print("Merging data and generating Argoverse format...")
    merge_to_argoverse_format(map_data, dynamic_data, output_json)
    print("Conversion completed!")