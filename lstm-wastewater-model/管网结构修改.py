import os

# 1. 设置你的文件路径 (请确保这里是纯英文路径)
input_file = r'E:\PY\LSTM\inp\xygw.inp'
output_file = r'E:\PY\LSTM\inp\xygw_fixed.inp'  # 修复后的新文件

print("开始读取模型文件并进行结构手术...")

try:
	# 尝试用不同编码读取
	try:
		with open(input_file, 'r', encoding='utf-8') as f:
			lines = f.readlines()
	except UnicodeDecodeError:
		with open(input_file, 'r', encoding='gbk') as f:
			lines = f.readlines()
	
	new_lines = []
	j231_elevation = "0"
	in_storage = False
	
	# 2. 遍历每一行，把 J231 从 [STORAGE] 中“切除”并记住它的标高
	for line in lines:
		if line.strip().upper() == '[STORAGE]':
			in_storage = True
			new_lines.append(line)
			continue
		elif line.strip().startswith('['):
			in_storage = False
		
		# 如果在 STORAGE 模块里发现了 J231
		if in_storage and line.strip().startswith('J231'):
			parts = line.split()
			if len(parts) >= 2:
				j231_elevation = parts[1]  # 提取原来的底标高
			print(f"✅ 已找到原水池 J231, 提取标高: {j231_elevation}m，并将其从水池列表中移除。")
			continue  # 跳过这一行，相当于删除
		
		new_lines.append(line)
	
	# 3. 把 J231 作为排口添加到 [OUTFALLS] 模块中
	has_outfalls = any(line.strip().upper() == '[OUTFALLS]' for line in new_lines)
	
	if not has_outfalls:
		# 如果原来连 [OUTFALLS] 模块都没有，我们就新建一个
		new_lines.append('\n[OUTFALLS]\n')
		new_lines.append(';;Name           Elevation  Type       Stage Data       Gated    Route To\n')
		new_lines.append(';;-------------- ---------- ---------- ---------------- -------- ----------------\n')
		new_lines.append(f'J231             {j231_elevation}      FREE                        NO\n')
	else:
		# 如果有，就插在 [OUTFALLS] 模块下面
		for i, line in enumerate(new_lines):
			if line.strip().upper() == '[OUTFALLS]':
				new_lines.insert(i + 2, f'J231             {j231_elevation}      FREE                        NO\n')
				break
	
	print(f"✅ 已成功将 J231 注册为 FREE(自由流) 类型的排口！")
	
	# 4. 保存为新的修复文件
	with open(output_file, 'w', encoding='utf-8') as f:
		f.writelines(new_lines)
	
	print(f"🎉 修复完成！新文件已保存至: {output_file}")

except Exception as e:
	print(f"❌ 处理出错: {e}")