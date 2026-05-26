import os
import sys
import signal
import paddle

def handle_signal(signum, frame):
    print(f"\n[!] 捕获到信号 {signum}，可能是底层C++崩溃")
    sys.exit(1)

for sig in (signal.SIGABRT, signal.SIGSEGV, signal.SIGILL):
    signal.signal(sig, handle_signal)

print("CUDA version:", paddle.version.cuda())
print("cuDNN version:", paddle.version.cudnn())

paddle.utils.run_check()
