import os
import glob
import win32com.client
import pandas as pd
import numpy as np

def consolidate_files():
    inlet_dir = r"E:\PY\research\0520\智慧水务资料\3.数据端\2026.1-4月小时数据\进口"
    outlet_dir = r"E:\PY\research\0520\智慧水务资料\3.数据端\2026.1-4月小时数据\出口"
    scratch_dir = r"E:\PY\research\0520\智慧水务资料\scratch"
    os.makedirs(scratch_dir, exist_ok=True)
    
    inlet_files = sorted(glob.glob(os.path.join(inlet_dir, "*.xls")))
    outlet_files = sorted(glob.glob(os.path.join(outlet_dir, "*.xls")))
    
    # Column mapping
    columns = [
        'index_no', 'time', 
        'COD_conc', 'COD_limit', 'COD_load',
        'NH3N_conc', 'NH3N_limit', 'NH3N_load',
        'TP_conc', 'TP_limit', 'TP_load',
        'TN_conc', 'TN_limit', 'TN_load',
        'pH', 'temp', 'flow',
        'flag_auto', 'flag_manual'
    ]
    
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        # We will temporary save as this path
        temp_csv = os.path.join(scratch_dir, "temp_convert.csv")
        
        def process_folder(files, label):
            all_dfs = []
            for idx, fpath in enumerate(files):
                if idx % 20 == 0:
                    print(f"Processing {label}: {idx}/{len(files)}...")
                try:
                    wb = excel.Workbooks.Open(fpath)
                    wb.SaveAs(temp_csv, FileFormat=6) # 6 is xlCSV
                    wb.Close(SaveChanges=False)
                    
                    # Read csv
                    df = pd.read_csv(temp_csv, encoding='gbk', skiprows=2, header=None)
                    if df.shape[1] >= len(columns):
                        df = df.iloc[:, :len(columns)]
                        df.columns = columns
                        # Drop rows where 'time' is null or looks like headers
                        df = df.dropna(subset=['time'])
                        # Convert data columns to numeric
                        for col in ['COD_conc', 'NH3N_conc', 'TP_conc', 'TN_conc', 'pH', 'temp', 'flow']:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        all_dfs.append(df)
                except Exception as e:
                    print(f"Error processing file {fpath}: {e}")
            
            if all_dfs:
                consolidated = pd.concat(all_dfs, ignore_index=True)
                # Sort by time
                consolidated['time'] = pd.to_datetime(consolidated['time'], errors='coerce')
                consolidated = consolidated.dropna(subset=['time']).sort_values('time').reset_index(drop=True)
                return consolidated
            return pd.DataFrame()

        print("Starting Inlet processing...")
        inlet_df = process_folder(inlet_files, "Inlet")
        inlet_out_path = os.path.join(scratch_dir, "inlet_consolidated.csv")
        inlet_df.to_csv(inlet_out_path, index=False, encoding='utf-8-sig')
        print(f"Saved Inlet consolidated to {inlet_out_path}, shape: {inlet_df.shape}")
        
        print("Starting Outlet processing...")
        outlet_df = process_folder(outlet_files, "Outlet")
        outlet_out_path = os.path.join(scratch_dir, "outlet_consolidated.csv")
        outlet_df.to_csv(outlet_out_path, index=False, encoding='utf-8-sig')
        print(f"Saved Outlet consolidated to {outlet_out_path}, shape: {outlet_df.shape}")
        
        # Delete temp csv
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            
        # Write basic summary statistics to a file
        summary_path = os.path.join(scratch_dir, "data_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as sf:
            sf.write("=== DATA CONSOLIDATION SUMMARY ===\n\n")
            sf.write(f"Total rows in Inlet: {inlet_df.shape[0]}\n")
            sf.write(f"Inlet Time Range: {inlet_df['time'].min()} to {inlet_df['time'].max()}\n\n")
            sf.write("Inlet Describe:\n")
            sf.write(inlet_df.describe().to_string())
            sf.write("\n\n" + "="*40 + "\n\n")
            sf.write(f"Total rows in Outlet: {outlet_df.shape[0]}\n")
            sf.write(f"Outlet Time Range: {outlet_df['time'].min()} to {outlet_df['time'].max()}\n\n")
            sf.write("Outlet Describe:\n")
            sf.write(outlet_df.describe().to_string())
            
        print(f"Saved summary statistics to {summary_path}")
        
    except Exception as e:
        print(f"Global error: {e}")
    finally:
        if excel:
            excel.Quit()

if __name__ == "__main__":
    consolidate_files()
