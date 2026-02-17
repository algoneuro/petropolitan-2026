import sys
from collections import Counter

# Эталонные порядки букв (по убыванию частоты)
RUSSIAN_ORDER = ['о', 'е', 'а', 'и', 'н', 'т', 'с', 'р', 'в', 'л', 'к', 'м', 'д', 'п', 'у', 'я', 'ы', 'ь', 'г', 'з', 'б', 'ч', 'й', 'х', 'ж', 'ш', 'ю', 'ц', 'щ', 'э', 'ф', 'ъ', 'ё']
ENGLISH_ORDER = ['e', 't', 'a', 'o', 'i', 'n', 's', 'h', 'r', 'd', 'l', 'c', 'u', 'm', 'w', 'f', 'g', 'y', 'p', 'b', 'v', 'k', 'j', 'x', 'q', 'z']

def read_data(filename):
    """Читает TSV-файл с тремя колонками: телефон, email, адрес."""
    records = []
    with open(filename, 'r', encoding='utf-8') as f:
        # Пропускаем возможный заголовок
        first = f.readline().strip()
        if not first.startswith('Телефон'):
            f.seek(0)
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                records.append(tuple(parts))
    return records

def get_letters(text):
    """Извлекает только буквы из строки."""
    return ''.join(c for c in text if c.isalpha())

def freq_analysis(texts):
    """Возвращает словарь частот букв в объединённом тексте."""
    all_letters = ''.join(get_letters(t) for t in texts).lower()
    if not all_letters:
        return {}
    cnt = Counter(all_letters)
    total = len(all_letters)
    return {ch: cnt[ch]/total for ch in cnt}

def build_key(cipher_freq, target_order):
    """Строит ключ подстановки: cipher -> plain по убыванию частоты."""
    sorted_cipher = sorted(cipher_freq.items(), key=lambda x: x[1], reverse=True)
    key = {}
    for (c, _), p in zip(sorted_cipher, target_order):
        key[c] = p
    return key

def apply_key(text, key):
    """Применяет ключ к тексту (сохраняя регистр)."""
    result = []
    for ch in text:
        low = ch.lower()
        if low in key:
            repl = key[low]
            result.append(repl.upper() if ch.isupper() else repl)
        else:
            result.append(ch)
    return ''.join(result)

def main():
    if len(sys.argv) < 2:
        print("Usage: python deanon.py <input_file> [output_file]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'deanon_output.txt'

    records = read_data(input_file)
    addresses = [r[2] for r in records]
    emails = [r[1] for r in records]

    # Частотный анализ
    ru_freq = freq_analysis(addresses)
    en_freq = freq_analysis(emails)

    # Построение начальных ключей
    ru_key = build_key(ru_freq, RUSSIAN_ORDER)
    en_key = build_key(en_freq, ENGLISH_ORDER)

    # Корректировка по известным словам (можно дополнить)
    ru_key.update({'щ': 'у', 'с': 'л', 'л': 'к', 'г': 'в'})
    en_key.update({'q': 'c', 'x': 'o', 'o': 'm'})

    # Расшифровка
    decrypted = []
    for phone, email, addr in records:
        dec_email = apply_key(email, en_key)
        dec_addr = apply_key(addr, ru_key)
        decrypted.append((phone, dec_email, dec_addr))

    # Запись результата с ключом
    key_str = f"ru_key: {ru_key}\nen_key: {en_key}"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Телефон\temail\tадрес\tключ\n")
        for phone, email, addr in decrypted:
            f.write(f"{phone}\t{email}\t{addr}\t{key_str}\n")

    print(f"Результат сохранён в {output_file}")

if __name__ == '__main__':
    main()
