# Manual Agent for Manuals Access

Suna now includes a Manual Agent that provides centralized access to PDF manuals across all chat instances and projects. This feature allows you to upload product manuals and documentation to a shared location, making it accessible to agents working on any project.

## Features

- **Cloud-based Manual Storage**: All manuals are securely stored in Supabase cloud storage
- **Product Lookup**: Find which manual contains information about a specific product
- **Content Extraction**: Extract and search through manual content
- **Cross-Project Access**: Access manuals from any chat project via Supabase storage
- **Versioning and Backup**: Automatic versioning and backup of manuals through Supabase

## How to Use

### Setup

1. Upload PDF manuals using one of these methods:
   - Use the web interface to upload individual manuals
   - Use the batch upload script for multiple manuals:
     ```bash
     python backend/utils/scripts/batch_process_manuals.py file1.pdf file2.pdf ...
     ```
2. The system will automatically:
   - Extract text content from PDFs
   - Store both PDF and text in Supabase storage
   - Index the content for searching
   - Update the metadata database

### Agent Commands

The Manual Agent supports the following operations:

- **List all manuals**:
  - `list_manuals`: Shows all available manuals in the repository

- **Find a manual for a specific product**:
  - `find_product_manual`: Searches for which manual contains information about a given product
  - Example: "Which manual contains information about the Dayliff XL-5000 pump?"

- **Extract content from a manual**:
  - `extract_manual_content`: Extract content from a specific manual, optionally limiting to specific pages
  - Example: "Show me the installation instructions from the Dayliff XL-5000 manual"

### Example Prompts

- "List all the manuals available in the repository"
- "Find the manual that contains information about Dayliff SQ-Series pumps"
- "Extract pages 2-5 from the Dayliff XL-5000 manual"
- "Search for 'troubleshooting' in the SQ-Series solar pump manual"

## Technical Implementation

The manuals feature is implemented as a custom tool (`ManualsFileTool`) that extends the standard `SandboxFilesTool`. It provides specialized functions for accessing, searching, and extracting content from PDF manuals stored in a shared volume.

### Directory Structure

- `/manuals`: Root directory containing all PDF manuals
  - Mounted as a volume to all Suna containers
  - Accessible by all projects and chat instances

### Advanced Features

- **Automatic indexing**: The system automatically indexes product information from manuals
- **Content search**: Full-text search through manual content
- **Highlighted results**: Search results include context with highlighted matching terms
