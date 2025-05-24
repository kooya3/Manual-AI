import os
import subprocess
import sys
import asyncio
from datetime import datetime
from services.supabase import SupabaseService
from utils.logger import logger

sys.path.append('/home/elyees/Davin-n-Shirtliff/Agent/suna/backend')

def process_and_upload_manuals(files):
    """
    Process and upload PDF manuals to Supabase storage.
    
    Args:
        files: List of file paths to PDF manuals to process
    """
    supabase = SupabaseService()

    async def process_file(file_path):
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
            
        if not file_path.lower().endswith('.pdf'):
            logger.error(f"Not a PDF file: {file_path}")
            return

        # Create temporary file for extracted text
        extracted_text_path = os.path.join('/tmp', os.path.basename(file_path).replace('.pdf', '.txt'))

        # Extract text using pdftotext
        try:
            subprocess.run(['pdftotext', file_path, extracted_text_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return

        # Upload original PDF
        try:
            with open(file_path, 'rb') as pdf_file:
                await supabase.upload_file(
                    bucket='manuals',
                    path=f'originals/{os.path.basename(file_path)}',
                    file=pdf_file,
                    content_type='application/pdf'  # Ensure correct MIME type
                )
        except Exception as e:
            logger.error(f"Failed to upload original PDF {file_path}: {e}")
            return

        # Upload extracted text
        try:
            with open(extracted_text_path, 'rb') as text_file:
                await supabase.upload_file(bucket='manuals', path=f'extracted/{os.path.basename(extracted_text_path)}', file=text_file)
        except Exception as e:
            logger.error(f"Failed to upload extracted text for {file_path}: {e}")
            return

        # Update metadata
        try:
            original_pdf_storage_path = f'originals/{os.path.basename(file_path)}'
            extracted_text_storage_path = f'extracted/{os.path.basename(extracted_text_path)}'

            row_data = {
                'name': os.path.basename(file_path), # Matches 'name' column in 'manuals' table
                'size': os.path.getsize(file_path),   # Size of the original PDF
                'upload_date': datetime.now().isoformat(), # ISO format for TIMESTAMP
                'metadata': { # Data for the JSONB 'metadata' column
                    'original_pdf_storage_path': original_pdf_storage_path,
                    'extracted_text_storage_path': extracted_text_storage_path,
                    'original_file_type': 'application/pdf',
                    'extracted_file_type': 'text/plain',
                }
            }
            await supabase.insert_metadata('manuals', row_data)
        except Exception as e:
            logger.error(f"Failed to update metadata for {file_path}: {e}")

    async def process_files():
        semaphore = asyncio.Semaphore(4)  # Limit to 4 concurrent uploads

        async def sem_task(file_path):
            async with semaphore:
                await process_file(file_path)

        tasks = [sem_task(file_path) for file_path in files]
        await asyncio.gather(*tasks)

    asyncio.run(process_files())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process and upload PDF manuals to Supabase')
    parser.add_argument('files', nargs='+', help='PDF files to process and upload')
    
    args = parser.parse_args()
    
    # Validate all files exist and are PDFs before starting
    valid_files = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue
            
        if not file_path.lower().endswith('.pdf'):
            logger.error(f"Not a PDF file: {file_path}")
            continue
            
        valid_files.append(file_path)
    
    if not valid_files:
        logger.error("No valid PDF files provided")
        sys.exit(1)
        
    process_and_upload_manuals(valid_files)
