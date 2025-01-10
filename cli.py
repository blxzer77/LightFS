#!/usr/bin/env python3
import os
import sys
import cmd
from lightfs import LightFS

class LightFSShell(cmd.Cmd):
    intro = '欢迎使用LightFS文件系统。输入 help 或 ? 查看可用命令。\n'
    prompt = 'lightfs> '

    # 命令分类和说明
    command_descriptions = {
        'create': '创建新文件',
        'rename': '重命名文件',
        'delete': '删除文件',
        'list': '列出所有文件',
        'cat': '显示文件内容',
        'write': '写入文本到文件',
        'import': '从外部导入文件',
        'export': '导出文件到外部',
        'info': '显示存储统计信息',
        'exit': '退出系统',
        'help': '显示帮助信息'
    }

    def do_help(self, arg):
        """显示帮助信息"""
        if arg:
            # 如果指定了具体命令，显示该命令的详细帮助
            super().do_help(arg)
        else:
            # 显示所有命令的简要说明
            print("\n可用命令:")
            print("=" * 50)
            # 计算最长的命令名长度，用于对齐
            max_cmd_len = max(len(cmd) for cmd in self.command_descriptions.keys())
            # 格式化输出
            for cmd, desc in self.command_descriptions.items():
                print(f"{cmd:<{max_cmd_len + 2}} - {desc}")
            print("\n使用 'help <命令名>' 查看具体命令的详细用法")
            print("=" * 50)

    def __init__(self):
        super().__init__()
        self.fs = LightFS('light.fs')
        if not os.path.exists('light.fs'):
            print("正在初始化文件系统...")
            self.fs.initialize()

    def do_create(self, arg):
        """创建新文件
用法: create <文件名>
示例: create test.txt"""
        if not arg:
            print("请提供文件名")
            return
        try:
            self.fs.create_file(arg)
            print(f"文件 {arg} 创建成功")
        except Exception as e:
            print(f"创建失败: {str(e)}")

    def do_rename(self, arg):
        """重命名文件
用法: rename <旧文件名> <新文件名>
示例: rename old.txt new.txt"""
        try:
            old_name, new_name = arg.split()
            self.fs.rename_file(old_name, new_name)
            print(f"文件 {old_name} 已重命名为 {new_name}")
        except ValueError:
            print("用法: rename <旧文件名> <新文件名>")
        except Exception as e:
            print(f"重命名失败: {str(e)}")

    def do_delete(self, arg):
        """删除文件
用法: delete <文件名>
示例: delete test.txt"""
        if not arg:
            print("请提供文件名")
            return
        try:
            self.fs.delete_file(arg)
            print(f"文件 {arg} 已删除")
        except Exception as e:
            print(f"删除失败: {str(e)}")

    def do_list(self, arg):
        """列出所有文件
用法: list
示例: list"""
        try:
            files = self.fs.list_files()
            if not files:
                print("文件系统为空")
            else:
                for f in files:
                    print(f)
        except Exception as e:
            print(f"列表获取失败: {str(e)}")

    def do_cat(self, arg):
        """显示文件内容
用法: cat <文件名>
示例: cat test.txt"""
        if not arg:
            print("请提供文件名")
            return
        try:
            content = self.fs.read_file(arg)
            print(content.decode('utf-8'))
        except Exception as e:
            print(f"读取失败: {str(e)}")

    def do_write(self, arg):
        """写入文本到文件
用法: write <文件名>
示例: write test.txt
(然后输入文本内容，输入单独的一行 .end 结束输入)"""
        if not arg:
            print("请提供文件名")
            return
            
        try:
            filename = arg
            print("请输入文件内容（输入单独的一行 .end 结束）:")
            content_lines = []
            while True:
                line = input()
                if line.strip() == '.end':
                    break
                content_lines.append(line)
            
            content = '\n'.join(content_lines)
            self.fs.write_file(filename, content.encode('utf-8'))
            print(f"内容已写入到文件 {filename}")
        except Exception as e:
            print(f"写入失败: {str(e)}")

    def do_import(self, arg):
        """从外部导入文件
用法: import <外部文件路径> <导入后的文件名>
示例: import /home/user/test.txt internal.txt"""
        try:
            ext_path, int_name = arg.split()
            self.fs.import_file(ext_path, int_name)
            print(f"文件 {ext_path} 已导入为 {int_name}")
        except ValueError:
            print("用法: import <外部文件路径> <导入后的文件名>")
        except Exception as e:
            print(f"导入失败: {str(e)}")

    def do_export(self, arg):
        """导出文件到外部
用法: export <文件名> <导出路径>
示例: export internal.txt /home/user/exported.txt"""
        try:
            int_name, ext_path = arg.split()
            self.fs.export_file(int_name, ext_path)
            print(f"文件 {int_name} 已导出到 {ext_path}")
        except ValueError:
            print("用法: export <文件名> <导出路径>")
        except Exception as e:
            print(f"导出失败: {str(e)}")

    def do_info(self, arg):
        """显示存储统计信息
用法: info
示例: info"""
        try:
            used, free = self.fs.get_storage_info()
            print(f"已用空间: {used/1024/1024:.2f}MB")
            print(f"空闲空间: {free/1024/1024:.2f}MB")
        except Exception as e:
            print(f"获取存储信息失败: {str(e)}")

    def do_exit(self, arg):
        """退出LightFS
用法: exit"""
        print("再见!")
        return True

    def help_create(self):
        print(self.do_create.__doc__)

    def help_rename(self):
        print(self.do_rename.__doc__)

    def help_delete(self):
        print(self.do_delete.__doc__)

    def help_list(self):
        print(self.do_list.__doc__)

    def help_cat(self):
        print(self.do_cat.__doc__)

    def help_write(self):
        print(self.do_write.__doc__)

    def help_import(self):
        print(self.do_import.__doc__)

    def help_export(self):
        print(self.do_export.__doc__)

    def help_info(self):
        print(self.do_info.__doc__)

    def help_exit(self):
        print(self.do_exit.__doc__)

if __name__ == '__main__':
    LightFSShell().cmdloop() 