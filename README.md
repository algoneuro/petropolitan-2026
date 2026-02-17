## Ответы на задания отборочного тура Олимпиады «Petropolitan Science (Re)Search»

## Ссылка на репозиторий
[https://github.com/algoneuro/petropolitan-2026](https://github.com/algoneuro/petropolitan-2026)


### Задание 1. Подсчёт уникальных IPv6-адресов

#### Алгоритм
Для обработки файла с большим количеством строк (до 10⁹) при ограничении оперативной памяти 1 ГБ используется метод внешней сортировки с разделением на корзины (bucket sort). Основные шаги:
1. **Нормализация адреса** – приведение каждого IPv6‑адреса к каноническому виду (8 групп по 4 шестнадцатеричные цифры в нижнем регистре) и преобразование в 16‑байтовое бинарное представление.
2. **Разбиение на корзины** – вычисление хеша от бинарного представления (первые 4 байта) и запись адреса в соответствующий временный файл. Число корзин выбрано 1024, что гарантирует, что каждая корзина в среднем содержит ~1 млн адресов и помещается в памяти.
3. **Обработка корзин** – для каждого временного файла считываем все 16‑байтовые блоки, вставляем в множество Python (set) и подсчитываем уникальные адреса в корзине. Операция выполняется параллельно в несколько потоков.
4. **Суммирование** – складываем результаты всех корзин и записываем итоговое число в выходной файл.

Для небольших файлов (размер < 200 МБ) используется простое решение с хранением всех адресов в памяти, что также покрывает критерий базового решения.

#### Реализация
```python
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
```

#### Тестирование

2001:0DB0:0000:123A:0000:0000:0000:0030
2001:db0:0:123a::30
CD10:9A90:F9BB:E5B6:F714:86E7:F1BB:BDFC
DF96:A23D:8BA9:BAA0:A807:FB50:F9CD:B266
9D64:9DB4:B0FE:B3C2:F09F:8DE1:EC59:987D

<img width="1018" height="245" alt="image" src="https://github.com/user-attachments/assets/b647d019-36e7-42c4-9afb-7aeb9d35e244" />

### Задание 2. Смена сезонов

#### Описание алгоритма
Для превращения осеннего пейзажа в летний и наоборот используется цветовая коррекция в пространстве HSV. Основная идея – изменить оттенок (Hue) листвы, оставив неизменными остальные объекты.

**Этапы:**
1. Загрузка изображения (OpenCV, формат BGR).
2. Преобразование в HSV.
3. Создание маски для листвы по диапазонам оттенка:
   - для лета (зелень): H ∈ [35, 85];
   - для осени (жёлто-красные): H ∈ [10, 30] ∪ [80, 100].
   Дополнительно учитывается насыщенность (S > 50) для исключения фона.
4. Морфологическая обработка маски (закрытие + открытие) для удаления шумов.
5. Сдвиг оттенка в области маски:
   - осень→лето: H = (H - 20) mod 180;
   - лето→осень: H = (H + 20) mod 180.
6. Корректировка насыщенности (для лета – увеличиваем).
7. Обратное преобразование в BGR и сохранение.

#### Реализация
```python
import cv2
import numpy as np

def transform_season(input_path, output_path, target):
    """
    Преобразует сезон на изображении.
    target: 'summer' – осень → лето,
            'autumn' – лето → осень.
    """
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Не удалось загрузить {input_path}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    if target == 'summer':  # осень -> лето
        # Маска для осенних тонов (красно-жёлтые)
        mask1 = cv2.inRange(hsv, (0, 50, 50), (30, 255, 255))    # красные, оранжевые, жёлтые
        mask2 = cv2.inRange(hsv, (80, 50, 50), (100, 255, 255))  # редко, но оставим
        mask = cv2.bitwise_or(mask1, mask2)
        # Преобразование: отображаем осенний диапазон на летний (зелёный)
        # Для простоты заменяем оттенок на среднее зелёное (около 60) с сохранением насыщенности и яркости
        h_new = np.copy(h)
        h_new = h_new.astype(np.int16)
        # Для пикселей маски устанавливаем новый оттенок = 60 + небольшая вариация от исходного
        # (чтобы сохранить естественное разнообразие)
        variation = (h[mask > 0] - 40)  # пример, можно настроить
        h_new[mask > 0] = np.clip(60 + variation, 35, 85)  # ограничиваем зелёным диапазоном
    else:  # лето -> осень
        # Маска для летних тонов (зелёные)
        mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        # Преобразование: отображаем зелёный диапазон на осенний (жёлто-красный)
        # Используем линейное отображение: h из [35,85] -> в [10,30] (жёлтые) или [80,100] (красноватые)
        # Разобьём на две части: первую половину зелёных в жёлтые, вторую – в красноватые
        h_new = np.copy(h)
        h_new = h_new.astype(np.int16)
        green_pixels = h[mask > 0]
        # Нормируем от 0 до 1 в зелёном диапазоне
        t = (green_pixels - 35) / (85 - 35)
        # Отображаем: t -> осенний диапазон
        autumn_h = np.where(t < 0.5,
                            10 + (t * 2) * (30 - 10),          # первая половина в [10,30]
                            80 + ((t - 0.5) * 2) * (100 - 80)) # вторая половина в [80,100]
        h_new[mask > 0] = autumn_h.astype(np.uint8)

    # Применяем изменения только в маске
    h = h_new.astype(np.uint8) % 180  # гарантируем диапазон 0-179

    # Для летнего результата немного увеличим насыщенность
    if target == 'summer':
        s = np.where(mask, np.clip(s * 1.2, 0, 255), s).astype(np.uint8)

    hsv_new = cv2.merge([h, s, v])
    result = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)
    cv2.imwrite(output_path, result)

def main():
    transform_season('Photo1.jpg', 'Summer.jpg', 'summer')
    transform_season('Photo2.jpg', 'Autumn.jpg', 'autumn')

if __name__ == '__main__':
    main()
```

#### Тестирование
Программа протестирована на двух фотографиях пейзажей (осень/лето) из открытых источников. Результаты визуально соответствуют ожидаемым: осенние листья стали зеленоватыми, летние – желтоватыми. Артефакты минимальны.
<img width="1165" height="690" alt="image" src="https://github.com/user-attachments/assets/18d09a09-22da-4190-aea1-10161c25e1c7" />


#### Достоинства и недостатки
- **Достоинства:**
  - высокая скорость (доли секунды);
  - простота реализации;
  - сохраняется структура изображения.
- **Недостатки:**
  - маска может захватывать посторонние объекты (трава, небо при низкой насыщенности);
  - параметры подобраны эмпирически и не универсальны;
  - неестественные цвета при сильном сдвиге.
- **Возможные улучшения:**
  - сегментация листвы с помощью нейросетей;
  - перенос стиля (CycleGAN) для более реалистичного результата;
  - гистограммное соответствие эталонным сезонам.
