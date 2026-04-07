import os
import glob
from Cython.Build import cythonize
from setuptools import Extension
from setuptools import setup
import numpy

import shutil

def copy_file(src, dst):
    """支持文件和目录的复制，如果目标存在则强制覆盖
    Args:
        src: 源文件或目录路径
        dst: 目标文件或目录路径
    """
    try:
        # 检查源是否存在
        if not os.path.exists(src):
            print(f"源路径不存在: {src}")
            return
        
        # 如果源是文件
        if os.path.isfile(src):
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # 强制覆盖复制文件
            shutil.copy2(src, dst)
            print(f'文件复制成功: {src} -> {dst}')
        
        # 如果源是目录
        elif os.path.isdir(src):
            # 如果目标目录已存在，先删除
            if os.path.exists(dst):
                shutil.rmtree(dst)
                print(f'删除已存在的目标目录: {dst}')
            
            # 递归复制目录
            shutil.copytree(src, dst)
            print(f'目录复制成功: {src} -> {dst}')
    
    except Exception as e:
        print(f'复制失败: {e}')


def get_build_target_dir():

    # return os.path.join(os.path.dirname(__file__), "build")
    # 获取build目录下的第一层子目录
    build_dir = "build"
    sub_dirs = [d for d in os.listdir(build_dir) if os.path.isdir(os.path.join(build_dir, d))]

    # 或者使用glob模式匹配（推荐）
    sub_dirs = glob.glob(os.path.join(build_dir, "lib.*"))

    if sub_dirs:
        # 获取第一个匹配的目录名（通常只有一个）
        platform_dir = os.path.basename(sub_dirs[0])
        print(f"获取到的平台目录名: {platform_dir}")
        
        # 完整路径
        full_path = os.path.join(build_dir, platform_dir)
        print(f"完整路径: {full_path}")
    else:
        print("未找到build目录下的子目录")

    return full_path

# 获取所有需要编译的Python文件
SRC_FILES = []

# 查找所有下级目录中的.py文件，不包括当前目录
for py_file in glob.glob("*/**/*.py", recursive=True):
    # 排除不需要编译的文件
    if not py_file.startswith("venv") and \
       not py_file.startswith(".venv") and \
       not py_file.startswith("logs") and \
       not py_file.startswith("build") and \
       not py_file.startswith("charts") and \
       not py_file.startswith("tests"):

        print(f"加入待编译文件: {py_file}")
        SRC_FILES.append(py_file)

# 创建扩展对象列表
extensions = []
for file in SRC_FILES:
    # 创建扩展模块名称（将路径分隔符替换为点）
    module_name = os.path.splitext(file)[0].replace(os.path.sep, '.')
    extensions.append(Extension(module_name, [file]))

# 编译所有扩展模块
if __name__ == '__main__':
    print("开始编译...")

    setup(
        name="oddasr",
        ext_modules=cythonize(
            SRC_FILES, 
            compiler_directives={
                'language_level': 3,
                'boundscheck': False,
                'wraparound': False
            }),
        zip_safe=False,
        include_dirs=[numpy.get_include()]
    )
    print("编译完成！")

    # 将根目录下的所有.py文件复制到build目录下
    print("复制基础文件列表到build目录...")
    for py_file in glob.glob("*.py"):
        build_target_dir = get_build_target_dir()
        if not py_file.startswith("venv") and \
           not py_file.startswith(".venv") and \
           not py_file.startswith("logs") and \
           not py_file.startswith("build") and \
           not py_file.startswith("charts") and \
           not py_file.startswith("tests"):
            print(f"复制文件: {py_file}")
            copy_file(py_file, f"{build_target_dir}/{py_file}")
    
    copy_file("templates", f"{build_target_dir}/templates")
    copy_file("static", f"{build_target_dir}/static")
    copy_file("tests", f"{build_target_dir}/tests")
    copy_file("requirements.txt", f"{build_target_dir}/requirements.txt")
    copy_file("start.bat", f"{build_target_dir}/start.bat")
    copy_file("start.sh", f"{build_target_dir}/start.sh")
    print("复制完成！")
