from flask import Flask, render_template, request, redirect, url_for
import os
import filecmp
import difflib
import shutil

app = Flask(__name__)


def compare_files(file1, file2):
    """
    比较两个文件内容并返回差异行数，处理不同的编码。

    :param file1: 第一个文件路径
    :param file2: 第二个文件路径
    :return: 返回差异的行数和差异详细信息
    """
    try:
        with open(file1, 'r', encoding='utf-8', errors='ignore') as f1, open(file2, 'r', encoding='utf-8',
                                                                             errors='ignore') as f2:
            file1_lines = f1.readlines()
            file2_lines = f2.readlines()
    except UnicodeDecodeError as e:
        print(f"无法解码文件: {file1} 或 {file2}, 错误: {e}")
        return 0, []  # 返回0行差异，空的差异详情

    diff = difflib.unified_diff(file1_lines, file2_lines, lineterm='')
    diff_list = list(diff)

    # 统计不同的行数
    diff_count = len([line for line in diff_list if line.startswith('- ') or line.startswith('+ ')])

    return diff_count, diff_list


def compare_directories(dir1, dir2, ignore_files=None, ignore_dirs=None):
    """
    比较两个目录中的所有文件，忽略指定的文件和文件夹。

    :param dir1: 第一个目录路径
    :param dir2: 第二个目录路径
    :param ignore_files: 要忽略的文件列表
    :param ignore_dirs: 要忽略的文件夹列表
    :return: 返回不同文件的列表和差异信息
    """
    if ignore_files is None:
        ignore_files = []
    if ignore_dirs is None:
        ignore_dirs = []

    diff_results = []

    # 遍历第一个目录中的所有文件和文件夹
    for root, dirs, files in os.walk(dir1):
        relative_path = os.path.relpath(root, dir1)

        # 如果该目录在忽略列表中，跳过
        if any(os.path.commonpath([root]) == os.path.commonpath([os.path.join(dir1, ig)]) for ig in ignore_dirs):
            continue

        # 过滤掉忽略的文件夹
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file in ignore_files:
                continue

            file1 = os.path.join(root, file)
            file2 = os.path.join(dir2, relative_path, file)

            # 如果文件不存在或文件内容不同
            if os.path.exists(file2) and not filecmp.cmp(file1, file2, shallow=False):
                diff_count, diff_lines = compare_files(file1, file2)
                diff_results.append({
                    'file1': file1,
                    'file2': file2,
                    'diff_count': diff_count,
                    'diff_lines': diff_lines
                })
            elif not os.path.exists(file2):
                diff_results.append({
                    'file1': file1,
                    'file2': file2,
                    'diff_count': '文件不存在',
                    'diff_lines': []
                })

    # 再遍历第二个目录中的所有文件和文件夹
    for root, dirs, files in os.walk(dir2):
        relative_path = os.path.relpath(root, dir2)

        if any(os.path.commonpath([root]) == os.path.commonpath([os.path.join(dir2, ig)]) for ig in ignore_dirs):
            continue

        # 过滤掉忽略的文件夹
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file in ignore_files:
                continue

            file2 = os.path.join(root, file)
            file1 = os.path.join(dir1, relative_path, file)

            # 如果文件只在第二个目录中存在
            if not os.path.exists(file1):
                diff_results.append({
                    'file1': file1,
                    'file2': file2,
                    'diff_count': '文件不存在',
                    'diff_lines': []
                })

    return diff_results


@app.route('/')
def index():
    dir1 = "/Users/huangjiabao/GitHub/WebSite/hexo-theme-anzhiyu"
    dir2 = "/Users/huangjiabao/GitHub/WebSite/AndersonHJB.github.io/themes/anzhiyu"
    ignore_files = [".DS_Store"]
    ignore_dirs = [".git"]

    differences = compare_directories(dir1, dir2, ignore_files, ignore_dirs)
    return render_template('index.html', differences=differences)


@app.route('/overwrite', methods=['POST'])
def overwrite():
    file1 = request.form['file1']
    file2 = request.form['file2']

    # 执行文件覆盖操作
    shutil.copy(file1, file2)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
