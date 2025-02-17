import os
import re
import xml.etree.ElementTree as ET
import csv

def print_red(text):
    """
    使用 ANSI 转义序列将文本以红色显示。
    """
    print(f"\033[91m{text}\033[0m")  # 91 是红色代码，0m 重置颜色

def format_track_id(track_id):
    """
    Format TRACK_ID to match the required format: 00000000-0000-0000-0000-00000000000000
    with 32 decimal digits.
    """
    track_id_str = str(track_id).zfill(32)
    return f"{track_id_str[:8]}-{track_id_str[8:12]}-{track_id_str[12:16]}-{track_id_str[16:20]}-{track_id_str[20:]}"

def check_file_size(file_path, expected_size):
    """
    检查文件大小是否与指定值匹配。
    :param file_path: 文件路径
    :param expected_size: 指定文件大小 (单位: 字节)
    :return: 如果文件大小匹配返回 True，否则返回 False
    """
    try:
        actual_size = os.path.getsize(file_path)
        return 0.98 * expected_size < actual_size < 1.02 * expected_size
    except Exception as e:
        print(f"Error checking file size for {file_path}: {e}")
        return False


def extract_ego_position_from_file(file_path):
    """
    Extract the x_init and y_init values for the Ego vehicle by parsing the file text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()

        for line in content:
            if "x_init" in line and "y_init" in line:
                match = re.search(r"x_init\s*=\s*(-?[\d\.]+),\s*y_init\s*=\s*(-?[\d\.]+)", line)
                if match:
                    x_init = float(match.group(1))
                    y_init = float(match.group(2))
                    return x_init, y_init

        raise ValueError("Ego position (x_init, y_init) not found in comments.")
    except Exception as e:
        print(f"Error while extracting ego position from {file_path}: {e}")
        return None, None

def parse_xosc_trajectory(file_path, city_name, use_obstacle_as_ego=False):
    """
    Parse .xosc file to extract trajectories of vehicles and their position data.
    :param use_obstacle_as_ego: Boolean flag to determine if an obstacle vehicle should be used as the Ego vehicle.
    """
    x_init, y_init = extract_ego_position_from_file(file_path)
    agent_num = 0
    city_name = "MIA"

    if x_init is None or y_init is None:
        print(f"Using default ego position for {file_path}: x_init=0.0, y_init=0.0")
        x_init, y_init = 0.0, 0.0

    tree = ET.parse(file_path)
    root = tree.getroot()

    trajectory_data = []
    all_timestamps = set()
    obstacle_candidates = {}  # Track obstacle vehicles

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
                # if object_type == "AGENT":
                #     agent_num += 1

                entry = {
                    "TIMESTAMP": time,
                    "TRACK_ID": formatted_track_id,
                    "OBJECT_TYPE": object_type,
                    "X": x,
                    "Y": y,
                    "CITY_NAME": city_name
                }

                trajectory_data.append(entry)

                # Collect potential obstacles
                if object_type == "AGENT":
                    if time < 3.0:
                        agent_num += 1
                    if formatted_track_id not in obstacle_candidates:
                        obstacle_candidates[formatted_track_id] = []
                    obstacle_candidates[formatted_track_id].append(entry)

    if use_obstacle_as_ego:
        # Find an obstacle that exists at all timestamps
        for track_id, entries in obstacle_candidates.items():
            timestamps = {entry["TIMESTAMP"] for entry in entries}
            if timestamps == all_timestamps:
                print(f"Using obstacle vehicle {track_id} as Ego vehicle.")
                for entry in trajectory_data:
                    if entry["TRACK_ID"] == track_id:
                        if entry["TIMESTAMP"] < 3.0:
                            agent_num -= 1
                        entry["OBJECT_TYPE"] = "AV"
                        entry["TRACK_ID"] = "00000000-0000-0000-0000-000000000000"
                break
        else:
            print("No suitable obstacle vehicle found. Falling back to fixed Ego position.")
            for time in all_timestamps:
                trajectory_data.append({
                    "TIMESTAMP": time,
                    "TRACK_ID": "00000000-0000-0000-0000-000000000000",
                    "OBJECT_TYPE": "AV",
                    "X": x_init,
                    "Y": y_init,
                    "CITY_NAME": city_name
                })

    else:
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
    return trajectory_data, agent_num

def save_to_csv(data, output_file):
    """
    Save the formatted data to a CSV file.
    """
    fieldnames = ["TIMESTAMP", "TRACK_ID", "OBJECT_TYPE", "X", "Y", "CITY_NAME"]
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def batch_process_xosc_files(input_dir, output_dir, use_obstacle_as_ego=False, sequential_filenames=False,
                             check_size=False, expected_size=0):
    """
    Batch process .xosc files in a directory structure with optional .xodr file size check.
    :param check_size: 是否检查 .xodr 文件大小
    :param expected_size: 指定的 .xodr 文件大小 (单位: 字节)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    counter = 1
    for folder_name in os.listdir(input_dir):
        folder_path = os.path.join(input_dir, folder_name)
        if os.path.isdir(folder_path):
            # 找到对应文件夹下的 .xodr 文件
            xodr_file = next((f for f in os.listdir(folder_path) if f.endswith('.xodr')), None)
            if xodr_file:
                xodr_path = os.path.join(folder_path, xodr_file)

                # 如果启用文件大小检查，跳过不符合大小的文件
                if check_size and not check_file_size(xodr_path, expected_size):
                    print(f"Skipping {xodr_path}: File size does not match {expected_size} bytes.")
                    continue

            # 找到对应文件夹下的 .xosc 文件
            xosc_file = next((f for f in os.listdir(folder_path) if f.endswith('.xosc')), None)
            if xosc_file:
                xosc_path = os.path.join(folder_path, xosc_file)

                if sequential_filenames:
                    csv_file_name = f"{counter}.csv"
                else:
                    csv_file_name = f"{folder_name}.csv"
                csv_path = os.path.join(output_dir, csv_file_name)

                try:
                    trajectory_data, agent_num = parse_xosc_trajectory(xosc_path, folder_name, use_obstacle_as_ego)
                    # print(agent_num, counter)
                    if agent_num == 0:
                        print_red(f"{xosc_path}: No agent in first 3s!")
                        continue
                    save_to_csv(trajectory_data, csv_path)
                    counter += 1
                except Exception as e:
                    print_red(f"Failed to process {xosc_path}: {e}")

if __name__ == "__main__":
    input_directory = "E:\\RLearning\\18.Onsite-2\\4.第一赛道B卷\\replay"  # "input_mia"  # Replace with your input directory
    output_directory = "output_mia"  # Replace with your output directory

    # 配置选项
    use_obstacle = True  # 是否使用障碍车作为自车
    sequential_filenames = True  # 是否使用顺序命名的文件名
    check_size = True  # 是否检查文件大小
    expected_size = 35 * 1024  # 指定文件大小，单位字节（例如：1024 字节）

    batch_process_xosc_files(input_directory, output_directory, use_obstacle_as_ego=use_obstacle,
                             sequential_filenames=sequential_filenames, check_size=check_size, expected_size=expected_size)
    print("Batch processing completed.")

