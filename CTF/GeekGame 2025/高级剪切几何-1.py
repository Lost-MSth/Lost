import io
import os

import numpy as np
import torch
from PIL import Image, ImageFilter

from clip_classifier import Classifier

# Huggingface 镜像
# $env:HF_ENDPOINT = "https://hf-mirror.com"

# PATH = 'flag2_images/'
# IMG_NUM = 1344
PATH = 'flag1_images/'
IMG_NUM = 1416


def classify_image(classifier, images):
    # memory limitation, so batch size = 64
    batch_size = 64
    results = []
    for i in range(0, len(images), batch_size):
        image_batch = images[i:i + batch_size]

        # 1. Preprocess the image(s) to get the required tensor
        pixel_values = classifier.preprocess(image_batch)
        # print(f"\nImage tensor shape after preprocessing: {pixel_values.shape}")

        logits = classifier(pixel_values)

        logits_cpu = logits.cpu().detach()

        print(f"Logits (cat=0, dog=1): {logits_cpu.numpy()}")

        # Determine the predicted class
        predicted_indices = torch.argmax(logits_cpu, dim=1).numpy()
        for idx in predicted_indices:
            predicted_label = ["cat", "dog"][idx]
            print(f"Predicted class: {predicted_label} ({idx})")

        results.extend(predicted_indices.tolist())

    return results


def bit_to_byte(results):
    ans = bytearray()
    for i in range(0, len(results), 8):
        x = results[i:i+8][::-1]
        number = 0
        for bit in x:
            number = (number << 1) | bit
        ans.append(number)
    return ans


def main():

    classifier = Classifier()
    print(f"Classifier is running on device: {classifier.device}")

    images = []
    blurred_images = []

    for i in range(IMG_NUM):
        image_path = os.path.join(PATH, f"{i}.png")
        with Image.open(image_path) as image:
            image = image.convert('RGB')
            # blurred_image = image.filter(ImageFilter.GaussianBlur(radius=1))
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=25)
            blurred_image = Image.open(output)
            images.append(image)
            blurred_images.append(blurred_image)

    print("Classifying original images:")
    results = classify_image(classifier, images)
    print("Classifying blurred images:")
    blurred_results = classify_image(classifier, blurred_images)

    # print overall results
    print("\nOverall Results:")
    print(results)
    print("\nOverall Results (Blurred):")
    print(blurred_results)
    # bits to bytes
    print(len(results))

    hint = bit_to_byte(results)
    print(bytes(hint))
    print(hint.decode('utf-8', errors='ignore'))

    # 对比模糊前后的结果，相同为 0，不同为 1
    diff_results = []
    for r1, r2 in zip(results, blurred_results):
        diff_results.append(0 if r1 == r2 else 1)

    print("\nDifference Results:")
    print(diff_results)
    ans = bit_to_byte(diff_results)
    print(bytes(ans))
    print(ans.decode('utf-8', errors='ignore'))


if __name__ == '__main__':
    main()
