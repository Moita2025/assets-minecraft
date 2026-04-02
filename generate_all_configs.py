import os
import json
from pathlib import Path

def format_keys(keys, per_line=10, indent=6):
    lines = []
    for i in range(0, len(keys), per_line):
        chunk = keys[i:i+per_line]
        line = ', '.join(json.dumps(k, ensure_ascii=False) for k in chunk)
        lines.append(' ' * indent + line)
    return '[\n' + ',\n'.join(lines) + '\n' + ' ' * (indent - 2) + ']'

def main():
    # 当前脚本所在目录
    current_dir = Path(__file__).parent.resolve()
    
    # 用于存储最终结果：[{ "path": "相对路径", "keys": ["name1", "name2", ...] }]
    all_configs = []
    
    # 用于收集所有 chineseName，避免重复（可选，如果你不希望去重可以注释掉）
    seen_names = set()
    
    # 遍历当前目录及其所有子目录
    for root, dirs, files in os.walk(current_dir):
        if 'config.json' in files:
            config_path = Path(root) / 'config.json'
            
            # 计算相对于当前目录的路径
            relative_path = config_path.relative_to(current_dir).as_posix()
            seen_names = set()
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 假设 data 是数组
                if not isinstance(data, list):
                    print(f"警告: {relative_path} 不是一个 JSON 数组，已跳过")
                    continue
                
                chinese_names = []
                for item in data:
                    if isinstance(item, dict) and 'chineseName' in item:
                        name = item['chineseName']
                        if name not in seen_names:  # 可选：去重
                            chinese_names.append(name)
                            seen_names.add(name)
                    # 如果你希望即使重复也保留，可以直接 append，不检查 seen_names
                
                if chinese_names:  # 只有收集到名字才添加
                    all_configs.append({
                        "path": relative_path,
                        "keys": chinese_names
                    })
                
                print(f"已处理: {relative_path}，提取 {len(chinese_names)} 个 chineseName")
                
            except json.JSONDecodeError as e:
                print(f"错误: {relative_path} JSON 格式错误 - {e}")
            except Exception as e:
                print(f"错误: 无法读取 {relative_path} - {e}")
    
    # 生成 all_configs.json
    output_path = current_dir / 'all_configs.json'
    try:
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     json.dump(all_configs, f, ensure_ascii=False, indent=2)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('[\n')
            for idx, item in enumerate(all_configs):
                f.write('  {\n')
                f.write(f'    "path": {json.dumps(item["path"], ensure_ascii=False)},\n')
                
                formatted_keys = format_keys(item["keys"], per_line=10)
                f.write(f'    "keys": {formatted_keys}\n')
                
                f.write('  }')
                if idx != len(all_configs) - 1:
                    f.write(',')
                f.write('\n')
            f.write(']\n')

        print(f"\n成功生成 {output_path}，共包含 {len(all_configs)} 个 config.json 的信息")
    except Exception as e:
        print(f"错误: 无法写入 all_configs.json - {e}")

if __name__ == '__main__':
    main()