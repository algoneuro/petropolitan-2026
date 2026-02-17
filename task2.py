import cv2
import numpy as np

def transform_season(input_path, output_path, target):
    """
    target: 'summer' (осень→лето) или 'autumn' (лето→осень)
    """
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Не удалось загрузить {input_path}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    if target == 'summer':  # осень -> лето
        # маска для осенних тонов
        mask1 = cv2.inRange(hsv, (10, 50, 50), (30, 255, 255))
        mask2 = cv2.inRange(hsv, (80, 50, 50), (100, 255, 255))
        mask = cv2.bitwise_or(mask1, mask2)
        shift = -20
    else:  # лето -> осень
        mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        shift = 20

    # морфологическая обработка
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # сдвиг оттенка
    h = h.astype(np.int16)
    h = np.where(mask, (h + shift) % 180, h)
    h = h.astype(np.uint8)

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
