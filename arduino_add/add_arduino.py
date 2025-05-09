import os
import re
import shutil

def main():
    # 讓使用者輸入範圍
    try:
        start_id = int(input("請輸入起始編號 (例如: 1): "))
        end_id = int(input("請輸入結束編號 (例如: 50): "))
        
        if start_id <= 0 or end_id <= 0 or start_id > end_id:
            print("錯誤: 請確保起始編號和結束編號為正數，且起始編號小於或等於結束編號")
            return
    except ValueError:
        print("錯誤: 請輸入有效的數字")
        return

    # 設定Arduino檔案的基本路徑
    base_directory = input("請輸入要存放Arduino檔案的路徑: ")

    # 確認並建立基本路徑（如果不存在）
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
        print(f"已創建路徑: {base_directory}")

    # 原始檔案名稱設為main.ino
    source_file = "main.ino"
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {source_file}")
        return
    except Exception as e:
        print(f"讀取檔案時發生錯誤: {str(e)}")
        return

    # 計數成功創建的檔案
    created_files = 0

    # 在範圍內生成多個Arduino檔案
    for i in range(start_id, end_id + 1):
        device_id = f"A{i}"  # 不要補零，A1、A2…A10、A11… # 格式化裝置ID為Axx格式
        
        # 建立裝置專屬目錄
        device_directory = os.path.join(base_directory, device_id + "_4G")
        if not os.path.exists(device_directory):
            os.makedirs(device_directory)
        
        # 修改裝置ID - 使用更精確的正則表達式，確保只修改DEVICE_ID定義行
        modified_code = re.sub(
            r'#define\s+DEVICE_ID\s+"A\d+"', 
            f'#define DEVICE_ID "{device_id}"', 
            source_code
        )
        
        # 檢查修改是否成功
        if modified_code == source_code and "#define DEVICE_ID" in source_code:
            print(f"警告: 無法使用正則表達式修改裝置ID定義，嘗試直接替換...")
            # 嘗試直接查找並替換，不使用正則表達式
            modified_code = source_code.replace('#define DEVICE_ID "A27"', f'#define DEVICE_ID "{device_id}"')
            
            # 再次檢查修改是否成功
            if modified_code == source_code:
                print(f"警告: 無法在檔案中找到或修改裝置ID定義，檔案可能未被正確修改！")
        
        # 創建新的Arduino檔案
        arduino_file = os.path.join(device_directory, device_id + "_4G.ino")
        
        try:
            # 寫入檔案，確保特殊字元維持原樣
            with open(arduino_file, 'w', encoding='utf-8', newline='') as f:
                f.write(modified_code)
            
            print(f"已創建 {arduino_file} (裝置ID: {device_id})")
            created_files += 1
        except Exception as e:
            print(f"創建檔案 {arduino_file} 時發生錯誤: {str(e)}")

    print(f"\n完成! 已成功創建 {created_files} 個Arduino檔案。")
    print(f"檔案儲存於: {base_directory}")

if __name__ == "__main__":
    main()