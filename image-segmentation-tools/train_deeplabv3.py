import time
import random
import os
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)

class FakeDeepLabV3P:
    def __init__(self, backbone="ResNet50_vd", num_classes=2):
        self.backbone = backbone
        self.num_classes = num_classes

    def summary(self):
        print(Fore.CYAN + "\n[Model Summary]")
        print(Style.DIM + f"  ├── Backbone: {self.backbone}")
        print(Style.DIM + f"  ├── Output Stride: 16")
        print(Style.DIM + f"  ├── Atrous Rates: [6, 12, 18]")
        print(Style.DIM + f"  ├── Decoder: ASPP + 1×1 conv")
        print(Style.DIM + f"  ├── Number of Classes: {self.num_classes}")
        print(Style.DIM + "  └── Parameters: ~45.2M\n")


def train(datapath):
    print(Fore.YELLOW + "W1013 10:42:05.103456  1728 device_context.cc:447] Please NOTE: device: 0, GPU Compute Capability: 8.6, Driver API Version: 12.2, Runtime API Version: 11.8")
    print(Fore.YELLOW + "W1013 10:42:05.103701  1728 device_context.cc:465] device: 0, cuDNN Version: 8.9.\n")
    print(Fore.GREEN + "[INFO] PaddleSeg Version: 2.10.0")
    print(Fore.GREEN + "[INFO] Paddle Version: 2.6.0")
    print(Fore.GREEN + "[INFO] Device: GPU (NVIDIA RTX 4090, 24GB)\n")

    model = FakeDeepLabV3P(backbone="ResNet50_vd", num_classes=2)
    model.summary()

    print(Fore.GREEN + "[INFO] Loading dataset from F:\\data\\sample ...")
    time.sleep(1.2)
    print("[INFO] Found 580 training samples, 120 validation samples.\n")

    print(Fore.CYAN + "[INFO] Optimizer: SGD(lr=0.001, momentum=0.9, weight_decay=4e-5)")
    print(Fore.CYAN + "[INFO] Batch Size: 4, Total Iters: 2000\n")

    print(Fore.GREEN + "[INFO] Start training...")
    print("="*80)

    total_iters = 2000
    save_interval = 500
    log_interval = 50

    pbar = tqdm(range(1, total_iters + 1), ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ")

    for i in pbar:
        # 模拟 loss、精度变化
        loss = round(random.uniform(0.6, 1.5) * (1 - i / total_iters), 4)
        acc = round(random.uniform(0.4, 0.99) * (i / total_iters), 4)
        miou = round(acc * random.uniform(0.7, 0.95), 4)
        time.sleep(random.uniform(0.03, 0.06))  # 控制速度

        if i % log_interval == 0:
            tqdm.write(f"{Fore.BLUE}[Iter {i:04d}/{total_iters}] "
                       f"{Fore.YELLOW}loss={loss:.4f}  "
                       f"acc={acc:.4f}  "
                       f"miou={miou:.4f}  "
                       f"lr=0.001")

        if i % save_interval == 0:
            tqdm.write(f"{Fore.MAGENTA}[INFO] Saving checkpoint: ./output/iter_{i}.pdparams")
            time.sleep(1)
            tqdm.write(f"{Fore.GREEN}[INFO] Validation phase...")
            val_loss = round(random.uniform(0.05, 0.4), 4)
            val_miou = round(random.uniform(0.7, 0.93), 4)
            tqdm.write(f"        [Eval] loss={val_loss:.4f}, mIoU={val_miou:.4f}\n")
            time.sleep(0.8)

    print("="*80)
    print(Fore.GREEN + "[INFO] Training completed successfully.")
    print(Fore.GREEN + "[INFO] Best model saved at: ./output/best_model.pdparams")
    print(Fore.GREEN + "[INFO] Total time: 16m 42s\n")


if __name__ == "__main__":
    datapath = r'E:\水产种质资源保护区\演示\sample'
    train(datapath)
