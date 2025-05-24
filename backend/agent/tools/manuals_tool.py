from agentpress.tool import ToolResult, openapi_schema, xml_schema, XMLNodeMapping
from agent.tools.sb_files_tool import SandboxFilesTool
from utils.files_utils import should_exclude_file, clean_path
from agentpress.thread_manager import ThreadManager
from utils.logger import logger
from services.supabase import SupabaseService
from typing import List, Dict, Any, Optional
import os
import json
import logging
import re
import inspect

logger = logging.getLogger(__name__)

class ManualsTool(SandboxFilesTool):
    """Tool for accessing manual PDFs from Supabase storage."""

    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.supabase = SupabaseService()
        self.bucket = 'manuals'
        # No local/manual sync logic
        self.product_manual_cache = {}

    def _extract_category_from_path(self, rel_path: str) -> str:
        parts = rel_path.split('/')
        parts = [p for p in parts if p and not p.lower().endswith('.pdf') and not p.lower().endswith('.txt')]
        if not parts:
            return 'Uncategorized'
        return ' > '.join(parts)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_manuals",
            "description": "List all available PDF manuals in the central manuals repository",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="list_manuals",
        mappings=[],
        example="<list_manuals></list_manuals>"
    )
    async def list_manuals(self) -> ToolResult:
        try:
            client = await self.supabase.db_connection.client
            all_files = []
            limit = 100
            offset = 0
            while True:
                res = await client.storage.from_(self.bucket).list('originals', {"limit": limit, "offset": offset})
                if hasattr(res, 'error') and res.error:
                    raise Exception(res.error.message)
                files = res.data if hasattr(res, 'data') else res
                if not isinstance(files, list):
                    raise Exception(f"Unexpected response type from Supabase: {type(files)} - {files}")
                if not files:
                    break
                all_files.extend(files)
                if len(files) < limit:
                    break
                offset += limit
            manuals = []
            for file in all_files:
                if not file['name'].lower().endswith('.pdf'):
                    continue
                manuals.append({
                    'name': file['name'],
                    'path': f"originals/{file['name']}",
                    'size': file['metadata']['size'] if 'metadata' in file and 'size' in file['metadata'] else file.get('size', 0),
                    'modified': file.get('updated_at', ''),
                    'category': self._extract_category_from_path(file['name'])
                })
            return ToolResult(success=True, output=json.dumps({
                'manuals': manuals,
                'message': f"Found {len(manuals)} manuals."
            }))
        except Exception as e:
            logger.error(f"Error listing manuals: {e}")
            return ToolResult(success=False, output=json.dumps({
                'manuals': [],
                'message': f"Error listing manuals: {str(e)}"
            }))

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "find_product_manual",
            "description": "Find which manual contains information about a specific product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to search for"
                    },
                    "refresh_cache": {
                        "type": "boolean",
                        "description": "Whether to refresh the cached mapping",
                        "default": False
                    }
                },
                "required": ["product_name"]
            }
        }
    })
    @xml_schema(
        tag_name="find_product_manual",
        mappings=[
            {
                "param_name": "product_name",
                "node_type": "element",
                "path": "product_name"
            },
            {
                "param_name": "refresh_cache",
                "node_type": "element",
                "path": "refresh_cache",
                "required": False
            }
        ],
        example="<find_product_manual><product_name>Pump XYZ</product_name></find_product_manual>"
    )
    async def find_product_manual(self, product_name: str, refresh_cache: bool = False) -> ToolResult:
        try:
            # Search all extracted text files for the product name
            client = await self.supabase.db_connection.client
            res = await client.storage.from_(self.bucket).list('extracted')
            if hasattr(res, 'error') and res.error:
                raise Exception(res.error.message)
            files = res.data if hasattr(res, 'data') else res
            if not isinstance(files, list):
                raise Exception(f"Unexpected response type from Supabase: {type(files)} - {files}")
            matches = []
            for file in files:
                if not file['name'].lower().endswith('.txt'):
                    continue
                # Download the extracted text
                txt_path = f"extracted/{file['name']}"
                txt_file = await client.storage.from_(self.bucket).download(txt_path)
                if hasattr(txt_file, 'error') and txt_file.error:
                    continue
                # Handle bytes directly since Supabase returns bytes
                if isinstance(txt_file, bytes):
                    text = txt_file.decode('utf-8', errors='ignore')
                else:
                    # Fallback for other response types
                    text = (await txt_file.read()).decode('utf-8', errors='ignore')
                if re.search(re.escape(product_name), text, re.IGNORECASE):
                    matches.append({
                        'manual': file['name'].replace('.txt', '.pdf'),
                        'path': f"originals/{file['name'].replace('.txt', '.pdf')}",
                        'match': True
                    })
            return ToolResult(success=True, output=json.dumps({
                'manuals': matches,
                'message': f"Found {len(matches)} manuals containing '{product_name}'."
            }))
        except Exception as e:
            logger.error(f"Error finding product manual: {e}")
            return ToolResult(success=False, output=json.dumps({
                'manuals': [],
                'message': f"Error finding product manual: {str(e)}"
            }))

    async def fetch_manuals_from_supabase(self):
        # No-op: all access is now direct from Supabase
        logger.info("fetch_manuals_from_supabase is a no-op (Supabase is source of truth)")
        return

    async def _build_product_manual_cache(self) -> None:
        # No-op: cache not needed, always fetch live from Supabase
        logger.info("_build_product_manual_cache is a no-op (Supabase is source of truth)")
        return

    async def _search_pdf_contents(self, search_term: str) -> List[Dict[str, Any]]:
        # Search all extracted text files for the search term
        try:
            client = await self.supabase.db_connection.client
            res = await client.storage.from_(self.bucket).list('extracted')
            if hasattr(res, 'error') and res.error:
                raise Exception(res.error.message)
            files = res.data if hasattr(res, 'data') else res
            if not isinstance(files, list):
                raise Exception(f"Unexpected response type from Supabase: {type(files)} - {files}")
            results = []
            for file in files:
                if not file['name'].lower().endswith('.txt'):
                    continue
                txt_path = f"extracted/{file['name']}"
                txt_file = await client.storage.from_(self.bucket).download(txt_path)
                if hasattr(txt_file, 'error') and txt_file.error:
                    continue
                # Handle bytes directly since Supabase returns bytes
                if isinstance(txt_file, bytes):
                    text = txt_file.decode('utf-8', errors='ignore')
                else:
                    # Fallback for other response types
                    text = (await txt_file.read()).decode('utf-8', errors='ignore')
                matches = [m for m in re.finditer(re.escape(search_term), text, re.IGNORECASE)]
                if matches:
                    results.append({
                        'manual': file['name'].replace('.txt', '.pdf'),
                        'path': f"originals/{file['name'].replace('.txt', '.pdf')}",
                        'matches': [
                            {
                                'start': m.start(),
                                'end': m.end(),
                                'context': text[max(0, m.start()-40):m.end()+40]
                            } for m in matches
                        ]
                    })
            return results
        except Exception as e:
            logger.error(f"Error searching PDF contents: {e}")
            return []

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "extract_manual_content",
            "description": "Extract the content of a manual or specific pages",
            "parameters": {
                "type": "object",
                "properties": {
                    "manual_name": {
                        "type": "string",
                        "description": "Name of the manual to extract content from"
                    },
                    "page_range": {
                        "type": "string",
                        "description": "Page range to extract (e.g., '1-5'). If not provided, extracts the first 3 pages.",
                        "default": "1-3"
                    }
                },
                "required": ["manual_name"]
            }
        }
    })
    async def extract_manual_content(self, manual_name: str, page_range: str = "1-3") -> ToolResult:
        try:
            # Download extracted text from Supabase
            txt_path = f"extracted/{manual_name.replace('.pdf', '.txt')}"
            pdf_path = f"originals/{manual_name}"
            client = await self.supabase.db_connection.client
            txt_file = await client.storage.from_(self.bucket).download(txt_path)
            if hasattr(txt_file, 'error') and txt_file.error:
                raise Exception(txt_file.error.message)
            # Handle bytes directly since Supabase returns bytes
            if isinstance(txt_file, bytes):
                text = txt_file.decode('utf-8', errors='ignore')
            else:
                # Fallback for other response types
                text = (await txt_file.read()).decode('utf-8', errors='ignore')
            return ToolResult(success=True, output=json.dumps({
                'content': {
                    'manual_name': manual_name,
                    'extracted_text': text,
                    'pdf_url': await self._get_public_url(pdf_path),
                    'txt_url': await self._get_public_url(txt_path)
                },
                'message': f"Extracted content for {manual_name}"
            }))
        except Exception as e:
            logger.error(f"Error extracting manual content: {e}")
            return ToolResult(success=False, output=json.dumps({
                'content': {},
                'message': f"Error extracting manual content: {str(e)}"
            }))

    async def _get_public_url(self, path: str) -> str:
        client = await self.supabase.db_connection.client
        res = await client.storage.from_(self.bucket).create_signed_url(path, 60*60*24)  # 24h
        if hasattr(res, 'error') and res.error:
            logger.error(f"Error getting public url for {path}: {res.error.message}")
            return ''
        return res.signed_url if hasattr(res, 'signed_url') else ''

    def _sync_manuals_to_sandbox(self):
        # No-op: all access is now direct from Supabase
        logger.info("_sync_manuals_to_sandbox is a no-op (Supabase is source of truth)")
        return

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "extract_manual_images",
            "description": "Extract all images from a manual PDF and return their URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manual_name": {
                        "type": "string",
                        "description": "Name of the manual PDF to extract images from"
                    }
                },
                "required": ["manual_name"]
            }
        }
    })
    @xml_schema(
        tag_name="extract_manual_images",
        mappings=[
            {"param_name": "manual_name", "node_type": "element", "path": "manual_name"}
        ],
        example="<extract_manual_images><manual_name>Bioliff Airblowers.pdf</manual_name></extract_manual_images>"
    )
    async def extract_manual_images(self, manual_name: str) -> ToolResult:
        try:
            import fitz  # PyMuPDF
            from io import BytesIO
            client = await self.supabase.db_connection.client
            pdf_path = f"originals/{manual_name}"
            pdf_file = await client.storage.from_(self.bucket).download(pdf_path)
            # Robustly convert to bytes
            pdf_bytes = None
            try:
                if isinstance(pdf_file, bytes):
                    pdf_bytes = pdf_file
                elif hasattr(pdf_file, 'read'):
                    read_method = pdf_file.read
                    if inspect.iscoroutinefunction(read_method):
                        data = await read_method()
                    else:
                        data = read_method()
                    # If data is BytesIO, get the value
                    if isinstance(data, BytesIO):
                        pdf_bytes = data.getvalue()
                    elif isinstance(data, bytes):
                        pdf_bytes = data
                    else:
                        raise TypeError(f"Unknown data type from .read(): {type(data)}")
                elif isinstance(pdf_file, BytesIO):
                    pdf_bytes = pdf_file.getvalue()
                else:
                    raise TypeError(f"Unknown pdf_file type: {type(pdf_file)}")
            except Exception as e:
                logger.error(f"Error converting pdf_file to bytes: {e}")
                raise
            logger.debug(f"PDF bytes type: {type(pdf_bytes)}, size: {len(pdf_bytes) if pdf_bytes else 'N/A'}")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            image_urls = []
            for i, page in enumerate(doc):
                images = page.get_images(full=True)
                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_name = f"img_{i}_{img_index}.{image_ext}"
                    image_path = f"extracted_images/{manual_name}/{image_name}"
                    upload_res = await client.storage.from_(self.bucket).upload(image_path, BytesIO(image_bytes), file_options={"upsert": "true"})
                    if hasattr(upload_res, 'error') and upload_res.error:
                        continue
                    url_res = await client.storage.from_(self.bucket).create_signed_url(image_path, 60*60*24)
                    if hasattr(url_res, 'error') and url_res.error:
                        continue
                    image_url = url_res.signed_url if hasattr(url_res, 'signed_url') else ''
                    if image_url:
                        image_urls.append(image_url)
            return ToolResult(success=True, output=json.dumps({
                'images': image_urls,
                'message': f"Extracted {len(image_urls)} images from {manual_name}."
            }))
        except Exception as e:
            logger.error(f"Error extracting images from manual: {e}")
            return ToolResult(success=False, output=json.dumps({
                'images': [],
                'message': f"Error extracting images: {str(e)}"
            }))

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "extract_text_from_pdf",
            "description": "Extract all text from a manual PDF and return it as a string. Optionally uploads the extracted text as a .txt file to storage for caching.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manual_name": {
                        "type": "string",
                        "description": "Name of the manual PDF to extract text from"
                    }
                },
                "required": ["manual_name"]
            }
        }
    })
    @xml_schema(
        tag_name="extract_text_from_pdf",
        mappings=[
            {"param_name": "manual_name", "node_type": "element", "path": "manual_name"}
        ],
        example="<extract_text_from_pdf><manual_name>Bioliff Airblowers.pdf</manual_name></extract_text_from_pdf>"
    )
    async def extract_text_from_pdf(self, manual_name: str) -> ToolResult:
        try:
            import fitz  # PyMuPDF
            from io import BytesIO
            client = await self.supabase.db_connection.client
            pdf_path = f"originals/{manual_name}"
            pdf_file = await client.storage.from_(self.bucket).download(pdf_path)
            # Robustly convert to bytes
            pdf_bytes = None
            try:
                if isinstance(pdf_file, bytes):
                    pdf_bytes = pdf_file
                elif hasattr(pdf_file, 'read'):
                    read_method = pdf_file.read
                    if inspect.iscoroutinefunction(read_method):
                        data = await read_method()
                    else:
                        data = read_method()
                    # If data is BytesIO, get the value
                    if isinstance(data, BytesIO):
                        pdf_bytes = data.getvalue()
                    elif isinstance(data, bytes):
                        pdf_bytes = data
                    else:
                        raise TypeError(f"Unknown data type from .read(): {type(data)}")
                elif isinstance(pdf_file, BytesIO):
                    pdf_bytes = pdf_file.getvalue()
                else:
                    raise TypeError(f"Unknown pdf_file type: {type(pdf_file)}")
            except Exception as e:
                logger.error(f"Error converting pdf_file to bytes: {e}")
                raise
            logger.debug(f"PDF bytes type: {type(pdf_bytes)}, size: {len(pdf_bytes) if pdf_bytes else 'N/A'}")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            txt_path = f"extracted/{manual_name.replace('.pdf', '.txt')}"
            await client.storage.from_(self.bucket).upload(txt_path, BytesIO(text.encode("utf-8")), file_options={"upsert": "true"})
            return ToolResult(success=True, output=json.dumps({
                'text': text,
                'message': f"Extracted text from {manual_name}."
            }))
        except Exception as e:
            logger.error(f"Error extracting text from manual: {e}")
            return ToolResult(success=False, output=json.dumps({
                'text': '',
                'message': f"Error extracting text: {str(e)}"
            }))
