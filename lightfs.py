#!/usr/bin/env python3
import os
import struct
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
import time

@dataclass
class FileEntry:
    """文件元数据条目"""
    filename: str        # 文件名
    size: int           # 文件大小
    blocks: List[int]   # 文件占用的块号列表
    create_time: float  # 创建时间
    modify_time: float  # 修改时间
    is_valid: bool      # 是否有效（用于删除标记）

class LightFS:
    # 文件系统常量
    TOTAL_SIZE = 256 * 1024 * 1024  # 256MB
    SYSTEM_SIZE = 56 * 1024 * 1024   # 56MB for system info
    DATA_SIZE = 200 * 1024 * 1024    # 200MB for data
    BLOCK_SIZE = 1 * 1024 * 1024     # 1MB per block
    MAX_FILENAME_LENGTH = 255        # 最大文件名长度
    MAX_FILE_SIZE = 16 * 1024 * 1024 # 16MB 最大文件大小
    
    # 文件系统布局常量
    SUPER_BLOCK_SIZE = 4096          # 超级块大小（4KB）
    BITMAP_OFFSET = SUPER_BLOCK_SIZE  # 位图开始位置
    TOTAL_BLOCKS = DATA_SIZE // BLOCK_SIZE  # 总块数
    BITMAP_SIZE = (TOTAL_BLOCKS + 7) // 8   # 位图大小（字节）
    FILE_ENTRY_SIZE = 512            # 每个文件元数据条目大小
    MAX_FILES = 1024                # 最大文件数
    
    # 数据区域偏移
    METADATA_OFFSET = BITMAP_OFFSET + BITMAP_SIZE
    DATA_OFFSET = SYSTEM_SIZE
    
    def __init__(self, filename: str):
        self.filename = filename
        self.initialized = os.path.exists(filename)
        self._file = None
        
    def _open(self):
        """打开文件系统文件"""
        if not self._file:
            self._file = open(self.filename, 'r+b' if os.path.exists(self.filename) else 'w+b')
    
    def _close(self):
        """关闭文件系统文件"""
        if self._file:
            self._file.close()
            self._file = None

    def initialize(self):
        """初始化文件系统"""
        if self.initialized:
            return False
        
        self._open()
        try:
            # 写入空数据填充整个文件系统
            self._file.write(b'\0' * self.TOTAL_SIZE)
            
            # 初始化超级块
            self._file.seek(0)
            # 魔数 + 版本号 + 块大小 + 总块数 + 最大文件数
            self._file.write(struct.pack('IIIII', 
                0x4C464653,  # 魔数 'LIFS'
                1,           # 版本号
                self.BLOCK_SIZE,
                self.TOTAL_BLOCKS,
                self.MAX_FILES
            ))
            
            # 初始化位图
            self._file.seek(self.BITMAP_OFFSET)
            self._file.write(b'\0' * self.BITMAP_SIZE)
            
        finally:
            self._close()
            
        self.initialized = True
        return True

    def _read_bitmap(self) -> bytearray:
        """读取位图"""
        self._file.seek(self.BITMAP_OFFSET)
        return bytearray(self._file.read(self.BITMAP_SIZE))

    def _write_bitmap(self, bitmap: bytearray):
        """写入位图"""
        self._file.seek(self.BITMAP_OFFSET)
        self._file.write(bitmap)

    def _get_block_status(self, bitmap: bytearray, block_num: int) -> bool:
        """获取块的使用状态"""
        byte_index = block_num // 8
        bit_index = block_num % 8
        return bool(bitmap[byte_index] & (1 << bit_index))

    def _set_block_status(self, bitmap: bytearray, block_num: int, used: bool):
        """设置块的使用状态"""
        byte_index = block_num // 8
        bit_index = block_num % 8
        if used:
            bitmap[byte_index] |= (1 << bit_index)
        else:
            bitmap[byte_index] &= ~(1 << bit_index)

    def _find_free_blocks(self, num_blocks: int) -> List[int]:
        """查找空闲块"""
        bitmap = self._read_bitmap()
        free_blocks = []
        
        for i in range(self.TOTAL_BLOCKS):
            if not self._get_block_status(bitmap, i):
                free_blocks.append(i)
                if len(free_blocks) == num_blocks:
                    break
        
        if len(free_blocks) < num_blocks:
            raise ValueError("没有足够的空闲空间")
        
        return free_blocks

    def _read_file_entry(self, index: int) -> Optional[FileEntry]:
        """读取文件元数据条目"""
        if index >= self.MAX_FILES:
            return None
            
        offset = self.METADATA_OFFSET + index * self.FILE_ENTRY_SIZE
        self._file.seek(offset)
        
        # 读取基本信息
        is_valid = bool(struct.unpack('B', self._file.read(1))[0])
        if not is_valid:
            return None
            
        filename_length = struct.unpack('B', self._file.read(1))[0]
        filename = self._file.read(filename_length).decode('utf-8')
        
        # 跳过文件名填充
        self._file.seek(offset + 2 + self.MAX_FILENAME_LENGTH)
        
        # 读取其他元数据
        size, create_time, modify_time, num_blocks = struct.unpack('QddI', self._file.read(28))
        
        # 读取块列表
        blocks = list(struct.unpack('16I', self._file.read(64)))[:num_blocks]
        
        return FileEntry(filename, size, blocks, create_time, modify_time, is_valid)

    def _write_file_entry(self, index: int, entry: FileEntry):
        """写入文件元数据条目"""
        if index >= self.MAX_FILES:
            raise ValueError("超出最大文件数限制")
            
        offset = self.METADATA_OFFSET + index * self.FILE_ENTRY_SIZE
        self._file.seek(offset)
        
        # 写入基本信息
        filename_bytes = entry.filename.encode('utf-8')
        self._file.write(struct.pack('B', 1 if entry.is_valid else 0))  # is_valid
        self._file.write(struct.pack('B', len(filename_bytes)))         # filename_length
        self._file.write(filename_bytes)                                # filename
        
        # 填充文件名到固定长度
        name_padding = self.MAX_FILENAME_LENGTH - len(filename_bytes)
        if name_padding > 0:
            self._file.write(b'\0' * name_padding)
        
        # 写入其他元数据
        self._file.write(struct.pack('QddI',
            entry.size,
            entry.create_time,
            entry.modify_time,
            len(entry.blocks)
        ))
        
        # 写入块列表（最多支持16个块，因为每个块1MB，最大文件16MB）
        blocks_array = entry.blocks + [0] * (16 - len(entry.blocks))
        self._file.write(struct.pack('16I', *blocks_array))

    def _find_file_entry(self, filename: str) -> Tuple[int, Optional[FileEntry]]:
        """查找文件元数据条目"""
        for i in range(self.MAX_FILES):
            entry = self._read_file_entry(i)
            if entry and entry.filename == filename and entry.is_valid:
                return i, entry
        return -1, None

    def _find_free_entry_index(self) -> int:
        """查找空闲的文件元数据条目索引"""
        for i in range(self.MAX_FILES):
            entry = self._read_file_entry(i)
            if not entry or not entry.is_valid:
                return i
        raise ValueError("超出最大文件数限制")

    def create_file(self, filename: str) -> bool:
        """创建新文件"""
        if len(filename.encode()) > self.MAX_FILENAME_LENGTH:
            raise ValueError("文件名过长")
            
        self._open()
        try:
            # 检查文件是否已存在
            index, existing = self._find_file_entry(filename)
            if existing:
                raise ValueError("文件已存在")
                
            # 创建新文件条目
            index = self._find_free_entry_index()
            current_time = time.time()
            entry = FileEntry(
                filename=filename,
                size=0,
                blocks=[],
                create_time=current_time,
                modify_time=current_time,
                is_valid=True
            )
            
            self._write_file_entry(index, entry)
            return True
            
        finally:
            self._close()

    def get_storage_info(self) -> Tuple[int, int]:
        """获取存储统计信息（已用空间，空闲空间）"""
        self._open()
        try:
            bitmap = self._read_bitmap()
            used_blocks = sum(bin(byte).count('1') for byte in bitmap)
            used_space = used_blocks * self.BLOCK_SIZE
            free_space = self.DATA_SIZE - used_space
            return used_space, free_space
        finally:
            self._close()

    def rename_file(self, old_name: str, new_name: str) -> bool:
        """重命名文件"""
        if len(new_name.encode()) > self.MAX_FILENAME_LENGTH:
            raise ValueError("新文件名过长")
            
        self._open()
        try:
            # 检查新文件名是否已存在
            _, existing = self._find_file_entry(new_name)
            if existing:
                raise ValueError("目标文件名已存在")
            
            # 查找原文件
            index, entry = self._find_file_entry(old_name)
            if not entry:
                raise ValueError("源文件不存在")
            
            # 更新文件名
            entry.filename = new_name
            entry.modify_time = time.time()
            self._write_file_entry(index, entry)
            
            return True
            
        finally:
            self._close()

    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        self._open()
        try:
            # 查找文件
            index, entry = self._find_file_entry(filename)
            if not entry:
                raise ValueError("文件不存在")
            
            # 释放数据块
            bitmap = self._read_bitmap()
            for block in entry.blocks:
                self._set_block_status(bitmap, block, False)
            self._write_bitmap(bitmap)
            
            # 标记文件为已删除
            entry.is_valid = False
            self._write_file_entry(index, entry)
            
            return True
            
        finally:
            self._close()

    def list_files(self) -> List[str]:
        """列出所有文件"""
        self._open()
        try:
            files = []
            for i in range(self.MAX_FILES):
                entry = self._read_file_entry(i)
                if entry and entry.is_valid:
                    files.append(f"{entry.filename} ({entry.size} bytes, 创建于 {time.ctime(entry.create_time)})")
            return files
        finally:
            self._close()

    def _read_block(self, block_num: int) -> bytes:
        """读取数据块"""
        offset = self.DATA_OFFSET + block_num * self.BLOCK_SIZE
        self._file.seek(offset)
        return self._file.read(self.BLOCK_SIZE)

    def _write_block(self, block_num: int, data: bytes):
        """写入数据块"""
        offset = self.DATA_OFFSET + block_num * self.BLOCK_SIZE
        self._file.seek(offset)
        self._file.write(data)
        # 如果数据不足一个块，用0填充
        if len(data) < self.BLOCK_SIZE:
            self._file.write(b'\0' * (self.BLOCK_SIZE - len(data)))

    def read_file(self, filename: str) -> bytes:
        """读取文件内容"""
        self._open()
        try:
            # 查找文件
            _, entry = self._find_file_entry(filename)
            if not entry:
                raise ValueError("文件不存在")
            
            # 读取所有数据块
            content = bytearray()
            for block_num in entry.blocks:
                block_data = self._read_block(block_num)
                content.extend(block_data)
            
            # 只返回实际大小的数据
            return bytes(content[:entry.size])
            
        finally:
            self._close()

    def write_file(self, filename: str, content: bytes) -> bool:
        """写入文件内容"""
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError("文件大小超过限制")
            
        self._open()
        try:
            # 查找或创建文件
            index, entry = self._find_file_entry(filename)
            if not entry:
                # 创建新文件
                index = self._find_free_entry_index()
                entry = FileEntry(
                    filename=filename,
                    size=0,
                    blocks=[],
                    create_time=time.time(),
                    modify_time=time.time(),
                    is_valid=True
                )
            
            # 计算需要的块数
            num_blocks = (len(content) + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
            
            # 如果文件已存在，先释放原有块
            bitmap = self._read_bitmap()
            for block in entry.blocks:
                self._set_block_status(bitmap, block, False)
            
            # 分配新块
            new_blocks = self._find_free_blocks(num_blocks)
            for block in new_blocks:
                self._set_block_status(bitmap, block, True)
            self._write_bitmap(bitmap)
            
            # 写入数据块
            for i, block_num in enumerate(new_blocks):
                start = i * self.BLOCK_SIZE
                end = min(start + self.BLOCK_SIZE, len(content))
                self._write_block(block_num, content[start:end])
            
            # 更新文件元数据
            entry.size = len(content)
            entry.blocks = new_blocks
            entry.modify_time = time.time()
            self._write_file_entry(index, entry)
            
            return True
            
        finally:
            self._close()

    def import_file(self, external_path: str, internal_name: str) -> bool:
        """导入外部文件"""
        # 检查外部文件是否存在
        if not os.path.exists(external_path):
            raise ValueError("外部文件不存在")
            
        # 检查文件大小
        file_size = os.path.getsize(external_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError("文件大小超过限制")
            
        # 读取外部文件内容
        with open(external_path, 'rb') as f:
            content = f.read()
            
        # 写入到文件系统
        return self.write_file(internal_name, content)

    def export_file(self, internal_name: str, external_path: str) -> bool:
        """导出文件到外部"""
        # 读取文件内容
        content = self.read_file(internal_name)
        
        # 写入到外部文件
        with open(external_path, 'wb') as f:
            f.write(content)
            
        return True 