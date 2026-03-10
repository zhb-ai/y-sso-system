import random
import string


def generate_strong_password(length: int = 8, is_strong: bool = True, default_password: str = "000000") -> str:
    """生成强密码，满足以下要求：
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    - 至少包含一个数字
    - 至少包含一个特殊字符

    Args:
        default_password:
        is_strong:
        length: 密码长度，默认12

    Returns:
        符合要求的强密码
    """
    if not is_strong:
        return default_password

    # 确保密码长度至少为8位
    length = max(length, 8)

    # 定义字符集
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # 确保至少包含每种类型的一个字符
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special_chars),
    ]

    # 填充剩余字符
    all_chars = uppercase + lowercase + digits + special_chars
    remaining_length = length - 4
    password += random.choices(all_chars, k=remaining_length)

    # 打乱顺序
    random.shuffle(password)

    return ''.join(password)


# 示例用法
if __name__ == "__main__":
    print(generate_strong_password(12, False))
    print(generate_strong_password(16))
