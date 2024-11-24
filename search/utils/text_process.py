from datasketch import MinHash, MinHashLSH
import jieba
def remove_duplicate_lines(raw_content, threshold=0.5, num_perm=128):
    """
    去除 raw_content 中的重复行。

    参数:
    - raw_content (str): 输入的多行字符串内容。
    - threshold (float): 判断相似度的阈值，越高则相似性要求越高。
    - num_perm (int): MinHash 签名长度，值越高判断越准确但计算量越大。

    返回:
    - str: 去重后的内容字符串。
    """
    # 将内容按行分割
    lines = raw_content.splitlines()
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    unique_lines = []

    for i, line in enumerate(lines):
        # 跳过空行
        if not line.strip():
            continue

        # 创建 MinHash
        m = MinHash(num_perm=num_perm)
        for token in jieba.cut(line):  # 中文分词
            m.update(token.encode('utf-8'))

        # 判断是否重复
        if not lsh.query(m):  # 如果未找到相似的行
            lsh.insert(i, m)  # 插入到 LSH
            if len(line) >= 100:
                unique_lines.append(line)  # 保存此行为不重复行
    # 将不重复的行重新组合成字符串返回
    return "\n".join(unique_lines)
