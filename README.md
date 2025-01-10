# LightFS - 轻量级文件系统

LightFS是一个基于Python实现的轻量级文件系统，它将所有数据存储在单个文件中，支持基本的文件操作功能。

## 特性

- 单文件存储：所有数据存储在`light.fs`文件中
- 固定大小：总大小256MB（56MB系统信息 + 200MB数据存储）
- 单个存储单元：1MB
- 最大文件大小：16MB
- 最大文件名长度：255字节

## 系统要求

- Python 3.6+

## 使用方法

1. 运行命令行界面：
```bash
python cli.py
```

2. 可用命令：
- `create <filename>` - 创建新文件
- `rename <old_name> <new_name>` - 重命名文件
- `delete <filename>` - 删除文件
- `list` - 列出所有文件
- `cat <filename>` - 显示文件内容
- `write <filename> <content>` - 写入文本到文件
- `import <external_path> <internal_name>` - 导入外部文件
- `export <internal_name> <external_path>` - 导出文件到外部
- `info` - 显示存储统计信息
- `exit` - 退出系统

## 示例

```bash
# 创建新文件
lightfs> create test.txt

# 写入内容
lightfs> write test.txt Hello, World!

# 查看文件内容
lightfs> cat test.txt

# 查看存储信息
lightfs> info
```

## 注意事项

1. 文件系统会在首次运行时自动初始化
2. 所有文件操作都会直接影响`light.fs`文件
3. 请不要手动修改`light.fs`文件，以免造成数据损坏 