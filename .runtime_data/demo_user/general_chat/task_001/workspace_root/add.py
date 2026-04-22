def add_one_plus_one():
    """计算 1+1 的结果"""
    return 1 + 1

def add(a, b):
    """通用加法函数"""
    return a + b

# 主程序
if __name__ == "__main__":
    # 调用 1+1 函数
    result = add_one_plus_one()
    print(f"1 + 1 = {result}")
    
    # 调用通用加法函数
    print(f"2 + 3 = {add(2, 3)}")
    print(f"5 + 7 = {add(5, 7)}")
