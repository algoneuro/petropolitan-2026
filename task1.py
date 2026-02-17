import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

def normalize_ipv6(addr: str) -> bytes:
    """Преобразует IPv6-адрес в 16-байтовое каноническое представление."""
    addr = addr.strip().lower()
    if '::' in addr:
        left, right = addr.split('::', 1)
        left_groups = left.split(':') if left else []
        right_groups = right.split(':') if right else []
        missing = 8 - len(left_groups) - len(right_groups)
        groups = left_groups + ['0'] * missing + right_groups
    else:
        groups = addr.split(':')
    hex_str = ''.join(part.zfill(4) for part in groups)
    return bytes.fromhex(hex_str)

def count_unique_simple(input_path: str) -> int:
    """Базовое решение для малых файлов – всё в памяти."""
    uniq = set()
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                uniq.add(normalize_ipv6(line))
    return len(uniq)

def process_bucket(bucket_path: str) -> int:
    """Подсчёт уникальных в одном временном файле."""
    uniq = set()
    with open(bucket_path, 'rb') as f:
        while chunk := f.read(16):
            uniq.add(chunk)
    return len(uniq)

def count_unique_optimized(input_path: str, num_buckets: int = 1024) -> int:
    """Оптимизированное решение с корзинами и многопоточностью."""
    temp_dir = tempfile.mkdtemp(prefix='ipv6_')
    bucket_files = [os.path.join(temp_dir, f'bucket_{i:04d}.bin') for i in range(num_buckets)]
    handles = [open(f, 'wb') for f in bucket_files]

    try:
        with open(input_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                if not line:
                    continue
                bin_addr = normalize_ipv6(line)
                bucket_id = int.from_bytes(bin_addr[:4], 'big') % num_buckets
                handles[bucket_id].write(bin_addr)
    finally:
        for h in handles:
            h.close()

    total = 0
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_bucket, f) for f in bucket_files]
        for future in as_completed(futures):
            total += future.result()

    for f in bucket_files:
        os.remove(f)
    os.rmdir(temp_dir)
    return total

def count_unique_ipv6(input_path: str, output_path: str):
    """Основная функция – выбирает метод в зависимости от размера файла."""
    size = os.path.getsize(input_path)
    if size < 200 * 1024 * 1024:  # меньше 200 МБ
        total = count_unique_simple(input_path)
    else:
        total = count_unique_optimized(input_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(total))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python unique_ipv6.py <input_file> <output_file>")
        sys.exit(1)
    count_unique_ipv6(sys.argv[1], sys.argv[2])
