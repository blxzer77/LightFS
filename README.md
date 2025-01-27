# LightFS - 轻量级文件系统

LightFS是一个基于Python实现的轻量级文件系统，它将所有数据存储在单个文件中，支持基本的文件操作功能。提供了友好的中文命令行界面，适合学习和研究文件系统的原理。

## 项目概述

本项目是一个轻量级文件系统的实现，主要特点如下：

### 核心特性
- 单文件存储：所有数据存储在`light.fs`文件中
- 固定大小：总大小256MB（56MB系统信息 + 200MB数据存储）
- 存储管理：使用位图管理数据块的分配
- 中文界面：完整的中文交互和帮助信息

### 系统架构

#### 存储布局
- 超级块（4KB）：存储文件系统的基本信息
- 位图区：用于管理数据块的分配状态
- 元数据区：存储文件的元数据信息
- 数据区：存储文件的实际内容

#### 技术特点
1. 数据组织
   - 单个存储单元：1MB
   - 最大文件大小：16MB
   - 最大文件名长度：255字节

2. 文件管理
   - 使用位图管理存储空间
   - 文件元数据和数据分离存储
   - 支持基本文件属性管理

### 主要功能
- 文件基本操作（创建、删除、重命名）
- 文件内容管理（读取、写入）
- 外部文件交互（导入、导出）
- 存储空间管理和统计

## 系统要求
- Python 3.6+
- 不需要额外的依赖包

## 项目结构
```
LightFS/
├── src/
│   ├── cli.py      # 命令行界面实现
│   └── lightfs.py  # 文件系统核心实现
├── README.md       # 项目概述
└── manual.md       # 使用说明
```

## 详细文档
- [使用说明](manual.md) 