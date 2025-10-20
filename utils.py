import re

def normalize_command(cmd):
    """
    最终优化的命令参数归一化函数
    
    功能：
    1. 智能处理重定向符号（>、>>、<等）确保前后有空格
    2. 保持引号内的内容不受影响
    3. + 号选项放在最前面
    4. 字母选项（-a, -B）按小写字母→大写字母顺序
    5. 数字选项（-10）保持整体并按数值排序
    6. 智能处理混合选项（如 -6v → -v -6）
    
    参数:
    cmd (str): 原始命令字符串
    
    返回:
    str: 归一化后的命令字符串
    """
    def normalize_redirections(command_str):
        """智能处理重定向符号，确保前后有空格，同时保护引号内的内容"""
        # 保护引号内的内容不被修改
        protected = []
        def protect_quotes(match):
            token = match.group(0)
            key = f"__PROTECTED_{len(protected)}__"
            protected.append((key, token))
            return key
        
        # 使用临时令牌替换引号内的内容
        quoted_str = re.sub(r'(\'[^\']*\'|\"[^\"]*\")', protect_quotes, command_str)
        
        # 处理重定向符号（确保前后有空格）
        # 匹配所有重定向符号：> >> >| >& < << <> &> &>> 2> 2>> 等
        redir_pattern = r'(\||[0-9]*&?>[&|]?|[0-9]*<[<]?|[0-9]*>>|<<-|<>|[0-9]*>\()'
        spaced = re.sub(redir_pattern, r' \1 ', quoted_str)
        
        # 清理多余空格
        cleaned = re.sub(r'\s+', ' ', spaced).strip()
        
        # 恢复被保护的内容
        for key, token in protected:
            cleaned = cleaned.replace(key, token)
        
        return cleaned

    # 预处理：智能处理重定向符号
    cmd = normalize_redirections(cmd.strip())
    
    # 分割命令为多个部分
    parts = cmd.split()
    if not parts:
        return cmd

    # 初始化分类容器
    cmd_name = parts[0]
    plus_opts = []
    minus_letters = []
    minus_digits = []
    long_opts = []
    redirections = []   # 存储重定向符号及其参数
    other_args = []
    
    # 分类处理各个部分
    i = 1
    while i < len(parts):
        part = parts[i]
        
        # 处理重定向符号及后续参数
        if re.match(r'^(\||[0-9]*&?>[&|]?|[0-9]*<[<]?|[0-9]*>>|<<-|<>|[0-9]*>\()$', part):
            # 保存重定向符号
            redirection = part
            
            # 获取重定向目标（下一个参数）
            if i + 1 < len(parts):
                target = parts[i + 1]
                # 添加到重定向列表
                redirections.append(redirection)
                redirections.append(target)
                # 跳过下一个参数（目标）
                i += 2
                continue
        
        # 处理 + 号选项
        if part.startswith('+') and len(part) > 1:
            plus_opts.append(part)
        
        # 处理长选项
        elif part.startswith('--') and len(part) > 2:
            long_opts.append(part)
        
        # 处理 - 开头的选项
        elif part.startswith('-') and len(part) > 1:
            # 纯数字选项
            if part[1:].isdigit():
                minus_digits.append(part)
            
            # 混合选项（字母+数字）
            elif any(c.isalpha() for c in part[1:]) and any(c.isdigit() for c in part[1:]):
                # 分离字母和数字
                letters = ''.join(c for c in part[1:] if c.isalpha())
                digits = ''.join(c for c in part[1:] if c.isdigit())
                
                # 添加分离后的选项
                if letters:
                    for c in letters:
                        minus_letters.append(f"-{c}")
                if digits:
                    minus_digits.append(f"-{digits}")
            
            # 纯字母选项
            elif part[1:].isalpha():
                for c in part[1:]:
                    minus_letters.append(f"-{c}")
            
            # 其他特殊选项
            else:
                other_args.append(part)
        
        # 处理其他参数
        else:
            other_args.append(part)
        
        i += 1
    
    # 排序函数
    def sort_plus(opt):
        num = opt[1:]
        return (0, int(num)) if num.isdigit() else (1, num.lower())
    
    def sort_letter(opt):
        char = opt[1]
        return (0, char) if char.islower() else (1, char)
    
    def sort_digit(opt):
        num_part = opt[1:]
        return int(num_part) if num_part.isdigit() else float('inf')
    
    # 执行排序
    plus_opts.sort(key=sort_plus)
    minus_letters.sort(key=sort_letter)
    minus_digits.sort(key=sort_digit)
    
    # 构建最终命令
    normalized = [cmd_name]
    normalized.extend(plus_opts)
    normalized.extend(minus_letters)
    normalized.extend(minus_digits)
    normalized.extend(long_opts)
    normalized.extend(other_args)
    normalized.extend(redirections)  # 重定向符号放在最后
    
    return ' '.join(normalized)

if __name__ == "__main__":
    # 增强的测试用例
    test_cases = [
        ("基础命令", [
            "ls -al",
            "tail -6v +3"
        ]),
        ("重定向命令", [
            "echo hello>/tmp/test.txt",
            "echo 'hello world' >>log.txt",
            "echo \"hello\">>/tmp/test.txt",
            "cat<file.txt",
            "grep error 2>/dev/null",
            "sort | uniq -c",
            "echo \"hello>world\" > output.txt"
        ]),
        ("混合命令", [
            "more +5 -10 /etc/passwd >output.txt",
            "tail -f -n20 access.log 2>errors.log",
            "find . -name '*.py' | grep import >results.txt"
        ]),
        ("复杂重定向", [
            "cmd1 | cmd2 >output.txt",
            "cmd1 2>&1",
            "cmd >>log.txt 2>errors.txt"
        ]),
        ("特殊案例", [
            "echo 'Hello>' world",  # 引号内保持原样
            "echo \"Hello>>\" world",  # 引号内保持原样
            "curl -o - https://example.com > output.bin"
        ])
    ]
    
    print("=" * 80)
    print("最终优化的命令归一化测试报告".center(80))
    print("=" * 80)
    
    for category, cases in test_cases:
        print(f"\n{category.upper()}:")
        for cmd in cases:
            print(f"\n原始命令: {cmd}")
            normalized = normalize_command(cmd)
            print(f"归一化后: {normalized}")
            print("-" * 80)