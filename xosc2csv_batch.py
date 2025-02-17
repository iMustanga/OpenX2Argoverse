import os
import re
import xml.etree.ElementTree as ET
import csv


def format_track_id(track_id):
    """
    Format TRACK_ID to match the required format: 00000000-0000-0000-0000-00000000000000
    with 32 decimal digits.
    """
    track_id_str = str(track_id).zfill(32)
    return f"{track_id_str[:8]}-{track_id_str[8:12]}-{track_id_str[12:16]}-{track_id_str[16:20]}-{track_id_str[20:]}"


def extract_ego_position_from_file(file_path):
    """
    Extract the x_init and y_init values for the Ego vehicle by parsing the file text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()

        for line in content:
            if "x_init" in line and "y_init" in line:
                # match = re.search(r"x_init\s*=\s*([\d\.]+),\s*y_init\s*=\s*([\d\.]+)", line)
                match = re.search(r"x_init\s*=\s*(-?[\d\.]+),\s*y_init\s*=\s*(-?[\d\.]+)", line)
                if match:
                    x_init = float(match.group(1))
                    y_init = float(match.group(2))
                    return x_init, y_init

        raise ValueError("Ego position (x_init, y_init) not found in comments.")
    except Exception as e:
        print(f"Error while extracting ego position from {file_path}: {e}")
        return None, None

def extract_ego_position_v2(file_path):
    """
    从 xosc 文件中提取自车的初始位置 (x_init, y_init)。
    如果未找到，返回默认值。
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # 查找 <Private entityRef="Ego"> 节点
        ego_section = root.find(".//Private[@entityRef='Ego']")
        if ego_section is not None:
            # 提取注释内容
            comments = [elem for elem in ego_section.iter() if elem.tag is ET.Comment]
            for comment in comments:
                match = re.search(r"x_init\s*=\s*([\d\.\-]+),\s*y_init\s*=\s*([\d\.\-]+)", comment.text)
                if match:
                    x_init = float(match.group(1))
                    y_init = float(match.group(2))
                    return x_init, y_init
        # 如果未找到注释
        raise ValueError("Ego position (x_init, y_init) not found in comments.")
    except Exception as e:
        print(f"Error while extracting ego position: {e}")
        # 返回默认值
        return 0.0, 0.0


def parse_xosc_trajectory(file_path, city_name):
    """
    Parse .xosc file to extract trajectories of vehicles and their position data.
    """
    x_init, y_init = extract_ego_position_from_file(file_path)
    # x_init, y_init = extract_ego_position_v2(file_path)

    city_name = 'MIA'

    if x_init is None or y_init is None:
        print(f"Using default ego position for {file_path}: x_init=0.0, y_init=0.0")
        x_init, y_init = 0.0, 0.0

    tree = ET.parse(file_path)
    root = tree.getroot()

    trajectory_data = []
    all_timestamps = set()

    for trajectory in root.findall(".//Trajectory"):
        trajectory_name = trajectory.get("name")

        for vertex in trajectory.findall(".//Vertex"):
            time = float(vertex.get("time"))
            position = vertex.find(".//Position/WorldPosition")

            if position is not None:
                x = float(position.get("x"))
                y = float(position.get("y"))

                all_timestamps.add(time)

                object_type = "AV" if "Ego" in trajectory_name else "AGENT"
                track_id = 0 if "Ego" in trajectory_name else abs(hash(trajectory_name))
                formatted_track_id = format_track_id(track_id)

                trajectory_data.append({
                    "TIMESTAMP": time,
                    "TRACK_ID": formatted_track_id,
                    "OBJECT_TYPE": object_type,
                    "X": x,
                    "Y": y,
                    "CITY_NAME": city_name
                })

    for time in all_timestamps:
        trajectory_data.append({
            "TIMESTAMP": time,
            "TRACK_ID": "00000000-0000-0000-0000-000000000000",
            "OBJECT_TYPE": "AV",
            "X": x_init,
            "Y": y_init,
            "CITY_NAME": city_name
        })

    trajectory_data.sort(key=lambda x: x["TIMESTAMP"])
    return trajectory_data


def save_to_csv(data, output_file):
    """
    Save the formatted data to a CSV file.
    """
    fieldnames = ["TIMESTAMP", "TRACK_ID", "OBJECT_TYPE", "X", "Y", "CITY_NAME"]
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def batch_process_xosc_files(input_dir, output_dir):
    """
    Batch process .xosc files in a directory structure.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for folder_name in os.listdir(input_dir):
        folder_path = os.path.join(input_dir, folder_name)
        if os.path.isdir(folder_path):
            xosc_file = next((f for f in os.listdir(folder_path) if f.endswith('.xosc')), None)
            if xosc_file:
                xosc_path = os.path.join(folder_path, xosc_file)
                csv_file_name = f"{folder_name}.csv"
                csv_path = os.path.join(output_dir, csv_file_name)

                # print(f"Processing {xosc_path} -> {csv_path}")
                try:
                    trajectory_data = parse_xosc_trajectory(xosc_path, folder_name)  # Pass folder_name as city_name
                    save_to_csv(trajectory_data, csv_path)
                    # print(f"Saved CSV: {csv_path}")
                except Exception as e:
                    print(f"Failed to process {xosc_path}: {e}")


if __name__ == "__main__":
    # Specify the input directory and output directory
    input_directory = "input_mia"  # Replace with your input directory
    output_directory = "output_mia"  # Replace with your output directory

    batch_process_xosc_files(input_directory, output_directory)
    print("Batch processing completed.")
