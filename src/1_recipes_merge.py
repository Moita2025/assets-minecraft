import os
import json

input_directory = ""
output_json_file = "recipes_original.json"

def process_json_files(input_dir, output_file):
    results = []

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 获取 originalName
                    original_name = None

                    if isinstance(data, dict):
                        result = data.get("result", {})
                        if isinstance(result, dict):
                            original_name = result.get("id")

                    # 如果没有 result.id，用文件名（去掉后缀）
                    if not original_name:
                        original_name = os.path.splitext(file)[0]

                    # 添加字段
                    from collections import OrderedDict
                    # 构造有序字典：originalName 放第一，其余保持原顺序
                    new_data = OrderedDict()
                    new_data["originalName"] = original_name
                    for k, v in data.items():
                        new_data[k] = v

                    results.append(new_data)

                except Exception as e:
                    print(f"处理文件失败: {file_path}, 错误: {e}")

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"处理完成，共 {len(results)} 个文件，输出至: {output_file}")


if __name__ == "__main__":

    process_json_files(input_directory, output_json_file)