import os
import glob

def check_all_files():
    inlet_dir = r"E:\PY\research\0520\智慧水务资料\3.数据端\2026.1-4月小时数据\进口"
    outlet_dir = r"E:\PY\research\0520\智慧水务资料\3.数据端\2026.1-4月小时数据\出口"
    
    inlet_files = sorted(glob.glob(os.path.join(inlet_dir, "*.xls")))
    outlet_files = sorted(glob.glob(os.path.join(outlet_dir, "*.xls")))
    
    print(f"Total inlet files: {len(inlet_files)}")
    print(f"Total outlet files: {len(outlet_files)}")
    
    inlet_basenames = [os.path.basename(f) for f in inlet_files]
    outlet_basenames = [os.path.basename(f) for f in outlet_files]
    
    if inlet_basenames == outlet_basenames:
        print("Inlet and Outlet file names match exactly.")
    else:
        print("Mismatch between inlet and outlet file names.")
        
    print("Inlet files sample (first 10):", inlet_basenames[:10])
    print("Inlet files sample (last 10):", inlet_basenames[-10:])

if __name__ == "__main__":
    check_all_files()
