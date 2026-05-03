#!/usr/bin/env python3
"""
一键打包脚本 - 自动生成可执行文件
支持多平台打包（Windows/Linux/Mac）
"""

import os
import sys
import subprocess
import shutil

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, 
                               capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"命令执行失败: {cmd}")
            print(f"错误信息: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except subprocess.TimeoutExpired:
        print(f"命令执行超时: {cmd}")
        return False, "超时"
    except Exception as e:
        print(f"命令执行异常: {cmd} - {e}")
        return False, str(e)

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    success, output = run_command("pip install -r requirements.txt")
    if not success:
        print(f"依赖安装失败: {output}")
        return False
    print("依赖安装成功")
    return True

def build_exe():
    """使用 PyInstaller 打包"""
    print("开始打包...")
    
    # 检查是否安装了 pyinstaller
    success, output = run_command("pip show pyinstaller")
    if not success:
        print("安装 PyInstaller...")
        success, output = run_command("pip install pyinstaller")
        if not success:
            return False
    
    # 根据平台选择不同的打包命令
    if sys.platform == 'win32':
        cmd = 'pyinstaller --onefile --windowed --name=SSQ_Predictor --icon=app.ico 1claude_opus_4.5.py'
    elif sys.platform == 'darwin':
        cmd = 'pyinstaller --onefile --windowed --name=SSQ_Predictor --icon=app.icns 1claude_opus_4.5.py'
    else:
        cmd = 'pyinstaller --onefile --name=ssq_predictor 1claude_opus_4.5.py'
    
    success, output = run_command(cmd)
    if not success:
        print(f"打包失败: {output}")
        return False
    
    print("打包成功")
    print(f"可执行文件位置: dist/{'SSQ_Predictor.exe' if sys.platform == 'win32' else 'ssq_predictor'}")
    return True

def create_shortcut():
    """创建快捷方式（仅Windows）"""
    if sys.platform != 'win32':
        return True
    
    print("创建快捷方式...")
    shortcut_path = os.path.join(os.path.expanduser("~"), "Desktop", "双色球预测器.lnk")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "双色球预测器.lnk")
        
        target = os.path.join(os.getcwd(), "dist", "SSQ_Predictor.exe")
        wDir = os.getcwd()
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.save()
        
        print("快捷方式创建成功")
        return True
    except ImportError:
        print("警告：需要安装 pywin32 来创建快捷方式")
        print("运行: pip install pywin32")
        return True
    except Exception as e:
        print(f"创建快捷方式失败: {e}")
        return True

def main():
    """主函数"""
    print("=" * 60)
    print("      双色球预测程序 - 一键打包脚本")
    print("=" * 60)
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("检测到虚拟环境，继续执行...")
    else:
        print("警告：建议在虚拟环境中运行此脚本")
        if input("是否继续？(y/n): ").lower() != 'y':
            return
    
    # 步骤1: 安装依赖
    if not install_dependencies():
        return
    
    # 步骤2: 打包
    if not build_exe():
        return
    
    # 步骤3: 创建快捷方式
    create_shortcut()
    
    print("=" * 60)
    print("打包完成！")
    print("可执行文件位于: dist/ 目录")
    print("=" * 60)

if __name__ == '__main__':
    main()