import re, collections  # re是正则表达式库，collections是集合库

def get_stats(vocab):
	"""统计词元对频率"""
	pairs = collections.defaultdict(int)  # 创建一个字典(键值对). 默认值为0
	for word, freq in vocab.items():
		symbols = word.split()
		for i in range(len(symbols) - 1):
			pairs[symbols[i], symbols[i + 1]] += freq  # 累加词元对的频率
	return pairs

def merge_vocab(pair, v_in):
	"""合并词元对"""
	v_out = {}
	bigram = re.escape(
		" ".join(pair)
	)  # 先将pair用 ' '连接起来，再用 escape()函数用于转义特殊字符，确保它们在正则表达式中被正确处理
	p = re.compile(
		r"(?<!\S)" + bigram + r"(?!\S)"
	)  # \S 表示非空格字符    ?<! 表示非贪婪匹配，?!\ 表示非贪婪匹配，用于查找不包含空格的词元对
	for word in v_in:
		w_out = p.sub(
			"".join(pair), word
		)  # p.sub()函数用于替换匹配到的词元对，将其替换为 ''.join(pair)中的字符串
		v_out[w_out] = v_in[word]
	return v_out

# 准备语料库，每个词末尾加上</w>表示结束，并切分好字符
vocab = {"h u g </w>": 1, "p u g </w>": 1, "p u n </w>": 1, "b u n </w>": 1}
num_merges = 8  # 设置合并次数

for i in range(num_merges):
	pairs = get_stats(vocab)
	if not pairs:
		break
	best = max(pairs, key=pairs.get)
	vocab = merge_vocab(best, vocab)
	print(f"第{i+1}次合并: {best} -> {''.join(best)}")
	print(f"新词表（部分）: {list(vocab.keys())}")
	print("-" * 20)
