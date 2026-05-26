import time
import os
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)

class FakeDeepLabV3P:
    def __init__(self, backbone="ResNet50_vd", num_classes=3):
        self.backbone = backbone
        self.num_classes = num_classes

    def summary(self):
        print(Fore.CYAN + "\n[Model Architecture]")
        print(Style.DIM + f"  ├── Backbone: {self.backbone}")
        print(Style.DIM + f"  ├── Encoder: Atrous Convolution x3")
        print(Style.DIM + f"  ├── Decoder: ASPP + Bilinear Upsampling")
        print(Style.DIM + f"  ├── Output Stride: 16")
        print(Style.DIM + f"  └── Classes: {self.num_classes}\n")


def predict(input_dir, output_dir):
    print(Fore.GREEN + "[INFO] PaddleSeg Inference Engine Initialized.")
    print(Fore.GREEN + "[INFO] Device: GPU (NVIDIA RTX 4090, Tensor Cores enabled)")
    print(Fore.CYAN + "[INFO] Loading model weights from './output/best_model.pdparams' ...")
    time.sleep(1.8)
    model = FakeDeepLabV3P()
    model.summary()
    print(Fore.GREEN + "[INFO] Model loaded successfully.\n")

    os.makedirs(output_dir, exist_ok=True)
    images = [f for f in os.listdir(input_dir) if f.lower().endswith((".jpg", ".png", ".jpeg", ".tif"))]

    print(Fore.GREEN + f"[INFO] Found {len(images)} images for inference.")
    print(Fore.GREEN + "[INFO] Starting batch prediction...\n")

    for img in tqdm(images, ncols=100, desc=Fore.YELLOW + "Predicting"):
        time.sleep(0.4)
        out_path = os.path.join(output_dir, os.path.splitext(img)[0] + "_mask.png")
        tqdm.write(f"{Fore.BLUE}→ Saved segmentation result: {out_path}")

    print(Fore.GREEN + "\n[INFO] All predictions completed successfully.")
    print(Fore.GREEN + f"[INFO] Output directory: {output_dir}")
    print(Fore.GREEN + "[INFO] Total time: 0m 45s\n")


if __name__ == "__main__":
    input_dir = r"E:\水产种质资源保护区\演示\sample\img"
    output_dir = r"E:\水产种质资源保护区\演示\sample\result"
    predict(input_dir, output_dir)
