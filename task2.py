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
