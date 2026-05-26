import fitz  # PyMuPDF
import os
# import fitz
print(fitz.__doc__)

def compress_pdf(input_path, output_path, dpi=100):
    # 打开原始 PDF
    doc = fitz.open(input_path)

    # 创建一个新的 PDF 文档用于输出
    new_pdf = fitz.open()

    for page in doc:
        # 将每页作为图像重新渲染
        pix = page.get_pixmap(dpi=dpi, alpha=False)  # 你可以调低 dpi 来降低质量

        # 将图像插入到新文档中
        img_pdf = fitz.open("pdf", pix.tobytes("jpeg"))
        new_pdf.insert_pdf(img_pdf)

    # 保存压缩后的 PDF
    new_pdf.save(output_path, deflate=True, compress=True)
    new_pdf.close()
    doc.close()

    # 打印结果大小
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"✅ 压缩后文件大小：{size_mb:.2f} MB")


# 使用示例
input_pdf = r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-07\五维2024年度审计报告.pdf"
output_pdf = r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-07\五维2024年度审计报告压缩.pdf"
compress_pdf(input_pdf, output_pdf, dpi=100)  # dpi 可调，如 80、72 进一步压缩
